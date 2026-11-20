#!/usr/bin/env python3
"""Build deterministic overlap data for the Tool Overlap Checker.

Reads from:
- data/tools.json (tool catalog with categories, names, logos)
- docs/internal/STACK-OVERLAP-READINESS.json (alternatives and shared jobs)
- compare/ directory (existing comparison pages)

Outputs:
- data/overlap-data.json (machine-readable overlap data)
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_JSON = ROOT / "data" / "tools.json"
OVERLAP_READINESS = ROOT / "docs" / "internal" / "STACK-OVERLAP-READINESS.json"
COMPARE_DIR = ROOT / "compare"
OUTPUT = ROOT / "data" / "overlap-data.json"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def build_tool_catalog():
    """Build a catalog of all tools with their metadata."""
    tools_data = load_json(TOOLS_JSON)
    catalog = {}
    for t in tools_data["tools"]:
        catalog[t["id"]] = {
            "id": t["id"],
            "name": t["name"],
            "category": t.get("cat", ""),
            "best_for": t.get("best", ""),
            "pros": t.get("pros", []),
            "logo": t.get("logo", ""),
            "site": t.get("site", ""),
        }
    return catalog


def build_comparison_map():
    """Build a map of comparison pairs to their HTML pages."""
    comparisons = {}
    if not COMPARE_DIR.exists():
        return comparisons

    for f in sorted(COMPARE_DIR.glob("*.html")):
        stem = f.stem  # e.g., "adobeexpress-vs-canva"
        match = re.match(r"^(.+)-vs-(.+)$", stem)
        if match:
            tool_a, tool_b = match.group(1), match.group(2)
            # Store both orderings
            comparisons[(tool_a, tool_b)] = f"/compare/{stem}.html"
            comparisons[(tool_b, tool_a)] = f"/compare/{stem}.html"
    return comparisons


def build_overlap_data():
    """Build the complete overlap data structure."""
    catalog = build_tool_catalog()
    comparisons = build_comparison_map()

    # Load overlap readiness data
    overlap_readiness = load_json(OVERLAP_READINESS)

    # Build alternatives map from overlap readiness
    alternatives_map = {}
    shared_jobs_map = {}
    for tool in overlap_readiness.get("tools", []):
        tid = tool["tool_id"]
        # Deduplicate alternatives
        alts = list(dict.fromkeys(tool.get("alternatives", [])))
        alternatives_map[tid] = [a for a in alts if a in catalog]
        shared_jobs_map[tid] = tool.get("shared_jobs_with", [])

    # Build overlap pairs
    overlap_pairs = []
    for tid, alts in sorted(alternatives_map.items()):
        for alt in alts:
            if alt not in catalog:
                continue
            # Determine shared category
            cat_a = catalog[tid]["category"]
            cat_b = catalog[alt]["category"]
            shared_cat = cat_a if cat_a == cat_b else ""

            # Check if comparison page exists
            comparison_url = comparisons.get((tid, alt), "")

            # Check if alt is in shared_jobs
            is_shared_job = alt in shared_jobs_map.get(tid, [])

            overlap_pairs.append({
                "tool_a": tid,
                "tool_b": alt,
                "shared_category": shared_cat,
                "has_comparison": bool(comparison_url),
                "comparison_url": comparison_url,
                "shared_job": is_shared_job,
            })

    # Build category groups
    category_groups = {}
    for tid, tool in sorted(catalog.items()):
        cat = tool["category"]
        if cat:
            if cat not in category_groups:
                category_groups[cat] = []
            category_groups[cat].append(tid)

    # Build the output structure
    output = {
        "schema_version": "overlap-data-v1",
        "generated_at": "2026-11-20",
        "description": "Deterministic overlap data for Tool Overlap Checker. Derived from tools.json, STACK-OVERLAP-READINESS.json, and compare/ directory.",
        "total_tools": len(catalog),
        "total_pairs": len(overlap_pairs),
        "total_comparisons": len(set(v for v in comparisons.values())),
        "tools": catalog,
        "categories": {cat: sorted(ids) for cat, ids in sorted(category_groups.items())},
        "alternatives": {tid: alts for tid, alts in sorted(alternatives_map.items())},
        "shared_jobs": {tid: jobs for tid, jobs in sorted(shared_jobs_map.items())},
        "overlap_pairs": overlap_pairs,
    }

    return output


def main():
    print("Building overlap data...")
    data = build_overlap_data()

    # Write output
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Generated {OUTPUT}")
    print(f"  Tools: {data['total_tools']}")
    print(f"  Overlap pairs: {data['total_pairs']}")
    print(f"  Comparison pages: {data['total_comparisons']}")
    print(f"  Categories: {len(data['categories'])}")


if __name__ == "__main__":
    main()
