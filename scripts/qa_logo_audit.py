#!/usr/bin/env python3
"""
qa_logo_audit.py — Comprehensive logo audit for all ToolNest tool review pages.

Checks each tool page for:
  1. Tool logo incorrectly placed in the navigation header
  2. Duplicate p-plate elements in the hero section
  3. Duplicate tile.has-logo elements in the hero section
  4. Both .wm (wordmark) and .tile (icon) logos in the same hero
  5. Missing hero logo when a logo file exists in assets/logos/
  6. Logo identity mismatch (wrong logo for the page's tool)

The script understands component boundaries (header vs hero vs body) and does
not flag legitimate related-tool logos elsewhere on the page.

Usage:
    python3 scripts/qa_logo_audit.py [--json]
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
DATA_FILE = ROOT / "data" / "tools.json"
LOGOS_DIR = ROOT / "assets" / "logos"

SKIP_SLUGS = {"index", "automation-budget-estimator"}


def load_tools_data():
    """Load tools.json and return a dict mapping slug -> tool info."""
    with open(DATA_FILE) as f:
        data = json.load(f)
    return {t["id"]: t for t in data["tools"]}


def extract_section(html, pattern):
    """Extract a section from HTML using a regex pattern. Returns None if not found."""
    m = re.search(pattern, html, re.DOTALL)
    return m.group(1) if m else None


def audit_page(slug, html, tools_data):
    """Audit a single tool page for logo issues. Returns a list of issue strings."""
    issues = []

    # --- Header checks ---
    header = extract_section(html, r'<header class="top"[^>]*>(.*?)</header>')
    if header:
        # Check for p-plate in header (tool logo in navigation)
        if 'class="p-plate"' in header:
            issues.append("NAV_LOGO: tool logo p-plate found in navigation header")
        # Check for tile.has-logo in header
        if "tile has-logo" in header:
            if not any("NAV_LOGO" in i for i in issues):
                issues.append("NAV_TILE: tile.has-logo found in navigation header")

    # --- Hero checks ---
    hero = extract_section(html, r'<section class="hero phero"[^>]*>(.*?)</section>')
    if hero:
        plate_count = len(re.findall(r'<div class="p-plate">', hero))
        tile_count = len(re.findall(r'class="tile has-logo"', hero))
        wm_count = len(re.findall(r'class="wm"', hero))

        # Duplicate p-plate
        if plate_count > 1:
            issues.append(f"DUP_PLATE: {plate_count} p-plate elements in hero (expected 1)")

        # Duplicate tile.has-logo
        if tile_count > 1:
            issues.append(f"DUP_TILE: {tile_count} tile.has-logo elements in hero (expected 0 or 1)")

        # Both .wm and .tile in same hero
        if wm_count > 0 and tile_count > 0:
            issues.append("MIXED_LOGO: both .wm wordmark and .tile icon found in hero")

        # No p-plate at all
        if plate_count == 0:
            issues.append("NO_PLATE: no p-plate found in hero section")

        # Logo identity check: if there's a data-logo attribute, it should match the slug
        data_logos = re.findall(r'data-logo="([^"]*)"', hero)
        for dl in data_logos:
            if dl and dl != slug:
                issues.append(f"IDENTITY_MISMATCH: data-logo='{dl}' but page slug is '{slug}'")

    else:
        issues.append("NO_HERO: no hero section found")

    # --- Missing logo check ---
    tool_info = tools_data.get(slug)
    if tool_info:
        logo_path = tool_info.get("logo", "")
        if logo_path:
            # Logo is defined in tools.json — check if it's rendered in the hero
            if hero:
                logo_filename = Path(logo_path).name
                if logo_filename not in hero:
                    issues.append(f"MISSING_RENDER: logo '{logo_path}' defined in tools.json but not rendered in hero")
        else:
            # No logo in tools.json — check if a logo file exists
            for ext in [".png", ".svg"]:
                logo_file = LOGOS_DIR / f"{slug}{ext}"
                if logo_file.exists():
                    issues.append(f"MISSING_DATA: logo file '{slug}{ext}' exists but not defined in tools.json")
                    break

    return issues


def main():
    tools_data = load_tools_data()

    all_issues = {}
    total_pages = 0
    pages_with_issues = 0

    for html_file in sorted(TOOLS_DIR.glob("*.html")):
        slug = html_file.stem
        if slug in SKIP_SLUGS:
            continue

        total_pages += 1
        html = html_file.read_text()
        issues = audit_page(slug, html, tools_data)

        if issues:
            pages_with_issues += 1
            all_issues[slug] = issues

    # Print results
    print(f"Logo Audit Report")
    print(f"=" * 60)
    print(f"Total pages audited: {total_pages}")
    print(f"Pages with issues: {pages_with_issues}")
    print(f"Clean pages: {total_pages - pages_with_issues}")
    print()

    if all_issues:
        print("ISSUES FOUND:")
        print("-" * 60)
        for slug, issues in sorted(all_issues.items()):
            print(f"\n  {slug}.html:")
            for issue in issues:
                print(f"    - {issue}")
        print()
    else:
        print("No issues found. All pages are clean.")
        print()

    # Summary by issue type
    if all_issues:
        issue_types = {}
        for issues in all_issues.values():
            for issue in issues:
                type_name = issue.split(":")[0]
                issue_types[type_name] = issue_types.get(type_name, 0) + 1
        print("Issue Summary:")
        for type_name, count in sorted(issue_types.items()):
            print(f"  {type_name}: {count}")
        print()

    # JSON output
    if "--json" in sys.argv:
        output = {
            "total_pages": total_pages,
            "pages_with_issues": pages_with_issues,
            "issues": all_issues
        }
        print(json.dumps(output, indent=2))

    # Exit code
    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
