#!/usr/bin/env python3
"""Check alternatives pages for minimum content quality.

Usage:
    python3 scripts/check_alternatives_quality.py

Checks:
1. Alternatives pages with zero recommendation cards must be noindex
2. No indexed page links to empty alternatives stubs
3. Summary of alternatives page quality
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_alternatives_quality():
    """Check all alternatives pages for quality issues."""
    alt_dir = ROOT / "alternatives"
    errors = []
    warnings = []

    # Find all alternatives pages
    empty_stubs = []
    with_content_noindex = []
    indexed_with_cards = []

    for f in sorted(alt_dir.glob("*.html")):
        if f.name == "index.html":
            continue  # Skip the alternatives index page
        content = f.read_text(encoding="utf-8")
        cards = len(re.findall(r'<article class="p-rank"', content))
        robots = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', content)
        is_noindex = robots and "noindex" in robots.group(1)

        if cards == 0:
            if is_noindex:
                empty_stubs.append(f.name)
            else:
                errors.append(f"{f.name}: zero cards but not noindex")
        elif is_noindex:
            with_content_noindex.append((f.name, cards))
        else:
            indexed_with_cards.append((f.name, cards))

    # Check for indexed pages linking to empty stubs
    empty_stub_names = {s for s in empty_stubs}
    for html_file in ROOT.rglob("*.html"):
        if "node_modules" in str(html_file) or ".git" in str(html_file):
            continue
        # Skip alternatives directory files
        if "alternatives" in html_file.parts:
            continue
        content = html_file.read_text(encoding="utf-8", errors="replace")
        rel = str(html_file.relative_to(ROOT))
        for stub in empty_stub_names:
            if f"alternatives/{stub}" in content:
                errors.append(f"{rel} links to empty stub {stub}")

    # Report
    print(f"Alternatives Quality Check")
    print(f"==========================")
    print(f"Indexed with cards: {len(indexed_with_cards)}")
    print(f"Noindex with content: {len(with_content_noindex)}")
    print(f"Empty stubs (noindex): {len(empty_stubs)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if errors:
        print(f"\nErrors:")
        for e in errors:
            print(f"  ✗ {e}")

    if warnings:
        print(f"\nWarnings:")
        for w in warnings:
            print(f"  ⚠ {w}")

    if not errors:
        print(f"\n✓ All checks passed")

    return errors


if __name__ == "__main__":
    errors = check_alternatives_quality()
    sys.exit(1 if errors else 0)
