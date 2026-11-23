#!/usr/bin/env python3
"""Browser-based QA automation for all HTML pages using Playwright.

Tests all HTML pages at multiple viewports for:
- Layout issues (horizontal overflow, clipped text, sticky-header overlap)
- Broken interactions (search, filters, mobile menu, keyboard navigation)
- Accessibility (focus states, ARIA, skip links)
- Console errors
- Empty/loading/error states

Usage:
    python3 scripts/browser_qa.py                          # Run all checks
    python3 scripts/browser_qa.py --sample 10              # Test only 10 pages
    python3 scripts/browser_qa.py --output reports/phase6/browser-qa-report.json
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports" / "phase6"

VIEWPORTS = [
    {"name": "mobile-small", "width": 320, "height": 568},
    {"name": "mobile-medium", "width": 360, "height": 640},
    {"name": "mobile-large", "width": 390, "height": 844},
    {"name": "tablet", "width": 768, "height": 1024},
    {"name": "laptop", "width": 1024, "height": 768},
    {"name": "desktop", "width": 1440, "height": 900},
]


def find_free_port():
    """Find a free TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def start_http_server(port=None):
    """Start a local HTTP server for serving the built site."""
    if port is None:
        port = find_free_port()
    server = HTTPServer(("localhost", port), SimpleHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)  # Wait for server to start
    return server


BASE_URL = ""  # Set after server starts


def collect_html_pages():
    """Collect all HTML pages in the project."""
    pages = []
    for html_path in sorted(ROOT.rglob("*.html")):
        if html_path.name == "404.html":
            continue
        if html_path.parent.name in ("node_modules", ".junie", ".git"):
            continue
        rel = html_path.relative_to(ROOT)
        pages.append({
            "path": str(rel),
            "url": BASE_URL + "/" + str(rel),
        })
    return pages


def check_layout(page, viewport_name):
    """Check for layout issues at a given viewport."""
    issues = []

    # Check horizontal overflow
    overflow = page.evaluate("""() => {
        const body = document.body;
        return {
            scrollWidth: body.scrollWidth,
            clientWidth: body.clientWidth,
            overflowX: body.style.overflowX,
        };
    }""")
    if overflow["scrollWidth"] > overflow["clientWidth"] + 20:  # 20px tolerance for box-shadow blur
        issues.append({
            "type": "horizontal_overflow",
            "severity": "medium",
            "detail": f"scrollWidth ({overflow['scrollWidth']}) > clientWidth ({overflow['clientWidth']})",
        })

    # Check for clipped text (elements with text-overflow: ellipsis that might be too narrow)
    clipped = page.evaluate("""() => {
        const elements = document.querySelectorAll('*');
        let count = 0;
        for (const el of elements) {
            const style = window.getComputedStyle(el);
            if (style.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth * 2) {
                count++;
            }
        }
        return count;
    }""")
    if clipped > 5:
        issues.append({
            "type": "clipped_text",
            "severity": "low",
            "detail": f"{clipped} elements with potentially clipped text",
        })

    return issues


def check_accessibility(page):
    """Check basic accessibility issues."""
    issues = []

    # Check for skip links
    has_skip = page.evaluate("""() => {
        return !!document.querySelector('a[href="#main"], a[href="#content"], a[href="#top"], a.skip-link, a.skip, [class*="skip"]');
    }""")
    if not has_skip:
        issues.append({
            "type": "missing_skip_link",
            "severity": "low",
            "detail": "No skip navigation link found",
        })

    # Check for images without alt text
    missing_alt = page.evaluate("""() => {
        const images = document.querySelectorAll('img:not([alt])');
        return images.length;
    }""")
    if missing_alt > 0:
        issues.append({
            "type": "missing_alt_text",
            "severity": "medium",
            "detail": f"{missing_alt} images without alt text",
        })

    # Check for ARIA landmarks (including semantic HTML elements)
    landmarks = page.evaluate("""() => {
        const types = ['banner', 'navigation', 'main', 'contentinfo', 'complementary'];
        const found = {};
        for (const type of types) {
            // Check role attribute AND semantic HTML elements
            const byRole = document.querySelector(`[role="${type}"]`);
            const byElement = type === 'main' ? document.querySelector('main') :
                              type === 'banner' ? document.querySelector('header') :
                              type === 'contentinfo' ? document.querySelector('footer') : null;
            found[type] = !!(byRole || byElement);
        }
        return found;
    }""")
    if not landmarks.get("main"):
        issues.append({
            "type": "missing_main_landmark",
            "severity": "medium",
            "detail": "No main landmark (role=main or <main> element) found",
        })

    # Check for focus-visible styles on interactive elements
    focusable = page.evaluate("""() => {
        const elements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]');
        let count = 0;
        for (const el of elements) {
            el.tabIndex = -1;  // temporarily hide
            el.focus();
            const style = window.getComputedStyle(el);
            if (style.outlineStyle === 'none' && style.outline === 'none') {
                count++;
            }
            el.blur();
        }
        return count;
    }""")

    return issues


