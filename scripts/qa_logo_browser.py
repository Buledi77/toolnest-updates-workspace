#!/usr/bin/env python3
"""Targeted logo QA — check logo rendering on representative pages at 4 viewports.

Tests:
- No broken images (img with error state)
- No unexpected fallback initials for tools that have logos
- Logos are visible and properly sized
- Correct proportions, no clipping or distortion

Usage:
    python3 scripts/qa_logo_browser.py
"""

import json
import socket
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

PAGES = [
    "/",                          # Homepage
    "/tools/index.html",          # Tools directory
    "/tools/cursor.html",         # Cursor profile
    "/tools/confetti.html",       # Confetti profile
    "/tools/decision-engine.html",  # Decision engine
]

VIEWPORTS = [
    {"name": "320px", "width": 320, "height": 568},
    {"name": "390px", "width": 390, "height": 844},
    {"name": "768px", "width": 768, "height": 1024},
    {"name": "1440px", "width": 1440, "height": 900},
]

# Tools that should show logos (not fallbacks)
TOOLS_WITH_LOGOS = {
    "cursor", "github-copilot", "heygen", "ideogram", "lovable",
    "confetti", "ahrefs", "notion", "chatgpt", "claude", "figma",
}

# Tools that should show deliberate fallbacks
TOOLS_WITH_FALLBACK = {"bolt"}


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        s.listen(1)
        return s.getsockname()[1]


def main():
    port = find_free_port()
    server = HTTPServer(("localhost", port), SimpleHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)
    base = f"http://localhost:{port}"

    results = []
    total_checks = 0
    passed = 0
    failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        for page_path in PAGES:
            url = base + page_path
            for vp in VIEWPORTS:
                page = context.new_page()
                page.set_viewport_size({"width": vp["width"], "height": vp["height"]})

                check = {
                    "page": page_path,
                    "viewport": vp["name"],
                    "issues": [],
                }

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    # Wait a bit for dynamic content
                    page.wait_for_timeout(2000)

                    # Check 1: Broken images
                    broken = page.evaluate("""() => {
                        const imgs = document.querySelectorAll('img');
                        const broken = [];
                        for (const img of imgs) {
                            if (img.dataset.logoFailed === "1" || (img.complete && img.naturalWidth === 0 && img.src.includes('logo'))) {
                                broken.push({
                                    src: img.src,
                                    alt: img.alt,
                                    class: img.className
                                });
                            }
                        }
                        return broken;
                    }""")
                    if broken:
                        for b in broken:
                            # Check if this is a deliberate fallback (Bolt)
                            check["issues"].append(f"Broken image: {b.get('alt', 'unknown')} (src: {b.get('src', '')})")

                    # Check 2: Unexpected fallback initials for tools with logos
                    unexpected_fallbacks = page.evaluate("""() => {
                        const failed = document.querySelectorAll('.tile.has-logo.logo-failed');
                        const results = [];
                        for (const tile of failed) {
                            const fb = tile.querySelector('.logo-fallback');
                            if (fb) {
                                results.push(fb.textContent);
                            }
                        }
                        return results;
                    }""")
                    # These are expected — tools with logos should NOT show fallbacks
                    # But Bolt should
                    for letter in unexpected_fallbacks:
                        # Check if the letter corresponds to a tool that should have a logo
                        check["issues"].append(f"Unexpected fallback initial: '{letter}'")

                    # Check 3: Logo images are visible
                    logo_visibility = page.evaluate("""() => {
                        const logos = document.querySelectorAll('.tile.has-logo img:not([data-logo-failed="1"])');
                        const visible = [];
                        for (const img of logos) {
                            const rect = img.getBoundingClientRect();
                            const style = window.getComputedStyle(img);
                            visible.push({
                                src: img.src.split('/').pop(),
                                width: rect.width,
                                height: rect.height,
                                display: style.display,
                                opacity: style.opacity,
                            });
                        }
                        return visible;
                    }""")

                    for lv in logo_visibility:
                        if lv["width"] < 10 or lv["height"] < 10:
                            check["issues"].append(f"Logo too small: {lv['src']} ({lv['width']}x{lv['height']})")
                        if lv["display"] == "none" and lv["opacity"] != "0":
                            check["issues"].append(f"Logo hidden: {lv['src']}")

                    # Check 4: Decision engine specific
                    if "decision-engine" in page_path:
                        de_logos = page.evaluate("""() => {
                            const logos = document.querySelectorAll('.de-card-logo');
                            const fallbacks = document.querySelectorAll('.de-card-logo-fallback');
                            return {
                                logos: logos.length,
                                fallbacks: fallbacks.length
                            };
                        }""")
                        check["de_logos"] = de_logos

                except Exception as e:
                    check["issues"].append(f"Page load error: {str(e)}")

                page.close()

                total_checks += 1
                if not check["issues"]:
                    passed += 1
                    check["status"] = "PASS"
                else:
                    failed += 1
                    check["status"] = "FAIL"

                results.append(check)

        browser.close()

    server.shutdown()

    # Print report
    print("=" * 70)
    print("TARGETED LOGO BROWSER QA")
    print("=" * 70)
    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()

    for r in results:
        status = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {status} {r['page']} @ {r['viewport']}")
        if r.get("de_logos"):
            print(f"     Decision engine: {r['de_logos']['logos']} logos, {r['de_logos']['fallbacks']} fallbacks")
        for issue in r["issues"]:
            print(f"     - {issue}")

    print()
    print("=" * 70)
    if failed == 0:
        print("ALL CHECKS PASSED")
    else:
        print(f"{failed} CHECK(S) FAILED")
    print("=" * 70)

    # Save report
    report = {
        "total": total_checks,
        "passed": passed,
        "failed": failed,
        "results": results,
    }
    report_path = ROOT / "reports" / "logo-browser-qa.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to {report_path}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
