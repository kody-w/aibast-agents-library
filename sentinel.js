/* The Sentinel skill rubric, in the browser.
 *
 * scripts/review_skills.py is the reference implementation. This is the same
 * rubric, client-side, so anyone can run it against their OWN raw skill.md —
 * no clone, no token, no service. Point it at a file, a GitHub raw URL, or a
 * whole repository and it reports what would drift and why.
 *
 * A gate compares this against the Python output for every skill in the
 * library. If the two disagree the rubric is broken, and the build says so.
 *
 * Deterministic residents only. The interpretive ones need a model, and this
 * file deliberately holds no endpoint and no key — the operator attaches their
 * own intelligence, exactly as the pipeline does.
 *
 * Keep in lockstep with scripts/review_skills.py. Both are gated.
 */
(function (global) {
  "use strict";

  var RUBRIC_VERSION = "1.0.0";

  var PRINCIPLES = {
    provenance: "Can a reader tell where this came from and what licence it carries?",
    usability: "Can a model tell when to reach for this, without guessing?",
    determinism: "Would two runs of these steps produce the same thing?",
    safety: "Can following these instructions damage something?",
    completeness: "Is everything needed here, in this one file?"
  };

  var REQUIRED_FRONTMATTER = ["schema", "name", "version", "description",
    "source_url", "source_license", "converted_from"];

  var SEMVER = /^\d+\.\d+\.\d+$/;
  var SECRET_LITERAL = /(api[_-]?key|secret|password|token)\s*[:=]\s*['"]?[A-Za-z0-9_\-]{20,}/i;
  var DESTRUCTIVE = /(rm\s+-rf\s+\/|DROP\s+TABLE|TRUNCATE\s+TABLE|git\s+push\s+--force|Remove-Item\s+-Recurse\s+-Force\s+[A-Za-z]:\\)/i;
  var ABS_PATH = /(\/Users\/[a-z]|\/home\/[a-z]|[A-Za-z]:\\Users\\)/;
  var STEP_LINE = /^[ \t]*(\d+[.)]\s+|[-*]\s+)/gm;
  var EMAIL_RE = /\b[\w.+-]+@([\w-]+\.[\w.]+)\b/g;
  var DEMO_DOMAINS = ["contoso.com", "fabrikam.com", "example.com", "example.org",
    "microsoft.com", "github.com", "localhost"];

  function splitFrontmatter(text) {
    if (text.indexOf("---") !== 0) return { meta: {}, body: text };
    var end = text.indexOf("\n---", 3);
    if (end === -1) return { meta: {}, body: text };
    var meta = {};
    text.slice(3, end).split("\n").forEach(function (line) {
      line = line.trim();
      if (!line || line.indexOf(":") === -1 || line.charAt(0) === "#") return;
      var i = line.indexOf(":");
      meta[line.slice(0, i).trim()] = line.slice(i + 1).trim().replace(/^['"]|['"]$/g, "");
    });
    return { meta: meta, body: text.slice(end + 4).replace(/^\n+/, "") };
  }

  function review(text, name) {
    var sf = splitFrontmatter(text);
    var meta = sf.meta, body = sf.body;
    var checks = [];

    function add(id, principle, level, title, failed, detail, teachable) {
      var c = { id: id, principle: principle, level: level, title: title, passed: !failed };
      if (failed) { c.detail = detail; c.teachable = teachable; }
      checks.push(c);
    }

    /* provenance */
    var missing = REQUIRED_FRONTMATTER.filter(function (k) { return !meta[k]; });
    add("K1", "provenance", "error", "Carries a complete RAPP skill manifest",
      missing.length, "frontmatter missing: " + missing.join(", "),
      "The manifest is what makes a skill discoverable and traceable. Without " +
      "`source_url` and `source_license` a redistributed skill is indistinguishable " +
      "from one we wrote, which is both a licence problem and a credit problem.");

    var noAttrib = body.indexOf("Converted skill") === -1 &&
      body.toLowerCase().indexOf("converted from") === -1;
    add("K2", "provenance", "error", "Credits the original author in the body",
      noAttrib, "no attribution block in the body",
      "Frontmatter is metadata; a reader opening the file sees the body. " +
      "Redistribution with credit means the credit is visible to the person " +
      "reading, not only to the parser.");

    add("K3", "provenance", "warn", "Version is a semantic version",
      !SEMVER.test(String(meta.version || "")), "version is " + JSON.stringify(meta.version),
      "Consumers pin skills. A version that does not sort predictably cannot be " +
      "pinned, so every consumer silently tracks whatever is newest — including " +
      "a breaking change.");

    /* usability */
    var desc = String(meta.description || "");
    add("K4", "usability", "warn", "Description is specific enough to route on",
      desc.length < 80, "description is " + desc.length + " characters",
      "A skill competes for attention against every other skill loaded. A short " +
      "description loses that competition and the skill is never reached for. " +
      "State the trigger and the artifact produced.");

    add("K5", "usability", "warn", "Says when to use it, not only what it is",
      !/##\s*When to use/i.test(body), "no 'When to use this' section",
      "What a skill *is* does not tell a model *when* to invoke it. The trigger " +
      "condition is the single most load-bearing sentence in a skill file, and it " +
      "belongs under its own heading.");

    var tags = meta.tags || "";
    add("K6", "usability", "warn", "Carries tags for discovery",
      !tags || tags === "[]" || tags === "''", "no tags",
      "Tags are how a skill is found by someone who does not already know its " +
      "name — which is everyone, the first time.");

    /* determinism */
    add("K7", "determinism", "error", "States a deterministic contract",
      body.toLowerCase().indexOf("deterministic layer") === -1,
      "no deterministic-layer section",
      "A skill that does not state its inputs, outputs, and verification step " +
      "produces a different result every run, because the model fills the gaps " +
      "differently each time. Stating the contract is what separates a skill " +
      "from a suggestion.");

    STEP_LINE.lastIndex = 0;
    var steps = (body.match(STEP_LINE) || []).length;
    add("K8", "determinism", "warn", "Gives followable steps",
      steps < 3, "only " + steps + " enumerated step(s) found",
      "Prose describing an approach is not a procedure. Numbered steps are what " +
      "make two runs comparable — and what make a failure locatable to a specific " +
      "step rather than to the whole skill.");

    add("K9", "determinism", "warn", "Names a verification step",
      !/verif|confirm|check that|validate/i.test(body), "no verification language in the body",
      "Without a verification step the skill reports success whenever it finishes, " +
      "which is not the same thing. Say what to check before claiming the work is done.");

    /* safety */
    var secret = SECRET_LITERAL.exec(text);
    add("K10", "safety", "error", "No credential literals",
      !!secret, secret ? "credential-shaped literal near offset " + secret.index : "",
      "A key in a public file is compromised on push and stays in git history " +
      "after deletion. Reference the environment variable by name and let the " +
      "operator supply the value.");

    var destructive = DESTRUCTIVE.exec(text);
    add("K11", "safety", "error", "No unguarded destructive command",
      !!destructive, destructive ? "destructive command: " + destructive[0].slice(0, 50) : "",
      "A skill is executed by a model on someone else's machine. A destructive " +
      "command with no confirmation step will eventually run against something " +
      "that mattered. Require explicit confirmation, and scope the target.");

    EMAIL_RE.lastIndex = 0;
    var domains = {}, m;
    while ((m = EMAIL_RE.exec(text)) !== null) {
      if (DEMO_DOMAINS.indexOf(m[1].toLowerCase()) === -1) domains[m[1]] = true;
    }
    var real = Object.keys(domains).sort();
    add("K12", "safety", "warn", "Sample data uses fictional domains",
      real.length, "addresses at: " + real.slice(0, 3).join(", "),
      "Example data in a published skill must be fictional. Anything else is " +
      "personal data that every fork copies forever.");

    /* completeness */
    add("K13", "completeness", "error", "No absolute path from the author's machine",
      ABS_PATH.test(text), "contains an absolute home-directory path",
      "The path exists on exactly one machine. Name the file relative to the " +
      "working directory, or take the location as an input.");

    add("K14", "completeness", "warn", "Substantial enough to act on",
      body.trim().length < 400, "body is " + body.trim().length + " characters",
      "A skill this short is a title with an intention attached. If the procedure " +
      "genuinely fits in a paragraph, it is a note, not a skill — and publishing " +
      "it as one costs the reader a click.");

    // Referenced companion files cannot be resolved from a browser, so this
    // check reports what a local run would resolve rather than guessing.
    var dangling = [];
    var ref = /see\s+(?:the\s+)?[`"']([^`"']+\.(?:md|py|json))[`"']/ig, r;
    while ((r = ref.exec(body)) !== null) dangling.push(r[1]);
    add("K15", "completeness", "warn", "Self-contained: no unresolvable references",
      false, "", "");
    checks[checks.length - 1].unresolvable_here = dangling;

    var weights = { error: 2, warn: 1 };
    var scores = {};
    Object.keys(PRINCIPLES).forEach(function (p) {
      var rel = checks.filter(function (c) { return c.principle === p; });
      var total = 0, got = 0;
      rel.forEach(function (c) { total += weights[c.level]; if (c.passed) got += weights[c.level]; });
      scores[p] = total ? Math.round(100 * got / total) : 100;
    });

    var errors = checks.filter(function (c) { return !c.passed && c.level === "error"; });
    var warns = checks.filter(function (c) { return !c.passed && c.level === "warn"; });
    var vals = Object.keys(scores).map(function (k) { return scores[k]; });
    var overall = Math.round(vals.reduce(function (a, b) { return a + b; }, 0) / vals.length);
    var verdict = errors.length ? "blocked"
      : overall >= 85 ? "review-ready"
      : overall >= 60 ? "needs-work" : "not-ready";

    return {
      slug: name || meta.name || "skill",
      ref: meta.name || name || "skill",
      review_type: "machine",
      subject_kind: "skill",
      rubric_version: RUBRIC_VERSION,
      verdict: verdict,
      overall: overall,
      scores: scores,
      error_count: errors.length,
      warn_count: warns.length,
      checks: checks
    };
  }

  /* Shape a RAW skill into the RAPP format — the same transformation the
   * pipeline applies, so an author can see exactly what changes and why. */
  function toRappSkill(text, opts) {
    opts = opts || {};
    var sf = splitFrontmatter(text);
    var meta = sf.meta, body = sf.body;
    var name = meta.name || opts.name || "untitled-skill";
    var ns = opts.namespace || "@your-org";
    var ref = name.indexOf("@") === 0 ? name : ns + "/" + name.replace(/[^A-Za-z0-9_-]+/g, "_");
    var desc = meta.description || (body.split("\n").filter(Boolean)[0] || "").slice(0, 240);
    var version = SEMVER.test(String(meta.version || "")) ? meta.version : "1.0.0";
    var author = meta.author || opts.author || "unknown";
    var when = meta.agentDescription || desc;

    return "---\n" +
      "schema: rapp-skill/1.0\n" +
      "name: " + ref + "\n" +
      "version: " + version + "\n" +
      "display_name: " + JSON.stringify(meta.display_name || name) + "\n" +
      "description: " + JSON.stringify(desc) + "\n" +
      "author: " + JSON.stringify(author) + "\n" +
      "tags: " + (meta.tags && meta.tags.charAt(0) === "[" ? meta.tags : "[]") + "\n" +
      "category: " + (meta.category || "general") + "\n" +
      "requires_env: []\n" +
      "source_ref: " + ref + "\n" +
      "source_url: " + (opts.sourceUrl || meta.source_url || "") + "\n" +
      "source_license: " + (opts.license || meta.source_license || "UNSPECIFIED") + "\n" +
      "converted_from: " + (opts.convertedFrom || meta.converted_from || "a raw skill file") + "\n" +
      "converted_on: " + (opts.date || "") + "\n" +
      "---\n\n" +
      "# " + (meta.display_name || name) + "\n\n" +
      "> **Converted skill.** This is a RAPP single-file skill converted from\n" +
      "> **" + (opts.convertedFrom || "a raw skill file") + "**, redistributed under\n" +
      "> **" + (opts.license || meta.source_license || "UNSPECIFIED") + "** with attribution. " +
      "Original author: " + author + ".\n>\n" +
      "> Drop this file into your brainstem's skills folder, or read it and run the\n" +
      "> steps yourself. Everything the skill needs is in this one file.\n\n" +
      "## When to use this\n\n" + when + "\n\n" +
      "## The deterministic layer\n\n" +
      "RAPP skills state their contract explicitly, so two runs of the same skill do\n" +
      "the same thing:\n\n" +
      "- **Inputs** — whatever the steps below name. If an input is missing, say so\n" +
      "  and stop rather than guessing.\n" +
      "- **Outputs** — the artifact the steps produce, named where it is written.\n" +
      "- **Verification** — before reporting success, confirm the output exists and\n" +
      "  matches what was asked. A silent partial result is a failure.\n" +
      "- **Configuration** — never hardcode an endpoint, key, or tenant. Read them\n" +
      "  from the environment (`requires_env` above lists what this skill needs).\n\n" +
      "## Skill\n\n" + body.trim() + "\n";
  }

  global.RAPPSentinel = {
    RUBRIC_VERSION: RUBRIC_VERSION,
    PRINCIPLES: PRINCIPLES,
    review: review,
    toRappSkill: toRappSkill,
    splitFrontmatter: splitFrontmatter
  };
})(window);
