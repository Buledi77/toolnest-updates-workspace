"""Audit the complete Decision Engine scoring pipeline.

Traces: USER INPUT → normalized requirement → catalog field → evidence state → scoring rule → score → recommendation

Documents every scoring dimension and identifies where UNKNOWN data behaves as positive evidence.

Outputs:
- reports/phase3/scoring-audit.json
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
CONFIG_PATH = ROOT / "data" / "decision-engine-config.json"
EVIDENCE_LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
REPORTS_DIR = ROOT / "reports" / "phase3"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def audit_data_coverage(tools):
    """Audit data coverage for scoring dimensions."""
    total = len(tools)
    
    # Use case tags coverage
    tools_with_uc = sum(1 for t in tools if t.get("useCaseTags"))
    total_uc_tags = sum(len(t.get("useCaseTags", [])) for t in tools)
    
    # Category coverage
    tools_with_cat = sum(1 for t in tools if t.get("cat"))
    
    # Best for coverage
    tools_with_best = sum(1 for t in tools if t.get("best"))
    tools_with_bestfor = sum(1 for t in tools if t.get("bestFor"))
    
    # Platform coverage
    tools_with_platform = sum(1 for t in tools if t.get("platforms"))
    
    # Pricing coverage
    tools_with_pricing = 0
    tools_with_free_plan = 0
    tools_with_tiers = 0
    for t in tools:
        pricing = t.get("pricing", {})
        if pricing:
            tools_with_pricing += 1
            fp = pricing.get("freePlan", {})
            if fp.get("available") is not None:
                tools_with_free_plan += 1
                if fp.get("available") is True:
                    pass  # count true separately if needed
            if pricing.get("tiers"):
                tools_with_tiers += 1
    
    # Cons coverage
    tools_with_cons = sum(1 for t in tools if t.get("cons"))
    
    # Evidence ledger coverage
    ledger = load_json(EVIDENCE_LEDGER_PATH) if EVIDENCE_LEDGER_PATH.exists() else {"claims": []}
    tool_ids_with_claims = set()
    for claim in ledger.get("claims", []):
        tid = claim.get("tool_id")
        if tid:
            tool_ids_with_claims.add(tid)
    
    return {
        "total_tools": total,
        "use_case_tags": {
            "tools_with_tags": tools_with_uc,
            "coverage_pct": round(tools_with_uc / total * 100, 1) if total else 0,
            "total_tags": total_uc_tags
        },
        "category": {
            "tools_with_category": tools_with_cat,
            "coverage_pct": round(tools_with_cat / total * 100, 1) if total else 0
        },
        "best_for": {
            "tools_with_best": tools_with_best,
            "tools_with_bestfor": tools_with_bestfor,
            "coverage_pct": round((tools_with_best + tools_with_bestfor) / total * 100, 1) if total else 0
        },
        "platforms": {
            "tools_with_platforms": tools_with_platform,
            "coverage_pct": round(tools_with_platform / total * 100, 1) if total else 0
        },
        "pricing": {
            "tools_with_pricing": tools_with_pricing,
            "tools_with_free_plan_known": tools_with_free_plan,
            "tools_with_tiers": tools_with_tiers,
            "coverage_pct": round(tools_with_pricing / total * 100, 1) if total else 0
        },
        "cons": {
            "tools_with_cons": tools_with_cons,
            "coverage_pct": round(tools_with_cons / total * 100, 1) if total else 0
        },
        "evidence_ledger": {
            "tools_with_claims": len(tool_ids_with_claims),
            "coverage_pct": round(len(tool_ids_with_claims) / total * 100, 1) if total else 0,
            "total_claims": len(ledger.get("claims", []))
        }
    }


def audit_config_vs_frontend(config):
    """Compare config scoring rules vs actual frontend implementation."""
    config_rules = config.get("scoring", {}).get("rules", [])
    
    # Frontend weights (from decision-engine.html)
    frontend_weights = {
        "use_case_match": 40,
        "category_match": 20,
        "best_for_match": 20,
        "platform_match": 10,
        "evidence_quality": 0,  # NOT implemented
        "pricing_known": 0      # NOT implemented
    }
    
    discrepancies = []
    for rule in config_rules:
        rule_id = rule.get("id", "")
        config_weight = rule.get("weight", 0)
        frontend_weight = frontend_weights.get(rule_id, 0)
        
        if config_weight != frontend_weight:
            discrepancies.append({
                "rule": rule_id,
                "config_weight": config_weight,
                "frontend_weight": frontend_weight,
                "issue": "weight_mismatch" if frontend_weight and config_weight != frontend_weight else "not_implemented" if not frontend_weight else "unknown"
            })
    
    return discrepancies


def audit_three_state_gaps(tools):
    """Identify where UNKNOWN data currently behaves as positive evidence."""
    issues = []
    
    for tool in tools:
        tool_id = tool["id"]
        
        # Check for empty useCaseTags that could still score via category
        uc_tags = tool.get("useCaseTags", [])
        cat = tool.get("cat", "")
        best = tool.get("best", "")
        
        if not uc_tags and not best:
            # Tool can only score via category match — generic match risk
            issues.append({
                "tool_id": tool_id,
                "issue": "generic_category_only",
                "severity": "warning",
                "detail": f"Tool has no useCaseTags or best data — can only score via category match ({cat})"
            })
        
        # Check for unknown pricing that could be misinterpreted
        pricing = tool.get("pricing", {})
        free_plan = pricing.get("freePlan", {})
        if free_plan.get("available") is None and pricing.get("tiers") == []:
            issues.append({
                "tool_id": tool_id,
                "issue": "unknown_pricing",
                "severity": "info",
                "detail": "Pricing data is unknown — should not count as free or paid"
            })
    
    return issues


def audit_scoring_pipeline():
    """Main audit function."""
    tools_data = load_json(TOOLS_V1_PATH)
    tools = tools_data["tools"]
    config = load_json(CONFIG_PATH)
    
    # 1. Data coverage audit
    coverage = audit_data_coverage(tools)
    
    # 2. Config vs frontend discrepancies
    discrepancies = audit_config_vs_frontend(config)
    
    # 3. Three-state gaps
    three_state_issues = audit_three_state_gaps(tools)
    
    # 4. Scoring dimension trace
    scoring_trace = {
        "user_input": {
            "use_cases": "Multi-select chips from useCaseTags",
            "categories": "Multi-select chips from cat field",
            "platforms": "Multi-select chips (disabled due to low coverage)",
            "free_plan": "Toggle (disabled due to low coverage)"
        },
        "normalization": {
            "method": "toLowerCase().replace(/[^a-z0-9]/g, '')",
            "issue": "Aggressive normalization may cause false matches"
        },
        "catalog_fields": {
            "use_case_match": "useCaseTags array",
            "category_match": "cat string",
            "best_for_match": "bestFor array",
            "platform_match": "platforms array"
        },
        "evidence_state": {
            "verified_match": "Field exists and matches user input",
            "verified_mismatch": "Field exists and does NOT match",
            "unknown": "Field is empty/null — currently treated as neutral but could be misinterpreted"
        },
        "scoring_rules": {
            "config_rules": config.get("scoring", {}).get("rules", []),
            "frontend_implementation": {
                "use_case_match": "40pts, percentage of selected use cases matched",
                "category_match": "20pts, binary match",
                "best_for_match": "20pts, percentage of selected use cases matched",
                "platform_match": "10pts, percentage of selected platforms matched",
                "evidence_quality": "NOT IMPLEMENTED in frontend",
                "pricing_known": "NOT IMPLEMENTED in frontend"
            },
            "total_max_score_config": 90,
            "total_max_score_frontend": 90
        },
        "recommendation": {
            "min_score_to_show": 5,
            "confidence_levels": {
                "high": "≥63 = Strong Match",
                "medium": "≥36 = Good Match",
                "low": "≥5 = Possible Match"
            }
        }
    }
    
    # Build report
    report = {
        "generated_at": date.today().isoformat(),
        "schema_version": "scoring-audit-v1",
        "summary": {
            "total_tools": len(tools),
            "data_coverage": coverage,
            "config_frontend_discrepancies": len(discrepancies),
            "three_state_issues": len(three_state_issues),
            "critical_findings": [
                "Config weights (15/15/40/5) differ from frontend weights (40/20/20/10)",
                "evidence_quality dimension in config but NOT implemented in frontend",
                "pricing_known dimension in config but NOT implemented in frontend",
                "No three-state reasoning — UNKNOWN data treated as neutral, not explicitly handled",
                "No disqualifiers implemented",
                "No evidence confidence score separate from fit score"
            ]
        },
        "config_frontend_discrepancies": discrepancies,
        "three_state_issues": three_state_issues[:20],  # First 20
        "scoring_trace": scoring_trace,
        "recommendations": [
            "Align config weights with frontend implementation or vice versa",
            "Implement evidence_quality and pricing_known in frontend scoring",
            "Add three-state reasoning: VERIFIED MATCH, VERIFIED MISMATCH, UNKNOWN",
            "Add evidence confidence score separate from fit score",
            "Implement high-impact disqualifiers for verified mismatches",
            "Add 'Why It Matched' and 'Trade-offs' sections to frontend"
        ]
    }
    
    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "scoring-audit.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"Scoring audit written to {output_path}")
    print(f"\nData Coverage:")
    for key, value in coverage.items():
        if isinstance(value, dict) and "coverage_pct" in value:
            print(f"  {key}: {value['coverage_pct']}%")
    
    print(f"\nConfig vs Frontend Discrepancies: {len(discrepancies)}")
    for d in discrepancies:
        print(f"  {d['rule']}: config={d['config_weight']}, frontend={d['frontend_weight']} ({d['issue']})")
    
    print(f"\nThree-State Issues: {len(three_state_issues)}")
    print(f"\nCritical Findings:")
    for finding in report["summary"]["critical_findings"]:
        print(f"  ⚠️  {finding}")
    
    return report


if __name__ == "__main__":
    audit_scoring_pipeline()
