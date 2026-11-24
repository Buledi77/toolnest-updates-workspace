#!/usr/bin/env python3
"""Structural validation for all 153 tool profile pages.

Checks each generated profile for:
- Correct tool identity (name, category, logo)
- Canonical URL
- Pricing section present
- Evidence/verification state
- Limitations section (if data exists)
- Alternatives section (if data exists)
- No broken internal links to tool profiles
- No unknown-price-as-free
- Affiliate disclosure present

Usage:
    python3 scripts/validate_tool_profiles.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_JSON_DIR = ROOT / "data" / "tools"
TOOLS_HTML_DIR = ROOT / "tools"


def load_tool(slug: str) -> dict:
    path = TOOLS_JSON_DIR / f"{slug}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_html(slug: str) -> str:
    path = TOOLS_HTML_DIR / f"{slug}.html"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def validate(slug: str) -> list[str]:
    """Return a list of issues found for a tool profile."""
    issues = []
    data = load_tool(slug)
    html_content = load_html(slug)

    if not data:
        issues.append(f"No JSON data for {slug}")
        return issues

    if not html_content:
        issues.append(f"No HTML file for {slug}")
        return issues

    identity = data.get("identity", {})
    name = identity.get("name", "")
    expected_slug = identity.get("slug", slug)

    # Check name appears in HTML (handle HTML entity escaping: & -> &amp;)
    if name:
        name_in_html = html_content.replace("&amp;", "&").lower()
        if name.lower() not in name_in_html:
            issues.append(f"Tool name '{name}' not found in HTML")

    # Check canonical URL
    canonical = f"/tools/{expected_slug}.html"
    if canonical not in html_content:
        issues.append(f"Canonical URL {canonical} not found")

    # Check category (handle HTML entity escaping)
    discovery = data.get("discovery", {})
    cats = discovery.get("categories", [])
    if cats:
        cat = cats[0]
        cat_in_html = html_content.replace("&amp;", "&").lower()
        if cat.lower() not in cat_in_html:
            issues.append(f"Category '{cat}' not found in HTML")

    # Check logo
    logo = identity.get("logo", "")
    if logo and logo not in html_content:
        issues.append(f"Logo '{logo}' not found in HTML")

    # Check pricing section
    if 'id="pricing"' not in html_content:
        issues.append("No pricing section found")

    # Check for unknown-price-as-free
    # If pricing is unknown, it should NOT say "Free" as the only pricing
    pricing = data.get("pricing", {})
    factual = data.get("factual_profile", {})
    has_plans = bool(pricing.get("plans", []))
    has_free_plan = pricing.get("freePlan") or factual.get("free_plan_status")

    if not has_plans and not has_free_plan:
        # No pricing data — check that HTML doesn't claim free
        if 'id="pricing"' in html_content:
            # Extract pricing section
            pricing_match = re.search(r'id="pricing".*?(?=<section|</main|</div class="p-main")', html_content, re.DOTALL)
            if pricing_match:
                pricing_html = pricing_match.group(0)
                # Check if it says "Free" without qualification
                if re.search(r'\bFree\b', pricing_html) and 'not confirmed' not in pricing_html.lower() and 'pending' not in pricing_html.lower():
                    issues.append("May incorrectly imply free pricing")

    # Check limitations section (if data exists)
    limitations = factual.get("limitations", [])
    if limitations:
        if 'id="limitations"' not in html_content:
            issues.append("Has limitations data but no limitations section")

    # Check alternatives section (if data exists)
    relationships = data.get("relationships", {})
    alternatives = relationships.get("alternatives", [])
    if alternatives:
        if 'id="alternatives"' not in html_content:
            issues.append("Has alternatives data but no alternatives section")

    # Check internal links to alternatives
    for alt_id in alternatives:
        alt_slug = alt_id if alt_id != "moz-pro" else "mozpro"
        alt_link = f"/tools/{alt_slug}.html"
        if alt_link not in html_content:
            issues.append(f"Alternative link {alt_link} missing")

    # Check affiliate disclosure
    if 'affiliate-disclosure.html' not in html_content:
        issues.append("No affiliate disclosure link")

    # Check best-for section
    editorial = data.get("editorial", {})
    best_for = editorial.get("best_for", [])
    if best_for:
        if 'id="best-for"' not in html_content:
            issues.append("Has best_for data but no best-for section")

    # Check capabilities section (if data exists with descriptions)
    capabilities = factual.get("capabilities", [])
    # Only flag if there are capabilities with actual descriptions
    has_real_capabilities = False
    for cap in capabilities:
        if isinstance(cap, dict) and cap.get("description"):
            has_real_capabilities = True
            break
        if isinstance(cap, str) and cap.strip():
            has_real_capabilities = True
            break
    if has_real_capabilities:
        if 'id="capabilities"' not in html_content:
            issues.append("Has capabilities data but no capabilities section")

    # Check evidence section (if claims exist)
    claims = data.get("claims", [])
    if claims:
        if 'id="evidence"' not in html_content:
            issues.append("Has claims data but no evidence section")

    # Check FAQ section
    if 'id="questions"' not in html_content:
        issues.append("No FAQ section found")

    # Check aside/sidebar
    if 'class="p-aside"' not in html_content:
        issues.append("No aside/sidebar found")

    # Check structured data
    if 'application/ld+json' not in html_content:
        issues.append("No structured data found")

    # Check breadcrumb
    if 'aria-label="Breadcrumb"' not in html_content:
        issues.append("No breadcrumb navigation found")

    # Check mobile viewport
    if 'viewport' not in html_content:
        issues.append("No viewport meta tag")

    return issues


def main():
    json_files = sorted(TOOLS_JSON_DIR.glob("*.json"))
    total = len(json_files)
    passed = 0
    failed = 0
    all_issues = {}

    print(f"Validating {total} tool profiles...\n")

    for json_path in json_files:
        slug = json_path.stem
        issues = validate(slug)
        if issues:
            failed += 1
            all_issues[slug] = issues
            print(f"  FAIL {slug}: {len(issues)} issue(s)")
            for issue in issues:
                print(f"    - {issue}")
        else:
            passed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {total} total")

    if all_issues:
        print(f"\nFailed profiles:")
        for slug, issues in sorted(all_issues.items()):
            print(f"  {slug}: {', '.join(issues[:3])}")
            if len(issues) > 3:
                print(f"    ... and {len(issues) - 3} more")

    # Summary stats
    print(f"\n{'='*60}")
    print(f"STRUCTURAL VALIDATION: {'PASS' if failed == 0 else f'{failed} FAILED'}")
    print(f"PROFILES CHECKED: {total}")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")


if __name__ == "__main__":
    main()
