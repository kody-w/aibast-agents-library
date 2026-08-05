#!/usr/bin/env python3
"""T8 — headless render test for agents.html and metrics.html.

Serves the repo root on a local port and drives both pages with Playwright:
  * agents.html: >0 agent cards render from registry.json; typing in search
    narrows them; an industry chip filters; the code viewer opens.
  * metrics.html: KPI tiles render from state/metrics.json.

Exit 0 = both pages verified. Skipped (exit 0 with SKIP notice) only if
Playwright is genuinely unavailable — the live suite then covers rendering.
"""
import contextlib
import http.server
import json
import socket
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    # Playwright is often installed in its own virtual environment because the
    # system interpreter is externally managed. Re-exec into that interpreter
    # rather than making the whole test suite run under it — the suite's other
    # cases need the system interpreter's packages.
    import os
    import subprocess

    _alt = os.environ.get("PLAYWRIGHT_PYTHON")
    if not _alt:
        for _cand in (Path.home() / ".playwright-venv" / "bin" / "python",
                      ROOT / ".venv" / "bin" / "python"):
            if _cand.is_file():
                _alt = str(_cand)
                break
    if _alt and os.environ.get("_RENDER_HEADLESS_REEXEC") != "1":
        _env = {**os.environ, "_RENDER_HEADLESS_REEXEC": "1"}
        sys.exit(subprocess.run([_alt, __file__, *sys.argv[1:]], env=_env).returncode)
    sync_playwright = None


