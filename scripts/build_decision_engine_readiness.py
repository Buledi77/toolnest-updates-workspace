#!/usr/bin/env python3
"""
Decision Engine Readiness — Phase 3

Using Decision Graph + tools-v2 + existing relationships, classify each tool:
- ready: sufficient explainable attributes for decision guidance
- partially_ready: some attributes present, gaps remain
- blocked_by_evidence: insufficient data for any decision guidance

Represent explainable attributes only:
- jobs, best fit, skip conditions, strengths, limitations, alternatives,
  comparisons, category, supported pricing/free-plan fit, evidence confidence

No opaque score or invented weights.

Output: docs/internal/DECISION-ENGINE-READINESS.json
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


def get_comparison_count(tool_id):
    """Count comparison pages referencing this tool."""
    compare_dir = Path("compare")
    if not compare_dir.exists():
        return 0, []
    comparisons = []
    for f in compare_dir.iterdir():
        if f.suffix == ".html" and f.name != "index.html":
            if tool_id in f.name:
                comparisons.append(f"/compare/{f.name}")
    return len(comparisons), comparisons


def get_alternatives_page(tool_id):
    alt_path = f"alternatives/{tool_id}-alternatives.html"
    return f"/alternatives/{tool_id}-alternatives.html" if os.path.exists(alt_path) else None


def get_best_of_references(tool_id):
    best_dir = Path("best")
    if not best_dir.exists():
        return []
    refs = []
    for f in best_dir.iterdir():
        if f.suffix == ".html" and f.name != "index.html":
            with open(f) as fh:
                if tool_id in fh.read().lower():
                    refs.append(f"/best/{f.name}")
    return refs


def get_evidence_claims(tool_id):
    ledger = load_json("data/evidence/evidence-ledger.json")
    claims = [c for c in ledger.get("claims", []) if c.get("tool_id") == tool_id]
    return claims


def build_decision_engine_readiness():
    catalog = load_json("data/tools.json")
    tools = {t["id"]: t for t in catalog.get("tools", [])}

    # Load commercial data
    commercial = {}
    if os.path.exists("docs/internal/COMMERCIAL-DATA.json"):
        cd = load_json("docs/internal/COMMERCIAL-DATA.json")
        commercial = {t["tool_id"]: t for t in cd["tools"]}

    # Load free plan/trial foundation
    free_trial = {}
    if os.path.exists("docs/internal/FREE-PLAN-TRIAL-FOUNDATION.json"):
        ft = load_json("docs/internal/FREE-PLAN-TRIAL-FOUNDATION.json")
        free_trial = {t["tool_id"]: t for t in ft["tools"]}

    readiness = {
        "schema_version": "decision-engine-readiness-v1",
        "generated_at": "2026-11-20",
        "description": "Decision Engine readiness classification for all tools. No opaque scores — only explainable attributes.",
        "total_tools": len(tools),
        "tools": []
    }

    for tool_id in sorted(tools.keys()):
        tool = tools[tool_id]
        v2_record = get_tools_v2_record(tool_id)
        claims = get_evidence_claims(tool_id)
        comp_count, comp_pages = get_comparison_count(tool_id)
        alt_page = get_alternatives_page(tool_id)
        best_of_refs = get_best_of_references(tool_id)

        # Evaluate explainable attributes
        attributes = {
            "category": tool.get("cat"),
            "best_fit": tool.get("best"),
            "strengths": tool.get("pros", []),
            "jobs": [],
            "limitations": [],
            "skip_conditions": [],
            "alternatives": [],
            "comparisons": [],
            "pricing_fit": None,
            "free_plan_fit": None,
            "evidence_confidence": "none"
        }

        # From tools.json
        if tool.get("cat"):
            attributes["category"] = tool["cat"]
        if tool.get("best"):
            attributes["best_fit"] = tool["best"]
        if tool.get("pros"):
            attributes["strengths"] = tool["pros"]

        # From tools-v2
        if v2_record:
            fp = v2_record.get("factual_profile", {})
            if fp.get("primary_purpose"):
                attributes["jobs"] = [fp["primary_purpose"]]
            if fp.get("limitations"):
                # Limitations are claim references
                attributes["limitations"] = ["tools_v2_limitations_present"]
            rels = v2_record.get("relationships", {})
            if rels.get("alternatives"):
                attributes["alternatives"] = rels["alternatives"]
            if rels.get("meaningful_comparisons"):
                attributes["comparisons"] = rels["meaningful_comparisons"]

        # From comparison/alternatives pages
        if comp_pages:
            attributes["comparisons"] = comp_pages
        if alt_page:
            attributes["alternatives"] = alt_page

        # From commercial data
        if tool_id in commercial:
            cd = commercial[tool_id]
            if cd.get("pricing_model") and cd["pricing_model"] != "unknown":
                attributes["pricing_fit"] = cd["pricing_model"]
            if cd.get("confidence"):
                attributes["evidence_confidence"] = cd["confidence"]

        # From free plan/trial foundation
        if tool_id in free_trial:
            ft = free_trial[tool_id]
            if ft.get("free_plan_status") and ft["free_plan_status"] != "unknown":
                attributes["free_plan_fit"] = ft["free_plan_status"]

        # Count present attributes
        present_attrs = 0
        total_attrs = 10  # category, best_fit, strengths, jobs, limitations, alternatives, comparisons, pricing_fit, free_plan_fit, evidence_confidence

        if attributes["category"]:
            present_attrs += 1
        if attributes["best_fit"]:
            present_attrs += 1
        if attributes["strengths"]:
            present_attrs += 1
        if attributes["jobs"]:
            present_attrs += 1
        if attributes["limitations"]:
            present_attrs += 1
        if attributes["alternatives"]:
            present_attrs += 1
        if attributes["comparisons"]:
            present_attrs += 1
        if attributes["pricing_fit"]:
            present_attrs += 1
        if attributes["free_plan_fit"]:
            present_attrs += 1
        if attributes["evidence_confidence"] != "none":
            present_attrs += 1

        # Classify readiness
        if present_attrs >= 7:
            status = "ready"
        elif present_attrs >= 4:
            status = "partially_ready"
        else:
            status = "blocked_by_evidence"

        # Determine blockers
        blockers = []
        if not attributes["category"]:
            blockers.append("missing_category")
        if not attributes["best_fit"]:
            blockers.append("missing_best_fit")
        if not attributes["strengths"]:
            blockers.append("missing_strengths")
        if not attributes["jobs"]:
            blockers.append("missing_jobs")
        if not attributes["limitations"]:
            blockers.append("missing_limitations")
        if not attributes["alternatives"]:
            blockers.append("missing_alternatives")
        if not attributes["comparisons"]:
            blockers.append("missing_comparisons")
        if not attributes["pricing_fit"]:
            blockers.append("missing_pricing_fit")
        if not attributes["free_plan_fit"]:
            blockers.append("missing_free_plan_fit")
        if attributes["evidence_confidence"] == "none":
            blockers.append("missing_evidence_confidence")

        record = {
            "tool_id": tool_id,
            "status": status,
            "attributes_present": present_attrs,
            "attributes_total": total_attrs,
            "explainable_attributes": attributes,
            "blockers": blockers,
            "infrastructure": {
                "has_tools_v2": v2_record is not None,
                "has_evidence_claims": len(claims) > 0,
                "comparison_pages": len(comp_pages),
                "has_alternatives_page": alt_page is not None,
                "best_of_references": len(best_of_refs)
            }
        }

        readiness["tools"].append(record)

    # Summary
    status_counts = {}
    for t in readiness["tools"]:
        status_counts[t["status"]] = status_counts.get(t["status"], 0) + 1

    readiness["summary"] = {
        "status_distribution": status_counts,
        "ready_count": status_counts.get("ready", 0),
        "partially_ready_count": status_counts.get("partially_ready", 0),
        "blocked_count": status_counts.get("blocked_by_evidence", 0),
        "avg_attributes_present": sum(t["attributes_present"] for t in readiness["tools"]) / len(readiness["tools"]) if readiness["tools"] else 0
    }

    return readiness


def main():
    print("=== Building Decision Engine Readiness ===\n")
    data = build_decision_engine_readiness()

    output_path = "docs/internal/DECISION-ENGINE-READINESS.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Output: {output_path}")
    print(f"Total tools: {data['total_tools']}")
    print()

    summary = data["summary"]
    print("=== Status Distribution ===")
    for status, count in sorted(summary["status_distribution"].items()):
        print(f"  {status}: {count}")
    print()
    print(f"Average attributes present: {summary['avg_attributes_present']:.1f}/{summary.get('attributes_total', 10)}")

    # Show blocked tools
    print("\n=== Blocked Tools ===")
    for t in data["tools"]:
        if t["status"] == "blocked_by_evidence":
            print(f"  {t['tool_id']}: {t['attributes_present']} attrs, blockers: {', '.join(t['blockers'][:3])}")

    print(f"\n=== Written to {output_path} ===")


if __name__ == "__main__":
    main()
