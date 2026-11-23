#!/usr/bin/env python3
"""
Decision-Critical Coverage Metrics for ToolNest.

Generates per-tool coverage across 11 decision-critical fields, tracking:
- verified_official: Backed by VERIFIED_OFFICIAL evidence
- verified: Backed by verified evidence (non-official but confirmed)
- editorial: Backed by EDITORIAL_ASSESSMENT
- data_present: Field has content but no evidence claim
- unknown: Field is empty or missing

Output: data/decision-critical-coverage.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
TOOLS_V2_DIR = ROOT / "data" / "tools-v2"
EVIDENCE_LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
READINESS_SUMMARY_PATH = ROOT / "data" / "decision-readiness-summary.json"

DECISION_CRITICAL_FIELDS = [
    "core_use_case",
    "meaningful_capabilities",
    "important_limitations",
    "platform",
    "pricing_model",
    "pricing_state",
    "free_plan_status",
    "trial_status",
    "target_user",
    "meaningful_alternatives",
    "evidence_freshness"
]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_coverage_metrics() -> Dict[str, Any]:
    """Build per-tool coverage metrics from the decision readiness summary."""
    print("=" * 60)
    print("ToolNest Decision-Critical Coverage Metrics")
    print("=" * 60)
    
    # Load the decision readiness summary (which now has evidence_status per field)
    if not READINESS_SUMMARY_PATH.exists():
        print("ERROR: decision-readiness-summary.json not found. Run build_decision_readiness.py first.")
        return {}
    
    readiness = load_json(READINESS_SUMMARY_PATH)
    tools_data = readiness.get("tools", [])
    
    print(f"\n  Tools in readiness summary: {len(tools_data)}")
    
    # Build per-tool coverage
    coverage_by_tool: Dict[str, Dict] = {}
    
    # Aggregate counts
    aggregate: Dict[str, Dict[str, int]] = {
        field: {
            "verified_official": 0,
            "verified": 0,
            "editorial": 0,
            "data_present": 0,
            "unknown": 0
        }
        for field in DECISION_CRITICAL_FIELDS
    }
    
    for tool_entry in tools_data:
        tool_id = tool_entry["tool_id"]
        
        # Get field details from the readiness summary
        # The readiness summary stores field_details in v2 JSON files
        # We need to load from v2 files for detailed field info
        v2_path = ROOT / "data" / "tools-v2" / "legacy" / f"{tool_id}.json"
        if not v2_path.exists():
            v2_path = ROOT / "data" / "tools-v2" / "expansion" / f"{tool_id}.json"
        
        field_details = {}
        if v2_path.exists():
            try:
                v2_data = load_json(v2_path)
                field_details = (v2_data.get("decision_readiness") or {}).get("field_details", {})
            except (json.JSONDecodeError, KeyError):
                pass
        
        tool_coverage: Dict[str, Any] = {
            "tool_id": tool_id,
            "state": tool_entry.get("state", ""),
            "fields": {}
        }
        
        for field in DECISION_CRITICAL_FIELDS:
            fd = field_details.get(field, {})
            evidence_status = fd.get("evidence_status", "UNKNOWN")
            
            # Map evidence_status to coverage categories
            if evidence_status == "VERIFIED_OFFICIAL":
                category = "verified_official"
            elif evidence_status == "VERIFIED":
                category = "verified"
            elif evidence_status == "EDITORIAL":
                category = "editorial"
            elif evidence_status == "DATA_PRESENT":
                category = "data_present"
            else:
                category = "unknown"
            
            tool_coverage["fields"][field] = {
                "evidence_status": evidence_status,
                "verified": fd.get("verified", False),
                "has_data": fd.get("has_data", False)
            }
            
            # Update aggregate
            aggregate[field][category] += 1
        
        coverage_by_tool[tool_id] = tool_coverage
    
    # Calculate summary statistics
    total_tools = len(coverage_by_tool)
    
    # Count tools by coverage level
    tools_by_coverage = {
        "fully_verified": 0,  # All fields verified
        "high_coverage": 0,    # 8+ fields with any evidence
        "medium_coverage": 0,  # 5-7 fields with any evidence
        "low_coverage": 0,     # 3-4 fields with any evidence
        "minimal_coverage": 0  # <3 fields with any evidence
    }
    
    for tool_id, coverage in coverage_by_tool.items():
        fields_with_evidence = 0
        for field in DECISION_CRITICAL_FIELDS:
            fd = coverage["fields"].get(field, {})
            if fd.get("has_data") or fd.get("verified"):
                fields_with_evidence += 1
        
        if fields_with_evidence >= 11:
            tools_by_coverage["fully_verified"] += 1
        elif fields_with_evidence >= 8:
            tools_by_coverage["high_coverage"] += 1
        elif fields_with_evidence >= 5:
            tools_by_coverage["medium_coverage"] += 1
        elif fields_with_evidence >= 3:
            tools_by_coverage["low_coverage"] += 1
        else:
            tools_by_coverage["minimal_coverage"] += 1
    
    # Build output
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_tools": total_tools,
        "decision_critical_fields": DECISION_CRITICAL_FIELDS,
        "aggregate_coverage": {
            field: {
                **aggregate[field],
                "total": total_tools,
                "verified_percentage": round(
                    (aggregate[field]["verified_official"] + aggregate[field]["verified"]) / total_tools * 100
                ) if total_tools else 0,
                "any_evidence_percentage": round(
                    (aggregate[field]["verified_official"] + aggregate[field]["verified"] + aggregate[field]["editorial"]) / total_tools * 100
                ) if total_tools else 0
            }
            for field in DECISION_CRITICAL_FIELDS
        },
        "tools_by_coverage_level": tools_by_coverage,
        "tools": coverage_by_tool
    }
    
    # Save
    output_path = ROOT / "data" / "decision-critical-coverage.json"
    save_json(output_path, output)
    print(f"\n  Coverage metrics saved to {output_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("COVERAGE SUMMARY")
    print("=" * 60)
    
    print(f"\n  Tools by Coverage Level:")
    for level, count in tools_by_coverage.items():
        pct = round(count / total_tools * 100) if total_tools else 0
        print(f"    {level}: {count} ({pct}%)")
    
    print(f"\n  Field-Level Coverage:")
    for field in DECISION_CRITICAL_FIELDS:
        agg = output["aggregate_coverage"][field]
        print(f"    {field}:")
        print(f"      verified_official: {agg['verified_official']}")
        print(f"      verified: {agg['verified']}")
        print(f"      editorial: {agg['editorial']}")
        print(f"      data_present: {agg['data_present']}")
        print(f"      unknown: {agg['unknown']}")
        print(f"      verified_pct: {agg['verified_percentage']}%")
    
    return output


def main():
    output = build_coverage_metrics()
    if not output:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