def free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    if sync_playwright is None:
        print("SKIP: playwright not installed (browser rendering unverified)")
        return 0
    port = free_port()
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(ROOT), **kw)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    failures = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()

        # ---- agents.html ----
        page.goto(f"{base}/agents.html", wait_until="networkidle")
        page.wait_for_timeout(400)
        cards = page.locator(".card").count()
        if cards < 10:
            failures.append(f"agents.html rendered only {cards} cards")
        total_stat = page.locator("#statAgents").inner_text()
        reg = json.loads((ROOT / "registry.json").read_text())
        if str(reg["stats"]["total_agents"]) not in total_stat:
            failures.append(f"hero stat '{total_stat}' != registry count")
        page.fill("#agentSearch", "emission")
        page.wait_for_timeout(250)
        after_search = page.locator(".card:visible").count()
        if not (0 < after_search < cards):
            failures.append(f"search did not narrow: {cards} -> {after_search}")
        page.fill("#agentSearch", "")
        chip = page.locator(".chip", has_text="Healthcare").first
        if chip.count():
            chip.click()
            page.wait_for_timeout(250)
            if page.locator(".card:visible").count() >= cards:
                failures.append("industry chip did not filter")
        else:
            failures.append("no Healthcare industry chip")
        # code viewer
        viewer_link = page.locator("[data-view]").first
        if viewer_link.count():
            viewer_link.click()
            page.wait_for_timeout(600)
            if not page.locator("#codeModal").is_visible():
                failures.append("code viewer modal did not open")
        else:
            failures.append("no code-viewer trigger on cards")

        # ---- metrics.html ----
        page.goto(f"{base}/metrics.html", wait_until="networkidle")
        page.wait_for_timeout(400)
        kpis = page.locator(".kpi").count()
        if kpis < 5:
            failures.append(f"metrics.html rendered only {kpis} KPI tiles")

        # ---- solutions.html ----
        # Not networkidle: this page embeds video elements that keep fetching
        # metadata, so "the network went quiet" never reliably happens. Wait for
        # the thing actually being asserted instead.
        page.goto(f"{base}/solutions.html", wait_until="load")
        page.wait_for_selector(".grid .card", timeout=15000)
        sol_cards = page.locator(".grid .card").count()
        if sol_cards < 20:
            failures.append(f"solutions.html rendered only {sol_cards} solution cards")
        if page.locator("video").count() < 1:
            failures.append("solutions.html showed no hosted demo video")

        # ---- onepager.html, solution mode ----
        first = page.locator('a[href^="onepager.html?solution="]').first
        slug = first.get_attribute("href") if first.count() else ""
        page.goto(f"{base}/{slug}", wait_until="load")
        page.wait_for_selector(".sheet h1", timeout=15000)
        if not page.locator(".sheet h1").count():
            failures.append("onepager solution mode rendered no sheet")
        if not page.locator(".rpanel.human").count():
            failures.append("onepager solution mode showed no community panel")

        # ---- onepager.html, agent mode: both review panels, never merged ----
        page.goto(f"{base}/onepager.html?agent=@aibast-agents-library/art-generator",
                  wait_until="load")
        # The source lives inside a collapsed <details>, so it is attached
        # but not visible until a reader opens it.
        page.wait_for_selector("details.src pre.code", state="attached", timeout=15000)
        title = page.locator(".sheet h1").inner_text() if page.locator(".sheet h1").count() else ""
        if not title:
            failures.append("onepager agent mode rendered no sheet")
        human = page.locator(".rpanel.human").count()
        machine = page.locator(".rpanel.machine").count()
        if human != 1 or machine != 1:
            failures.append(f"expected exactly one panel of each kind, got human={human} machine={machine}")
        if page.locator(".rpanel.machine .finding").count() < 1:
            failures.append("machine panel showed no findings or pass note")
        if "machine" not in page.locator(".rpanel.machine .rtag").inner_text().lower():
            failures.append("machine panel is not labelled as machine-produced")
        if not page.locator("details.src pre.code").count():
            failures.append("agent source was not streamed into the one-pager")

        # ---- onepager.html, aggregated-skill mode ----
        page.goto(f"{base}/onepager.html?skill=@cat-agent-skills/accessibility_pass",
                  wait_until="load")
        page.wait_for_selector(".sheet h1", timeout=15000)
        if not page.locator(".rpanel.machine").count():
            failures.append("aggregated skill got no machine review panel")
        if not page.locator("details.src pre.code").count():
            failures.append("converted skill.md was not streamed into its one-pager")
        if "MIT" not in page.locator(".subline").inner_text():
            failures.append("aggregated skill did not show its resolved licence")

        # ---- RAPPVision storyboard + remix, on the aggregated entry ----
        if not page.locator(".story .act").count():
            failures.append("aggregated skill got no generated walkthrough")
        slots = page.locator(".remix input[data-slot]").count()
        if slots < 1:
            failures.append("walkthrough exposed no remix slots")
        else:
            page.locator(".remix input[data-slot]").first.fill("Contoso, 400 stores")
            page.wait_for_timeout(150)
            with page.expect_download(timeout=10000) as dl:
                page.locator("#remixDl").click()
            name = dl.value.suggested_filename
            if "my-walkthrough" not in name:
                failures.append(f"remix download had unexpected name {name}")

        # ---- the mirroring, proved in the browser ----
        # The page derives agent.py from skill.md client-side. Compare that
        # output against the committed Python export: two independent
        # implementations, or the "one contract, two formats" claim is empty.
        import pathlib as _pl
        md_files = sorted(_pl.Path("skills/@cat-agent-skills").glob("*.md"))
        drift = []
        for sk in md_files:
            js = page.evaluate("(t) => RAPPMirror.exportAgent(t)",
                               sk.read_text(encoding="utf-8"))
            if js != sk.with_suffix(".py").read_text(encoding="utf-8"):
                drift.append(sk.stem)
        if drift:
            failures.append(f"browser export differs from committed agent.py: {drift[:3]}")
        mirrored = len(md_files)

        if not page.locator("#dlAgentPy").count():
            failures.append("no agent.py download offered beside skill.md")
        else:
            with page.expect_download(timeout=10000) as pyd:
                page.locator("#dlAgentPy").click()
            if not pyd.value.suggested_filename.endswith(".py"):
                failures.append("agent.py download had the wrong extension")

        browser.close()
    server.shutdown()

    if failures:
        print("FAIL:\n  " + "\n  ".join(failures))
        return 1
    print(f"headless OK: {cards} cards, search+chip filter, viewer, {kpis} KPIs, "
          f"{sol_cards} solutions, one-pager all modes, "
          f"{mirrored} skill.md/agent.py pairs re-derived in-browser and matching")
    return 0


if __name__ == "__main__":
    sys.exit(main())
