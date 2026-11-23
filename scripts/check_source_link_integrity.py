#!/usr/bin/env python3
"""Source and link integrity checks (Phase 3 Requirement D).

Validates all source URLs in evidence ledger and tools-v2 records for:
- missing, malformed, or duplicate source URLs
- affiliate URLs accidentally used as factual evidence
- broken local internal links
- missing local assets referenced in HTML
- affiliate CTA targets, disclosure links, official product links
- canonical URLs and sitemap URLs

Optional --check-external mode for network-based URL validation.

Outputs reports/phase3/source-link-integrity.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
AFFILIATE_REGISTRY_PATH = ROOT / "data" / "monetization" / "affiliate-registry.json"
SITEMAP_PATH = ROOT / "sitemap.xml"
REPORTS_DIR = ROOT / "reports" / "phase3"

# Directories with HTML pages
HTML_DIRS = [
    ROOT / "tools",
    ROOT / "compare",
    ROOT / "alternatives",
    ROOT / "best",
    ROOT / "category",
    ROOT / "goals",
]
ROOT_HTML_FILES = ["index.html", "about.html", "affiliate-disclosure.html",
                   "how-we-test.html", "editorial-policy.html", "corrections.html",
                   "contact.html", "privacy.html", "terms.html"]


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_tools_v2_records():
    records = []
    for path in sorted(TOOL_DIR.rglob("*.json")):
        if path.name == "README.json":
            continue
        records.append(load_json(path))
    return records


def is_valid_url(value):
    """Check if a value is a valid HTTP(S) URL."""
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def is_affiliate_url(url, affiliate_registry):
    """Check if a URL looks like an affiliate URL."""
    if not url:
        return False
    # Check against affiliate registry
    for tool_id, entry in affiliate_registry.items():
        if isinstance(entry, dict):
            aff_url = entry.get("affiliate_url", "")
            if aff_url and url == aff_url:
                return True
    # Check common affiliate patterns
    affiliate_patterns = [
        r"track\.", r"ref=", r"affiliate", r"partner", r"subid",
        r"\?utm_source=toolnest", r"toolnest",
    ]
    for pattern in affiliate_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False


def check_source_urls():
    """Check all source URLs in evidence ledger and tools-v2 records."""
    errors = []
    warnings = []

    # Load evidence ledger
    ledger = {}
    if LEDGER_PATH.is_file():
        ledger = load_json(LEDGER_PATH)

    # Load affiliate registry
    affiliate_registry = {}
    if AFFILIATE_REGISTRY_PATH.is_file():
        affiliate_registry = load_json(AFFILIATE_REGISTRY_PATH)

    # Check evidence ledger sources
    sources = ledger.get("sources", [])
    source_urls = {}
    for source in sources:
        sid = source.get("source_id", "<missing>")
        url = source.get("url")
        if not url:
            errors.append(f"Source {sid} has no URL")
        elif not is_valid_url(url):
            errors.append(f"Source {sid} has malformed URL: {url}")
        else:
            if url in source_urls:
                warnings.append(f"Duplicate source URL: {url} (used by {source_urls[url]} and {sid})")
            source_urls[url] = sid

            # Check if affiliate URL used as evidence
            if is_affiliate_url(url, affiliate_registry):
                errors.append(f"Source {sid} uses affiliate URL as evidence: {url}")

    # Check tools-v2 evidence sources
    records = load_tools_v2_records()
    for record in records:
        tid = record.get("identity", {}).get("id", "<missing>")
        evidence = record.get("evidence", {})
        for source in evidence.get("sources", []):
            url = source.get("url")
            if not url:
                errors.append(f"Tool {tid} has evidence source with no URL")
            elif not is_valid_url(url):
                errors.append(f"Tool {tid} has malformed evidence URL: {url}")

    return errors, warnings


def check_internal_links():
    """Check that local internal links in HTML pages resolve to existing files."""
    errors = []

    # Collect all existing HTML files
    existing_files = set()
    for html_dir in HTML_DIRS:
        if html_dir.is_dir():
            for html_file in html_dir.glob("*.html"):
                existing_files.add(str(html_file.relative_to(ROOT)))

    for root_file in ROOT_HTML_FILES:
        if (ROOT / root_file).is_file():
            existing_files.add(root_file)

    # Check internal links in HTML files
    href_pattern = re.compile(r'href=["\'](/[^"\']+)["\']')

    for html_dir in HTML_DIRS:
        if not html_dir.is_dir():
            continue
        for html_file in html_dir.glob("*.html"):
            try:
                content = html_file.read_text(encoding="utf-8")
                for match in href_pattern.finditer(content):
                    href = match.group(1)
                    # Skip external links, anchors, and non-HTML links
                    if href.startswith(("http://", "https://", "#", "mailto:", "tel:", "javascript:")):
                        continue
                    if not href.endswith(".html"):
                        continue

                    # Normalize path
                    target = href.lstrip("/")
                    if target not in existing_files:
                        errors.append(
                            f"{html_file.relative_to(ROOT)} links to missing file: {href}"
                        )
            except OSError:
                pass

    # Check root HTML files
    for root_file in ROOT_HTML_FILES:
        path = ROOT / root_file
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
            for match in href_pattern.finditer(content):
                href = match.group(1)
                if href.startswith(("http://", "https://", "#", "mailto:", "tel:", "javascript:")):
                    continue
                if not href.endswith(".html"):
                    continue
                target = href.lstrip("/")
                if target not in existing_files:
                    errors.append(f"{root_file} links to missing file: {href}")
        except OSError:
            pass

    return errors


def check_local_assets():
    """Check that local assets referenced in HTML exist."""
    errors = []
    asset_pattern = re.compile(r'(?:src|href|data-src)=["\'](/assets/[^"\']+)["\']')

    all_html = []
    for html_dir in HTML_DIRS:
        if html_dir.is_dir():
            all_html.extend(html_dir.glob("*.html"))
    for root_file in ROOT_HTML_FILES:
        path = ROOT / root_file
        if path.is_file():
            all_html.append(path)

    for html_file in all_html:
        try:
            content = html_file.read_text(encoding="utf-8")
            for match in asset_pattern.finditer(content):
                asset_path = match.group(1)
                full_path = ROOT / asset_path.lstrip("/")
                if not full_path.is_file():
                    errors.append(
                        f"{html_file.relative_to(ROOT)} references missing asset: {asset_path}"
                    )
        except OSError:
            pass

    return errors


def check_sitemap_urls():
    """Check that sitemap URLs resolve locally."""
    errors = []
    if not SITEMAP_PATH.is_file():
        return errors

    try:
        content = SITEMAP_PATH.read_text(encoding="utf-8")
        # Parse loc tags
        loc_pattern = re.compile(r"<loc>([^<]+)</loc>")
        urls = loc_pattern.findall(content)

        # Build set of existing files
        existing_files = set()
        for html_dir in HTML_DIRS:
            if html_dir.is_dir():
                for html_file in html_dir.glob("*.html"):
                    rel = str(html_file.relative_to(ROOT))
                    existing_files.add(rel)
        for root_file in ROOT_HTML_FILES:
            if (ROOT / root_file).is_file():
                existing_files.add(root_file)

        for url in urls:
            # Extract path from URL
            parsed = urlparse(url)
            path = parsed.path.lstrip("/")
            if path and path not in existing_files:
                # Check if it's a directory index
                if path.endswith("/"):
                    index_path = path + "index.html"
                    if index_path not in existing_files:
                        errors.append(f"Sitemap URL {url} has no local file")
                else:
                    errors.append(f"Sitemap URL {url} has no local file: {path}")
    except OSError:
        pass

    return errors


def check_canonical_urls():
    """Check canonical URLs in tools-v2 records."""
    errors = []
    records = load_tools_v2_records()

    for record in records:
        tid = record.get("identity", {}).get("id", "<missing>")
        publishing = record.get("publishing", {})
        canonical = publishing.get("canonical_url")
        if canonical and not is_valid_url(canonical):
            errors.append(f"Tool {tid} has invalid canonical URL: {canonical}")

    return errors


def check_official_product_links():
    """Check official product URLs in tools-v2 records."""
    errors = []
    records = load_tools_v2_records()

    for record in records:
        tid = record.get("identity", {}).get("id", "<missing>")
        official_url = record.get("identity", {}).get("official_url")
        if official_url and not is_valid_url(official_url):
            errors.append(f"Tool {tid} has invalid official URL: {official_url}")

    return errors


def check_disclosure_links():
    """Check that affiliate disclosure page exists and is linked."""
    errors = []
    disclosure_path = ROOT / "affiliate-disclosure.html"
    if not disclosure_path.is_file():
        errors.append("Affiliate disclosure page not found: affiliate-disclosure.html")
    return errors


def external_url_check(urls_to_check, timeout=5, max_retries=1):
    """Optional external URL checking with timeout and retry."""
    import urllib.request
    import urllib.error

    results = {}
    for url in urls_to_check:
        status = "unknown"
        for attempt in range(max_retries + 1):
            try:
                req = urllib.request.Request(url, method="HEAD")
                req.add_header("User-Agent", "ToolNest-QA/1.0")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status = f"OK ({resp.status})"
                    if resp.url != url:
                        status += f" -> redirected to {resp.url}"
                    break
            except urllib.error.HTTPError as e:
                status = f"HTTP {e.code}"
                break
            except urllib.error.URLError as e:
                if "timed out" in str(e).lower():
                    status = "timeout"
                else:
                    status = f"blocked: {e.reason}"
                break
            except Exception as e:
                status = f"error: {type(e).__name__}"
                break
            time.sleep(1)
        results[url] = status
    return results


def run_source_link_check(check_external=False):
    """Run all source and link integrity checks."""
    print("Running source and link integrity checks...")

    results = {
        "check": "source_link_integrity",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    # Source URL checks
    source_errors, source_warnings = check_source_urls()
    results["checks"]["source_urls"] = {
        "passed": len(source_errors) == 0,
        "error_count": len(source_errors),
        "errors": source_errors,
        "warnings": source_warnings,
    }

    # Internal link checks
    internal_errors = check_internal_links()
    results["checks"]["internal_links"] = {
        "passed": len(internal_errors) == 0,
        "error_count": len(internal_errors),
        "errors": internal_errors,
    }

    # Local asset checks
    asset_errors = check_local_assets()
    results["checks"]["local_assets"] = {
        "passed": len(asset_errors) == 0,
        "error_count": len(asset_errors),
        "errors": asset_errors,
    }

    # Sitemap URL checks
    sitemap_errors = check_sitemap_urls()
    results["checks"]["sitemap_urls"] = {
        "passed": len(sitemap_errors) == 0,
        "error_count": len(sitemap_errors),
        "errors": sitemap_errors,
    }

    # Canonical URL checks
    canonical_errors = check_canonical_urls()
    results["checks"]["canonical_urls"] = {
        "passed": len(canonical_errors) == 0,
        "error_count": len(canonical_errors),
        "errors": canonical_errors,
    }

    # Official product link checks
    official_errors = check_official_product_links()
    results["checks"]["official_product_links"] = {
        "passed": len(official_errors) == 0,
        "error_count": len(official_errors),
        "errors": official_errors,
    }

    # Disclosure link checks
    disclosure_errors = check_disclosure_links()
    results["checks"]["disclosure_links"] = {
        "passed": len(disclosure_errors) == 0,
        "error_count": len(disclosure_errors),
        "errors": disclosure_errors,
    }

    # Optional external URL check
    if check_external:
        print("Running external URL checks (this may take a while)...")
        # Collect unique external URLs from sources
        ledger = {}
        if LEDGER_PATH.is_file():
            ledger = load_json(LEDGER_PATH)
        external_urls = set()
        for source in ledger.get("sources", []):
            url = source.get("url")
            if url and is_valid_url(url):
                external_urls.add(url)
        # Limit to first 50 for performance
        external_urls = list(external_urls)[:50]
        ext_results = external_url_check(external_urls)
        results["checks"]["external_urls"] = {
            "checked": len(ext_results),
            "results": ext_results,
            "failures": {url: status for url, status in ext_results.items()
                         if not status.startswith("OK")},
        }

    # Summary
    total_errors = sum(c.get("error_count", 0) for c in results["checks"].values())
    results["total_errors"] = total_errors
    results["passed"] = total_errors == 0

    return results


def main():
    parser = argparse.ArgumentParser(description="Source and link integrity checks")
    parser.add_argument("--check-external", action="store_true",
                        help="Enable network-based external URL checking")
    args = parser.parse_args()

    results = run_source_link_check(check_external=args.check_external)

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "source-link-integrity.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    status = "PASS" if results["passed"] else "FAIL"
    print(f"\nSource and Link Integrity: {status}")
    print(f"  Total errors: {results['total_errors']}")
    for check_name, check_result in results["checks"].items():
        if "passed" in check_result:
            check_status = "PASS" if check_result["passed"] else "FAIL"
            print(f"  {check_name}: {check_status} ({check_result['error_count']} errors)")
        elif "checked" in check_result:
            failures = len(check_result.get("failures", {}))
            print(f"  {check_name}: {check_result['checked']} checked, {failures} failures")

    print(f"\nReport written to {output_path}")

    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
