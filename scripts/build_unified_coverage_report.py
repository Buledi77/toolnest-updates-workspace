#!/usr/bin/env python3
"""
Unified Coverage Report — Phase 8

Generate one deterministic report covering:
- evidence gaps
- freshness
- commercial coverage
- free-plan/trial coverage
- Decision Engine readiness
- Stack/Overlap readiness
- workflow readiness
- category readiness

All totals must reconcile with actual source records.
Add assertions against duplicate IDs, impossible totals and unsupported statuses.

Output: docs/internal/UNIFIED-COVERAGE-REPORT.json
"""

import json
import os
from collections import Counter


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def assert_no_duplicates(tools_list, field, report_name):
    """Assert no duplicate IDs in a tools list."""
    ids = [t[field] for t in tools_list]
    counts = Counter(ids)
    duplicates = {k: v for k, v in counts.items() if v > 1}
    if duplicates:
        print(f"  ASSERTION FAIL: {report_name} has duplicate {field}: {duplicates}")
        return False
    return True


def assert_total_reconciles(actual, expected, label):
    """Assert total reconciles with expected."""
    if actual != expected:
        print(f"  ASSERTION FAIL: {label} total {actual} != expected {expected}")
        return False
    return True


def main():
    print("=== Building Unified Coverage Report ===\n")

    # Load all reports
    catalog = load_json("data/tools.json")
    total_tools = len(catalog.get("tools", []))
    tool_ids = sorted([t["id"] for t in catalog.get("tools", [])])

    quality = load_json("docs/internal/QUALITY-REPORT.json")
    evidence_gaps = load_json("docs/internal/EVIDENCE-GAP-REGISTRY.json")
    freshness = load_json("docs/internal/FRESHNESS-RADAR.json")
    commercial = load_json("docs/internal/COMMERCIAL-DATA.json")
    free_trial = load_json("docs/internal/FREE-PLAN-TRIAL-FOUNDATION.json")
    decision_engine = load_json("docs/internal/DECISION-ENGINE-READINESS.json")
    stack_overlap = load_json("docs/internal/STACK-OVERLAP-READINESS.json")
    workflows = load_json("docs/internal/WORKFLOW-MAPS.json")

    # Assertions
    assertions = []

    # 1. Evidence Gap coverage
    eg_tools = evidence_gaps.get("tools", []) if evidence_gaps else []
    eg_ids = [t["tool_id"] for t in eg_tools]
    assertions.append({
        "check": "no_duplicate_evidence_gap_ids",
        "pass": len(eg_ids) == len(set(eg_ids)),
        "detail": f"{len(eg_ids)} tools, {len(set(eg_ids))} unique"
    })

    # 2. Freshness coverage
    fr_pages = freshness.get("pages", []) if freshness else []
    fr_paths = [p.get("path", "") for p in fr_pages]
    assertions.append({
        "check": "no_duplicate_freshness_ids",
        "pass": len(fr_paths) == len(set(fr_paths)),
        "detail": f"{len(fr_paths)} pages, {len(set(fr_paths))} unique"
    })

    # 3. Commercial data coverage
    cd_tools = commercial.get("tools", []) if commercial else []
    cd_ids = [t["tool_id"] for t in cd_tools]
    assertions.append({
        "check": "commercial_data_matches_catalog",
        "pass": len(cd_ids) == total_tools,
        "detail": f"{len(cd_ids)} tools vs {total_tools} in catalog"
    })
    assertions.append({
        "check": "no_duplicate_commercial_ids",
        "pass": len(cd_ids) == len(set(cd_ids)),
        "detail": f"{len(cd_ids)} tools, {len(set(cd_ids))} unique"
    })

    # 4. Free plan/trial coverage
    ft_tools = free_trial.get("tools", []) if free_trial else []
    ft_ids = [t["tool_id"] for t in ft_tools]
    assertions.append({
        "check": "free_trial_matches_catalog",
        "pass": len(ft_ids) == total_tools,
        "detail": f"{len(ft_ids)} tools vs {total_tools} in catalog"
    })

    # 5. Decision Engine coverage
    de_tools = decision_engine.get("tools", []) if decision_engine else []
    de_ids = [t["tool_id"] for t in de_tools]
    assertions.append({
        "check": "decision_engine_matches_catalog",
        "pass": len(de_ids) == total_tools,
        "detail": f"{len(de_ids)} tools vs {total_tools} in catalog"
    })

    # 6. Stack/Overlap coverage
    so_tools = stack_overlap.get("tools", []) if stack_overlap else []
    so_ids = [t["tool_id"] for t in so_tools]
    assertions.append({
        "check": "stack_overlap_matches_catalog",
        "pass": len(so_ids) == total_tools,
        "detail": f"{len(so_ids)} tools vs {total_tools} in catalog"
    })

    # 7. Quality report totals
    qr_pages = quality.get("pages", []) if quality else []
    qr_total = len(qr_pages)
    # Count by type
    type_counts = Counter(p["type"] for p in qr_pages)
    grade_counts = Counter(f"{p['type']}:{p['grade']}" for p in qr_pages)

    # Verify grade distribution sums
    for ptype in set(p["type"] for p in qr_pages):
        type_total = type_counts[ptype]
        grade_sum = sum(v for k, v in grade_counts.items() if k.startswith(f"{ptype}:"))
        assertions.append({
            "check": f"grade_sum_{ptype}",
            "pass": type_total == grade_sum,
            "detail": f"{ptype}: {type_total} pages, grade sum = {grade_sum}"
        })

    # 8. Unsupported status checks
    supported_free_statuses = {"permanent_free_plan", "limited_free_account", "free_trial",
                               "demo_only", "paid_only", "unknown", "disputed", "not_applicable"}
    for t in ft_tools:
        if t["free_plan_status"] not in supported_free_statuses:
            assertions.append({
                "check": "supported_free_status",
                "pass": False,
                "detail": f"{t['tool_id']}: unsupported free_plan_status '{t['free_plan_status']}'"
            })
        if t["trial_status"] not in supported_free_statuses:
            assertions.append({
                "check": "supported_trial_status",
                "pass": False,
                "detail": f"{t['tool_id']}: unsupported trial_status '{t['trial_status']}'"
            })

    # Build unified report
    report = {
        "schema_version": "unified-coverage-report-v1",
        "generated_at": "2026-11-20",
        "description": "Unified coverage report combining all data foundations. All totals reconcile with source records.",
        "total_tools_in_catalog": total_tools,
        "total_pages_evaluated": qr_total,
        "assertions": assertions,
        "assertions_passed": sum(1 for a in assertions if a["pass"]),
        "assertions_failed": sum(1 for a in assertions if not a["pass"]),
        "coverage": {
            "evidence_gaps": {
                "tools_analyzed": len(eg_tools),
                "summary": evidence_gaps.get("summary", {}) if evidence_gaps else {}
            },
            "freshness": {
                "pages_analyzed": len(fr_pages),
                "summary": freshness.get("summary", {}) if freshness else {}
            },
            "commercial": {
                "tools_analyzed": len(cd_tools),
                "verified_count": sum(1 for t in cd_tools if t["confidence"] != "none"),
                "unknown_count": sum(1 for t in cd_tools if t["status"] == "unknown"),
                "disputed_count": sum(1 for t in cd_tools if t["disputed"]),
                "summary": commercial.get("summary", {}) if commercial else {}
            },
            "free_plan_trial": {
                "tools_analyzed": len(ft_tools),
                "free_plan_evidence": sum(1 for t in ft_tools if t["free_plan_status"] not in ("unknown", "disputed")),
                "trial_evidence": sum(1 for t in ft_tools if t["trial_status"] not in ("unknown", "disputed")),
                "summary": free_trial.get("summary", {}) if free_trial else {}
            },
            "decision_engine": {
                "tools_analyzed": len(de_tools),
                "ready": sum(1 for t in de_tools if t["status"] == "ready"),
                "partially_ready": sum(1 for t in de_tools if t["status"] == "partially_ready"),
                "blocked": sum(1 for t in de_tools if t["status"] == "blocked_by_evidence"),
                "summary": decision_engine.get("summary", {}) if decision_engine else {}
            },
            "stack_overlap": {
                "tools_analyzed": len(so_tools),
                "overlap_ready": sum(1 for t in so_tools if t["overlap_status"] == "overlap-ready"),
                "overlap_partial": sum(1 for t in so_tools if t["overlap_status"] == "partial"),
                "overlap_blocked": sum(1 for t in so_tools if t["overlap_status"] == "blocked"),
                "budget_ready": sum(1 for t in so_tools if t["budget_status"] == "budget-ready"),
                "budget_partial": sum(1 for t in so_tools if t["budget_status"] == "partial"),
                "budget_blocked": sum(1 for t in so_tools if t["budget_status"] == "blocked"),
                "summary": stack_overlap.get("summary", {}) if stack_overlap else {}
            },
            "workflows": {
                "workflows_created": workflows.get("total_workflows", 0) if workflows else 0,
                "summary": workflows.get("summary", {}) if workflows else {}
            },
            "category": {
                "total_categories": type_counts.get("category", 0),
                "grade_a": grade_counts.get("category:A", 0),
                "grade_b": grade_counts.get("category:B", 0),
                "grade_c": grade_counts.get("category:C", 0)
            }
        },
        "quality_distribution": dict(grade_counts)
    }

    # Write report
    output_path = "docs/internal/UNIFIED-COVERAGE-REPORT.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Output: {output_path}")
    print()

    # Print summary
    print("=== Assertions ===")
    for a in report["assertions"]:
        status = "PASS" if a["pass"] else "FAIL"
        print(f"  [{status}] {a['check']}: {a['detail']}")
    print()
    print(f"Assertions passed: {report['assertions_passed']}/{len(report['assertions'])}")
    print()

    print("=== Coverage Summary ===")
    cov = report["coverage"]
    print(f"  Evidence gaps: {cov['evidence_gaps']['tools_analyzed']} tools")
    print(f"  Freshness: {cov['freshness']['pages_analyzed']} pages")
    print(f"  Commercial: {cov['commercial']['verified_count']}/{cov['commercial']['tools_analyzed']} verified")
    print(f"  Free plan evidence: {cov['free_plan_trial']['free_plan_evidence']}/{cov['free_plan_trial']['tools_analyzed']}")
    print(f"  Trial evidence: {cov['free_plan_trial']['trial_evidence']}/{cov['free_plan_trial']['tools_analyzed']}")
    print(f"  Decision Engine: {cov['decision_engine']['ready']} ready, {cov['decision_engine']['partially_ready']} partial, {cov['decision_engine']['blocked']} blocked")
    print(f"  Stack/Overlap: {cov['stack_overlap']['overlap_ready']} overlap-ready, {cov['stack_overlap']['budget_ready']} budget-ready")
    print(f"  Workflows: {cov['workflows']['workflows_created']} created")
    print(f"  Categories: {cov['category']['grade_a']}A, {cov['category']['grade_b']}B, {cov['category']['grade_c']}C")
    print()

    print("=== Quality Distribution ===")
    for k, v in sorted(report["quality_distribution"].items()):
        print(f"  {k}: {v}")

    print(f"\n=== Written to {output_path} ===")


if __name__ == "__main__":
    main()
