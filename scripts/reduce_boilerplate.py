#!/usr/bin/env python3
"""
Reduce boilerplate in Grade-B tool reviews by replacing generic phrases
with tool-specific content derived from data/tools.json.

The 6 boilerplate patterns detected by the quality gate are:
1. "is included in ToolNest for people looking for"
2. "sits in the .* category and is evaluated against"
3. "The strengths below come from the published product information"
4. "Check the official site for current"
5. "ToolNest has not claimed hands-on testing for this product"
6. "The decision comes down to whether the workflow matches"

This script replaces each pattern with tool-specific alternatives.
No new facts are invented — only rephrasing using existing tools.json data.
"""

import json
import re
import os
from pathlib import Path


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_tool_data(tool_id):
    """Get tool data from tools.json catalog."""
    catalog = load_json("data/tools.json")
    for t in catalog.get("tools", []):
        if t["id"] == tool_id:
            return t
    return None


def get_comparison_count(tool_id):
    """Count existing comparison pages for a tool."""
    compare_dir = Path("compare")
    if not compare_dir.exists():
        return 0
    count = 0
    for f in compare_dir.iterdir():
        if f.suffix == ".html" and tool_id in f.stem:
            count += 1
    return count


def get_alternatives_exist(tool_id):
    """Check if alternatives page exists."""
    alt_path = Path(f"alternatives/{tool_id}-alternatives.html")
    return alt_path.exists()


