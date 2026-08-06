/* Stream large media from a branch, without carrying it in the main clone.

   THE PATTERN, and why it exists.

   Large binaries make a repository expensive to install. Every blob ever
   committed stays in history, so deleting a video from the tip does not make
   `git clone` any cheaper — this library measured 20 MB of tracked files and a
   2.6 GB clone. The install now clones at depth 1, and depth 1 implies
   single-branch: it fetches the tip of ONE branch and nothing else. Objects
   that live only on another branch are never downloaded. Measured: a depth-1
   clone of the code branch is a 3.7 MB .git, and the media branch's blobs are
   not reachable from it at all.

   So the media branch is a second repository without the cost of one. Same
   remote, same permissions, same review — just never in the clone.

   Serving it back: GitHub Pages publishes a single branch, so it cannot serve
   the media branch. Two sources can, and this file tries them in cost order.

   1. jsDelivr (`cdn.jsdelivr.net/gh/owner/repo@branch/path`) returns
      `content-type: video/mp4` with real range support, and is a CDN.
   2. `raw.githubusercontent.com` returns the bytes with
      `access-control-allow-origin: *` and `accept-ranges: bytes`, but labels
      them `application/octet-stream` under `x-content-type-options: nosniff`.

   A note on (2), because the obvious inference is wrong and was believed here
   until it was tested: octet-stream plus nosniff does NOT stop a <video> from
   playing. Measured in Chromium against a real file, a plain `<video src>`
   pointed straight at raw loaded and reported its duration. nosniff constrains
   script and style, not media sniffing. Do not "fix" that with a Blob on the
   assumption that it is broken.

   Blob injection is therefore the FALLBACK, not the mechanism: fetch the bytes,
   wrap them in a Blob whose type we declare, hand over an object URL. It is
   what to reach for when a source mislabels a file in a way a given browser
   does refuse, and it is the only path that lets us set the type ourselves.
   Its cost is real — an object URL has no range requests, so the whole file
   downloads before playback and seeking is not progressive. Right for a 3-4 MB
   demo, wrong for a feature film. Above ~25 MB use a release asset or a CDN.

   PRELOAD, and the bug that hid here. The direct-CDN path resolves by waiting
   for `loadedmetadata`. A `<video preload="none">` never fires it — the media
   element stops after resource selection and fetches nothing until play is
   asked for. So every card timed out (12 s) and fell through to the Blob path,
   which downloads the ENTIRE file. The catalog was quietly pulling megabytes it
   had no use for and giving up range requests to do it. The fix is one line:
   raise `preload` to `metadata` when we attach a source. These files are
   faststart (moov at byte 32, ahead of mdat), so metadata costs ~150 KB, not
   3 MB, and the CDN path — the one with range requests — actually wins.

   THE BUFFER GATE. A media element will start playing the instant it has one
   decodable frame ahead of the playhead, which on a thin connection means it
   starts, stutters, and shows compression artefacts while the buffer catches
   up. Playback here is therefore gated: a play request is held until the
   element reports at least HAVE_FUTURE_DATA *and* has `minBuffer` seconds
   buffered ahead of the playhead at the current quality. The hold is visible
   (a determinate progress readout), escapable ("Play anyway"), and re-arms on
   a mid-playback stall so a stutter costs one pause rather than ten. It gates
   the *buffer*, never the page: nothing is synchronous and nothing blocks
   render. The one non-obvious rule — a paused element eventually stops
   downloading, so the hold must also end on "the browser stopped filling", not
   only on "the target was met" — is spelled out at check(), with the
   measurement that forced it.

   QUALITY LADDER. The gate makes "wait longer" the answer to a slow network;
   the honest other answer is "send fewer bytes". That needs more than one
   encode of each file, and today there is exactly one — see `renditionsFor()`
   for the manifest this reads and what has to be published for the control to
   become interactive. It is deliberately not a menu that pretends.

   Usage:
     RappMedia.configure({ owner: "...", repo: "...", branch: "media" });
     RappMedia.play(videoEl, "media/videos/ask-hr-agent.mp4");
     RappMedia.url("media/videos/x.mp4").then(u => ...);   // object URL
*/
(function (global) {
  "use strict";

  /* Owner and repo are read off the Pages URL rather than hard-coded, so the
     same file works on a fork and on the upstream without an edit. A fork that
     has not published its own media branch still resolves — to its own branch,
     which is the correct failure. */
  function fromLocation() {
    var m = /^([^.]+)\.github\.io$/.exec(global.location.hostname || "");
    if (!m) return null;
    var seg = (global.location.pathname || "/").split("/").filter(Boolean);
    return { owner: m[1], repo: seg.length ? seg[0] : (m[1] + ".github.io") };
  }

  var here = fromLocation() || {};
  var CFG = {
    owner: here.owner || "microsoft",
    repo: here.repo || "aibast-agents-library",
    branch: "media-server",
    /* Where to look when this repo has no media branch of its own yet.
       A fork inherits the pages but not the media, and upstream will not have
       the branch until the migration script has run. Rather than show a broken
       player in the meantime, fall back to the repo that does have it — and
       stop using the fallback the moment the local branch answers, so the
       cutover needs no code change. Set to null once migration is done. */
    fallback: { owner: "kody-w", repo: "aibast-agents-library", branch: "media-server" },
    /* Above this, an object URL is the wrong tool: it buffers the whole file
       and gives up range requests. Fail loudly rather than hang a page. */
    maxBytes: 25 * 1024 * 1024,
    /* Seconds of media that must sit ahead of the playhead before playback is
       allowed to start. Six is a demo-length compromise: long enough that a
       brief dip in throughput is absorbed silently, short enough that the wait
       on a healthy connection is under a second. */
    minBuffer: 6,
    /* Optional ladder manifest on the media branch. Absent today; see
       renditionsFor(). */
    renditionsPath: "media/renditions.json"
  };

  var TYPES = {
    mp4: "video/mp4", m4v: "video/mp4", webm: "video/webm", mov: "video/quicktime",
    mp3: "audio/mpeg", m4a: "audio/mp4", wav: "audio/wav", caf: "audio/x-caf",
    png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg",
    gif: "image/gif", webp: "image/webp", pdf: "application/pdf"
  };

  var cache = {};        /* path -> object URL, so a replay costs nothing */
  var inflight = {};     /* path -> promise, so two players share one fetch */

  function configure(o) {
    for (var k in (o || {})) if (o.hasOwnProperty(k)) CFG[k] = o[k];
    return CFG;
  }

  function mimeFor(path) {
    var ext = String(path).split(".").pop().toLowerCase();
    return TYPES[ext] || "application/octet-stream";
  }

  function rawURL(path, o) {
    o = o || CFG;
    return "https://raw.githubusercontent.com/" + o.owner + "/" + o.repo +
           "/" + o.branch + "/" + String(path).replace(/^\/+/, "");
  }

  /* jsDelivr serves the same branch with a correct Content-Type and real range
     support, so it is the better source when it has the file. It is a cache in
     front of GitHub, not a different truth. Only used as a first try. */
  function cdnURL(path, o) {
    o = o || CFG;
    return "https://cdn.jsdelivr.net/gh/" + o.owner + "/" + o.repo +
           "@" + o.branch + "/" + String(path).replace(/^\/+/, "");
  }

  /* Sources in preference order: this repo's own media branch first, the
     fallback only if there is one. Returning a list rather than a string is
     what lets the cutover happen by data instead of by deploy. */
  function sourcesFor(path) {
    var out = [cdnURL(path), rawURL(path)];
    var f = CFG.fallback;
    if (f && (f.owner !== CFG.owner || f.repo !== CFG.repo || f.branch !== CFG.branch)) {
      out.push(cdnURL(path, f), rawURL(path, f));
    }
    return out;
  }

  function fetchBytes(url, onProgress) {
    return fetch(url, { mode: "cors", cache: "force-cache" }).then(function (r) {
      if (!r.ok) throw new Error(r.status + " " + r.statusText);
      var total = parseInt(r.headers.get("content-length") || "0", 10);
      if (total && total > CFG.maxBytes) {
        throw new Error("file is " + Math.round(total / 1048576) + "MB; over " +
                        Math.round(CFG.maxBytes / 1048576) + "MB use a CDN or a " +
                        "release asset, not an object URL");
      }
      if (!onProgress || !r.body || !total) return r.arrayBuffer();
      /* Streamed read purely so a slow connection can show progress; the bytes
         still all land before playback either way. */
      var reader = r.body.getReader(), chunks = [], got = 0;
      return (function pump() {
        return reader.read().then(function (s) {
          if (s.done) {
            var out = new Uint8Array(got), at = 0;
            chunks.forEach(function (c) { out.set(c, at); at += c.length; });
            return out.buffer;
          }
          chunks.push(s.value); got += s.value.length;
          onProgress(got / total);
          return pump();
        });
      })();
    });
  }

  /* Resolve a path to a playable object URL. */
  function url(path, opts) {
    opts = opts || {};
    if (cache[path]) return Promise.resolve(cache[path]);
    if (inflight[path]) return inflight[path];

    var mime = opts.type || mimeFor(path);
    // Walk the source list so a repo without its own media branch still plays.
    var srcs = sourcesFor(path);
    var p = srcs.reduce(function (chain, u, i) {
      return i === 0 ? fetchBytes(u, opts.onProgress)
                     : chain.catch(function () { return fetchBytes(u, opts.onProgress); });
    }, null)
      .then(function (buf) {
        // The declared type is ours. This is the whole trick: the response may
        // have arrived as application/octet-stream under nosniff, but a Blob we
        // build carries the type we give it, and an object URL from it plays.
        var u = URL.createObjectURL(new Blob([buf], { type: mime }));
        cache[path] = u;
        delete inflight[path];
        return u;
      })
      .catch(function (e) { delete inflight[path]; throw e; });
    inflight[path] = p;
    return p;
  }

  /* ------------------------------------------------------------------ *
   * The quality ladder                                                  *
   * ------------------------------------------------------------------ *

     There is one encode of each demo on the media branch: 960x540, ~110 kbps,
     ~3.2 MB. One encode is not a ladder, and a picker over a single entry is a
     control that lies. So the picker is driven by a manifest that does not
     exist yet, and until it does the player shows a labelled, focusable
     read-out of what is actually being served instead of a <select>.

     To light it up, publish `media/renditions.json` on the media branch beside
     the videos:

       { "schema": "rapp-media-renditions/1.0",
         "videos": {
           "media/videos/ask-hr-agent.mp4": [
             { "label": "540p", "height": 540, "path": "media/videos/540p/ask-hr-agent.mp4" },
             { "label": "360p", "height": 360, "path": "media/videos/360p/ask-hr-agent.mp4" }
           ]
         } }

     Every listed `path` must be a real object on the same branch. Entries are
     offered highest-first alongside "Source", the file named in `data-media`.
     Nothing else has to change here.

     One thing this cannot fix, and it is worth saying plainly rather than
     burying: a lower rendition helps a slow link, it does not help a soft
     picture. The published encodes are 960x540 at ~110 kbps for ~2.5 minutes,
     which is roughly a fifth of the bitrate 540p wants. That softness is in the
     file, so it survives any amount of buffering and any ladder built from
     these masters. Fixing it means re-encoding from the sources at a sane
     bitrate (~1.2-1.8 Mbps for 540p, more for 720p) and republishing. */

  var LADDER = null;
  function renditionsFor(path) {
    if (!LADDER) {
      LADDER = fetch(cdnURL(CFG.renditionsPath), { cache: "force-cache" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .catch(function () { return null; })
        .then(function (d) {
          if (d) return d;
          return fetch(rawURL(CFG.renditionsPath), { cache: "force-cache" })
            .then(function (r) { return r.ok ? r.json() : null; })
            .catch(function () { return null; });
        })
        .then(function (d) { return (d && d.videos) || {}; });
    }
    return LADDER.then(function (v) {
      var list = v[path] || v[String(path).replace(/^\/+/, "")] || [];
      return list.filter(function (r) { return r && r.path && r.label; })
                 .sort(function (a, b) { return (b.height || 0) - (a.height || 0); });
    });
  }

  /* ------------------------------------------------------------------ *
   * Player chrome (styles injected once, so any page that loads this     *
   * file gets a working player without importing a stylesheet)           *
   * ------------------------------------------------------------------ */

  var CSS = [
    ".rm-shell{position:relative;display:block;width:100%;height:100%}",
    ".rm-shell>video{display:block}",
    ".rm-veil{position:absolute;inset:0;display:none;flex-direction:column;",
      "align-items:center;justify-content:center;gap:8px;padding:12px;",
      "background:rgba(0,0,0,.62);color:#fff;font:600 12px/1.4 'Segoe UI',",
      "-apple-system,system-ui,sans-serif;text-align:center;z-index:2}",
    ".rm-shell[data-play-state='buffering'] .rm-veil{display:flex}",
    ".rm-shell[data-media-state='error'] .rm-veil{display:flex}",
    ".rm-bar{width:min(180px,70%);height:3px;border-radius:3px;background:rgba(255,255,255,.28);overflow:hidden}",
    ".rm-bar i{display:block;height:100%;width:0;background:#fff;transition:width .18s linear}",
    ".rm-skip{border:1px solid rgba(255,255,255,.5);background:transparent;color:#fff;",
      "border-radius:5px;padding:3px 9px;font:600 11px/1 inherit;cursor:pointer}",
    ".rm-skip:hover{background:rgba(255,255,255,.16)}",
    ".rm-skip:focus-visible,.rm-q:focus-visible{outline:2px solid #fff;outline-offset:2px}",
    ".rm-qwrap{position:absolute;top:7px;right:7px;z-index:3}",
    ".rm-q{background:rgba(0,0,0,.66);color:#fff;border:1px solid rgba(255,255,255,.34);",
      "border-radius:5px;padding:2px 6px;font:600 10.5px/1.5 'Segoe UI',-apple-system,system-ui,sans-serif;",
      "letter-spacing:.03em;display:inline-block;cursor:pointer}",
    "span.rm-q{cursor:default;opacity:.82}",
    ".rm-sr{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;",
      "clip:rect(0 0 0 0);white-space:nowrap;border:0}"
  ].join("");

  function ensureCSS() {
    if (!global.document || document.getElementById("rm-media-css")) return;
    var s = document.createElement("style");
    s.id = "rm-media-css";
    s.textContent = CSS;
    (document.head || document.documentElement).appendChild(s);
  }

  /* ------------------------------------------------------------------ *
   * The buffer gate                                                     *
   * ------------------------------------------------------------------ */

  /* Seconds already buffered ahead of the playhead, in the range that
     contains it. A range that ends before the playhead is worthless, and a
     range that starts after it is a seek away, so neither counts. */
  function bufferedAhead(el) {
    var t = el.currentTime || 0, b = el.buffered, i;
    if (!b) return 0;
    for (i = 0; i < b.length; i++) {
      if (b.start(i) <= t + 0.25 && b.end(i) > t) return b.end(i) - t;
    }
    return 0;
  }

  /* How much we insist on. Clamped by what is left of the file, so the last
     seconds of a clip are not an unsatisfiable demand. */
  function needFor(el, want) {
    var d = el.duration, t = el.currentTime || 0;
    if (isFinite(d) && d > 0) {
      var left = d - t;
      if (left <= 0) return 0;
      return Math.min(want, Math.max(0, left - 0.05));
    }
    return want;
  }

  /* Two conditions, not one. readyState alone is the browser's optimism —
     HAVE_FUTURE_DATA means "a frame or two", which is exactly the state that
     starts and immediately stalls. The buffered-seconds test is the real one;
     readyState is there so a decodable-frame guarantee backs it. */
  function gateReady(el, want) {
    return el.readyState >= 3 /* HAVE_FUTURE_DATA */ &&
           bufferedAhead(el) >= needFor(el, want) - 0.01;
  }

  function setPlayState(el, state) {
    el.setAttribute("data-play-state", state);
    var sh = el.__rmShell;
    if (sh) sh.setAttribute("data-play-state", state);
  }

  function qualityLabel(el) {
    if (el.__rmPick && el.__rmPick.label) return el.__rmPick.label;
    return el.videoHeight ? el.videoHeight + "p" : "source";
  }

  function gate(el, opts) {
    opts = opts || {};
    if (el.__rmGate) return el.__rmGate;
    if (!el.tagName || !/^(VIDEO|AUDIO)$/.test(el.tagName)) return null;

    var want = opts.minBuffer != null ? opts.minBuffer : CFG.minBuffer;
    var g = {
      want: want, pending: false, releasing: false, selfPause: false,
      bypass: false, timer: 0, reason: null,
      /* How long the buffer may sit still before the hold is treated as
         finished rather than slow. See the note on release(). */
      stallMs: opts.stallMs != null ? opts.stallMs : 1500,
      lastAhead: -1, lastGrow: 0
    };
    el.__rmGate = g;

    function paint() {
      var need = needFor(el, g.want);
      var pct = need <= 0 ? 1 : Math.max(0, Math.min(1, bufferedAhead(el) / need));
      var sh = el.__rmShell;
      if (sh && sh.__rmFill) {
        sh.__rmFill.style.width = (pct * 100).toFixed(0) + "%";
        sh.__rmTxt.textContent = "Buffering " + qualityLabel(el) + " · " +
                                 (pct * 100).toFixed(0) + "%";
        sh.__rmVeil.setAttribute("aria-valuenow", (pct * 100).toFixed(0));
      }
      return pct;
    }

    function stop() { if (g.timer) { clearInterval(g.timer); g.timer = 0; } }

    function release(why) {
      if (!g.pending) return;
      g.pending = false;
      g.reason = why || "buffered";
      stop();
      setPlayState(el, "playing");
      g.releasing = true;
      var p = el.play();
      if (p && p.catch) p.catch(function () { setPlayState(el, "paused"); });
      global.setTimeout(function () { g.releasing = false; }, 0);
    }

    /* The ceiling, measured, because it is what makes a naive buffer gate hang
       forever rather than merely wait:

       A PAUSED media element does not keep downloading. Without MSE there is no
       way to ask for more; Chromium fills its own modest prefetch target and
       then suspends the request. Throttled to 48 KB/s against a real 187 kbps
       demo, a paused element parked at 2.3 s of buffer and grew by nothing over
       the next 25 s. At 12 KB/s — well under the content's own bitrate, so
       readyState never reached HAVE_ENOUGH_DATA — it parked at 2.26 s and held
       for 30 s. `minBuffer` is therefore a target, not a promise: past the
       browser's cap, waiting stops buying anything, because nothing more is
       coming until playback resumes and pulls it.

       So the hold ends on either of two facts:
         - the target was met, or
         - the buffer stopped growing for `stallMs` while the element has
           decodable data ahead of the playhead (HAVE_FUTURE_DATA). That is the
           browser saying "this is all you get while paused".
       Either way the viewer starts with every second the platform was willing
       to hand over, instead of the single frame a bare <video> starts on.
       `g.reason` records which of the two ended it. */
    function check() {
      if (!g.pending) return;
      paint();
      if (g.bypass) return release("bypass");
      if (gateReady(el, g.want)) return release("buffered");

      var now = Date.now(), ahead = bufferedAhead(el);
      if (ahead > g.lastAhead + 0.01) { g.lastAhead = ahead; g.lastGrow = now; }
      else if (el.readyState >= 3 && now - g.lastGrow > g.stallMs) {
        release("browser-capped");
      }
    }

    function hold() {
      if (g.pending) return;
      g.pending = true;
      g.reason = null;
      g.lastAhead = bufferedAhead(el);
      g.lastGrow = Date.now();
      /* Only now is the whole file worth wanting. Until a play was asked for,
         `metadata` was the right appetite. */
      if (el.preload !== "auto") el.preload = "auto";
      g.selfPause = true;
      el.pause();
      setPlayState(el, "buffering");
      paint();
      if (el.readyState === 0) { try { el.load(); } catch (e) {} }
      stop();
      /* `progress` is emitted at the browser's discretion and can go quiet for
         a second at a time; a slow poll keeps the read-out honest and is the
         only thing that ticks when a range request lands whole. */
      g.timer = global.setInterval(check, 250);
    }

    ["progress", "canplay", "canplaythrough", "loadeddata", "timeupdate",
     "durationchange", "seeked"].forEach(function (ev) {
      el.addEventListener(ev, check);
    });

    el.addEventListener("play", function () {
      if (g.releasing) return;
      if (g.bypass || gateReady(el, g.want)) { setPlayState(el, "playing"); return; }
      hold();
    });

    el.addEventListener("pause", function () {
      if (g.selfPause) { g.selfPause = false; return; }
      /* A real pause during the hold is a cancellation, not a stall. */
      if (g.pending) { g.pending = false; stop(); }
      if (!el.ended) setPlayState(el, "paused");
    });

    /* A stall mid-playback gets the same treatment as a cold start: hold once
       and refill, rather than let it stutter its way forward. */
    el.addEventListener("waiting", function () {
      if (el.paused || g.bypass) return;
      hold();
    });

    el.addEventListener("playing", function () { if (!g.pending) setPlayState(el, "playing"); });
    el.addEventListener("ended", function () { stop(); setPlayState(el, "idle"); });

    g.skip = function () { g.bypass = true; release("bypass"); };
    g.rearm = function () { g.bypass = false; };
    setPlayState(el, "idle");
    return g;
  }

  /* ------------------------------------------------------------------ *
   * Shell: veil (buffering read-out) + quality control                  *
   * ------------------------------------------------------------------ */

  function mount(el, path, opts) {
    if (el.__rmShell) return el.__rmShell;
    if (!el.parentNode || !el.tagName || el.tagName !== "VIDEO") return null;
    ensureCSS();

    var sh = document.createElement("div");
    sh.className = "rm-shell";
    sh.setAttribute("data-play-state", "idle");
    el.parentNode.insertBefore(sh, el);
    sh.appendChild(el);
    el.__rmShell = sh;

    var veil = document.createElement("div");
    veil.className = "rm-veil";
    veil.setAttribute("role", "progressbar");
    veil.setAttribute("aria-live", "polite");
    veil.setAttribute("aria-valuemin", "0");
    veil.setAttribute("aria-valuemax", "100");
    veil.setAttribute("aria-label", "Buffering before playback");
    var txt = document.createElement("span");
    txt.textContent = "Buffering…";
    var bar = document.createElement("div"); bar.className = "rm-bar";
    var fill = document.createElement("i"); bar.appendChild(fill);
    var skip = document.createElement("button");
    skip.type = "button"; skip.className = "rm-skip";
    skip.textContent = "Play anyway";
    skip.setAttribute("aria-label", "Start playing now without waiting for the buffer");
    skip.addEventListener("click", function (e) {
      e.preventDefault(); e.stopPropagation();
      if (el.__rmGate) el.__rmGate.skip();
    });
    veil.appendChild(txt); veil.appendChild(bar); veil.appendChild(skip);
    sh.appendChild(veil);
    sh.__rmVeil = veil; sh.__rmTxt = txt; sh.__rmFill = fill;

    var qwrap = document.createElement("div");
    qwrap.className = "rm-qwrap";
    sh.appendChild(qwrap);
    sh.__rmQ = qwrap;
    /* Static read-out first, synchronously. Looking the manifest up is a
       network round trip that, in the steady state, is a 404 — waiting on it
       would leave the player with no quality read-out at all for as long as a
       CDN takes to say "no". Draw the truth we already have, then upgrade. */
    staticQuality(el);
    upgradeQuality(el, path, opts);
    return sh;
  }

  /* Shape one: no alternate renditions. A <select> here would be a menu with a
     single entry that changes nothing, so this is a read-out — focusable and
     labelled with the reason, but not pretending to be a choice. */
  function staticQuality(el) {
    var sh = el.__rmShell;
    if (!sh || !sh.__rmQ || sh.__rmLadder) return;
    var q = sh.__rmQ;
    q.innerHTML = "";
    var note = document.createElement("span");
    note.className = "rm-q";
    note.tabIndex = 0;
    note.setAttribute("role", "note");
    var h = el.videoHeight || 0;
    var shown = h ? h + "p" : "source";
    note.textContent = shown;
    note.title = "Only the source encode is published for this demo (" + shown +
      "). Alternate resolutions become selectable here as soon as a rendition " +
      "ladder is published on the media branch.";
    note.setAttribute("aria-label", "Video quality: " + shown +
      ", source encode. No alternate resolutions are published for this video.");
    q.appendChild(note);
    /* videoHeight is unknown until metadata lands; relabel once it does. */
    if (!h) el.addEventListener("loadedmetadata", function once () {
      el.removeEventListener("loadedmetadata", once);
      staticQuality(el);
    });
  }

  /* Shape two: a ladder was published. Only then does a real control appear. */
  function upgradeQuality(el, path, opts) {
    var sh = el.__rmShell;
    if (!sh || !sh.__rmQ) return;
    renditionsFor(path).then(function (list) {
      var q = sh.__rmQ;
      if (!list.length) return;   /* stay a read-out */
      sh.__rmLadder = true;
      q.innerHTML = "";

      var id = "rmq-" + Math.random().toString(36).slice(2, 8);
      var lab = document.createElement("label");
      lab.className = "rm-sr"; lab.setAttribute("for", id);
      lab.textContent = "Video quality";
      var sel = document.createElement("select");
      sel.className = "rm-q"; sel.id = id;
      sel.setAttribute("aria-label", "Video quality");
      sel.title = "Lower the resolution if the demo is not loading fast enough.";

      var src = document.createElement("option");
      src.value = ""; src.textContent = "Source";
      sel.appendChild(src);
      list.forEach(function (r, i) {
        var o = document.createElement("option");
        o.value = String(i); o.textContent = r.label;
        sel.appendChild(o);
      });
      sel.value = el.__rmPick ? String(list.indexOf(el.__rmPick)) : "";
      sel.addEventListener("change", function () {
        var pick = sel.value === "" ? null : list[parseInt(sel.value, 10)];
        switchTo(el, path, pick, opts);
      });
      q.appendChild(lab); q.appendChild(sel);
    });
  }

  /* Swap the source under a running player: keep the playhead, keep the
     intent, and let the gate refill before anything is shown moving. */
  function switchTo(el, path, rend, opts) {
    var at = el.currentTime || 0;
    var wasPlaying = !el.paused && !el.ended;
    el.__rmPick = rend || null;
    if (el.__rmGate) el.__rmGate.rearm();
    el.src = cdnURL(rend ? rend.path : path);
    try { el.load(); } catch (e) {}
    function off() {
      el.removeEventListener("loadedmetadata", ok);
      el.removeEventListener("error", bad);
    }
    function ok() {
      off();
      try { el.currentTime = at; } catch (e) {}
      if (wasPlaying) { var p = el.play(); if (p && p.catch) p.catch(function () {}); }
    }
    /* A rendition listed in the manifest but missing from the branch must not
       leave the viewer with a dead player. Fall back to the file we know is
       there — the one named in data-media — rather than to an error. */
    function bad() {
      off();
      if (rend) switchTo(el, path, null, opts);
    }
    el.addEventListener("loadedmetadata", ok);
    el.addEventListener("error", bad);
    return el.src;
  }

  /* Point a <video>/<audio>/<img> at a branch-hosted file. */
  function play(el, path, opts) {
    opts = opts || {};
    if (!el) return Promise.reject(new Error("no element"));
    el.setAttribute("data-media-state", "loading");

    /* Cheapest path first: let the element stream the CDN directly, which
       keeps range requests and starts playing before the file is complete.
       Only if the element rejects it do we buy the bytes and retype them. */
    if (!opts.forceBlob && el.tagName && /^(VIDEO|AUDIO)$/.test(el.tagName)) {
      if (opts.gate !== false) gate(el, opts);
      /* preload="none" would leave loadedmetadata unfired forever and send
         every element down the Blob path on a 12 s timeout. metadata is the
         smallest appetite that still lets the direct source prove itself. */
      if (el.preload === "none" || !el.preload) el.preload = "metadata";
      return new Promise(function (resolve) {
        var done = false;
        function ok() { if (done) return; done = true; cleanup();
          el.setAttribute("data-media-state", "ready"); resolve(el.src); }
        function bad() {
          if (done) return;
          // Try the next source before giving up on streaming altogether.
          if (el.__rmNext && el.__rmNext()) return;
          done = true; cleanup();
          resolve(blobPlay(el, path, opts));
        }
        function cleanup() {
          el.removeEventListener("loadedmetadata", ok);
          el.removeEventListener("error", bad);
        }
        el.addEventListener("loadedmetadata", ok);
        el.addEventListener("error", bad);
        // Same order for the direct-stream path: own branch, then fallback.
        var list = sourcesFor(path), at = 0;
        el.__rmNext = function () {
          at += 1;
          if (at >= list.length) return false;
          el.src = list[at];
          return true;
        };
        el.src = list[0];
        setTimeout(bad, opts.timeout || 12000);
      });
    }
    return blobPlay(el, path, opts);
  }

  function blobPlay(el, path, opts) {
    opts = opts || {};
    return url(path, opts).then(function (u) {
      el.src = u;
      el.setAttribute("data-media-state", "ready");
      if (el.__rmShell) el.__rmShell.setAttribute("data-media-state", "ready");
      if (opts.autoplay && el.play) { var r = el.play(); if (r && r.catch) r.catch(function () {}); }
      return u;
    }).catch(function (e) {
      var msg = e && e.message ? e.message : String(e);
      el.setAttribute("data-media-state", "error");
      el.setAttribute("data-media-error", msg);
      var sh = el.__rmShell;
      if (sh) {
        sh.setAttribute("data-media-state", "error");
        if (sh.__rmTxt) sh.__rmTxt.textContent = "This demo could not be loaded.";
        if (sh.__rmFill) sh.__rmFill.style.width = "0%";
      }
      throw e;
    });
  }

  /* Wire every [data-media] element on the page. Lazy by default: a catalog of
     forty-eight demos must not fetch forty-eight files to render. */
  function bind(root, opts) {
    opts = opts || {};
    var nodes = (root || document).querySelectorAll("[data-media]");
    var out = [];
    Array.prototype.forEach.call(nodes, function (el) {
      var path = el.getAttribute("data-media");
      if (!path || el.getAttribute("data-media-state")) return;
      /* The shell is built now, synchronously, even though the bytes are not
         requested until the card scrolls into view: the buffering read-out and
         the quality read-out have to exist before there is anything to say. */
      if (opts.chrome !== false) mount(el, path, opts);
      if (opts.eager || !("IntersectionObserver" in global)) {
        out.push(play(el, path, opts));
        return;
      }
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          io.disconnect();
          play(el, path, opts);
        });
      }, { rootMargin: "200px" });
      io.observe(el);
    });
    return out;
  }

  function revoke() {
    Object.keys(cache).forEach(function (k) {
      try { URL.revokeObjectURL(cache[k]); } catch (e) {}
      delete cache[k];
    });
  }

  global.RappMedia = {
    configure: configure, url: url, play: play, bind: bind,
    rawURL: rawURL, cdnURL: cdnURL, revoke: revoke, config: CFG,
    gate: gate, renditions: renditionsFor, bufferedAhead: bufferedAhead
  };
})(window);