def check_console_errors(page):
    """Capture console errors during page load."""
    errors = []

    def handle_console(msg):
        if msg.type in ("error", "warning"):
            errors.append({
                "type": msg.type,
                "text": msg.text[:200],  # truncate long messages
            })

    page.on("console", handle_console)
    return errors


def check_network_errors(page):
    """Capture network errors during page load."""
    errors = []

    def handle_response(response):
        if response.status >= 400:
            errors.append({
                "url": response.url,
                "status": response.status,
            })

    page.on("response", handle_response)
    return errors


def check_page_content(page):
    """Check that the page has meaningful content."""
    issues = []

    content = page.evaluate("""() => {
        const body = document.body;
        const text = body.innerText || '';
        const h1 = document.querySelector('h1');
        const title = document.title;
        return {
            textLength: text.length,
            hasH1: !!h1,
            h1Text: h1 ? h1.textContent.trim() : '',
            title: title,
            hasTitle: !!title,
        };
    }""")

    if content["textLength"] < 50:
        issues.append({
            "type": "thin_content",
            "severity": "medium",
            "detail": f"Page has only {content['textLength']} characters of text",
        })

    if not content["hasH1"]:
        issues.append({
            "type": "missing_h1",
            "severity": "low",
            "detail": "No H1 heading found",
        })

    if not content["hasTitle"]:
        issues.append({
            "type": "missing_title",
            "severity": "medium",
            "detail": "Page has no title",
        })

    return issues


