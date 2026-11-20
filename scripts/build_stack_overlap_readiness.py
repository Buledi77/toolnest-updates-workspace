#!/usr/bin/env python3
"""
Stack / Overlap Readiness — Phase 4

Create structured foundation for future Tool Overlap Checker and Stack Budget Planner.

Use supported primary jobs, shared jobs, alternatives/substitutions,
complementary relationships and verified commercial cost only.

Never estimate price or infer overlap merely from category.

Report overlap-ready/partial/blocked and budget-ready/partial/blocked counts.

Output: docs/internal/STACK-OVERLAP-READINESS.json
"""

import json
import os
from pathlib import Path


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_v2_id_for_legacy(tool_id):
    try:
        mapping = load_json("data/migrations/legacy-to-v2-map.json")
        for record in mapping.get("records", []):
            if record.get("legacy_id") == tool_id:
                return record.get("v2_id")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return None


def get_tools_v2_record(tool_id):
    for path in [f"data/tools-v2/{tool_id}.json",
                 f"data/tools-v2/legacy/{tool_id}.json",
                 f"data/tools-v2/expansion/{tool_id}.json"]:
        if os.path.exists(path):
            return load_json(path)
    v2_id = get_v2_id_for_legacy(tool_id)
    if v2_id and v2_id != tool_id:
        path = f"data/tools-v2/{v2_id}.json"
        if os.path.exists(path):
            return load_json(path)
    return None


def build_stack_overlap_readiness():
    catalog = load_json("data/tools.json")
    tools = {t["id"]: t for t in catalog.get("tools", [])}

    # Load commercial data
    commercial = {}
    if os.path.exists("docs/internal/COMMERCIAL-DATA.json"):
        cd = load_json("docs/internal/COMMERCIAL-DATA.json")
        commercial = {t["tool_id"]: t for t in cd["tools"]}

    # Load stack builder
    stack_builder = load_json("data/stack/stack-builder-v1.json")

    # Load taxonomy
    taxonomy = load_json("data/taxonomy/taxonomy-v1.json")

    readiness = {
        "schema_version": "stack-overlap-readiness-v1",
        "generated_at": "2026-11-20",
        "description": "Structured foundation for Tool Overlap Checker and Stack Budget Planner. Never estimates price or infers overlap merely from category.",
        "total_tools": len(tools),
        "tools": []
    }

    # Build category-to-tools mapping
    category_tools = {}
    for tool_id, tool in tools.items():
        cat = tool.get("cat", "unknown")
        if cat not in category_tools:
            category_tools[cat] = []
        category_tools[cat].append(tool_id)

    # Build overlap pairs from alternatives pages
    overlap_pairs = []
    alt_dir = Path("alternatives")
    if alt_dir.exists():
        for f in alt_dir.iterdir():
            if f.suffix == ".html" and f.name != "index.html":
                base_tool = f.stem.replace("-alternatives", "")
                with open(f) as fh:
                    content = fh.read()
                # Find alternative tools mentioned
                for other_id in tools.keys():
                    if other_id != base_tool and other_id in content:
                        overlap_pairs.append({
                            "tool_a": base_tool,
                            "tool_b": other_id,
                            "relationship": "alternative",
                            "source": f"/alternatives/{f.name}"
                        })

    # Build complementary pairs from tools-v2
    complementary_pairs = []
    for tool_id in tools:
        v2 = get_tools_v2_record(tool_id)
        if v2:
            rels = v2.get("relationships", {})
            if rels.get("compatible_tools"):
                for compat in rels["compatible_tools"]:
                    complementary_pairs.append({
                        "tool_a": tool_id,
                        "tool_b": compat,
                        "relationship": "complementary",
                        "source": f"data/tools-v2/{tool_id}.json"
                    })

    for tool_id in sorted(tools.keys()):
        tool = tools[tool_id]
        v2_record = get_tools_v2_record(tool_id)

        # Primary jobs
        primary_jobs = []
        if tool.get("cat"):
            primary_jobs.append(tool["cat"])
        if v2_record:
            fp = v2_record.get("factual_profile", {})
            if fp.get("primary_purpose"):
                primary_jobs.append(fp["primary_purpose"])

        # Shared jobs (tools in same category)
        shared_jobs = []
        cat = tool.get("cat", "unknown")
        if cat in category_tools:
            shared_jobs = [t for t in category_tools[cat] if t != tool_id]

        # Alternatives/substitutions
        alternatives = []
        for pair in overlap_pairs:
            if pair["tool_a"] == tool_id:
                alternatives.append(pair["tool_b"])
            elif pair["tool_b"] == tool_id:
                alternatives.append(pair["tool_a"])

        # Complementary relationships
        complements = []
        for pair in complementary_pairs:
            if pair["tool_a"] == tool_id:
                complements.append(pair["tool_b"])
            elif pair["tool_b"] == tool_id:
                complements.append(pair["tool_a"])

        # Verified commercial cost
        has_verified_cost = tool_id in commercial and commercial[tool_id].get("confidence") in ("high", "medium")

        # Overlap readiness
        if len(alternatives) >= 2 and v2_record:
            overlap_status = "overlap-ready"
        elif len(alternatives) >= 1:
            overlap_status = "partial"
        else:
            overlap_status = "blocked"

        # Budget readiness
        if has_verified_cost and len(alternatives) >= 1:
            budget_status = "budget-ready"
        elif has_verified_cost or len(alternatives) >= 1:
            budget_status = "partial"
        else:
            budget_status = "blocked"

        record = {
            "tool_id": tool_id,
            "primary_jobs": primary_jobs,
            "shared_jobs_with": shared_jobs,
            "alternatives": alternatives,
            "complementary_tools": complements,
            "has_verified_cost": has_verified_cost,
            "overlap_status": overlap_status,
            "budget_status": budget_status
        }

        readiness["tools"].append(record)

    # Summary
    overlap_counts = {}
    budget_counts = {}
    for t in readiness["tools"]:
        overlap_counts[t["overlap_status"]] = overlap_counts.get(t["overlap_status"], 0) + 1
        budget_counts[t["budget_status"]] = budget_counts.get(t["budget_status"], 0) + 1

    readiness["summary"] = {
        "overlap_distribution": overlap_counts,
        "budget_distribution": budget_counts,
        "total_overlap_pairs": len(overlap_pairs),
        "total_complementary_pairs": len(complementary_pairs),
        "tools_with_verified_cost": sum(1 for t in readiness["tools"] if t["has_verified_cost"]),
        "stack_workflows": [
            {
                "id": req["id"],
                "label": req["label"],
                "preferred_categories": req.get("preferred_categories", []),
                "max_tools": req.get("max_tools")
            }
            for req in stack_builder.get("requirements", [])
        ]
    }

    return readiness


def main():
    print("=== Building Stack / Overlap Readiness ===\n")
    data = build_stack_overlap_readiness()

    output_path = "docs/internal/STACK-OVERLAP-READINESS.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Output: {output_path}")
    print(f"Total tools: {data['total_tools']}")
    print()

    summary = data["summary"]
    print("=== Overlap Readiness ===")
    for status, count in sorted(summary["overlap_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    print("=== Budget Readiness ===")
    for status, count in sorted(summary["budget_distribution"].items()):
        print(f"  {status}: {count}")
    print()

    print(f"Total overlap pairs: {summary['total_overlap_pairs']}")
    print(f"Total complementary pairs: {summary['total_complementary_pairs']}")
    print(f"Tools with verified cost: {summary['tools_with_verified_cost']}")

    print(f"\n=== Written to {output_path} ===")


if __name__ == "__main__":
    main()
