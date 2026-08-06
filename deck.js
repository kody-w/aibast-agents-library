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
    var rows = (items || []).filter(Boolean).slice(0, o.max || 8).map(function (i) {
      // The bullet belongs to each run. Setting it once on the text call marks
      // the first line only and leaves the rest hanging.
      return { text: txt(i), options: { breakLine: true, bullet: { characterCode: "2022" } } };
    });
    if (!rows.length) return;
    s.addText(rows, {
      x: o.x == null ? 0.62 : o.x, y: o.y == null ? 1.6 : o.y,
      w: o.w == null ? W - 1.24 : o.w, h: o.h == null ? 4.4 : o.h,
      fontFace: FONT, fontSize: o.size || 16, color: o.color || INK,
      lineSpacingMultiple: 1.25, valign: "top"
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
    var full = name + (/agent$/i.test(name) ? ""
                       : (kind === "skill" ? " Skill" : " Agent"));
    // "Supplier Risk Monitoring Agent" at 40pt overflowed the lozenge. Step the
    // size down by length rather than letting it run off the edge.
    var size = full.length > 34 ? 28 : (full.length > 26 ? 32 : 40);
    s.addText(full, {
      x: 1.8, y: 2.35, w: W - 3.6, h: 2.1, align: "center", valign: "middle",
      fontFace: FONT, fontSize: size, bold: true, color: PAPER, shrinkText: true
    });
    s.addText("Microsoft AIBAST · Agents Library", {
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

  function whatItIsSlide(pptx, pptxName, entry, jewel, arch, n) {
    var s = lightSlide(pptx);
    var j = jewel || {};
    var ac = (arch && arch.columns) || {};
    kicker(s, "What it is" + (j.industry ? " · " + j.industry : ""));
    heading(s, pptxName);
    s.addText(txt(j.lede || j.summary || (entry && entry.description))
      || "A single-file RAPP agent.", {
      x: 0.62, y: 1.5, w: W - 1.24, h: 1.1,
      fontFace: FONT, fontSize: 17, color: INK, valign: "top"
    });
    s.addText("Who it is for", {
      x: 0.62, y: 2.8, w: 5.6, h: 0.3, fontFace: FONT, fontSize: 12,
      bold: true, color: BLUE
    });
    /* Real job titles when the library one-pager has them; tags only as a
       fallback. "Plant Manager" tells a customer more than "manufacturing". */
    var who = (j.personas || j.audience || []).slice(0, 5);
    if (!who.length) {
      who = (entry && entry.tags || []).slice(0, 6)
        .map(function (t) { return titleCase(t); });
    }
    s.addText(who.length ? who.join(" · ") : "Any team running this workload", {
      x: 0.62, y: 3.15, w: 5.6, h: 1.0,
      fontFace: FONT, fontSize: 14, color: INK, valign: "top"
    });
    s.addText("What you get", {
      x: 6.6, y: 2.8, w: 6.1, h: 0.3, fontFace: FONT, fontSize: 12,
      bold: true, color: BLUE
    });
    bulletList(s, (j.business_value && j.business_value.length
      ? j.business_value.slice(0, 4)
      : ["A single file your team can deploy as-is",
         "Registers itself as a tool — no restart, no rebuild",
         "Runs locally, on Azure, or in Microsoft Copilot Studio"]),
      { x: 6.6, y: 3.15, w: 6.1, h: 2.2, size: 14 });
    /* The bottom third used to be white. It is the three questions every
       reviewer asks next, answered from the same derived architecture the
       slide after this one draws — so the two cannot disagree. */
    var tiles = [
      ["What it reads", labelsOf((ac.knowledge || {}).grounding, 3).join(" · ")
        || (j.requires || []).slice(0, 3).join(" · ")],
      ["Where the work happens",
        labelsOf((ac.interface || {}).surfaces, 3).join(" · ")
        || (j.built_with || []).slice(0, 3).join(" · ")],
      ["What it leaves behind",
        labelsOf((ac.reporting || {}).systems, 2).join(" · ")
        || "Audit logs and telemetry under Purview"]
    ];
    tiles.forEach(function (t, i) {
      if (!t[1]) return;
      var x = 0.62 + i * 4.25;
      s.addShape(pptx.ShapeType.roundRect, {
        x: x, y: 4.35, w: 3.95, h: 1.15, rectRadius: 0.1,
        fill: { color: "F4F4F8" }, line: { type: "none" }
      });
      s.addText([
        { text: t[0], options: { bold: true, breakLine: true, fontSize: 11,
                                 color: BLUE } },
        { text: t[1], options: { fontSize: 11.5 } }
      ], {
        x: x + 0.22, y: 4.35, w: 3.51, h: 1.15, valign: "middle",
        fontFace: FONT, color: INK
      });
    });
    if (j.featured_tools && j.featured_tools.length) {
      s.addText("Built with " + j.featured_tools.slice(0, 4).join(" · "), {
        x: 0.62, y: 5.6, w: W - 1.24, h: 0.3,
        fontFace: FONT, fontSize: 11, color: MUTED
      });
    }
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

  /* --- the end-to-end architecture, per industry ---------------------------

     REQUIRED in every deck. Nobody buys a chat window; they buy a thing that
     sits inside their estate, reads systems they already pay for, and leaves an
     audit trail. That is one slide, and it is the same four columns every time:
     Knowledge, Processing, User Interface, Reporting, over a Tools band and a
     Supporting Features band, with the six-step request flow numbered through
     them.

     Every box is derived from what the entry declares — see
     scripts/build_architecture.py. Nothing here is invented for the picture.
  */

  function labelsOf(list, max) {
    return (list || []).map(function (x) {
      return txt(x && x.label ? x.label : x);
    }).filter(function (v, i, a) { return v && a.indexOf(v) === i; })
      .slice(0, max || 4);
  }

  /* A titled panel with a rule under the title — one architecture column. */
  function column(pptx, s, x, y, w, h, title) {
    s.addShape(pptx.ShapeType.roundRect, {
      x: x, y: y, w: w, h: h, rectRadius: 0.08,
      fill: { color: "F4F4F8" }, line: { color: "E3E3EC", width: 0.75 }
    });
    s.addText(txt(title), {
      x: x, y: y + 0.06, w: w, h: 0.3, align: "center",
      fontFace: FONT, fontSize: 12, bold: true, color: INK
    });
  }

  /* A box inside a column. `step` prints the flow number in front of the text
     so the numbered request path reads without a separate legend. */
  function box(pptx, s, o) {
    s.addShape(pptx.ShapeType.roundRect, {
      x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.06,
      fill: { color: o.fill || PAPER },
      line: o.line ? { color: o.line, width: 0.75, dashType: o.dash || "solid" }
                   : { color: "DDDDE8", width: 0.5 }
    });
    var runs = [];
    if (o.head) {
      runs.push({ text: txt(o.head),
                  options: { bold: true, fontSize: o.headSize || 9,
                             breakLine: !!o.text } });
    }
    if (o.text) {
      runs.push({ text: (o.step ? o.step + ". " : "") + txt(o.text),
                  options: { fontSize: o.size || 8 } });
    }
    if (!runs.length) return;
    s.addText(runs, {
      x: o.x + 0.08, y: o.y, w: o.w - 0.16, h: o.h,
      valign: o.valign || "middle", align: o.align || "left",
      fontFace: FONT, color: o.color || INK
    });
  }

  /* Lay `items` out as evenly-spaced chips filling the band from y to y+span.
     Bullet lists left columns half empty and indented oddly; chips fill the
     space and read like the boxes on the reference architecture. */
  function chips(pptx, s, x, y, w, span, items, o) {
    o = o || {};
    var list = (items || []).slice(0, o.max || 4);
    if (!list.length) return y;
    var gap = 0.08;
    var h = Math.min(o.maxH || 0.55, (span - gap * (list.length - 1)) / list.length);
    list.forEach(function (t, i) {
      box(pptx, s, {
        x: x, y: y + i * (h + gap), w: w, h: h, text: t,
        size: o.size || 8.5, fill: o.fill, line: o.line, dash: o.dash
      });
    });
    return y + list.length * (h + gap);
  }

  function architectureSlide(pptx, arch, name, industry, n) {
    var s = lightSlide(pptx);
    var cols = (arch && arch.columns) || {};
    var K = cols.knowledge || {}, P = cols.processing || {};
    var U = cols.interface || {}, R = cols.reporting || {};
    function flow(i, fallback) {
      return (arch && arch.flow && arch.flow[i] && arch.flow[i].text) || fallback;
    }

    kicker(s, "End-to-end architecture" + (industry ? " · " + industry : ""));
    s.addText("How " + txt(name) + " works, end to end", {
      x: 0.62, y: 0.5, w: W - 1.24, h: 0.5,
      fontFace: FONT, fontSize: 23, bold: true, color: INK, valign: "middle"
    });
    s.addText("Read left to right: where the person starts, what it reads, "
              + "what it does, and where the work lands.", {
      x: 0.62, y: 1.0, w: W - 1.24, h: 0.28,
      fontFace: FONT, fontSize: 10.5, color: MUTED
    });

    /* COLUMN ORDER IS THE JOURNEY. Grouped by kind, the numbered flow ran
       3,4 then 1,2,6 then 5 across the page — each column right, the sequence
       unreadable. In the order things actually happen it reads 1 to 6. */
    var top = 1.45, ch = 4.35, gap = 0.13, x0 = 0.62;
    var ws = [3.05, 2.55, 3.85, 2.63];
    var xs = [x0];
    for (var i = 1; i < 4; i++) xs.push(xs[i - 1] + ws[i - 1] + gap);
    var caps = ["Where the person starts", "What it reads to answer",
                "What it actually does", "Where it lands, and what is logged"];
    var titles = [U.title || "User Interface", K.title || "Knowledge",
                  P.title || "Processing", R.title || "Reporting"];
    for (var ci = 0; ci < 4; ci++) {
      column(pptx, s, xs[ci], top, ws[ci], ch, titles[ci]);
      s.addText(caps[ci], {
        x: xs[ci], y: top + 0.3, w: ws[ci], h: 0.24, align: "center",
        fontFace: FONT, fontSize: 8, color: MUTED
      });
    }

    /* 1 — where the person starts */
    var y = chips(pptx, s, xs[0] + 0.12, top + 0.62, ws[0] - 0.24, 1.1,
                  labelsOf(U.surfaces, 3), { fill: "F4F4F8", maxH: 0.34, size: 8.5 });
    box(pptx, s, { x: xs[0] + 0.12, y: y + 0.12, w: ws[0] - 0.24, h: 0.62,
                   step: 1, text: flow(0, "Natural language input"), size: 8.5,
                   valign: "top" });
    box(pptx, s, { x: xs[0] + 0.12, y: y + 0.84, w: ws[0] - 0.24, h: 0.86,
                   step: 2, text: U.checks, size: 8, valign: "top" });
    var actors = labelsOf(U.actors, 2);
    if (actors.length) {
      s.addText("For: " + actors.join(" · "), {
        x: xs[0] + 0.12, y: top + ch - 0.5, w: ws[0] - 0.24, h: 0.4,
        fontFace: FONT, fontSize: 8.5, color: MUTED, valign: "top"
      });
    }

    /* 2 — what it reads */
    chips(pptx, s, xs[1] + 0.12, top + 0.62, ws[1] - 0.24, 1.9,
          labelsOf(K.grounding, 4), { line: "C9A227", dash: "dash", maxH: 0.5 });
    s.addText(txt(K.note || ""), {
      x: xs[1] + 0.12, y: top + 2.65, w: ws[1] - 0.24, h: 1.5,
      fontFace: FONT, fontSize: 8, color: MUTED, valign: "top"
    });

    /* 3 — what it does */
    box(pptx, s, { x: xs[2] + 0.12, y: top + 0.62, w: ws[2] - 0.24, h: 0.44,
                   step: 3, text: "Formulates a plan across the agents below",
                   size: 8.5 });
    s.addText(txt(P.orchestration || "Multi-agent orchestration"), {
      x: xs[2] + 0.12, y: top + 1.12, w: ws[2] - 0.24, h: 0.3, align: "center",
      fontFace: FONT, fontSize: 9.5, bold: true, color: INK
    });
    var agents = (P.agents || []).slice(0, 6);
    if (agents.length) {
      s.addText(agents.map(function (a, i) {
        return { text: "3." + (i + 1) + "  " + txt(a.name) + " — " + txt(a.does),
                 options: { breakLine: true, fontSize: 7 } };
      }), { x: xs[2] + 0.12, y: top + 1.46, w: ws[2] - 0.24, h: 2.1,
            fontFace: FONT, color: INK, valign: "top", lineSpacingMultiple: 1.06,
            shrinkText: true });
    } else {
      s.addText(labelsOf(P.actions, 6).map(function (a, i) {
        return { text: "3." + (i + 1) + "  " + txt(a),
                 options: { breakLine: true, fontSize: 8 } };
      }), { x: xs[2] + 0.12, y: top + 1.46, w: ws[2] - 0.24, h: 2.1,
            fontFace: FONT, color: INK, valign: "top", shrinkText: true });
    }
    box(pptx, s, { x: xs[2] + 0.12, y: top + ch - 0.7, w: ws[2] - 0.24, h: 0.55,
                   step: 4, text: flow(3, "NL response after guideline checks"),
                   size: 8.5, fill: "EEEBFA" });

    /* 4 — where it lands */
    box(pptx, s, { x: xs[3] + 0.12, y: top + 0.62, w: ws[3] - 0.24, h: 0.62,
                   step: 5, text: flow(4, "Action taken in the system of record"),
                   size: 8.5, fill: "EEEBFA", valign: "top" });
    box(pptx, s, { x: xs[3] + 0.12, y: top + 1.32, w: ws[3] - 0.24, h: 0.4,
                   step: 6, text: "Feedback", size: 8.5 });
    box(pptx, s, { x: xs[3] + 0.12, y: top + 1.82, w: ws[3] - 0.24, h: 0.95,
                   head: "Governance, risk & compliance", text: R.governance,
                   size: 7.5, headSize: 8.5, valign: "top",
                   fill: "FBF7EA", line: "E4D9A8" });
    chips(pptx, s, xs[3] + 0.12, top + 2.87, ws[3] - 0.24, 0.6,
          labelsOf(R.systems, 2), { maxH: 0.34, size: 8 });
    box(pptx, s, { x: xs[3] + 0.12, y: top + 3.55, w: ws[3] - 0.24, h: 0.7,
                   head: "Insights", text: R.insights, size: 7.5, headSize: 8.5,
                   valign: "top", fill: "FBF7EA", line: "E4D9A8" });

    footer(s, n);
    return s;
  }

  /* Fallback when the catalog cannot be fetched (opened from disk, say). The
     slide is required, so it is built from what the entry itself declares
     rather than skipped. Same shape, thinner content, no invention. */
  function deriveArchitecture(entry, jewel, name) {
    var e = entry || {}, j = jewel || {};
    var systems = (j.requires || j.featured_tools || e.systems || []).slice(0, 4);
    if (!systems.length) systems = ["The operator's own working context"];
    return {
      display_name: name,
      industries: j.industries || e.industries || [],
      columns: {
        knowledge: { title: "Knowledge", grounding: systems,
                     connectors: ["Power Platform connectors and actions"] },
        processing: { title: "Processing",
                      orchestration: "Multi-agent orchestration",
                      plan: "Formulates a plan comprised of multiple actions "
                            + "including context and tool selection, function "
                            + "matching and parameter determination, tool "
                            + "initiation, then result analysis and response "
                            + "formulation.",
                      actions: j.business_value || [] },
        interface: { title: "User Interface",
                     surfaces: j.built_with || ["Microsoft Copilot Studio"],
                     actors: j.personas || j.audience || ["Operator"],
                     checks: "Preliminary checks including responsible AI "
                             + "checks and security measures" },
        reporting: { title: "Reporting",
                     systems: ["Copilot Control System",
                               "Purview Data Security Posture Management for AI"],
                     governance: "Reviews audit logs, sensitivity labels, data "
                                 + "policies, CMK, DLP",
                     insights: "Logs and telemetry data for analysis and "
                               + "monitoring" }
      },
      tools_band: "Automatic orchestration using prompts, agent flows, computer "
                  + "use, custom connectors, Model Context Protocol and REST API",
      foundation_band: { identity: "Entra ID",
                         label: "Supporting features and foundation models" }
    };
  }

  function setupSlide(pptx, entry, arch, jewel, n) {
    var s = lightSlide(pptx);
    var cols = (arch && arch.columns) || {};
    kicker(s, "Setup");
    heading(s, "What it needs, and where it runs");

    /* Left: configuration. An empty column here used to print "No
       configuration" against half a page of white — true, and useless. What
       someone actually needs to know is what it touches. */
    s.addText("Configuration required", {
      x: 0.62, y: 1.45, w: 3.8, h: 0.3,
      fontFace: FONT, fontSize: 12, bold: true, color: BLUE
    });
    var env = (entry && entry.requires_env) || (arch && arch.configuration) || [];
    bulletList(s, env.length ? env
      : ["No keys or secrets — it runs as the signed-in user",
         "Permissions come from the caller's own access"],
      { y: 1.78, w: 3.8, h: 1.5, size: 12 });

    s.addText("Systems it connects to", {
      x: 4.68, y: 1.45, w: 3.8, h: 0.3,
      fontFace: FONT, fontSize: 12, bold: true, color: BLUE
    });
    var touches = labelsOf((cols.knowledge || {}).grounding, 3)
      .concat(labelsOf((cols.interface || {}).surfaces, 2))
      .concat(labelsOf((cols.reporting || {}).systems, 2));
    touches = touches.filter(function (v, i, a) { return a.indexOf(v) === i; })
      .slice(0, 5);
    bulletList(s, touches.length ? touches
      : (jewel && jewel.requires) || ["Microsoft Copilot Studio"],
      { x: 4.68, y: 1.78, w: 3.8, h: 1.5, size: 12 });

    s.addText("Parameters", {
      x: 8.74, y: 1.45, w: 3.97, h: 0.3,
      fontFace: FONT, fontSize: 12, bold: true, color: BLUE
    });
    var params = [];
    try {
      var props = entry && entry.metadata && entry.metadata.parameters &&
        entry.metadata.parameters.properties;
      params = props ? Object.keys(props) : (entry && entry.parameters) || [];
    } catch (e) { params = []; }
    bulletList(s, params.length ? params
      : ["None — it is asked in natural language",
         "Answers cite the record they came from"],
      { x: 8.74, y: 1.78, w: 3.97, h: 1.5, size: 12 });

    /* Middle band: the jewels. Who it is for and what it is worth, from the
       library one-pager when there is one. */
    var who = (jewel && (jewel.personas || jewel.audience)) ||
      labelsOf((cols.interface || {}).actors, 4);
    var worth = (jewel && jewel.business_value) ||
      labelsOf((cols.processing || {}).actions, 3);
    var band = [
      { text: "Who it is for  ", options: { bold: true, color: BLUE } },
      { text: (who || []).slice(0, 4).join(" · ") ||
              "Any team running this workload", options: { breakLine: true } }
    ];
    /* Only print the second line when there is something to print on it. A
       bold label over nothing is the same empty slide this replaced. */
    if (worth && worth.length) {
      band.push({ text: "What it is worth  ",
                  options: { bold: true, color: BLUE } });
      band.push({ text: worth.slice(0, 4).join(" · ") });
    }
    s.addShape(pptx.ShapeType.roundRect, {
      x: 0.62, y: 3.3, w: W - 1.24, h: 0.85, rectRadius: 0.1,
      fill: { color: "FBE9F7" }, line: { type: "none" }
    });
    s.addText(band, {
      x: 0.85, y: 3.3, w: W - 1.7, h: 0.85, valign: "middle",
      fontFace: FONT, fontSize: 11.5, color: INK
    });

    s.addText("Where it runs", {
      x: 0.62, y: 4.4, w: W - 1.24, h: 0.3,
      fontFace: FONT, fontSize: 12, bold: true, color: BLUE
    });
    [["Run it locally", "On your own machine, with GitHub Copilot — no API keys"],
     ["Run it on Azure", "Azure Functions with Azure OpenAI"],
     ["Run it in Microsoft 365", "Copilot Studio and Microsoft Teams"]].forEach(function (t, i) {
      var x = 0.62 + i * 4.25;
      s.addShape(pptx.ShapeType.roundRect, {
        x: x, y: 4.76, w: 3.95, h: 1.1, rectRadius: 0.1,
        fill: { color: "F4F4F8" }, line: { type: "none" }
      });
      s.addText([
        { text: t[0], options: { bold: true, breakLine: true, fontSize: 14 } },
        { text: t[1], options: { fontSize: 11, color: MUTED } }
      ], {
        x: x + 0.22, y: 4.76, w: 3.51, h: 1.1, valign: "middle",
        fontFace: FONT, color: INK
      });
    });
    s.addText("Same single file in all three. The architecture slide shows the "
      + "estate it sits in.", {
      x: 0.62, y: 5.95, w: W - 1.24, h: 0.3,
      fontFace: FONT, fontSize: 10, color: MUTED
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

  /* --- the jewels: the library's own catalogs ------------------------------

     The deck used to be built from the manifest entry alone, which is why the
     setup slide could come out as "No configuration / None" over half a page of
     white. The library already holds the good material — who the agent is for,
     what it is worth, and the estate it sits in — in two generated catalogs.
     The deck fetches them itself so every caller gets them without changing.
  */

  var CATALOGS = null;

  function getJSON(paths) {
    if (typeof fetch !== "function") return Promise.resolve(null);
    var i = 0;
    function next() {
      if (i >= paths.length) return Promise.resolve(null);
      return fetch(paths[i++], { cache: "no-store" }).then(function (r) {
        return r.ok ? r.json() : next();
      }).catch(next);
    }
    return next();
  }

  function loadCatalogs() {
    if (CATALOGS) return Promise.resolve(CATALOGS);
    return Promise.all([
      getJSON(["api/v1/architectures.json", "data/architectures.json"]),
      getJSON(["api/v1/onepagers.json", "data/onepagers.json"])
    ]).then(function (r) {
      CATALOGS = {
        architectures: (r[0] && r[0].architectures) || [],
        onepagers: (r[1] && r[1].onepagers) || []
      };
      return CATALOGS;
    }).catch(function () {
      CATALOGS = { architectures: [], onepagers: [] };
      return CATALOGS;
    });
  }

  function slugOf(o) {
    var e = o.entry || {};
    var raw = o.slug || e.slug || e.ref || e.name || e.id ||
      (o.story && o.story.subject && o.story.subject.slug) || "";
    return String(raw).split("/").pop();
  }

  function findBySlug(list, slug, ref) {
    var hit = null;
    (list || []).forEach(function (x) {
      if (hit) return;
      if (x.slug === slug || (ref && x.ref === ref)) hit = x;
    });
    return hit;
  }

  /* --- entry point -------------------------------------------------------- */

  function build(pptx, o) {
    var name = displayName(o.kind, o.entry, o.story);
    var cat = o.catalogs || CATALOGS || { architectures: [], onepagers: [] };
    var slug = slugOf(o);
    var ref = (o.entry && o.entry.ref) || (o.entry && o.entry.name) || null;
    var jewel = findBySlug(cat.onepagers, slug, ref);
    var arch = o.arch || findBySlug(cat.architectures, slug, ref);

    pptx.defineLayout({ name: "AIBAST_WIDE", width: W, height: H });
    pptx.layout = "AIBAST_WIDE";
    pptx.author = "Microsoft AIBAST";
    pptx.company = "Microsoft";
    pptx.title = name;
    pptx.subject = "AIBAST Agents Library";

    if (!arch) arch = deriveArchitecture(o.entry, jewel, name);

    titleSlide(pptx, name, o.entry, o.kind);
    whatItIsSlide(pptx, name, o.entry, jewel, arch, 2);

    var panels = null;
    ((o.story && o.story.scenes) || []).forEach(function (sc) {
      if (sc.act === "overview" && sc.panels) panels = sc.panels;
    });
    var n = 3;
    if (panels) { overviewSlide(pptx, panels, n); n += 1; }
    n = walkthroughSlides(pptx, o.story, n);

    /* REQUIRED: the end-to-end architecture, one slide per industry it serves.
       Never conditional. If the catalog was unreachable the slide is derived
       from the entry rather than dropped — a deck without it does not ship. */
    var industries = (arch.industries && arch.industries.length
      ? arch.industries
      : (jewel && jewel.industries) || []).slice(0, 4);
    if (!industries.length) industries = [null];
    industries.forEach(function (ind) {
      architectureSlide(pptx, arch, name, ind, n); n += 1;
    });

    setupSlide(pptx, o.entry, arch, jewel, n); n += 1;
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
    /* A solution's deck used to come out three slides shorter than an agent's
       — no overview, no flow of work — only because the caller had no
       storyboard in hand. Look for one. */
    var story = o.story ? Promise.resolve(o.story) : (function () {
      var slug = slugOf(o);
      if (!slug) return Promise.resolve(null);
      /* A solution and its registry agent can be the same thing under two
         slugs — "patient-intake-agent" and "patient-intake". Try both. */
      var bare = slug.replace(/-agent$/, "");
      return getJSON(["media/walkthroughs/" + (o.kind || "agent") + "-" + slug + ".json",
                      "media/walkthroughs/solution-" + slug + ".json",
                      "media/walkthroughs/agent-" + slug + ".json",
                      "media/walkthroughs/agent-" + bare + ".json"]);
    })();
    return Promise.all([loadCatalogs(), story]).then(function (r) {
      if (!o.story && r[1]) o.story = r[1];
      return writeDeck(o, r[0], say);
    });
  }

  function writeDeck(o, cat, say) {
    var pptx = new PptxGenJS();
    try {
      o.catalogs = cat;
      build(pptx, o);
    } catch (e) {
      say("Could not build the deck: " + (e && e.message ? e.message : e));
      return Promise.reject(e);
    }
    var file = (displayName(o.kind, o.entry, o.story) || "agent")
      .replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "") + "-AIBAST.pptx";
    return save(pptx, file, { kind: o.kind || "agent", slug: slugOf(o) }, say, o);
  }


  /* --- the roadmap deck ---------------------------------------------------
     Built from the same object roadmap.html rendered from, so a slide and a
     lane cannot disagree. One lane per slide, because a roadmap read in a room
     is read a lane at a time.
  */

  function roadmapTitleSlide(pptx, r) {
    var s = darkSlide(pptx);
    s.addShape(pptx.ShapeType.roundRect, {
      x: 1.6, y: 2.35, w: W - 3.2, h: 2.1, rectRadius: 0.42,
      fill: { type: "solid", color: PINK }, line: { type: "none" }
    });
    s.addShape(pptx.ShapeType.roundRect, {
      x: 1.6, y: 2.35, w: W - 3.2, h: 2.1, rectRadius: 0.42,
      fill: { type: "solid", color: VIOLET, transparency: 45 }, line: { type: "none" }
    });
    s.addText(txt(r.title) || "Roadmap", {
      x: 1.8, y: 2.35, w: W - 3.6, h: 2.1, align: "center", valign: "middle",
      fontFace: FONT, fontSize: 36, bold: true, color: PAPER
    });
    s.addText(txt(r.subtitle), {
      x: 0.62, y: 5.05, w: W - 1.24, h: 0.5, align: "center",
      fontFace: FONT, fontSize: 15, color: "C7CBE6"
    });
    if (r.updated) {
      s.addText("Updated " + txt(r.updated), {
        x: 0.62, y: 5.6, w: W - 1.24, h: 0.35, align: "center",
        fontFace: FONT, fontSize: 12, color: "8C93B5"
      });
    }
    footer(s, null, true);
  }

  function laneSlide(pptx, lane, n) {
    var s = lightSlide(pptx);
    kicker(s, lane.label + " — " + (lane.items || []).length + " item"
              + ((lane.items || []).length === 1 ? "" : "s"));
    heading(s, txt(lane.blurb) || txt(lane.label));

    var items = (lane.items || []).slice(0, 6);
    var cols = items.length > 3 ? 2 : 1;
    var colW = cols === 2 ? (W - 1.24 - 0.5) / 2 : W - 1.24;
    var perCol = Math.ceil(items.length / cols);

    items.forEach(function (it, i) {
      var c = Math.floor(i / perCol), row = i % perCol;
      var x = 0.62 + c * (colW + 0.5);
      var h = (H - 2.6) / perCol;
      var y = 1.5 + row * h;
      s.addText([
        { text: txt(it.title), options: { bold: true, fontSize: 15, breakLine: true } },
        { text: txt(it.detail), options: { fontSize: 12, color: "3D3D4D", breakLine: true } },
        { text: txt(it.evidence), options: { fontSize: 10, color: MUTED, italic: true } }
      ], {
        x: x, y: y, w: colW, h: h - 0.18, valign: "top", fontFace: FONT, color: INK
      });
    });
    footer(s, n);
  }

  function principlesSlide(pptx, r, n) {
    var s = darkSlide(pptx);
    kicker(s, "How status is decided", true);
    heading(s, "The rules this roadmap is held to", { dark: true });
    bulletList(s, r.principles || [],
      { y: 1.9, h: 4.2, size: 16, color: "C7CBE6" });
    footer(s, n, true);
  }

  function exportRoadmap(o) {
    o = o || {};
    var say = o.onStatus || function () {};
    var r = o.roadmap;
    if (typeof PptxGenJS === "undefined") {
      say("PowerPoint export is unavailable — the deck library did not load.");
      return Promise.reject(new Error("PptxGenJS missing"));
    }
    if (!r) { say("No roadmap data."); return Promise.reject(new Error("no roadmap")); }
    say("Building the deck…");
    var pptx = new PptxGenJS();
    try {
      pptx.defineLayout({ name: "AIBAST_WIDE", width: W, height: H });
      pptx.layout = "AIBAST_WIDE";
      pptx.author = "Microsoft AIBAST";
      pptx.company = "Microsoft";
      pptx.title = txt(r.title) || "Roadmap";
      roadmapTitleSlide(pptx, r);
      var n = 2;
      (r.lanes || []).forEach(function (lane) { laneSlide(pptx, lane, n++); });
      principlesSlide(pptx, r, n);
    } catch (e) {
      say("Could not build the deck: " + (e && e.message ? e.message : e));
      return Promise.reject(e);
    }
    var file = "AIBAST-Roadmap-" + (txt(r.updated) || "current") + ".pptx";
    return save(pptx, file, { kind: "roadmap", slug: "roadmap" }, say, o);
  }

  /* --- every export leaves the building through here ----------------------
     One function writes the file, so one function can record that it happened.
     Wiring the signal into each exporter separately guarantees that the next
     exporter someone adds is the one that never gets counted — and a
     popularity report with a silent hole in it is worse than none, because
     nothing tells you the hole is there.

     The signal never gates the download: it fires after writeFile resolves and
     its failure is swallowed. See export-signal.js for what is recorded and
     what the number honestly means.
  */
  function save(pptx, file, sig, say, o) {
    return pptx.writeFile({ fileName: file }).then(function () {
      say("Saved " + file);
      if (global.RappExport && !(o && o.noSignal)) {
        try {
          global.RappExport.signal(sig.kind, sig.slug, { silent: o && o.silent });
        } catch (e) { /* a count is never worth breaking a download over */ }
      }
      return file;
    }).catch(function (e) {
      say("Export failed: " + (e && e.message ? e.message : e));
      throw e;
    });
  }


  /* --- the configuration guide -------------------------------------------
     A guide is slides because that is how it gets used: opened in a room,
     walked through, then taken away. The page renders the same objects, so a
     slide on screen and a slide in the file cannot disagree.

     Product marks are the real ones where a real one exists and a labelled
     chip where it does not. An approximated logo on a Microsoft deck is worse
     than a word.
  */

  function markPath(products, id) {
    var list = (products && products.products) || [];
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === id && list[i].mark_status === "mark") return list[i].mark;
    }
    /* A harness is not a catalog product — GitHub Copilot has a real mark on
       disk and no row in products.json, so this used to return null and the
       title slide drew the name with no logo beside it. */
    var idx = (products && products._index) || {};
    return (idx[id] && idx[id].file) || null;
  }

  /* A product row: mark if we have one, initial-chip if we do not. */
  function productRow(pptx, s, products, row, x, y, w, h) {
    var path = markPath(products, row.id);
    if (path) {
      s.addImage({ path: path, x: x + 0.1, y: y + (h - 0.42) / 2, w: 0.42, h: 0.42 });
    } else {
      s.addShape(pptx.ShapeType.roundRect, {
        x: x + 0.1, y: y + (h - 0.42) / 2, w: 0.42, h: 0.42, rectRadius: 0.08,
        fill: { color: "EEEBFA" }, line: { color: "DDDDE8", width: 0.5 }
      });
      s.addText(txt(row.product).replace(/^Microsoft /, "").charAt(0), {
        x: x + 0.1, y: y + (h - 0.42) / 2, w: 0.42, h: 0.42, align: "center",
        fontFace: FONT, fontSize: 14, bold: true, color: BLUE, valign: "middle"
      });
    }
    s.addText([
      { text: txt(row.product), options: { bold: true, fontSize: 12, breakLine: true } },
      { text: txt(row.role), options: { fontSize: 10, color: MUTED } }
    ], {
      x: x + 0.66, y: y, w: w - 0.78, h: h, valign: "middle",
      fontFace: FONT, color: INK
    });
  }

  /* The "so what" strip. A slide that makes the reader derive the conclusion
     is a slide that gets a different conclusion in every room. */
  function takeaway(pptx, s, sl) {
    if (!sl.takeaway) return;
    var y = H - 1.28;
    s.addShape(pptx.ShapeType.line, {
      x: 0.62, y: y - 0.12, w: W - 1.24, h: 0,
      line: { color: "DDDDE8", width: 0.75 }
    });
    s.addText([
      { text: "SO WHAT", options: { bold: true, color: BLUE, fontSize: 10,
                                    charSpacing: 1.1 } },
      { text: "   " + txt(sl.takeaway), options: { fontSize: 12.5, color: INK } }
    ], { x: 0.62, y: y, w: W - 1.24, h: 0.5, valign: "middle", fontFace: FONT });
  }

  function guideSummarySlide(pptx, sl, n) {
    var s = lightSlide(pptx);
    kicker(s, sl.kicker || "");
    heading(s, sl.title, { size: 25 });
    s.addText(txt(sl.body), {
      x: 0.62, y: 1.42, w: W - 1.24, h: 1.0,
      fontFace: FONT, fontSize: 13, color: MUTED, valign: "top",
      lineSpacingMultiple: 1.2
    });
    var pts = (sl.points || []).slice(0, 3);
    var gap = 0.26, cw = (W - 1.24 - gap * (pts.length - 1)) / Math.max(pts.length, 1);
    pts.forEach(function (p, i) {
      var x = 0.62 + i * (cw + gap);
      /* A rule over each column, not a box around it: the pyramid reads as
         three supports for one thought, not three unrelated cards. */
      s.addShape(pptx.ShapeType.rect, {
        x: x, y: 2.66, w: cw, h: 0.045,
        fill: { color: BLUE }, line: { type: "none" }
      });
      s.addText([
        { text: txt(p.lead), options: { bold: true, fontSize: 14, breakLine: true } },
        { text: txt(p.detail), options: { fontSize: 11, color: MUTED } }
      ], { x: x, y: 2.86, w: cw, h: 2.1, valign: "top", fontFace: FONT,
           color: INK, lineSpacingMultiple: 1.18 });
    });
    takeaway(pptx, s, sl);
    footer(s, n);
  }

  function guideTitleSlide(pptx, g, products) {
    var s = darkSlide(pptx);
    s.addShape(pptx.ShapeType.roundRect, {
      x: 0.62, y: 2.0, w: 0.9, h: 0.09, rectRadius: 0.04,
      fill: { color: PINK }, line: { type: "none" }
    });
    s.addText(txt(g.kicker || ""), {
      x: 0.62, y: 1.5, w: W - 1.24, h: 0.36,
      fontFace: FONT, fontSize: 12, bold: true, charSpacing: 1.4, color: PINK
    });
    s.addText(txt(g.title), {
      x: 0.62, y: 2.3, w: W - 2.4, h: 1.3,
      fontFace: FONT, fontSize: 42, bold: true, color: PAPER, valign: "middle"
    });
    s.addText(txt(g.sub), {
      x: 0.62, y: 3.65, w: W - 3.2, h: 0.6,
      fontFace: FONT, fontSize: 17, color: "C7CBE6", valign: "top"
    });
    /* The title slide named two products and showed neither. White plates so a
       monochrome mark and a full-colour one both read on the dark ground. */
    var harness = (g.harness || []).slice(0, 3);
    var hx = 0.62;
    harness.forEach(function (h) {
      var path = markPath(products, h.id);
      var w = 0.42 + 0.105 * txt(h.name).length + 0.5;
      s.addShape(pptx.ShapeType.roundRect, {
        x: hx, y: 4.55, w: w, h: 0.62, rectRadius: 0.1,
        fill: { color: PAPER }, line: { type: "none" }
      });
      if (path) s.addImage({ path: path, x: hx + 0.16, y: 4.68, w: 0.36, h: 0.36 });
      s.addText(txt(h.name), {
        x: hx + (path ? 0.6 : 0.2), y: 4.55, w: w - (path ? 0.72 : 0.4), h: 0.62,
        valign: "middle", fontFace: FONT, fontSize: 11.5, bold: true, color: INK
      });
      hx += w + 0.18;
    });
    footer(s, null, true);
  }

  function guideStatementSlide(pptx, sl, n) {
    var s = lightSlide(pptx);
    kicker(s, sl.kicker || "");
    heading(s, sl.title, { size: 26 });
    s.addText(txt(sl.body), {
      x: 0.62, y: 1.5, w: W - 1.24, h: 1.5,
      fontFace: FONT, fontSize: 15, color: INK, valign: "top",
      lineSpacingMultiple: 1.25
    });
    var tiles = (sl.tiles || []).slice(0, 3);
    if (tiles.length) {
      var gap = 0.18, tw = (W - 1.24 - gap * (tiles.length - 1)) / tiles.length;
      tiles.forEach(function (t, i) {
        var x = 0.62 + i * (tw + gap);
        s.addShape(pptx.ShapeType.roundRect, {
          x: x, y: 3.15, w: tw, h: 1.62, rectRadius: 0.08,
          fill: { color: "F4F4F8" }, line: { color: "E3E3EC", width: 0.75 }
        });
        s.addText([
          { text: txt(t.label).toUpperCase(),
            options: { fontSize: 10, bold: true, color: BLUE, charSpacing: 1.1,
                       breakLine: true } },
          { text: txt(t.value), options: { fontSize: 12, color: INK } }
        ], { x: x + 0.18, y: 3.28, w: tw - 0.36, h: 1.4, valign: "top",
             fontFace: FONT, lineSpacingMultiple: 1.2 });
      });
    }
    takeaway(pptx, s, sl);
    footer(s, n);
  }

  function guideProductsSlide(pptx, sl, products, n) {
    var s = lightSlide(pptx);
    kicker(s, sl.kicker || "");
    heading(s, sl.title, { size: 26 });
    if (sl.body) {
      s.addText(txt(sl.body), {
        x: 0.62, y: 1.32, w: W - 1.24, h: 0.4,
        fontFace: FONT, fontSize: 12, color: MUTED, valign: "top"
      });
    }
    var rows = (sl.rows || []).slice(0, 5);
    var top = 1.85, h = Math.min(0.92, (H - top - 0.9) / Math.max(rows.length, 1));
    rows.forEach(function (r, i) {
      var y = top + i * (h + 0.1);
      s.addShape(pptx.ShapeType.roundRect, {
        x: 0.62, y: y, w: W - 1.24, h: h, rectRadius: 0.06,
        fill: { color: PAPER }, line: { color: "DDDDE8", width: 0.5 }
      });
      productRow(pptx, s, products, r, 0.62, y, W - 1.24, h);
    });
    takeaway(pptx, s, sl);
    footer(s, n);
  }

  function guideAdventureSlide(pptx, sl, products, n) {
    var s = lightSlide(pptx);
    kicker(s, sl.kicker || "");
    heading(s, sl.title, { size: 26 });
    if (sl.body) {
      s.addText(txt(sl.body), {
        x: 0.62, y: 1.32, w: W - 1.24, h: 0.4,
        fontFace: FONT, fontSize: 12, color: MUTED, valign: "top"
      });
    }
    var rows = (sl.rows || []).slice(0, 4);
    var top = 1.9, h = Math.min(1.12, (H - top - 1.5) / Math.max(rows.length, 1));
    var cw = [2.6, 4.0, 5.0];                    /* need · already there · Microsoft */
    var cx = [0.62, 0.62 + cw[0] + 0.12, 0.62 + cw[0] + cw[1] + 0.24];
    ["The need", "If you already run something else", "The Microsoft path"]
      .forEach(function (t, i) {
        s.addText(t.toUpperCase(), {
          x: cx[i], y: top - 0.32, w: cw[i], h: 0.28,
          fontFace: FONT, fontSize: 9.5, bold: true, charSpacing: 1.1,
          color: i === 2 ? BLUE : MUTED
        });
      });
    rows.forEach(function (r, i) {
      var y = top + i * (h + 0.1);
      box(pptx, s, { x: cx[0], y: y, w: cw[0], h: h, text: r.need, size: 10.5 });
      box(pptx, s, { x: cx[1], y: y, w: cw[1], h: h, head: r.outside,
                     text: r.outside_how, size: 8.5, headSize: 10,
                     valign: "middle" });
      s.addShape(pptx.ShapeType.roundRect, {
        x: cx[2], y: y, w: cw[2], h: h, rectRadius: 0.06,
        fill: { color: "F2F6FC" }, line: { color: BLUE, width: 0.75 }
      });
      var path = markPath(products, r.microsoft_id);
      if (path) s.addImage({ path: path, x: cx[2] + 0.12, y: y + 0.14, w: 0.3, h: 0.3 });
      s.addText([
        { text: txt(r.microsoft),
          options: { bold: true, fontSize: 10.5, breakLine: true } },
        { text: txt(r.why), options: { fontSize: 8.5, color: MUTED } }
      ], { x: cx[2] + (path ? 0.5 : 0.14), y: y + 0.06, w: cw[2] - (path ? 0.64 : 0.28),
           h: h - 0.12, valign: "top", fontFace: FONT, color: INK });
    });
    takeaway(pptx, s, sl);
    footer(s, n);
  }

  function guideStepsSlide(pptx, sl, n) {
    var s = lightSlide(pptx);
    kicker(s, sl.kicker || "");
    heading(s, sl.title, { size: 26 });
    if (sl.body) {
      s.addText(txt(sl.body), {
        x: 0.62, y: 1.3, w: W - 1.24, h: 0.4,
        fontFace: FONT, fontSize: 12, color: MUTED, valign: "top"
      });
    }
    var steps = (sl.steps || []).slice(0, 6);
    var top = 1.85, h = Math.min(0.86, (H - top - 1.5) / Math.max(steps.length, 1));
    steps.forEach(function (t, i) {
      var y = top + i * (h + 0.08);
      s.addShape(pptx.ShapeType.roundRect, {
        x: 0.62, y: y, w: 0.42, h: 0.42, rectRadius: 0.21,
        fill: { color: BLUE }, line: { type: "none" }
      });
      s.addText(String(i + 1), {
        x: 0.62, y: y, w: 0.42, h: 0.42, align: "center", valign: "middle",
        fontFace: FONT, fontSize: 12, bold: true, color: PAPER
      });
      s.addText(txt(t), {
        x: 1.18, y: y - 0.04, w: W - 1.9, h: h,
        fontFace: FONT, fontSize: 12.5, color: INK, valign: "top",
        lineSpacingMultiple: 1.15
      });
    });
    takeaway(pptx, s, sl);
    footer(s, n);
  }

  function guideSyntheticSlide(pptx, sl, n) {
    var s = lightSlide(pptx);
    kicker(s, sl.kicker || "");
    heading(s, sl.title, { size: 24 });
    s.addText(txt(sl.body), {
      x: 0.62, y: 1.45, w: 6.0, h: 1.5,
      fontFace: FONT, fontSize: 12.5, color: INK, valign: "top",
      lineSpacingMultiple: 1.25
    });
    bulletList(s, sl.points, { y: 3.05, w: 6.0, h: 2.4, size: 11 });

    /* The prompt, printed so it survives the export. Someone reading the deck
       on a plane can retype it; someone on the page can copy it. The panel
       used to advertise an internal file format by name to an audience that
       has never heard of it. */
    s.addShape(pptx.ShapeType.roundRect, {
      x: 7.0, y: 1.4, w: 5.7, h: 4.6, rectRadius: 0.1,
      fill: { color: STAGE }, line: { type: "none" }
    });
    s.addText(txt(sl.prompt_title || "Paste this into Copilot"), {
      x: 7.25, y: 1.6, w: 5.2, h: 0.32,
      fontFace: FONT, fontSize: 11.5, bold: true, color: PAPER
    });
    s.addText(txt(sl.prompt), {
      x: 7.25, y: 2.0, w: 5.2, h: 3.85,
      fontFace: "Consolas", fontSize: 7.5, color: "C7CBE6",
      valign: "top", lineSpacingMultiple: 1.15, shrinkText: true
    });
    takeaway(pptx, s, sl);
    footer(s, n);
  }

  function guideCloseSlide(pptx, sl, n) {
    var s = darkSlide(pptx);
    s.addText(txt(sl.title), {
      x: 0.62, y: 2.6, w: W - 1.24, h: 1.0,
      fontFace: FONT, fontSize: 34, bold: true, color: PAPER, valign: "middle"
    });
    s.addText(txt(sl.sub), {
      x: 0.62, y: 3.7, w: W - 1.24, h: 0.5,
      fontFace: FONT, fontSize: 16, color: "C7CBE6"
    });
    footer(s, n, true);
  }

  function exportConfigGuide(o) {
    o = o || {};
    var say = o.onStatus || function () {};
    var g = o.guide;
    if (typeof PptxGenJS === "undefined") {
      say("PowerPoint export is unavailable — the deck library did not load.");
      return Promise.reject(new Error("PptxGenJS missing"));
    }
    if (!g) { say("No guide data."); return Promise.reject(new Error("no guide")); }
    say("Building the deck…");

    /* The architecture slide is the one the catalog already knows how to draw;
       reuse it rather than drawing a second, differently-shaped one. */
    var need = [Promise.all([
      getJSON(["data/products.json", "api/v1/products.json"]),
      getJSON(["assets/products/index.json"])
    ]).then(function (r) {
      var p = r[0] || { products: [] };
      p._index = (r[1] && r[1].marks) || {};
      return p;
    })];
    need.push(o.arch ? Promise.resolve(o.arch)
                     : getJSON(["data/architectures.json"]).then(function (d) {
      var list = (d && d.architectures) || [];
      for (var i = 0; i < list.length; i++) {
        if (list[i].slug === g.slug) return list[i];
      }
      return null;
    }));

    return Promise.all(need).then(function (r) {
      var products = r[0] || { products: [] }, arch = r[1];
      var pptx = new PptxGenJS();
      try {
        pptx.defineLayout({ name: "AIBAST_WIDE", width: W, height: H });
        pptx.layout = "AIBAST_WIDE";
        pptx.author = "Microsoft AIBAST";
        pptx.company = "Microsoft";
        pptx.title = txt(g.display_name) + " — configuration guide";
        var n = 1;
        (g.slides || []).forEach(function (sl) {
          switch (sl.kind) {
            case "title":       guideTitleSlide(pptx, sl, products); break;
            case "summary":     guideSummarySlide(pptx, sl, n); break;
            case "statement":   guideStatementSlide(pptx, sl, n); break;
            case "products":    guideProductsSlide(pptx, sl, products, n); break;
            case "adventure":   guideAdventureSlide(pptx, sl, products, n); break;
            case "steps":       guideStepsSlide(pptx, sl, n); break;
            case "synthetic":   guideSyntheticSlide(pptx, sl, n); break;
            case "close":       guideCloseSlide(pptx, sl, n); break;
            case "architecture":
              if (arch) {
                /* The catalog's own architecture renderer, reused so the
                   slide here and the one on architecture.html cannot differ.
                   It does not know about takeaways, so the strip is added
                   after — otherwise this is the one slide whose page and deck
                   disagree, which is the whole claim this export makes. */
                takeaway(pptx, architectureSlide(pptx, arch, g.display_name,
                                                 (g.industries || [])[0], n), sl);
              } else {
                /* Say so on the slide rather than shipping a blank one. */
                guideStatementSlide(pptx, {
                  kicker: sl.kicker, title: sl.title,
                  body: "No generated architecture is on file for this solution yet."
                }, n);
              }
              break;
            default:            guideStatementSlide(pptx, sl, n); break;
          }
          n += 1;
        });
      } catch (e) {
        say("Could not build the deck: " + (e && e.message ? e.message : e));
        throw e;
      }
      var file = txt(g.display_name).replace(/[^A-Za-z0-9]+/g, "-")
        .replace(/^-|-$/g, "") + "-Configuration-Guide-AIBAST.pptx";
      return save(pptx, file, { kind: "config-guide", slug: g.slug }, say, o);
    });
  }

  global.RappDeck = { export: exportDeck, build: build,
                     exportRoadmap: exportRoadmap,
                     exportConfigGuide: exportConfigGuide,
                     displayName: displayName };
})(window);
