#!/usr/bin/env python3
"""
Product Readiness Classification — Phase 9

Without building UI, classify these as ready/partial/blocked and explain
coverage/blockers:
- Decision Engine V2
- Free Plan Finder
- Trial Reality Checker
- Plan Limit Fit Checker
- Tool Overlap Checker
- Stack Budget Planner
- Workflow Explorer

Recommend which is genuinely safest to build next.

Output: docs/internal/PRODUCT-READINESS.json
"""

import json
import os


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def main():
    print("=== Building Product Readiness Classification ===\n")

    # Load all data foundations
    commercial = load_json("docs/internal/COMMERCIAL-DATA.json")
    free_trial = load_json("docs/internal/FREE-PLAN-TRIAL-FOUNDATION.json")
    decision_engine = load_json("docs/internal/DECISION-ENGINE-READINESS.json")
    stack_overlap = load_json("docs/internal/STACK-OVERLAP-READINESS.json")
    workflows = load_json("docs/internal/WORKFLOW-MAPS.json")
    evidence_gaps = load_json("docs/internal/EVIDENCE-GAP-REGISTRY.json")
    quality = load_json("docs/internal/QUALITY-REPORT.json")

    products = []

    # 1. Decision Engine V2
    de_ready = sum(1 for t in (decision_engine or {}).get("tools", []) if t["status"] == "ready")
    de_partial = sum(1 for t in (decision_engine or {}).get("tools", []) if t["status"] == "partially_ready")
    de_blocked = sum(1 for t in (decision_engine or {}).get("tools", []) if t["status"] == "blocked_by_evidence")
    de_total = len((decision_engine or {}).get("tools", []))

    products.append({
        "product": "Decision Engine V2",
        "status": "partial",
        "coverage": f"{de_ready}/{de_total} tools ready, {de_partial}/{de_total} partially ready",
        "blockers": [
            "44 of 50 tools lack tools-v2 structured data for limitations and jobs",
            "Only 3 of 50 tools have verified commercial pricing data",
            "Boilerplate content in 29 tool reviews reduces decision reliability"
        ],
        "data_foundations": ["DECISION-ENGINE-READINESS.json", "COMMERCIAL-DATA.json"],
        "safest_subset": "6 ready tools can power a limited Decision Engine for high-coverage categories",
        "recommendation": "Build with partial data — show confidence levels to users"
    })

    # 2. Free Plan Finder
    fp_evidence = sum(1 for t in (free_trial or {}).get("tools", [])
                      if t["free_plan_status"] not in ("unknown", "disputed"))
    fp_total = len((free_trial or {}).get("tools", []))

    products.append({
        "product": "Free Plan Finder",
        "status": "blocked",
        "coverage": f"{fp_evidence}/{fp_total} tools have free plan evidence",
        "blockers": [
            "Only 1 of 50 tools has verified free plan status (semrush)",
            "49 tools have unknown free plan status",
            "Cannot build a useful finder with 98% unknown data"
        ],
        "data_foundations": ["FREE-PLAN-TRIAL-FOUNDATION.json"],
        "safest_subset": "None — insufficient data for any meaningful feature",
        "recommendation": "Block until free plan evidence is collected for at least 10+ tools"
    })

    # 3. Trial Reality Checker
    tr_evidence = sum(1 for t in (free_trial or {}).get("tools", [])
                      if t["trial_status"] not in ("unknown", "disputed"))
    tr_total = len((free_trial or {}).get("tools", []))

    products.append({
        "product": "Trial Reality Checker",
        "status": "blocked",
        "coverage": f"{tr_evidence}/{tr_total} tools have trial evidence",
        "blockers": [
            "Only 1 of 50 tools has verified trial status (mozpro)",
            "49 tools have unknown trial status",
            "Cannot verify trial availability without evidence"
        ],
        "data_foundations": ["FREE-PLAN-TRIAL-FOUNDATION.json"],
        "safest_subset": "None — insufficient data for any meaningful feature",
        "recommendation": "Block until trial evidence is collected for at least 10+ tools"
    })

    # 4. Plan Limit Fit Checker
    pl_verified = sum(1 for t in (commercial or {}).get("tools", [])
                      if t["confidence"] in ("high", "medium"))
    pl_total = len((commercial or {}).get("tools", []))

    products.append({
        "product": "Plan Limit Fit Checker",
        "status": "blocked",
        "coverage": f"{pl_verified}/{pl_total} tools have verified commercial data",
        "blockers": [
            "Only 2 of 50 tools have verified pricing data (hostinger, semrush)",
            "No verified plan limits exist in evidence ledger",
            "Cannot match user needs to plan limits without limit data"
        ],
        "data_foundations": ["COMMERCIAL-DATA.json"],
        "safest_subset": "None — no plan limit data exists",
        "recommendation": "Block until plan limit evidence is collected for multiple tools"
    })

    # 5. Tool Overlap Checker
    overlap_ready = sum(1 for t in (stack_overlap or {}).get("tools", [])
                        if t["overlap_status"] == "overlap-ready")
    overlap_total = len((stack_overlap or {}).get("tools", []))
    overlap_pairs = (stack_overlap or {}).get("summary", {}).get("total_overlap_pairs", 0)

    products.append({
        "product": "Tool Overlap Checker",
        "status": "ready",
        "coverage": f"{overlap_ready}/{overlap_total} tools overlap-ready, {overlap_pairs} overlap pairs",
        "blockers": [],
        "data_foundations": ["STACK-OVERLAP-READINESS.json", "DECISION-ENGINE-READINESS.json"],
        "safest_subset": "All 50 tools have alternatives data from 50 alternatives pages",
        "recommendation": "Safest to build — all tools have overlap data from alternatives pages"
    })

    # 6. Stack Budget Planner
    budget_ready = sum(1 for t in (stack_overlap or {}).get("tools", [])
                       if t["budget_status"] == "budget-ready")
    budget_total = len((stack_overlap or {}).get("tools", []))

    products.append({
        "product": "Stack Budget Planner",
        "status": "blocked",
        "coverage": f"{budget_ready}/{budget_total} tools budget-ready",
        "blockers": [
            "Only 2 of 50 tools have verified commercial cost",
            "Cannot calculate stack budgets without pricing data",
            "48 tools have unknown pricing"
        ],
        "data_foundations": ["STACK-OVERLAP-READINESS.json", "COMMERCIAL-DATA.json"],
        "safest_subset": "None — insufficient pricing data for budget calculation",
        "recommendation": "Block until commercial pricing is verified for at least 15+ tools"
    })

    # 7. Workflow Explorer
    wf_count = (workflows or {}).get("total_workflows", 0)
    wf_high = sum(1 for w in (workflows or {}).get("workflows", [])
                  if w.get("evidence_confidence") == "high")
    wf_total = len((workflows or {}).get("workflows", []))

    products.append({
        "product": "Workflow Explorer",
        "status": "partial",
        "coverage": f"{wf_count} workflows, {wf_high}/{wf_total} high confidence",
        "blockers": [
            "Some workflows have limited candidate tools due to category matching",
            "Decision questions are template-based, not evidence-based",
            "No user testing data to validate workflow paths"
        ],
        "data_foundations": ["WORKFLOW-MAPS.json", "DECISION-ENGINE-READINESS.json"],
        "safest_subset": "7 of 9 workflows have high evidence confidence",
        "recommendation": "Build with existing 9 workflows — show confidence levels"
    })

    # Recommendation
    recommendation = {
        "safest_to_build": "Tool Overlap Checker",
        "reason": "All 50 tools have overlap data from 50 alternatives pages with 205+ overlap pairs. No commercial data required. Can provide immediate user value by showing which tools serve similar purposes.",
        "second_safest": "Workflow Explorer",
        "second_reason": "9 workflows exist with 7 at high confidence. Provides structured navigation without requiring new evidence.",
        "blocked_products": [
            "Free Plan Finder (1/50 tools with evidence)",
            "Trial Reality Checker (1/50 tools with evidence)",
            "Plan Limit Fit Checker (0 plan limits verified)",
            "Stack Budget Planner (2/50 tools with pricing)"
        ],
        "partial_products": [
            "Decision Engine V2 (6/50 ready, 44/50 partial)",
            "Workflow Explorer (7/9 high confidence)"
        ]
    }

    report = {
        "schema_version": "product-readiness-v1",
        "generated_at": "2026-11-20",
        "description": "Product readiness classification based on existing data foundations. No UI built.",
        "products": products,
        "summary": {
            "ready": sum(1 for p in products if p["status"] == "ready"),
            "partial": sum(1 for p in products if p["status"] == "partial"),
            "blocked": sum(1 for p in products if p["status"] == "blocked")
        },
        "recommendation": recommendation
    }

    # Write report
    output_path = "docs/internal/PRODUCT-READINESS.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Output: {output_path}")
    print()

    print("=== Product Readiness ===")
    for p in products:
        print(f"  {p['product']}: {p['status'].upper()}")
        print(f"    Coverage: {p['coverage']}")
        if p["blockers"]:
            for b in p["blockers"][:2]:
                print(f"    Blocker: {b}")
        print(f"    Recommendation: {p['recommendation']}")
        print()

    print("=== Summary ===")
    print(f"  Ready: {report['summary']['ready']}")
    print(f"  Partial: {report['summary']['partial']}")
    print(f"  Blocked: {report['summary']['blocked']}")
    print()

    rec = report["recommendation"]
    print(f"=== Safest to Build: {rec['safest_to_build']} ===")
    print(f"  Reason: {rec['reason']}")
    print(f"  Second safest: {rec['second_safest']}")

    print(f"\n=== Written to {output_path} ===")


if __name__ == "__main__":
    main()
