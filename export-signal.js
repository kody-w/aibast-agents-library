/* Export signal — an export is the strongest interest signal this site has.

   A view means someone landed. A play means someone watched. An export means
   someone took the deck away to use it in their own meeting — that is the
   signal worth ranking solutions by, and until now it left no trace at all.

   HOW IT IS RECORDED. The same way a play and a download already are: a
   reaction on a pinned tally comment in the solution's Discussion. There is no
   backend on a static site, so a browser cannot POST a number anywhere, and
   the alternatives are worse than they look — a counter in a JSON file cannot
   be written from a page, a third-party counter puts a tracker on a Microsoft
   page, and anything anonymous is trivially inflatable.

   So the number means "signed-in people who marked that they exported this",
   not "downloads". It is a smaller number than the true one, and a truer one.
   Every surface that shows it says that in words rather than implying traffic.

   THE FILE SAVES EITHER WAY. Signalling happens after the save resolves and
   never blocks it. A count that can cost someone their download is not worth
   having.

   WHAT A WORKFLOW SEES. scripts/export_engagement.py reads those reactions and
   scripts/build_popularity.py ranks every solution by them alongside plays,
   likes, comments and ratings. That is the report this exists to feed.
*/
(function (global) {
  "use strict";

  var FEED = "api/v1/export-engagement.json";
  var STORE = "aibast:exports";          // local, so a page can say "you took this"
  var DATA = null, LOADING = null;

  function load() {
    if (DATA) return Promise.resolve(DATA);
    if (LOADING) return LOADING;
    LOADING = fetch(FEED, { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { DATA = d || { exports: {} }; return DATA; })
      .catch(function () { DATA = { exports: {} }; return DATA; });
    return LOADING;
  }

  function statsFor(slug) {
    return load().then(function (d) {
      return (d.exports || {})[slug] || { exports: 0, thread: false };
    });
  }

  /* Local memory of what this browser took away. Never sent anywhere — it
     exists so a page can show "exported" without asking GitHub, and so a
     second export in the same session does not open the tab again. */
  function remembered() {
    try { return JSON.parse(global.localStorage.getItem(STORE) || "{}"); }
    catch (e) { return {}; }
  }

  function remember(key) {
    try {
      var m = remembered();
      m[key] = (m[key] || 0) + 1;
      global.localStorage.setItem(STORE, JSON.stringify(m));
      return m[key];
    } catch (e) { return 1; }
  }

  /* Record one export.

     kind  what was exported: "solution", "agent", "config-guide", "roadmap"
     slug  which one — the same slug the catalog and Discussions use
     opts  { silent: true } records locally and opens nothing (tests, batches)

     Returns a promise so a caller can await the trace; it never rejects,
     because a failed count must never look like a failed export. */
  function signal(kind, slug, opts) {
    opts = opts || {};
    var key = (kind || "export") + ":" + (slug || "unknown");
    var seen = remembered()[key];
    remember(key);
    if (opts.silent || seen) return Promise.resolve({ counted: false, key: key });

    return statsFor(slug).then(function (s) {
      var url = s.export_url || s.url;
      if (!url) return { counted: false, key: key, reason: "no thread yet" };
      // First export of this thing in this browser only. Opened alongside the
      // download, never in front of it.
      try { global.open(url, "_blank", "noopener"); } catch (e) {}
      return { counted: true, key: key, url: url };
    }).catch(function () {
      return { counted: false, key: key, reason: "feed unavailable" };
    });
  }

  function nfmt(n) {
    n = n || 0;
    return n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + "k" : String(n);
  }

  /* A one-line count for under an export button. Says what the number is. */
  function label(container, slug) {
    if (!container) return Promise.resolve(null);
    return statsFor(slug).then(function (s) {
      if (!s.exports) return s;
      container.textContent = "↓ " + nfmt(s.exports) + " exported";
      container.title = "People who marked that they exported this deck. " +
        "One per GitHub account, so it is not a download count.";
      return s;
    });
  }

  global.RappExport = {
    signal: signal, stats: statsFor, label: label,
    remembered: remembered, feed: FEED
  };
})(window);
