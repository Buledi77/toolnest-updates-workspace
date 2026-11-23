#!/usr/bin/env python3
"""Capture screenshots for representative page families at key viewports."""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = ROOT / "reports" / "phase6" / "screenshots"

VIEWPORTS = [
    {"name": "mobile-320", "width": 320, "height": 568},
    {"name": "mobile-390", "width": 390, "height": 844},
    {"name": "tablet-768", "width": 768, "height": 1024},
    {"name": "desktop-1440", "width": 1440, "height": 900},
]

# Representative page families
PAGES = [
    ("Homepage", "index.html"),
    ("Tools Directory", "tools/index.html"),
    ("Category", "category/writing.html"),
    ("Tool Profile", "tools/notion.html"),
    ("Comparison", "compare/notion-vs-clickup.html"),
    ("Best-of", "best/best-writing-tools.html"),
    ("Goal Hub", "goals/index.html"),
    ("Decision Engine", "tools/decision-engine.html"),
    ("Stack Analyzer", "tools/stack-analyzer.html"),
    ("Overlap Checker", "tools/overlap-checker.html"),
    ("Workflow Explorer", "tools/workflow-explorer.html"),
    ("Author", "about.html"),
    ("Methodology", "how-we-test.html"),
    ("Affiliate Disclosure", "affiliate-disclosure.html"),
]


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        s.listen(1)
        return s.getsockname()[1]


def start_server(port=None):
    if port is None:
        port = find_free_port()
    server = HTTPServer(("localhost", port), SimpleHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)
    return server, port


def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    server, port = start_server()
    base = f"http://localhost:{port}"

    results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for family, path in PAGES:
            family_results = []
            for vp in VIEWPORTS:
                page = browser.new_page(viewport={"width": vp["width"], "height": vp["height"]})
                safe_name = family.replace(" ", "-").lower()
                filename = f"{safe_name}-{vp['name']}.png"
                filepath = SCREENSHOTS_DIR / filename

                try:
                    page.goto(f"{base}/{path}", wait_until="networkidle", timeout=15000)
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(filepath))
                    family_results.append({
                        "viewport": vp["name"],
                        "width": vp["width"],
                        "height": vp["height"],
                        "screenshot": str(filepath.relative_to(ROOT)),
                        "status": "ok",
                    })
                except Exception as e:
                    family_results.append({
                        "viewport": vp["name"],
                        "width": vp["width"],
                        "height": vp["height"],
                        "status": f"error: {e}",
                    })
                page.close()
            results.append({"family": family, "path": path, "screenshots": family_results})
        browser.close()

    # Save manifest
    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pages": results,
    }
    with open(SCREENSHOTS_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Screenshots saved to {SCREENSHOTS_DIR}")
    total = sum(len(r["screenshots"]) for r in results)
    ok = sum(1 for r in results for s in r["screenshots"] if s["status"] == "ok")
    print(f"Total: {total}, OK: {ok}, Errors: {total - ok}")


if __name__ == "__main__":
    main()
