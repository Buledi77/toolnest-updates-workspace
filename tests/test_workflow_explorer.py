#!/usr/bin/env python3
"""Deterministic validation tests for the Workflow Explorer."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_MAPS = ROOT / "docs" / "internal" / "WORKFLOW-MAPS.json"
EXPLORER_HTML = ROOT / "tools" / "workflow-explorer.html"
ALLOWLIST = ROOT / "data" / "index-allowlist.json"

errors = []
passed = 0

def check(condition, msg):
    global passed, errors
    if condition:
        passed += 1
    else:
        errors.append(msg)
        print(f"  FAIL: {msg}")

def info(msg):
    print(f"  INFO: {msg}")

def test_workflow_maps_data():
    """Validate WORKFLOW-MAPS.json structure."""
    print("\n=== WORKFLOW-MAPS.json validation ===")
    data = json.loads(WORKFLOW_MAPS.read_text(encoding="utf-8"))

    check(data.get("schema_version") == "workflow-maps-v1", "Schema version is workflow-maps-v1")
    check(data.get("total_workflows") == 9, "Total workflows is 9")

    workflows = data.get("workflows", [])
    check(len(workflows) == 9, f"9 workflows present (got {len(workflows)})")

    valid_ids = set()
    valid_confidence = {"high", "medium", "low"}
    all_tool_ids = set()
    stage_counts = []

    for w in workflows:
        gid = w.get("goal_id", "")
        check(gid, "Each workflow has a goal_id")
        check(gid not in valid_ids, f"No duplicate goal_id: {gid}")
        valid_ids.add(gid)

        check(bool(w.get("goal_label")), f"goal_label present for {gid}")
        check(len(w.get("stages", [])) == 4, f"4 stages for {gid}")

        # Check stage numbering
        stages = w.get("stages", [])
        for i, s in enumerate(stages):
            check(s.get("step") == i + 1, f"Stage step numbering for {gid}")
            check(bool(s.get("name")), f"Stage name for {gid}")
            check(bool(s.get("description")), f"Stage description for {gid}")

        stage_counts.append(len(stages))

        # Decision questions
        dq = w.get("decision_questions", [])
        check(len(dq) > 0, f"At least 1 decision question for {gid}")

        # Candidate tools
        tools = w.get("candidate_tools", [])
        check(len(tools) > 0, f"At least 1 candidate tool for {gid}")
        for t in tools:
            all_tool_ids.add(t)
        # Check no duplicate tools within a workflow
        check(len(tools) == len(set(tools)), f"No duplicate tools in {gid}")

        # Comparisons
        comps = w.get("relevant_comparisons", [])
        check(len(comps) == w.get("comparison_count", -1), f"comparison_count matches for {gid}")
        for c in comps:
            check(c.startswith("/compare/"), f"Comparison path format for {gid}: {c}")

        # Alternatives
        alts = w.get("relevant_alternatives", [])
        check(len(alts) == w.get("alternatives_count", -1), f"alternatives_count matches for {gid}")
        for a in alts:
            check(a.startswith("/alternatives/"), f"Alternatives path format for {gid}: {a}")

        # Confidence
        conf = w.get("evidence_confidence", "")
        check(conf in valid_confidence, f"Valid confidence for {gid}: {conf}")

        # Unresolved gaps
        gaps = w.get("unresolved_gaps", [])
        check(isinstance(gaps, list), f"unresolved_gaps is a list for {gid}")

    # Summary checks
    summary = data.get("summary", {})
    check(summary.get("total_candidate_tools") == 66, f"Summary total_candidate_tools is 66")
    check(summary.get("total_comparisons") == 76, f"Summary total_comparisons is 76")
    check(summary.get("total_alternatives") == 66, f"Summary total_alternatives is 66")

    conf_dist = summary.get("confidence_distribution", {})
    check(conf_dist.get("high", 0) == 7, "7 high-confidence workflows")
    check(conf_dist.get("medium", 0) == 2, "2 medium-confidence workflows")

    info(f"Total unique tool IDs across workflows: {len(all_tool_ids)}")

def test_explorer_html():
    """Validate the Workflow Explorer HTML page."""
    print("\n=== Workflow Explorer HTML validation ===")
    check(EXPLORER_HTML.exists(), "workflow-explorer.html exists")

    content = EXPLORER_HTML.read_text(encoding="utf-8")

    # SEO checks
    title_match = re.search(r"<title>(.*?)</title>", content)
    check(bool(title_match), "Has <title> tag")
    if title_match:
        title = title_match.group(1)
        check(50 <= len(title) <= 60, f"Title length 50-60 chars (got {len(title)})")
        check("Workflow Explorer" in title, "Title contains 'Workflow Explorer'")

    desc_match = re.search(r'<meta name="description" content="([^"]*)"', content)
    check(bool(desc_match), "Has meta description")
    if desc_match:
        desc = desc_match.group(1)
        check(140 <= len(desc) <= 160, f"Description length 140-160 chars (got {len(desc)})")

    canonical = re.search(r'<link rel="canonical" href="([^"]*)"', content)
    check(bool(canonical), "Has canonical link")
    if canonical:
        check("workflow-explorer" in canonical.group(1), "Canonical contains workflow-explorer")

    h1_count = len(re.findall(r"<h1>", content, re.IGNORECASE))
    check(h1_count == 1, f"Exactly 1 H1 (got {h1_count})")

    check('lang="en"' in content, 'Has lang="en"')
    check('og-default.png' in content, "Has og:image reference")

    # Breadcrumbs
    breadcrumb_count = len(re.findall(r'"@type"\s*:\s*"BreadcrumbList"', content))
    check(breadcrumb_count == 1, f"Exactly 1 BreadcrumbList schema (got {breadcrumb_count})")

    # Workflow data embedded
    check('"goal_id": "write-better-english"' in content, "Contains write-better-english workflow")
    check('"goal_id": "organise-my-work"' in content, "Contains organise-my-work workflow")
    check('"goal_id": "add-voice-to-videos"' in content, "Contains add-voice-to-videos workflow")
    check('"goal_id": "edit-video-podcasts"' in content, "Contains edit-video-podcasts workflow")
    check('"goal_id": "write-ad-copy"' in content, "Contains write-ad-copy workflow")
    check('"goal_id": "get-search-traffic"' in content, "Contains get-search-traffic workflow")
    check('"goal_id": "sell-online"' in content, "Contains sell-online workflow")
    check('"goal_id": "launch-online-course"' in content, "Contains launch-online-course workflow")
    check('"goal_id": "launch-a-website"' in content, "Contains launch-a-website workflow")

    # Accessibility
    check('role="radiogroup"' in content, "Has radiogroup role for workflow selection")
    check('aria-live="polite"' in content, "Has aria-live polite for results")
    check('role="tablist"' in content, "Has tablist role for stage navigation")
    check('aria-checked' in content, "Has aria-checked attributes")
    check('aria-selected' in content, "Has aria-selected attributes")

    # Query string validation
    check("VALID_IDS" in content, "Has VALID_IDS for query validation")
    check("restoreFromQuery" in content, "Has restoreFromQuery function")
    check("updateQueryString" in content, "Has updateQueryString function")
    check("clearQueryString" in content, "Has clearQueryString function")

    # Reset functionality
    check("weReset" in content, "Has reset button")

    # Keyboard support
    check("ArrowDown" in content, "Has ArrowDown keyboard handler")
    check("ArrowUp" in content, "Has ArrowUp keyboard handler")
    check("ArrowRight" in content, "Has ArrowRight keyboard handler")
    check("ArrowLeft" in content, "Has ArrowLeft keyboard handler")
    check('"Home"' in content, "Has Home key handler")
    check('"End"' in content, "Has End key handler")

    # No horizontal overflow
    check("overflow-x:clip" in content or "overflow-x: hidden" in content or "max-width" in content,
          "Has overflow control")

    # Substantial static content
    check("How it works" in content, "Has 'How it works' section")
    check("Why workflows matter" in content, "Has 'Why workflows matter' section")
    check("Workflow data summary" in content, "Has 'Workflow data summary' section")

def test_allowlist():
    """Validate the page is in the index allowlist."""
    print("\n=== Index allowlist validation ===")
    data = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    paths = data.get("paths", [])
    check("/tools/workflow-explorer.html" in paths, "workflow-explorer.html in index-allowlist.json")

def test_no_invented_data():
    """Verify no invented workflows, tools, or capabilities."""
    print("\n=== No invented data validation ===")
    maps_data = json.loads(WORKFLOW_MAPS.read_text(encoding="utf-8"))
    explorer_content = EXPLORER_HTML.read_text(encoding="utf-8")

    # Extract goal_ids from WORKFLOW-MAPS
    maps_ids = {w["goal_id"] for w in maps_data["workflows"]}

    # Extract goal_ids from Explorer
    explorer_ids = set(re.findall(r'"goal_id":\s*"([^"]*)"', explorer_content))

    check(explorer_ids == maps_ids, "Explorer workflow IDs match WORKFLOW-MAPS exactly")
    check(len(explorer_ids) == 9, "Explorer has exactly 9 workflows")

    # Check no invented tool IDs
    maps_tools = set()
    for w in maps_data["workflows"]:
        maps_tools.update(w.get("candidate_tools", []))

    explorer_tools = set(re.findall(r'"candidate_tools":\s*\[([^\]]*)\]', explorer_content))
    # Parse tool lists
    for match in re.finditer(r'"candidate_tools":\s*\[([^\]]*)\]', explorer_content):
        tools_str = match.group(1)
        tools = set(re.findall(r'"([^"]*)"', tools_str))
        for t in tools:
            check(t in maps_tools, f"Tool {t} exists in WORKFLOW-MAPS")

def test_confidence_status():
    """Validate confidence statuses are correct."""
    print("\n=== Confidence status validation ===")
    maps_data = json.loads(WORKFLOW_MAPS.read_text(encoding="utf-8"))
    explorer_content = EXPLORER_HTML.read_text(encoding="utf-8")

    for w in maps_data["workflows"]:
        gid = w["goal_id"]
        conf = w["evidence_confidence"]
        check(f'"evidence_confidence": "{conf}"' in explorer_content,
              f"Confidence '{conf}' for {gid} in Explorer")

def test_empty_state():
    """Validate empty state handling."""
    print("\n=== Empty state validation ===")
    content = EXPLORER_HTML.read_text(encoding="utf-8")
    check("weResult" in content, "Has result container for empty state")
    check("display:none" in content, "Result hidden by default (empty state)")

def test_duplicate_detection():
    """Validate no duplicate stages or tools."""
    print("\n=== Duplicate detection ===")
    maps_data = json.loads(WORKFLOW_MAPS.read_text(encoding="utf-8"))

    for w in maps_data["workflows"]:
        gid = w["goal_id"]
        tools = w.get("candidate_tools", [])
        check(len(tools) == len(set(tools)), f"No duplicate tools in {gid}")

        stages = w.get("stages", [])
        stage_names = [s.get("name") for s in stages]
        check(len(stage_names) == len(set(stage_names)), f"No duplicate stage names in {gid}")

def test_missing_links():
    """Validate comparison and alternatives links exist."""
    print("\n=== Missing links validation ===")
    maps_data = json.loads(WORKFLOW_MAPS.read_text(encoding="utf-8"))

    for w in maps_data["workflows"]:
        gid = w["goal_id"]
        for comp in w.get("relevant_comparisons", []):
            comp_path = ROOT / comp.lstrip("/")
            check(comp_path.exists(), f"Comparison file exists: {comp} for {gid}")

        for alt in w.get("relevant_alternatives", []):
            alt_path = ROOT / alt.lstrip("/")
            check(alt_path.exists(), f"Alternatives file exists: {alt} for {gid}")

        for tool in w.get("candidate_tools", []):
            tool_path = ROOT / "tools" / f"{tool}.html"
            check(tool_path.exists(), f"Tool page exists: {tool} for {gid}")

if __name__ == "__main__":
    test_workflow_maps_data()
    test_explorer_html()
    test_allowlist()
    test_no_invented_data()
    test_confidence_status()
    test_empty_state()
    test_duplicate_detection()
    test_missing_links()

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {len(errors)} failed")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  - {e}")
        exit(1)
    else:
        print("All workflow explorer validation tests passed.")
        exit(0)