/* Engagement — plays, likes and comments, read from the static API.

   The counts come from state/video_engagement.json via api/v1, built by
   scripts/video_engagement.py from GitHub Discussions. Nothing is written from
   the browser: there is no backend to write to, and a number a visitor can
   inflate is worse than no number.

   A play is a reaction on a pinned tally comment, so it means "one signed-in
   person marked this", not "one hit". The copy says exactly that rather than
   implying traffic. Pressing play opens that comment in a new tab so marking it
   costs one click, and the video plays either way — the count is never a toll
   gate on watching. */
(function (global) {
  "use strict";
  var DATA = null, LOADING = null;

  function load() {
    if (DATA) return Promise.resolve(DATA);
    if (LOADING) return LOADING;
    LOADING = fetch("api/v1/video-engagement.json", { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { DATA = d || { videos: {} }; return DATA; })
      .catch(function () { DATA = { videos: {} }; return DATA; });
    return LOADING;
  }

  function nfmt(n) {
    n = n || 0;
    return n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + "k" : String(n);
  }

  function statsFor(slug) {
    return load().then(function (d) {
      return (d.videos || {})[slug] || { likes: 0, plays: 0, comments: 0, thread: false };
    });
  }

  /* Render a YouTube-shaped bar under a video and wire the play signal. */
  function engage(container, slug, opts) {
    opts = opts || {};
    if (!container) return Promise.resolve(null);
    return statsFor(slug).then(function (s) {
      var bar = document.createElement("div");
      bar.className = "vid-engage";
      bar.innerHTML =
        '<span class="ve-stat" title="People who marked that they watched this. ' +
          'One per GitHub account, so it is not a hit count.">▶ ' +
          nfmt(s.plays) + ' played</span>' +
        '<span class="ve-stat">♥ ' + nfmt(s.likes) + ' likes</span>' +
        '<span class="ve-stat">💬 ' + nfmt(s.comments) + ' comments</span>' +
        (s.thread
          ? '<a class="ve-act" target="_blank" rel="noopener" href="' + s.url + '">Like</a>' +
            '<a class="ve-act" target="_blank" rel="noopener" href="' + s.url + '">Comment</a>'
          : '<span class="ve-stat ve-muted">Thread not open yet</span>');
      container.appendChild(bar);

      var vid = container.querySelector("video");
      if (vid && s.play_url) {
        // First play only, and never blocking: the tab opens alongside, the
        // video keeps playing. A count that interrupts watching is worse than
        // no count.
        vid.addEventListener("play", function once() {
          vid.removeEventListener("play", once);
          if (opts.silent) return;
          try { global.open(s.play_url, "_blank", "noopener"); } catch (e) {}
        });
      }
      return s;
    });
  }

  global.RappMedia.engage = engage;
  global.RappMedia.stats = statsFor;
})(window);
