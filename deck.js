/* RAPP deck export — a real PowerPoint, built from the same static data the
   page you are looking at was rendered from.

   This replaces "Print / save as PDF". A printed page is a picture of a
   document: nobody can retitle a slide, drop one, paste a panel into their own
   deck, or put it in front of a customer without it looking like a printout.
   Everything here is a NATIVE slide — real text boxes, real shapes, real
   colours — so it opens in PowerPoint as something a person can edit.

   The pattern is the one used by the Copilot Studio streaming tech note:
   PptxGenJS in the browser, no server, no upload, nothing leaves the machine.
   The library is vendored rather than pulled from a CDN because the people who
   most need to hand a deck to a customer are the ones behind a network that
   blocks CDNs.

   Data in, slides out. The preview on the page and the exported deck are two
   renderings of one source, so they cannot drift.

   Usage:
     RappDeck.export({ kind, entry, story, onStatus })
*/
(function (global) {
  "use strict";

  /* AIBAST palette, sampled from the recordings the films are built on. */
  var INK = "1A1D3F";
  var STAGE = "070F26";
  var PINK = "E2669A";
  var VIOLET = "A86EE0";
  var BLUE = "5B5FC7";
  var MUTED = "6B7280";
  var PAPER = "FFFFFF";
  var FONT = "Segoe UI";

  var W = 13.333, H = 7.5;              /* 16:9, in inches */

  function txt(s) { return String(s == null ? "" : s); }

  function titleCase(s) {
    return txt(s).replace(/[-_]+/g, " ").replace(/\b\w/g, function (c) {
      return c.toUpperCase();
    });
  }

  function displayName(kind, entry, story) {
    if (story && story.subject && story.subject.display_name) {
      return story.subject.display_name;
    }
    var n = entry && (entry.display_name || entry.name || entry.slug || entry.id);
    return titleCase(String(n || "Agent").split("/").pop());
  }

  /* --- slide furniture, so every slide is laid out the same way ------------ */

  function darkSlide(pptx) {
    var s = pptx.addSlide();
    s.background = { color: STAGE };
    return s;
  }

  function lightSlide(pptx) {
    var s = pptx.addSlide();
    s.background = { color: PAPER };
    return s;
  }

  function heading(s, text, opts) {
    opts = opts || {};
    s.addText(txt(text), {
      x: 0.62, y: opts.y == null ? 0.55 : opts.y, w: W - 1.24, h: 0.8,
      fontFace: FONT, fontSize: opts.size || 30, bold: true,
      color: opts.dark ? PAPER : INK, valign: "middle"
    });
  }

  function kicker(s, text, dark) {
    s.addText(txt(text).toUpperCase(), {
      x: 0.62, y: 0.22, w: W - 1.24, h: 0.3,
      fontFace: FONT, fontSize: 11, bold: true, charSpacing: 1.2,
      color: dark ? PINK : BLUE
    });
  }

  function footer(s, n, dark) {
    s.addText("Microsoft AI Business Applications Specialist Team (AIBAST)", {
      x: 0.62, y: H - 0.62, w: 8.5, h: 0.3,
      fontFace: FONT, fontSize: 9, color: dark ? "8C93B5" : MUTED
    });
    if (n != null) {
      s.addText(String(n), {
        x: W - 1.24, y: H - 0.62, w: 0.62, h: 0.3, align: "right",
        fontFace: FONT, fontSize: 9, color: dark ? "8C93B5" : MUTED
      });
    }
  }

  function bulletList(s, items, o) {
    o = o || {};
    /* bullet must ride EACH item: a box-level bullet only marks the first
       paragraph once breakLine splits the rest into their own paragraphs */
    var rows = (items || []).filter(Boolean).slice(0, o.max || 8).map(function (i) {
      return { text: txt(i), options: {
        breakLine: true, bullet: { characterCode: "2022", indent: 12 }
      } };
    });
    if (!rows.length) return;
    s.addText(rows, {
      x: o.x == null ? 0.62 : o.x, y: o.y == null ? 1.6 : o.y,
      w: o.w == null ? W - 1.24 : o.w, h: o.h == null ? 4.4 : o.h,
      fontFace: FONT, fontSize: o.size || 16, color: o.color || INK,
      lineSpacingMultiple: 1.25, valign: "top"
    });
  }

  /* Jewels — the stat chips the MVP confirmation deck carries; here they are
     grounded in what is knowable about a library agent, never invented. */
  function jewelRow(pptx, s, jewels, o) {
    o = o || {};
    var live = (jewels || []).filter(function (j) { return j && j.big; });
    if (!live.length) return;
    var y = o.y == null ? 5.3 : o.y, cw = o.cw || 2.7, gap = 0.3;
    live.slice(0, 4).forEach(function (j, i) {
      var x = 0.62 + i * (cw + gap);
      s.addShape(pptx.ShapeType.roundRect, {
        x: x, y: y, w: cw, h: 1.15, rectRadius: 0.14,
        fill: { color: o.dark ? "1B2148" : "EFF3FE" }, line: { type: "none" }
      });
      s.addText([
        { text: txt(j.big), options: { fontSize: 24, bold: true,
          color: o.dark ? "F1B7D4" : BLUE, breakLine: true } },
        { text: txt(j.label), options: { fontSize: 10.5,
          color: o.dark ? "C7CBE6" : MUTED } }
      ], {
        x: x + 0.18, y: y, w: cw - 0.36, h: 1.15, valign: "middle",
        fontFace: FONT
      });
    });
  }

  /* --- the slides --------------------------------------------------------- */

  function titleSlide(pptx, name, entry, kind) {
    var s = darkSlide(pptx);
    /* The gradient lozenge the films open on, as a real shape. */
    s.addShape(pptx.ShapeType.roundRect, {
      x: 1.6, y: 2.35, w: W - 3.2, h: 2.1, rectRadius: 0.42,
      fill: { type: "solid", color: PINK },
      line: { type: "none" }
    });
    s.addShape(pptx.ShapeType.roundRect, {
      x: 1.6, y: 2.35, w: W - 3.2, h: 2.1, rectRadius: 0.42,
      fill: { type: "solid", color: VIOLET, transparency: 45 },
      line: { type: "none" }
    });
    s.addText(name + (/agent$/i.test(name) ? "" : (kind === "skill" ? " Skill" : " Agent")), {
      x: 1.8, y: 2.35, w: W - 3.6, h: 2.1, align: "center", valign: "middle",
      fontFace: FONT, fontSize: 40, bold: true, color: PAPER
    });
    s.addText("Microsoft AIBAST · RAPP Agents Library", {
      x: 0.62, y: 5.05, w: W - 1.24, h: 0.4, align: "center",
      fontFace: FONT, fontSize: 14, color: "C7CBE6"
    });
    if (entry && entry.category) {
      s.addText(titleCase(entry.category), {
        x: 0.62, y: 5.5, w: W - 1.24, h: 0.35, align: "center",
        fontFace: FONT, fontSize: 12, color: "8C93B5"
      });
    }
    footer(s, null, true);
  }

  function whatItIsSlide(pptx, pptxName, entry, n) {
    var s = lightSlide(pptx);
    kicker(s, "What it is");
    heading(s, pptxName);
    s.addText(txt(entry && entry.description) || "A single-file RAPP agent.", {
      x: 0.62, y: 1.5, w: W - 1.24, h: 1.1,
      fontFace: FONT, fontSize: 17, color: INK, valign: "top"
    });
    s.addText("Who it is for", {
      x: 0.62, y: 2.8, w: 5.6, h: 0.3, fontFace: FONT, fontSize: 12,
      bold: true, color: BLUE
    });
    bulletList(s, (entry && entry.tags || []).slice(0, 5).length
      ? (entry.tags || []).slice(0, 5) : ["Any RAPP operator"],
      { y: 3.15, w: 5.6, h: 2.2, size: 14 });
    s.addText("What you get", {
      x: 6.6, y: 2.8, w: 6.1, h: 0.3, fontFace: FONT, fontSize: 12,
      bold: true, color: BLUE
    });
    bulletList(s, [
      "A single file you can drop onto a brainstem",
      "Registers as a tool automatically — no restart",
      "Runs on all three tiers: local, Azure Functions, Copilot Studio"
    ], { x: 6.6, y: 3.15, w: 6.1, h: 2.2, size: 14 });
    var kb = entry && entry._size_kb;
    var tier = entry && entry.quality_tier;
    var params = paramNames(entry);
    jewelRow(pptx, s, [
      { big: kb ? Math.round(kb) + " KB" : "1",
        label: "single file to install" },
      { big: "3", label: "tiers it runs on" },
      { big: String((entry && entry.requires_env || []).length),
        label: "config keys required" },
      tier ? { big: titleCase(tier), label: "quality tier" }
           : { big: String(params.length), label: "parameters" }
    ], { y: 5.35 });
    footer(s, n);
  }

  function paramNames(entry) {
    try {
      var props = entry && entry.metadata && entry.metadata.parameters &&
        entry.metadata.parameters.properties;
      return props ? Object.keys(props) : (entry && entry.parameters) || [];
    } catch (e) { return []; }
  }

  /* The "Example architecture" slide (pattern: the Smart Onboarding Agent
     architecture slide) — where the agent sits between the person and the
     data, as labeled boxes a customer architect can lift into their own
     deck. Content is grounded in the entry and the film's overview panels. */
  function architectureSlide(pptx, name, entry, panels, n) {
    var s = lightSlide(pptx);
    kicker(s, "Example architecture");
    heading(s, "Where " + name + " sits");

    var lanes = [
      { title: "The person",
        body: (panels && panels["Flow of work"] || []).slice(0, 3),
        fallback: ["Microsoft Teams", "Microsoft 365 Copilot"], fill: "EFF3FE" },
      { title: name,
        body: [txt(entry && entry.description).split(". ")[0] ||
               "A single-file RAPP agent"],
        fallback: [], fill: "FBE9F7" },
      { title: "The runtime",
        body: ["Brainstem (local)", "Azure Functions",
               "Copilot Studio"], fallback: [], fill: "F1ECFB" },
      { title: "The sources",
        body: (panels && panels["Sources"] || []).slice(0, 4),
        fallback: ["The agent's packaged records"], fill: "EAF7F0" }
    ];
    var gap = 0.42, lw = (W - 1.24 - gap * 3) / 4;
    lanes.forEach(function (l, i) {
      var x = 0.62 + i * (lw + gap);
      var items = l.body.length ? l.body : l.fallback;
      s.addShape(pptx.ShapeType.roundRect, {
        x: x, y: 1.7, w: lw, h: 3.3, rectRadius: 0.12,
        fill: { color: l.fill }, line: { color: "D9DCEA", width: 1 }
      });
      s.addText(txt(l.title), {
        x: x + 0.12, y: 1.85, w: lw - 0.24, h: 0.5, align: "center",
        fontFace: FONT, fontSize: 13.5, bold: true, color: INK
      });
      s.addText(items.map(function (t) {
        return { text: txt(t), options: { breakLine: true } };
      }), {
        x: x + 0.18, y: 2.4, w: lw - 0.36, h: 2.4, align: "center",
        valign: "top", fontFace: FONT, fontSize: 11.5, color: "3B3F5C",
        lineSpacingMultiple: 1.3
      });
      if (i < lanes.length - 1) {
        s.addShape(pptx.ShapeType.chevron, {
          x: x + lw + 0.04, y: 3.1, w: 0.34, h: 0.5,
          fill: { color: VIOLET }, line: { type: "none" }
        });
      }
    });

    [["1", "The person asks in the flow of work — Teams or Microsoft 365 Copilot."],
     ["2", "The agent reasons only over its declared sources, on whichever tier it runs."],
     ["3", "The answer lands with its evidence — records cited, never assumed."]]
      .forEach(function (t, i) {
        var x = 0.62 + i * ((W - 1.24 - 0.6) / 3 + 0.3);
        var bw = (W - 1.24 - 0.6) / 3;
        s.addShape(pptx.ShapeType.ellipse, {
          x: x, y: 5.45, w: 0.34, h: 0.34,
          fill: { color: BLUE }, line: { type: "none" }
        });
        s.addText(t[0], {
          x: x, y: 5.45, w: 0.34, h: 0.34, align: "center", valign: "middle",
          fontFace: FONT, fontSize: 12, bold: true, color: PAPER
        });
        s.addText(t[1], {
          x: x + 0.44, y: 5.32, w: bw - 0.44, h: 0.75, valign: "middle",
          fontFace: FONT, fontSize: 10.5, color: MUTED
        });
      });
    footer(s, n);
  }

  /* The "Agent overview" card the films use: three gradient panels, in order. */
  function overviewSlide(pptx, panels, n) {
    var s = darkSlide(pptx);
    kicker(s, "Agent overview", true);
    heading(s, "How it works", { dark: true });

    var keys = Object.keys(panels || {}).slice(0, 3);
    if (!keys.length) return;
    var gap = 0.5, pw = (W - 1.24 - gap * (keys.length - 1)) / keys.length;

    keys.forEach(function (k, i) {
      var x = 0.62 + i * (pw + gap);
      s.addShape(pptx.ShapeType.roundRect, {
        x: x, y: 1.75, w: pw, h: 4.1, rectRadius: 0.14,
        fill: { color: INK }, line: { type: "none" }
      });
      s.addText(txt(k), {
        x: x, y: 1.92, w: pw, h: 0.45, align: "center",
        fontFace: FONT, fontSize: 16, bold: true, color: PAPER
      });
      s.addShape(pptx.ShapeType.roundRect, {
        x: x + 0.2, y: 2.5, w: pw - 0.4, h: 2.5, rectRadius: 0.1,
        fill: { color: i === 0 ? PINK : (i === 1 ? "C45FC0" : VIOLET) },
        line: { type: "none" }
      });
      s.addText((panels[k] || []).slice(0, 4).join("\n\n"), {
        x: x + 0.32, y: 2.62, w: pw - 0.64, h: 2.26, align: "center",
        valign: "middle", fontFace: FONT, fontSize: 12, bold: true,
        color: PAPER
      });
      if (i < keys.length - 1) {
        s.addShape(pptx.ShapeType.chevron, {
          x: x + pw + 0.06, y: 3.35, w: 0.38, h: 0.6,
          fill: { color: VIOLET }, line: { type: "none" }
        });
      }
    });
    footer(s, n, true);
  }

  /* The walkthrough, as the exchange it actually is. */
  function walkthroughSlides(pptx, story, startNo) {
    var scene = ((story && story.scenes) || []).filter(function (x) {
      return x.act === "walkthrough";
    })[0];
    if (!scene || !scene.turns) return startNo;
    var no = startNo;
    var pairs = [];
    for (var i = 0; i < scene.turns.length; i += 2) {
      if (scene.turns[i] && scene.turns[i + 1]) {
        pairs.push([scene.turns[i], scene.turns[i + 1]]);
      }
    }
    pairs.slice(0, 3).forEach(function (pair, idx) {
      var s = lightSlide(pptx);
      kicker(s, "In the flow of work · " + (idx + 1) + " of " + Math.min(3, pairs.length));
      heading(s, txt(pair[1].heading) || "The agent responds");

      s.addShape(pptx.ShapeType.roundRect, {
        x: 4.4, y: 1.45, w: 8.3, h: 0.85, rectRadius: 0.12,
        fill: { color: "EEEBFA" }, line: { type: "none" }
      });
      s.addText(txt(pair[0].text), {
        x: 4.6, y: 1.45, w: 7.9, h: 0.85, valign: "middle",
        fontFace: FONT, fontSize: 13, color: INK
      });

      var r = pair[1].rich || {};
      s.addText(txt(r.intro), {
        x: 0.62, y: 2.5, w: W - 1.24, h: 0.8,
        fontFace: FONT, fontSize: 14, color: INK, valign: "top"
      });
      var cols = (r.sections || []).slice(0, 2);
      cols.forEach(function (sec, ci) {
        var x = 0.62 + ci * 6.3;
        s.addText(txt(sec.label), {
          x: x, y: 3.4, w: 5.9, h: 0.3,
          fontFace: FONT, fontSize: 12, bold: true, color: BLUE
        });
        bulletList(s, sec.items, { x: x, y: 3.72, w: 5.9, h: 1.9, size: 12 });
      });
      if (r.callout && r.callout.headline) {
        s.addShape(pptx.ShapeType.roundRect, {
          x: 0.62, y: 5.7, w: W - 1.24, h: 0.85, rectRadius: 0.1,
          fill: { color: "FBE9F7" }, line: { type: "none" }
        });
        s.addText([
          { text: txt(r.callout.headline), options: { bold: true, breakLine: true } },
          { text: txt(r.callout.source), options: { fontSize: 11, color: MUTED } }
        ], {
          x: 0.85, y: 5.7, w: W - 1.7, h: 0.85, valign: "middle",
          fontFace: FONT, fontSize: 12, color: INK
        });
      }
      footer(s, no++);
    });
    return no;
  }

  function setupSlide(pptx, entry, n) {
    var s = lightSlide(pptx);
    kicker(s, "Setup");
    heading(s, "What it needs, and where it runs");

    s.addText("Configuration required", {
      x: 0.62, y: 1.5, w: 5.9, h: 0.3,
      fontFace: FONT, fontSize: 12, bold: true, color: BLUE
    });
    var env = (entry && entry.requires_env || []);
    bulletList(s, env.length ? env : ["No configuration"],
      { y: 1.85, w: 5.9, h: 1.9, size: 13 });

    s.addText("Parameters", {
      x: 6.8, y: 1.5, w: 5.9, h: 0.3,
      fontFace: FONT, fontSize: 12, bold: true, color: BLUE
    });
    var params = paramNames(entry);
    bulletList(s, params.length ? params : ["None"],
      { x: 6.8, y: 1.85, w: 5.9, h: 1.9, size: 13 });

    s.addText("Where it runs", {
      x: 0.62, y: 3.95, w: W - 1.24, h: 0.3,
      fontFace: FONT, fontSize: 12, bold: true, color: BLUE
    });
    [["Brainstem", "Local Flask server with GitHub Copilot — no API keys"],
     ["Spinal cord", "Azure Functions with Azure OpenAI"],
     ["Nervous system", "Copilot Studio and Teams"]].forEach(function (t, i) {
      var x = 0.62 + i * 4.25;
      s.addShape(pptx.ShapeType.roundRect, {
        x: x, y: 4.35, w: 3.95, h: 1.5, rectRadius: 0.1,
        fill: { color: "F4F4F8" }, line: { type: "none" }
      });
      s.addText([
        { text: t[0], options: { bold: true, breakLine: true, fontSize: 14 } },
        { text: t[1], options: { fontSize: 11, color: MUTED } }
      ], {
        x: x + 0.22, y: 4.35, w: 3.51, h: 1.5, valign: "middle",
        fontFace: FONT, color: INK
      });
    });
    footer(s, n);
  }

  function closeSlide(pptx, name, entry, links, n) {
    var s = darkSlide(pptx);
    s.addShape(pptx.ShapeType.roundRect, {
      x: 0.62, y: 1.5, w: W - 1.24, h: 3.1, rectRadius: 0.2,
      fill: { color: VIOLET }, line: { type: "none" }
    });
    s.addText([
      { text: "Get started on your agentic journey today.",
        options: { fontSize: 28, bold: true, breakLine: true } },
      { text: "Talk to your Microsoft representative to learn more.",
        options: { fontSize: 16 } }
    ], {
      x: 1.1, y: 1.5, w: W - 2.2, h: 3.1, align: "center", valign: "middle",
      fontFace: FONT, color: PAPER
    });
    bulletList(s, (links || []).filter(Boolean),
      { y: 4.9, h: 1.5, size: 12, color: "C7CBE6" });
    s.addText("Sample data in library agents is synthetic. Use is subject to " +
      "the AIBAST disclaimer.", {
      x: 0.62, y: 6.3, w: W - 1.24, h: 0.4,
      fontFace: FONT, fontSize: 10, color: "8C93B5"
    });
    footer(s, n, true);
  }

  /* --- entry point -------------------------------------------------------- */

  function build(pptx, o) {
    var name = displayName(o.kind, o.entry, o.story);
    /* LAYOUT_16x9 is 10" x 5.625" — everything here is laid out for the
       13.333" x 7.5" canvas, so the wide layout is the only correct one.
       (The old value cut every slide off at the right and bottom edge.) */
    pptx.defineLayout({ name: "RAPP_WIDE", width: W, height: H });
    pptx.layout = "RAPP_WIDE";
    pptx.author = "Microsoft AIBAST";
    pptx.company = "Microsoft";
    pptx.title = name;
    pptx.subject = "RAPP Agents Library";

    titleSlide(pptx, name, o.entry, o.kind);
    whatItIsSlide(pptx, name, o.entry, 2);

    var panels = null;
    ((o.story && o.story.scenes) || []).forEach(function (sc) {
      if (sc.act === "overview" && sc.panels) panels = sc.panels;
    });
    var n = 3;
    if (panels) { overviewSlide(pptx, panels, n); n += 1; }
    architectureSlide(pptx, name, o.entry, panels, n); n += 1;
    n = walkthroughSlides(pptx, o.story, n);
    setupSlide(pptx, o.entry, n); n += 1;
    closeSlide(pptx, name, o.entry, o.links, n);
    return n;
  }

  function exportDeck(o) {
    o = o || {};
    var say = o.onStatus || function () {};
    if (typeof PptxGenJS === "undefined") {
      say("PowerPoint export is unavailable — the deck library did not load.");
      return Promise.reject(new Error("PptxGenJS missing"));
    }
    say("Building the deck…");
    var pptx = new PptxGenJS();
    try {
      build(pptx, o);
    } catch (e) {
      say("Could not build the deck: " + (e && e.message ? e.message : e));
      return Promise.reject(e);
    }
    var file = (displayName(o.kind, o.entry, o.story) || "agent")
      .replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "") + "-AIBAST.pptx";
    return pptx.writeFile({ fileName: file }).then(function () {
      say("Saved " + file);
      return file;
    }).catch(function (e) {
      say("Export failed: " + (e && e.message ? e.message : e));
      throw e;
    });
  }

  global.RappDeck = { export: exportDeck, build: build, displayName: displayName };
})(window);