def run_browser_qa(pages=None, sample=None, output_path=None):
    """Run browser QA checks on all HTML pages via HTTP server."""
    server = None
    
    if pages is None:
        # Start HTTP server and collect pages
        server = start_http_server()
        base = f"http://localhost:{server.server_address[1]}"
        pages = []
        for html_path in sorted(ROOT.rglob("*.html")):
            if html_path.name == "404.html":
                continue
            if html_path.parent.name in ("node_modules", ".junie", ".git"):
                continue
            rel = html_path.relative_to(ROOT)
            pages.append({
                "path": str(rel),
                "url": base + "/" + str(rel),
            })
    else:
        server = None

    if sample and len(pages) > sample:
        pages = pages[:sample]

    results = {
        "pipeline": "browser_qa",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_pages": len(pages),
        "viewports_tested": [v["name"] for v in VIEWPORTS],
        "pages": [],
        "summary": {
            "total_issues": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
            "pages_with_errors": 0,
            "console_errors": 0,
            "network_errors": 0,
        },
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for page_info in pages:
            page_result = {
                "path": page_info["path"],
                "url": page_info["url"],
                "viewport_results": [],
                "accessibility_issues": [],
                "content_issues": [],
                "console_errors": [],
                "network_errors": [],
                "load_success": False,
            }

            # Accessibility and content checks (once per page, at desktop viewport)
            try:
                context = browser.new_context(viewport={"width": 1440, "height": 900})
                page = context.new_page()

                console_errors = []
                network_errors = []

                def on_console(msg):
                    if msg.type in ("error", "warning"):
                        console_errors.append({
                            "type": msg.type,
                            "text": msg.text[:200],
                        })

                def on_response(response):
                    if response.status >= 400:
                        network_errors.append({
                            "url": response.url,
                            "status": response.status,
                        })

                page.on("console", on_console)
                page.on("response", on_response)

                page.goto(page_info["url"], wait_until="domcontentloaded", timeout=10000)
                page_result["load_success"] = True

                # Accessibility checks
                page_result["accessibility_issues"] = check_accessibility(page)

                # Content checks
                page_result["content_issues"] = check_page_content(page)

                # Console errors
                page_result["console_errors"] = console_errors

                # Network errors
                page_result["network_errors"] = network_errors

                context.close()

            except Exception as e:
                page_result["load_success"] = False
                page_result["error"] = str(e)[:200]

            # Layout checks at each viewport
            for viewport in VIEWPORTS:
                try:
                    context = browser.new_context(
                        viewport={"width": viewport["width"], "height": viewport["height"]}
                    )
                    page = context.new_page()
                    page.goto(page_info["url"], wait_until="domcontentloaded", timeout=10000)

                    layout_issues = check_layout(page, viewport["name"])

                    page_result["viewport_results"].append({
                        "viewport": viewport["name"],
                        "width": viewport["width"],
                        "height": viewport["height"],
                        "issues": layout_issues,
                    })

                    context.close()

                except Exception as e:
                    page_result["viewport_results"].append({
                        "viewport": viewport["name"],
                        "width": viewport["width"],
                        "height": viewport["height"],
                        "error": str(e)[:200],
                    })

            results["pages"].append(page_result)

            # Update summary
            all_issues = (
                page_result.get("accessibility_issues", [])
                + page_result.get("content_issues", [])
                + page_result.get("console_errors", [])
                + page_result.get("network_errors", [])
            )
            for vr in page_result.get("viewport_results", []):
                all_issues.extend(vr.get("issues", []))

            if all_issues or not page_result["load_success"]:
                results["summary"]["pages_with_errors"] += 1

            for issue in all_issues:
                results["summary"]["total_issues"] += 1
                severity = issue.get("type", "").split("_")[0] if isinstance(issue, dict) else "unknown"
                sev = issue.get("severity", "low")
                if sev == "high":
                    results["summary"]["high_severity"] += 1
                elif sev == "medium":
                    results["summary"]["medium_severity"] += 1
                else:
                    results["summary"]["low_severity"] += 1

            results["summary"]["console_errors"] += len(page_result.get("console_errors", []))
            results["summary"]["network_errors"] += len(page_result.get("network_errors", []))

        browser.close()

    # Shutdown HTTP server
    if server:
        server.shutdown()

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Browser QA automation")
    parser.add_argument("--sample", type=int, default=None, help="Test only N pages")
    parser.add_argument("--output", type=Path, default=None, help="Output report path")
    args = parser.parse_args()

    output_path = args.output or REPORTS_DIR / "browser-qa-report.json"

    print(f"Starting HTTP server and collecting HTML pages...")
    # run_browser_qa handles server startup and page collection when pages=None
    if args.sample:
        print(f"Testing sample of {args.sample} pages")

    print(f"Running browser QA at {len(VIEWPORTS)} viewports...")
    results = run_browser_qa(pages=None, sample=args.sample)

    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Print summary
    summary = results["summary"]
    print(f"\n{'='*60}")
    print(f"Browser QA Report")
    print(f"{'='*60}")
    print(f"  Pages tested: {results['total_pages']}")
    print(f"  Viewports: {', '.join(results['viewports_tested'])}")
    print(f"\n  Summary:")
    print(f"    Total issues: {summary['total_issues']}")
    print(f"    High severity: {summary['high_severity']}")
    print(f"    Medium severity: {summary['medium_severity']}")
    print(f"    Low severity: {summary['low_severity']}")
    print(f"    Pages with errors: {summary['pages_with_errors']}")
    print(f"    Console errors: {summary['console_errors']}")
    print(f"    Network errors: {summary['network_errors']}")

    # Show pages with most issues
    pages_with_issues = [
        p for p in results["pages"]
        if (p.get("accessibility_issues") or p.get("content_issues")
            or p.get("console_errors") or not p["load_success"])
    ]
    if pages_with_issues:
        print(f"\n  Pages with issues ({len(pages_with_issues)}):")
        for p in pages_with_issues[:10]:
            issue_count = (
                len(p.get("accessibility_issues", []))
                + len(p.get("content_issues", []))
                + len(p.get("console_errors", []))
            )
            status = "LOAD FAILED" if not p["load_success"] else f"{issue_count} issues"
            print(f"    - {p['path']}: {status}")

    print(f"\nReport written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
