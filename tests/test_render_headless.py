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
    print("SKIP: playwright not installed")
    sys.exit(0)


def free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
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

        browser.close()
    server.shutdown()

    if failures:
        print("FAIL:\n  " + "\n  ".join(failures))
        return 1
    print(f"headless OK: {cards} cards, search+chip filter, viewer, {kpis} KPIs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
