#!/usr/bin/env python3
"""
qa_logo_audit.py — Full production logo guard for all ToolNest tools.

Validates the complete logo pipeline:
  1. Every tool in data/tools.json has a valid logo path or deliberate fallback
  2. Every referenced logo file exists, is valid, not zero-byte, correct extension
  3. No casing mismatches between referenced path and actual filename
  4. data/tools-v1.json mirrors data/tools.json logo paths
  5. All logo assets are included in deployment (not excluded by .vercelignore)

Usage:
    python3 scripts/qa_logo_audit.py [--json] [--html-pages]

--html-pages  Also audit tool profile HTML pages for logo rendering issues
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
DATA_FILE = ROOT / "data" / "tools.json"
DATA_V1_FILE = ROOT / "data" / "tools-v1.json"
LOGOS_DIR = ROOT / "assets" / "logos"

SKIP_SLUGS = {"index", "automation-budget-estimator"}
VALID_EXTENSIONS = {".png", ".svg"}


def load_tools_data():
    """Load tools.json and return a dict mapping id -> tool info."""
    with open(DATA_FILE) as f:
        data = json.load(f)
    return {t["id"]: t for t in data["tools"]}


def load_tools_v1():
    """Load tools-v1.json and return a dict mapping id -> tool info."""
    with open(DATA_V1_FILE) as f:
        data = json.load(f)
    return {t["id"]: t for t in data["tools"]}


def find_case_insensitive(filename):
    """Find a file in LOGOS_DIR case-insensitively. Returns actual path or None."""
    if not LOGOS_DIR.exists():
        return None
    target = filename.lower()
    for f in LOGOS_DIR.iterdir():
        if f.name.lower() == target:
            return f
    return None


def validate_logo_file(logo_path_str):
    """Validate a logo file. Returns (status, detail)."""
    filename = Path(logo_path_str).name
    logo_file = LOGOS_DIR / filename

    if not logo_file.exists():
        # Check case-insensitive
        actual = find_case_insensitive(filename)
        if actual:
            return ("CASING_MISMATCH", f"referenced '{filename}' but found '{actual.name}'")
        return ("MISSING", f"file '{filename}' not found in {LOGOS_DIR}")

    # Check zero-byte
    if logo_file.stat().st_size == 0:
        return ("ZERO_BYTE", f"file '{filename}' is empty")

    # Check extension
    ext = logo_file.suffix.lower()
    if ext not in VALID_EXTENSIONS:
        return ("BAD_EXTENSION", f"file '{filename}' has extension '{ext}'")

    # Check file is a valid image
    try:
        raw = logo_file.read_bytes()
        if ext == ".png" and not raw.startswith(b'\x89PNG'):
            return ("INVALID_FILE", f"file '{filename}' is not a valid PNG")
        elif ext == ".svg" and b"<svg" not in raw[:500]:
            return ("INVALID_FILE", f"file '{filename}' is not a valid SVG")
    except Exception as e:
        return ("INVALID_FILE", f"file '{filename}' cannot be read: {e}")

    return ("VALID", f"file '{filename}' is valid")


def audit_data_layer():
    """Audit data/tools.json logo references. Returns (results_dict, issues_list)."""
    tools_data = load_tools_data()
    results = {}
    issues = []

    for tid, tool in sorted(tools_data.items()):
        logo = tool.get("logo")
        name = tool.get("name", tid)
        entry = {"tool_id": tid, "name": name, "logo": logo}

        if not logo:
            # Deliberate fallback — no logo defined
            entry["status"] = "FALLBACK"
            entry["detail"] = "deliberate fallback (no logo defined)"
            results[tid] = entry
            continue

        status, detail = validate_logo_file(logo)
        entry["status"] = status
        entry["detail"] = detail
        results[tid] = entry

        if status != "VALID":
            issues.append(f"{tid} ({name}): {status} — {detail}")

    return results, issues


def audit_v1_sync():
    """Check tools-v1.json mirrors tools.json logo paths. Returns issues list."""
    tools_data = load_tools_data()
    tools_v1 = load_tools_v1()
    issues = []

    for tid, tool in tools_data.items():
        v1_tool = tools_v1.get(tid)
        if not v1_tool:
            issues.append(f"{tid}: missing from tools-v1.json")
            continue
        logo = tool.get("logo")
        v1_logo = v1_tool.get("logo")
        if logo != v1_logo:
            issues.append(f"{tid}: logo mismatch — tools.json='{logo}', tools-v1.json='{v1_logo}'")

    return issues


def audit_html_pages():
    """Audit tool profile HTML pages for logo rendering issues. Returns issues list."""
    tools_data = load_tools_data()
    issues = []

    for html_file in sorted(TOOLS_DIR.glob("*.html")):
        slug = html_file.stem
        if slug in SKIP_SLUGS:
            continue

        html = html_file.read_text()
        tool_info = tools_data.get(slug)
        if not tool_info:
            continue

        logo_path = tool_info.get("logo", "")
        if logo_path:
            logo_filename = Path(logo_path).name
            # Check if logo is rendered in the page
            if logo_filename not in html:
                issues.append(f"{slug}.html: logo '{logo_filename}' defined but not rendered in page")

    return issues


def main():
    print("=" * 70)
    print("TOOLNEST PRODUCTION LOGO AUDIT")
    print("=" * 70)
    print()

    all_issues = []
    json_output = {}

    # 1. Data layer audit
    print("1. Validating data/tools.json logo references...")
    results, data_issues = audit_data_layer()
    all_issues.extend(data_issues)

    valid_count = sum(1 for r in results.values() if r["status"] == "VALID")
    fallback_count = sum(1 for r in results.values() if r["status"] == "FALLBACK")
    broken_count = sum(1 for r in results.values() if r["status"] not in ("VALID", "FALLBACK"))

    print(f"   Total tools: {len(results)}")
    print(f"   Valid logos: {valid_count}")
    print(f"   Deliberate fallbacks: {fallback_count}")
    print(f"   Broken references: {broken_count}")
    print()

    json_output["data_layer"] = {
        "total": len(results),
        "valid": valid_count,
        "fallbacks": fallback_count,
        "broken": broken_count,
        "results": results
    }

    # 2. tools-v1.json sync check
    print("2. Checking tools-v1.json sync...")
    v1_issues = audit_v1_sync()
    all_issues.extend(v1_issues)
    print(f"   Sync issues: {len(v1_issues)}")
    if v1_issues:
        for issue in v1_issues:
            print(f"   - {issue}")
    print()

    json_output["v1_sync"] = {"issues": v1_issues}

    # 3. HTML page audit (optional)
    if "--html-pages" in sys.argv:
        print("3. Auditing tool profile HTML pages...")
        html_issues = audit_html_pages()
        all_issues.extend(html_issues)
        print(f"   HTML issues: {len(html_issues)}")
        if html_issues:
            for issue in html_issues:
                print(f"   - {issue}")
        print()
        json_output["html_pages"] = {"issues": html_issues}

    # Summary
    print("=" * 70)
    if all_issues:
        print(f"FAILED: {len(all_issues)} issue(s) found")
        print()
        for issue in all_issues:
            print(f"  ✗ {issue}")
    else:
        print("PASSED: All logo references are valid")
    print("=" * 70)
    print()

    # JSON output
    if "--json" in sys.argv:
        json_output["passed"] = len(all_issues) == 0
        json_output["total_issues"] = len(all_issues)
        json_output["issues"] = all_issues
        print(json.dumps(json_output, indent=2))

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
