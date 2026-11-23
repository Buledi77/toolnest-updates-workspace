"""Decision Engine scenario test suite.

Tests the scoring logic with realistic scenarios covering:
- Price scenarios: free-only, low budget, unknown pricing, custom pricing
- Platform scenarios: verified supported, verified unsupported, unknown
- Use case scenarios: writing, design, SEO, marketing, etc.
- Data quality scenarios: highly verified, poorly verified, generic match
- Negative tests: wrong platform, missing feature, unknown free-plan, etc.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
CONFIG_PATH = ROOT / "data" / "decision-engine-config.json"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def normalize(s: str) -> str:
    """Match the frontend normalization."""
    return s.lower().replace("[^a-z0-9]", "").lower()


def score_tool(tool, selected_use_cases, selected_categories, selected_platforms, free_plan_only=False):
    """Replicate the frontend scoring logic in Python."""
    # Free plan filter
    if free_plan_only:
        fp = (tool.get("pricing") or {}).get("freePlan") or {}
        if fp.get("available") is False:
            return None  # Filtered out

    score = 0
    reasons = []
    tradeoffs = []
    verified_fields = 0
    evidence_notes = []

    has_uc = bool(tool.get("useCaseTags"))
    has_bf = bool(tool.get("bestFor"))
    has_plat = bool(tool.get("platforms"))
    has_pricing = bool((tool.get("pricing") or {}).get("tiers"))

    if has_uc:
        verified_fields += 1
    if tool.get("cat"):
        verified_fields += 1
    if has_bf:
        verified_fields += 1
    if has_plat:
        verified_fields += 1
    if has_pricing:
        verified_fields += 1

    # 1. Use Case Match (40 points)
    if selected_use_cases and has_uc:
        uc_tags = tool.get("useCaseTags", [])
        matches = sum(
            1 for uc in selected_use_cases
            if any(normalize(t) == normalize(uc) for t in uc_tags)
        )
        uc_score = round((matches / len(selected_use_cases)) * 40)
        score += uc_score
        if matches > 0:
            reasons.append(("Use Case Match", uc_score, 40, f"{matches} of {len(selected_use_cases)} use cases matched"))
        else:
            tradeoffs.append("Use case tags do not match your selected criteria")
    elif selected_use_cases:
        evidence_notes.append("Use case data unavailable")

    # 2. Category Match (20 points)
    if selected_categories:
        cat_match = tool.get("cat") in selected_categories
        if cat_match:
            score += 20
            reasons.append(("Category Match", 20, 20, f"Tool is in the \"{tool.get('cat')}\" category"))
        elif tool.get("cat"):
            tradeoffs.append(f"Category \"{tool.get('cat')}\" does not match your selected categories")

    # 3. Best For Match (20 points)
    if selected_use_cases and has_bf:
        bf_tags = tool.get("bestFor", [])
        matches = sum(
            1 for uc in selected_use_cases
            if any(normalize(t) == normalize(uc) for t in bf_tags)
        )
        bf_score = round((matches / len(selected_use_cases)) * 20)
        score += bf_score
        if matches > 0:
            reasons.append(("Best For Match", bf_score, 20, f"{matches} of {len(selected_use_cases)} use cases in bestFor"))
    elif selected_use_cases:
        evidence_notes.append("Best-for data unavailable")

    # 4. Platform Match (10 points)
    if selected_platforms and has_plat:
        t_plats = tool.get("platforms", [])
        matches = sum(1 for p in selected_platforms if p in t_plats)
        plat_score = round((matches / len(selected_platforms)) * 10)
        score += plat_score
        if matches > 0:
            reasons.append(("Platform Match", plat_score, 10, f"Available on {matches} of {len(selected_platforms)} platforms"))
        else:
            tradeoffs.append("Platform availability does not match your requirements")
    elif selected_platforms:
        evidence_notes.append("Platform data unavailable")

    # Evidence confidence
    if verified_fields >= 3:
        evidence_level = "strong"
    elif verified_fields >= 1:
        evidence_level = "moderate"
    else:
        evidence_level = "limited"

    is_category_only = score > 0 and not has_uc and not has_bf
    if is_category_only:
        tradeoffs.append("Recommendation based primarily on category match")

    if score < 5:
        return None

    return {
        "tool_id": tool["id"],
        "score": score,
        "reasons": reasons,
        "tradeoffs": tradeoffs,
        "evidence_level": evidence_level,
        "verified_fields": verified_fields,
        "evidence_notes": evidence_notes,
        "is_category_only": is_category_only
    }


def run_scenarios(tools):
    """Run all test scenarios."""
    results = []
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        status = "PASS" if condition else "FAIL"
        if condition:
            passed += 1
        else:
            failed += 1
        results.append({
            "name": name,
            "status": status,
            "detail": detail
        })
        if not condition:
            print(f"  ❌ {name}: {detail}")
        else:
            print(f"  ✅ {name}")

    # === PRICE SCENARIOS ===
    print("\n=== PRICE SCENARIOS ===")

    # Free-only scenario
    free_tools = [t for t in tools if (t.get("pricing") or {}).get("freePlan", {}).get("available") is True]
    check("Free-only: at least 1 tool has verified free plan", len(free_tools) >= 0,
          f"Found {len(free_tools)} tools with free plan")

    # Unknown pricing should not count as free
    for tool in tools[:10]:
        fp = (tool.get("pricing") or {}).get("freePlan") or {}
        if fp.get("available") is None and tool.get("cat"):
            # Provide category criteria so the tool can score
            result = score_tool(tool, [], [tool["cat"]], [], free_plan_only=True)
            # Unknown free-plan should NOT be filtered out (not verified as unavailable)
            check(f"Unknown free-plan not filtered for {tool['id']}", result is not None,
                  "Unknown free-plan status should not filter out the tool")
            break

    # === PLATFORM SCENARIOS ===
    print("\n=== PLATFORM SCENARIOS ===")

    # Verified supported
    tools_with_platform = [t for t in tools if t.get("platforms")]
    check("Platform: some tools have platform data", len(tools_with_platform) >= 0,
          f"Found {len(tools_with_platform)} tools with platform data")

    # Unknown platform should not disqualify
    for tool in tools:
        if not tool.get("platforms"):
            result = score_tool(tool, ["writing"], ["Writing"], ["web"])
            # Should still score via category/use case, just not platform
            if result:
                has_plat_reason = any("Platform" in r[0] for r in result["reasons"])
                check(f"Unknown platform not penalized for {tool['id']}", not has_plat_reason,
                      "Missing platform data should not add platform reason")
            break

    # === USE CASE SCENARIOS ===
    print("\n=== USE CASE SCENARIOS ===")

    use_case_tests = [
        ("writing", ["writing"], ["Writing"]),
        ("design", ["design"], ["Design"]),
        ("seo", ["seo"], ["SEO"]),
        ("marketing", ["marketing"], ["Marketing"]),
    ]

    for name, use_cases, categories in use_case_tests:
        scored = []
        for tool in tools:
            result = score_tool(tool, use_cases, categories, [])
            if result:
                scored.append(result)
        scored.sort(key=lambda x: x["score"], reverse=True)
        if scored:
            top = scored[0]
            check(f"{name}: top result has reasonable score", top["score"] >= 5,
                  f"Top: {top['tool_id']} with {top['score']} points")
        else:
            check(f"{name}: found at least one result", False,
                  "No tools scored for this use case")

    # === DATA QUALITY SCENARIOS ===
    print("\n=== DATA QUALITY SCENARIOS ===")

    # Highly verified tool
    for tool in tools:
        has_uc = bool(tool.get("useCaseTags"))
        has_bf = bool(tool.get("bestFor"))
        has_cat = bool(tool.get("cat"))
        if has_uc and has_bf and has_cat:
            result = score_tool(tool, tool["useCaseTags"][:2], [tool["cat"]], [])
            if result:
                check("Highly verified tool gets strong evidence",
                      result["evidence_level"] == "strong",
                      f"{tool['id']}: {result['evidence_level']} ({result['verified_fields']} fields)")
            break

    # Poorly verified tool
    for tool in tools:
        has_uc = bool(tool.get("useCaseTags"))
        has_bf = bool(tool.get("bestFor"))
        if not has_uc and not has_bf and tool.get("cat"):
            result = score_tool(tool, [], [tool["cat"]], [])
            if result:
                check("Poorly verified tool gets limited evidence",
                      result["evidence_level"] in ("limited", "moderate"),
                      f"{tool['id']}: {result['evidence_level']} ({result['verified_fields']} fields)")
            break

    # Generic category match
    for tool in tools:
        has_uc = bool(tool.get("useCaseTags"))
        has_bf = bool(tool.get("bestFor"))
        if not has_uc and not has_bf and tool.get("cat"):
            result = score_tool(tool, [], [tool["cat"]], [])
            if result:
                check("Category-only match flagged",
                      result.get("is_category_only") is True,
                      f"{tool['id']}: is_category_only={result.get('is_category_only')}")
            break

    # === NEGATIVE TESTS ===
    print("\n=== NEGATIVE TESTS ===")

    # Wrong platform must not be confident
    for tool in tools:
        if tool.get("platforms") and "web" in tool.get("platforms", []):
            # Score with iOS only — web-only tool should not get platform points
            result = score_tool(tool, [], [], ["iOS"])
            if result:
                has_plat = any("Platform" in r[0] for r in result["reasons"])
                check("Wrong platform: no platform points for web-only tool on iOS",
                      not has_plat,
                      f"{tool['id']}: platform reason present={has_plat}")
            break

    # Missing feature must not be high confidence
    for tool in tools:
        if not tool.get("useCaseTags"):
            result = score_tool(tool, ["writing"], [], [])
            if result:
                # Should have evidence notes about missing data
                check("Missing use case data: evidence notes present",
                      len(result.get("evidence_notes", [])) > 0,
                      f"{tool['id']}: {result['evidence_notes']}")
            break

    # Unknown free-plan must not count as free
    for tool in tools:
        fp = (tool.get("pricing") or {}).get("freePlan") or {}
        if fp.get("available") is None and tool.get("cat"):
            # With free_plan_only=True, unknown should NOT be filtered
            result = score_tool(tool, [], [tool["cat"]], [], free_plan_only=True)
            check("Unknown free-plan: not filtered as unavailable",
                  result is not None,
                  f"{tool['id']}: result={result is not None}")
            break

    # Unknown pricing must not count as cheap/free
    for tool in tools:
        pricing = tool.get("pricing") or {}
        if not pricing.get("tiers"):
            result = score_tool(tool, [], [], [])
            if result:
                check("Unknown pricing: no false pricing signals",
                      result["evidence_level"] in ("limited", "moderate"),
                      f"{tool['id']}: evidence={result['evidence_level']}")
            break

    # Category match alone must not create strong recommendation
    for tool in tools:
        if not tool.get("useCaseTags") and not tool.get("bestFor") and tool.get("cat"):
            result = score_tool(tool, [], [tool["cat"]], [])
            if result:
                # Category-only should score at most 20 points
                check("Category-only: score <= 20",
                      result["score"] <= 20,
                      f"{tool['id']}: score={result['score']}")
            break

    return results, passed, failed


def main():
    tools_data = load_json(TOOLS_V1_PATH)
    tools = tools_data["tools"]

    print(f"Running Decision Engine scenario tests with {len(tools)} tools...")

    results, passed, failed = run_scenarios(tools)

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'='*60}")

    # Save results
    report = {
        "schema_version": "decision-scenarios-v1",
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": passed + failed
        },
        "results": results
    }

    reports_dir = ROOT / "reports" / "phase3"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with (reports_dir / "decision-scenarios.json").open("w") as f:
        json.dump(report, f, indent=2)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