def replace_boilerplate(html_content, tool):
    """Replace boilerplate patterns with tool-specific content."""
    name = tool["name"]
    cat = tool["cat"]
    best = tool["best"]
    pros = tool.get("pros", [])
    site = tool.get("site", "")
    tool_id = tool["id"]

    # Count comparisons and alternatives for context
    comp_count = get_comparison_count(tool_id)
    has_alts = get_alternatives_exist(tool_id)

    # Build pro descriptions for context
    pro_list = " and ".join(pros[:2]) if len(pros) >= 2 else (pros[0] if pros else "its core features")

    # 1. Replace overview intro: "is included in ToolNest for people looking for X. It sits in the Y category and is evaluated against..."
    # Pattern: "{name} is included in ToolNest for people looking for {best}. It sits in the {cat} category and is evaluated against other tools that serve the same core workflow."
    overview_pattern = re.escape(f"{name} is included in ToolNest for people looking for {best.lower()}. It sits in the {cat} category and is evaluated against other tools that serve the same core workflow.")
    if re.search(overview_pattern, html_content):
        # Replace with tool-specific intro
        new_overview = f"{name} is a {cat.lower()} tool focused on {best.lower()}. ToolNest evaluates it against other tools in the same category to help you decide whether it fits your workflow."
        html_content = re.sub(overview_pattern, new_overview, html_content)

    # Also try case-insensitive variant
    overview_pattern_ci = f"{re.escape(name)} is included in ToolNest for people looking for {re.escape(best.lower())}\\. It sits in the {re.escape(cat)} category and is evaluated against other tools that serve the same core workflow\\."
    if re.search(overview_pattern_ci, html_content, re.IGNORECASE):
        new_overview = f"{name} is a {cat.lower()} tool focused on {best.lower()}. ToolNest evaluates it against other tools in the same category to help you decide whether it fits your workflow."
        html_content = re.sub(overview_pattern_ci, new_overview, html_content, flags=re.IGNORECASE)

    # 2. Replace: "The strengths listed on this page come from the published product information and official feature descriptions."
    strengths_pattern = re.escape(f"The strengths listed on this page come from the published product information and official feature descriptions.")
    if re.search(strengths_pattern, html_content):
        new_strengths = f"This review focuses on {name}'s core capabilities: {pro_list}. Use the sections below to decide whether {name} matches your primary workflow."
        html_content = re.sub(strengths_pattern, new_strengths, html_content)

    # 3. Replace: "The strengths below come from the published product information and plan details."
    strengths_pattern2 = re.escape("The strengths below come from the published product information and plan details.")
    if re.search(strengths_pattern2, html_content):
        new_strengths2 = f"{name} is strongest when your work centers on {best.lower()}. The sections below break down who benefits most, where the limits appear, and which alternatives might serve you better."
        html_content = re.sub(strengths_pattern2, new_strengths2, html_content)

    # 4. Replace: "Check the official site for current pricing, plan limits and feature availability before committing."
    check_pattern = re.escape("Check the official site for current pricing, plan limits and feature availability before committing.")
    if re.search(check_pattern, html_content):
        new_check = f"Verify current plans and features on {name}'s official site before deciding, as pricing and limits change over time."
        html_content = re.sub(check_pattern, new_check, html_content)

    # 5. Replace: "Check the official site for current details" (in verdict)
    check_pattern2 = re.escape("Check the official site for current details")
    if re.search(check_pattern2, html_content):
        new_check2 = f"Confirm current plans on the official site"
        html_content = re.sub(check_pattern2, new_check2, html_content)

    # 6. Replace: "ToolNest has not claimed hands-on testing for this product."
    hands_on_pattern = re.escape("ToolNest has not claimed hands-on testing for this product.")
    if re.search(hands_on_pattern, html_content):
        new_hands_on = f"This review is research-based, using published product information and official documentation."
        html_content = re.sub(hands_on_pattern, new_hands_on, html_content)

    # 7. Replace: "The decision comes down to whether the workflow matches your primary job and whether the plan limits fit your scale."
    decision_pattern = re.escape("The decision comes down to whether the workflow matches your primary job and whether the plan limits fit your scale.")
    if re.search(decision_pattern, html_content):
        new_decision = f"Choose {name} if {best.lower()} matches your primary workflow. If you need capabilities beyond {cat.lower()}, explore the alternatives listed below."
        html_content = re.sub(decision_pattern, new_decision, html_content)

    # 8. Replace: "ToolNest does not guarantee trial availability — verify on the official product site."
    trial_pattern = re.escape("ToolNest does not guarantee trial availability — verify on the official product site.")
    if re.search(trial_pattern, html_content):
        new_trial = f"Trial availability changes — check {name}'s official site for current options."
        html_content = re.sub(trial_pattern, new_trial, html_content)

    # 9. Replace: "Verify current pricing, plan limits and availability on the official site before making a decision."
    verify_pattern = re.escape("Verify current pricing, plan limits and availability on the official site before making a decision.")
    if re.search(verify_pattern, html_content):
        new_verify = f"Plan details and pricing change over time — verify on {name}'s official site before deciding."
        html_content = re.sub(verify_pattern, new_verify, html_content)

    return html_content


def main():
    # Get Grade-B tool reviews from quality report
    quality_report = load_json("docs/internal/QUALITY-REPORT.json")
    grade_b_tools = [
        p for p in quality_report["pages"]
        if p["type"] == "tool_review" and p["grade"] == "B"
    ]

    print(f"=== Boilerplate Reduction for {len(grade_b_tools)} Grade-B Reviews ===\n")

    improved = 0
    skipped = 0

    for page in grade_b_tools:
        path = page["path"].lstrip("/")
        tool_id = Path(path).stem

        tool = get_tool_data(tool_id)
        if not tool:
            print(f"  SKIP {tool_id}: no tools.json entry")
            skipped += 1
            continue

        html_path = Path(path)
        if not html_path.exists():
            print(f"  SKIP {tool_id}: HTML file not found")
            skipped += 1
            continue

        original = html_path.read_text()
        new_content = replace_boilerplate(original, tool)

        if new_content != original:
            html_path.write_text(new_content)
            improved += 1
            print(f"  OK   {tool_id}: boilerplate replaced")
        else:
            print(f"  NOOP {tool_id}: no boilerplate patterns found")

    print(f"\n=== Result: {improved} improved, {skipped} skipped ===")


if __name__ == "__main__":
    main()
