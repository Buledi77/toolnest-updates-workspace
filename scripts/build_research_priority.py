#!/usr/bin/env python3
"""Research prioritization engine — rank RESEARCH_REQUIRED work by user impact.

Priority factors:
  - homepage exposure (featured tools)
  - Decision Engine recommendation frequency (use case tag count)
  - comparison frequency
  - alternative frequency
  - goal/workflow exposure
  - Stack Analyzer availability
  - category importance
  - affiliate/conversion relevance (priority only, never editorial verdict)

Affiliate relationship must NEVER increase recommendation score or factual confidence.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "data" / "tools-v1.json"
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_priority(tool, ledger_claims_by_tool):
    """Compute research priority score for a tool.

    Higher score = higher priority for research.
    """
    score = 0
    factors = []

    tool_id = tool.get("id", "")
    claims = ledger_claims_by_tool.get(tool_id, [])

    # 1. Homepage exposure (featured tools) — highest impact
    if tool.get("featured"):
        score += 30
        factors.append("homepage_featured")

    # 2. Badge/tools directory prominence
    badge = tool.get("badge", "")
    if badge:
        score += 15
        factors.append("has_badge")

    # 3. Use case tag count (Decision Engine recommendation frequency)
    uc_tags = tool.get("useCaseTags", [])
    if len(uc_tags) > 3:
        score += 15
        factors.append("many_use_cases")
    elif len(uc_tags) > 0:
        score += 5
        factors.append("has_use_cases")

    # 4. Comparison frequency
    comparisons = tool.get("comparisons", [])
    if len(comparisons) > 2:
        score += 15
        factors.append("frequently_compared")
    elif len(comparisons) > 0:
        score += 5
        factors.append("has_comparisons")

    # 5. Alternative frequency
    alternatives = tool.get("alternatives", [])
    if len(alternatives) > 3:
        score += 15
        factors.append("many_alternatives")
    elif len(alternatives) > 0:
        score += 5
        factors.append("has_alternatives")

    # 6. Goal/workflow exposure
    goals = tool.get("goals", [])
    if len(goals) > 1:
        score += 10
        factors.append("multiple_goals")
    elif len(goals) > 0:
        score += 5
        factors.append("has_goals")

    # 7. Category importance (categories with more tools are more important)
    # This is computed externally

    # 8. Evidence gaps — tools with fewer verified claims need more research
    verified_claims = sum(
        1 for c in claims if c.get("status") in ("verified", "verified_official")
    )
    if verified_claims == 0 and len(claims) == 0:
        score += 20
        factors.append("no_evidence_claims")
    elif verified_claims == 0:
        score += 10
        factors.append("no_verified_claims")

    # 9. Missing pricing data — high impact for decision making
    pricing = tool.get("pricing", {})
    if not pricing or not pricing.get("tiers"):
        score += 15
        factors.append("missing_pricing")

    # 10. Missing platforms
    platforms = tool.get("platforms", [])
    if not platforms:
        score += 10
        factors.append("missing_platforms")

    # 11. Missing bestFor
    best_for = tool.get("bestFor", [])
    if not best_for:
        score += 5
        factors.append("missing_best_for")

    # 12. Affiliate status — affects research priority for commercial
    # completeness but NEVER editorial verdict
    affiliate = tool.get("affiliate", {})
    if isinstance(affiliate, dict) and affiliate.get("status") in ("approved", "active"):
        score += 5
        factors.append("affiliate_tool")

    return score, factors


def build_priority_list():
    """Build and return prioritized research list."""
    tools_data = load_json(TOOLS_PATH)
    ledger = load_json(LEDGER_PATH)

    tools = tools_data.get("tools", [])
    claims = ledger.get("claims", [])

    # Index claims by tool_id
    claims_by_tool = {}
    for claim in claims:
        tid = claim.get("tool_id", "")
        if tid not in claims_by_tool:
            claims_by_tool[tid] = []
        claims_by_tool[tid].append(claim)

    # Count tools per category for category importance
    cat_counts = {}
    for tool in tools:
        cat = tool.get("cat", "")
        if cat:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Compute priority for each tool
    prioritized = []
    for tool in tools:
        score, factors = compute_priority(tool, claims_by_tool)

        # Add category importance bonus
        cat = tool.get("cat", "")
        if cat in cat_counts:
            cat_importance = min(cat_counts[cat] // 5, 10)
            score += cat_importance
            if cat_importance > 0:
                factors.append("important_category")

        prioritized.append({
            "tool_id": tool.get("id", ""),
            "name": tool.get("name", ""),
            "category": cat,
            "priority_score": score,
            "factors": factors,
            "has_pricing": bool(tool.get("pricing", {}).get("tiers")),
            "has_platforms": bool(tool.get("platforms")),
            "has_use_cases": bool(tool.get("useCaseTags")),
            "has_best_for": bool(tool.get("bestFor")),
            "evidence_claims": len(claims_by_tool.get(tool.get("id", ""), [])),
            "verified_claims": sum(
                1 for c in claims_by_tool.get(tool.get("id", ""), [])
                if c.get("status") in ("verified", "verified_official")
            ),
        })

    # Sort by priority score descending
    prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

    return prioritized


def main():
    prioritized = build_priority_list()

    # Show top 30
    print("Research Priority Ranking (Top 30):")
    print("=" * 80)
    print(f"{'Rank':<5} {'Tool ID':<25} {'Name':<25} {'Score':<6} {'Factors'}")
    print("-" * 80)

    for i, item in enumerate(prioritized[:30], 1):
        factors_str = ", ".join(item["factors"][:4])
        if len(item["factors"]) > 4:
            factors_str += f" (+{len(item['factors'])-4} more)"
        print(f"{i:<5} {item['tool_id']:<25} {item['name']:<25} {item['priority_score']:<6} {factors_str}")

    # Output full list as JSON
    output_path = ROOT / "data" / "research-priority.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prioritized, f, indent=2, ensure_ascii=False)

    print(f"\nFull list written to: {output_path}")
    print(f"Total tools ranked: {len(prioritized)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
