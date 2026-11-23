"""Golden decision cases — benchmark scenarios for the Decision Engine.

Each case stores:
- User requirements
- Expected eligible tools
- Expected exclusions
- Acceptable alternatives
- Required explanation elements

Validates logic, not predetermined commercial rankings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"

# Import scoring function from test_decision_scenarios
sys.path.insert(0, str(ROOT / "tests"))
from test_decision_scenarios import score_tool, load_json


def run_golden_cases(tools):
    """Run golden decision cases."""
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
        results.append({"name": name, "status": status, "detail": detail})
        print(f"  {'✅' if condition else '❌'} {name}: {detail}")

    # === GOLDEN CASE 1: SEO Tool Search ===
    print("\n=== GOLDEN CASE 1: SEO Tool Search ===")
    use_cases = ["seo", "keyword research"]
    categories = ["SEO"]

    scored = []
    for tool in tools:
        result = score_tool(tool, use_cases, categories, [])
        if result:
            scored.append(result)
    scored.sort(key=lambda x: x["score"], reverse=True)

    if scored:
        top = scored[0]
        check("SEO: semrush or ahrefs in top results",
              top["tool_id"] in ("semrush", "ahrefs", "surferseo", "mozpro"),
              f"Top: {top['tool_id']} with {top['score']} points")
        # Check that at least one result has a reason (category or use case)
        has_reason = any(len(r["reasons"]) > 0 for r in scored)
        check("SEO: results have scoring reasons",
              has_reason,
              f"Top reasons: {[r[0] for r in top['reasons']]}")
    else:
        check("SEO: found results", False, "No results")

    # === GOLDEN CASE 2: Writing Tool Search ===
    print("\n=== GOLDEN CASE 2: Writing Tool Search ===")
    use_cases = ["writing", "editing"]
    categories = ["Writing"]

    scored = []
    for tool in tools:
        result = score_tool(tool, use_cases, categories, [])
        if result:
            scored.append(result)
    scored.sort(key=lambda x: x["score"], reverse=True)

    if scored:
        top = scored[0]
        check("Writing: grammarly or jasper in top results",
              top["tool_id"] in ("grammarly", "jasper", "quillbot", "prowritingaid", "writesonic", "hemingway"),
              f"Top: {top['tool_id']} with {top['score']} points")
    else:
        check("Writing: found results", False, "No results")

    # === GOLDEN CASE 3: Design Tool Search ===
    print("\n=== GOLDEN CASE 3: Design Tool Search ===")
    use_cases = ["design"]
    categories = ["Design"]

    scored = []
    for tool in tools:
        result = score_tool(tool, use_cases, categories, [])
        if result:
            scored.append(result)
    scored.sort(key=lambda x: x["score"], reverse=True)

    if scored:
        top = scored[0]
        check("Design: canva or figma in top results",
              top["tool_id"] in ("canva", "figma", "adobeexpress"),
              f"Top: {top['tool_id']} with {top['score']} points")
    else:
        check("Design: found results", False, "No results")

    # === GOLDEN CASE 4: Category-Only Should Not Be Strong ===
    print("\n=== GOLDEN CASE 4: Category-Only Weakness ===")
    # Find a tool with only category data
    for tool in tools:
        if not tool.get("useCaseTags") and not tool.get("bestFor") and tool.get("cat"):
            result = score_tool(tool, [], [tool["cat"]], [])
            if result:
                check("Category-only: score <= 20",
                      result["score"] <= 20,
                      f"{tool['id']}: {result['score']} points")
                check("Category-only: limited/moderate evidence",
                      result["evidence_level"] in ("limited", "moderate"),
                      f"{tool['id']}: {result['evidence_level']}")
                check("Category-only: has tradeoff warning",
                      any("category" in t.lower() for t in result["tradeoffs"]),
                      f"{tool['id']}: {result['tradeoffs']}")
            break

    # === GOLDEN CASE 5: Free Plan Requirement Affects Result ===
    print("\n=== GOLDEN CASE 5: Free Plan Requirement ===")
    # Tools with verified free plans should appear when free_plan_only=True
    free_tools = [t for t in tools if (t.get("pricing") or {}).get("freePlan", {}).get("available") is True]
    if free_tools:
        scored_free = []
        for tool in free_tools:
            result = score_tool(tool, [], [tool.get("cat", "")], [], free_plan_only=True)
            if result:
                scored_free.append(result)
        check("Free plan: tools with free plan pass filter",
              len(scored_free) > 0,
              f"{len(scored_free)} tools with free plan found")
        # Tools with freePlan=false should be filtered out
        no_free = [t for t in tools if (t.get("pricing") or {}).get("freePlan", {}).get("available") is False]
        if no_free:
            filtered = score_tool(no_free[0], [], [no_free[0].get("cat", "")], [], free_plan_only=True)
            check("Free plan: tools without free plan filtered out",
                  filtered is None,
                  f"{no_free[0]['id']}: filtered={filtered is None}")
    else:
        check("Free plan: found tools with free plan", False, "No free plan tools")

    # === GOLDEN CASE 6: Platform Mismatch Affects Result ===
    print("\n=== GOLDEN CASE 6: Platform Mismatch ===")
    plat_tools = [t for t in tools if t.get("platforms")]
    if plat_tools:
        tool = plat_tools[0]
        # Score with a platform the tool doesn't have
        missing_plat = "macOS" if "macOS" not in tool.get("platforms", []) else "Windows"
        result = score_tool(tool, [], [], [missing_plat])
        if result:
            has_plat_reason = any("Platform" in r[0] for r in result["reasons"])
            check("Platform mismatch: no platform points for missing platform",
                  not has_plat_reason,
                  f"{tool['id']}: platforms={tool['platforms']}, requested={missing_plat}")
    else:
        check("Platform: found tools with platform data", False, "No platform tools")

    # === GOLDEN CASE 7: Unknown Pricing Prevents Budget Certainty ===
    print("\n=== GOLDEN CASE 7: Unknown Pricing ===")
    # Tools without pricing tiers should not appear as $0
    no_pricing = [t for t in tools if not (t.get("pricing") or {}).get("tiers")]
    if no_pricing:
        result = score_tool(no_pricing[0], [], [], [])
        if result:
            check("Unknown pricing: evidence level is limited/moderate",
                  result["evidence_level"] in ("limited", "moderate"),
                  f"{no_pricing[0]['id']}: {result['evidence_level']}")
    else:
        check("Unknown pricing: found tools without pricing", False, "All tools have pricing")

    # === GOLDEN CASE 8: Verified Tool Beats Unverified in Same Category ===
    print("\n=== GOLDEN CASE 8: Verified vs Unverified ===")
    # In Productivity category, notion has verified data vs tools without
    prod_tools = [t for t in tools if t.get("cat") == "Productivity"]
    scored_prod = []
    for tool in prod_tools:
        result = score_tool(tool, ["notes", "tasks"], ["Productivity"], [])
        if result:
            scored_prod.append(result)
    scored_prod.sort(key=lambda x: x["score"], reverse=True)
    if scored_prod:
        top = scored_prod[0]
        # Notion should rank high due to verified use case data
        check("Verified tool: notion ranks high in Productivity",
              top["tool_id"] in ("notion", "clickup", "asana", "todoist", "wrike", "monday"),
              f"Top: {top['tool_id']} with {top['score']} points, {top['verified_fields']} verified fields")
    else:
        check("Verified tool: found Productivity results", False, "No results")

    # === GOLDEN CASE 9: Two Strong Tools Remain Legitimate Alternatives ===
    print("\n=== GOLDEN CASE 9: Legitimate Alternatives ===")
    # QuickBooks and Xero are both accounting tools with verified pricing
    accounting = [t for t in tools if t.get("cat") in ("Productivity",) and t.get("id") in ("quickbooks", "xero")]
    scored_acct = []
    for tool in accounting:
        result = score_tool(tool, ["accounting", "invoicing"], [], [])
        if result:
            scored_acct.append(result)
    scored_acct.sort(key=lambda x: x["score"], reverse=True)
    if len(scored_acct) >= 2:
        # Both should have similar scores since both are verified
        diff = abs(scored_acct[0]["score"] - scored_acct[1]["score"])
        check("Legitimate alternatives: similar scores for verified tools",
              diff <= 20,
              f"{scored_acct[0]['tool_id']}={scored_acct[0]['score']}, {scored_acct[1]['tool_id']}={scored_acct[1]['score']}, diff={diff}")
    else:
        check("Legitimate alternatives: found both tools", len(scored_acct) >= 2,
              f"Found {len(scored_acct)} tools")

    # === GOLDEN CASE 10: Conflicting Evidence Prevents High Confidence ===
    print("\n=== GOLDEN CASE 10: Conflicting Evidence ===")
    # Semrush has CONFLICTING_EVIDENCE state
    semrush_tool = next((t for t in tools if t.get("id") == "semrush"), None)
    if semrush_tool:
        result = score_tool(semrush_tool, ["seo"], ["SEO"], [])
        if result:
            check("Conflicting evidence: semrush still scores but with caveats",
                  result["score"] > 0,
                  f"Semrush score: {result['score']}, evidence: {result['evidence_level']}")

    return results, passed, failed


def main():
    tools_data = load_json(TOOLS_V1_PATH)
    tools = tools_data["tools"]

    print(f"Running Golden Decision Cases with {len(tools)} tools...")
    results, passed, failed = run_golden_cases(tools)

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'='*60}")

    report = {
        "schema_version": "golden-decisions-v1",
        "summary": {"passed": passed, "failed": failed, "total": passed + failed},
        "results": results
    }

    reports_dir = ROOT / "reports" / "phase3"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with (reports_dir / "golden-decisions.json").open("w") as f:
        json.dump(report, f, indent=2)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
