(function () {
  "use strict";

  var ACK_VERSION = "aibast-download-ack:v1";
  var locked = ["pointer-events-none", "opacity-50", "cursor-not-allowed"];
  var messages = {
    agent: "This agent.py is community-provided, code-bearing code. It can run with your permissions or affect your environment; review it and download only from a trusted source.",
    skill: "This SKILL.md is community-provided instructions that can influence an agent's behavior and permissions. Review it and download only from a trusted source.",
    solution: "This Copilot Studio solution ZIP can configure components in an environment. Review it and download only from a trusted source."
  };

  function kindOf(link) {
    return link.getAttribute("data-download-kind") || "agent";
  }

  function gate() {
    return document.getElementById("trust-gate");
  }

  function ensureGate() {
    var existing = gate();
    if (existing) return existing;
    var section = document.createElement("section");
    section.id = "trust-gate";
    section.setAttribute("aria-labelledby", "trust-gate-title");
    section.setAttribute("data-ack-version", ACK_VERSION);
    section.innerHTML =
      '<h2 id="trust-gate-title">Add only what you trust</h2>' +
      '<p id="trust-artifact" role="status" aria-live="polite">Choose a gated download to see its artifact-specific trust boundary.</p>' +
      '<label for="trust-ack"><input type="checkbox" id="trust-ack">' +
      '<span><strong>Review required.</strong> I understand that a gated artifact may be community-provided and code-bearing, can run with my permissions or affect my environment, and should be downloaded only from a trusted source. Acknowledgement version: ' +
      ACK_VERSION +
      '.</span></label>';
    document.body.appendChild(section);
    return section;
  }

  function acknowledgement() {
    return document.getElementById("trust-ack");
  }

  function describe(link) {
    var artifact = document.getElementById("trust-artifact");
    if (artifact) artifact.textContent = messages[kindOf(link)] || messages.agent;
  }

  function links() {
    return document.querySelectorAll("[data-download-gated]");
  }

  function sync() {
    var ack = acknowledgement();
    if (!ack) return;
    var unlocked = ack.checked;
    links().forEach(function (link) {
      locked.forEach(function (name) {
        link.classList.toggle(name, !unlocked);
      });
      if (unlocked) {
        link.removeAttribute("aria-disabled");
        if (link.tagName === "BUTTON") link.disabled = false;
      } else {
        link.setAttribute("aria-disabled", "true");
        if (link.tagName === "BUTTON") link.disabled = true;
      }
    });
  }

  function register(link) {
    if (!link || !link.matches || !link.matches("[data-download-gated]")) return;
    if (!link.getAttribute("aria-disabled")) link.setAttribute("aria-disabled", "true");
    locked.forEach(function (name) { link.classList.add(name); });
    link.addEventListener("focus", function () { describe(link); });
  }

  function init() {
    ensureGate();
    var ack = acknowledgement();
    if (!ack || !gate()) return;
    ack.checked = false;
    links().forEach(register);
    document.addEventListener("click", function (event) {
      var link = event.target.closest && event.target.closest("[data-download-gated]");
      if (link && !ack.checked) {
        event.preventDefault();
        describe(link);
        ack.focus();
      }
    }, true);
    document.addEventListener("keydown", function (event) {
      var link = event.target.closest && event.target.closest("[data-download-gated]");
      if (link && !ack.checked && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        describe(link);
        ack.focus();
      }
    }, true);
    document.addEventListener("focusin", function (event) {
      var link = event.target.closest && event.target.closest("[data-download-gated]");
      if (link) describe(link);
    });
    ack.addEventListener("change", sync);
    new MutationObserver(function (records) {
      records.forEach(function (record) {
        record.addedNodes.forEach(function (node) {
          if (!(node instanceof Element)) return;
          if (node.matches("[data-download-gated]")) register(node);
          node.querySelectorAll && node.querySelectorAll("[data-download-gated]").forEach(register);
        });
      });
      sync();
    }).observe(document.documentElement, { childList: true, subtree: true });
    sync();
  }

  window.AibastTrustGate = { init: init, register: register, sync: sync };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
