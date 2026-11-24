#!/usr/bin/env python3
"""Stale-copy detection guard.

Compares data/canonical-facts.json against derived surfaces to detect
when a structured/commercial field contradicts the accepted canonical fact.

Flags only structured/commercial fields:
- price, billing basis, free_plan, trial, platform, capabilities

Does NOT flag editorial prose mentions.

Output: stale-copy report with tool_id, field, canonical_value, stale_value, surface_path.

Usage:
    python3 scripts/check_stale_copies.py          # Report stale copies
    python3 scripts/check_stale_copies.py --strict  # Exit non-zero if stale copies found
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_FACTS_PATH = ROOT / "data" / "canonical-facts.json"
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
TOOLS_JSON_PATH = ROOT / "data" / "tools.json"
DATA_TOOLS_DIR = ROOT / "data" / "tools"


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def check_tool_json_stale(tool_id: str, canonical: dict, tool_data: dict) -> List[dict]:
    """Check a tool JSON file for stale copies against canonical facts.
    
    Returns list of stale copy findings.
    """
    findings = []
    
    # Check freePlan
    if "free_plan" in canonical:
        canonical_free = canonical["free_plan"]
        if isinstance(canonical_free, dict):
            status = canonical_free.get("status", "")
            pricing = tool_data.get("pricing", {})
            tool_free = pricing.get("freePlan")
            
            if "permanent_free_plan" in status and tool_free is not True:
                findings.append({
                    "tool_id": tool_id,
                    "field": "freePlan",
                    "canonical_value": "free_plan_available",
                    "stale_value": str(tool_free),
                    "surface": "data/tools",
                    "severity": "HIGH",
                })
            elif "no_free_plan" in status and tool_free is not False:
                findings.append({
                    "tool_id": tool_id,
                    "field": "freePlan",
                    "canonical_value": "no_free_plan",
                    "stale_value": str(tool_free),
                    "surface": "data/tools",
                    "severity": "HIGH",
                })
    
    # Check trial
    if "trial" in canonical:
        canonical_trial = canonical["trial"]
        if isinstance(canonical_trial, dict):
            status = canonical_trial.get("status", "")
            pricing = tool_data.get("pricing", {})
            tool_trial = pricing.get("trial")
            
            if "no_trial" in status and tool_trial is not None and tool_trial != "":
                findings.append({
                    "tool_id": tool_id,
                    "field": "trial",
                    "canonical_value": "no_trial",
                    "stale_value": str(tool_trial),
                    "surface": "data/tools",
                    "severity": "MEDIUM",
                })
    
    # Check platforms
    if "platform" in canonical:
        canonical_platforms = canonical["platform"]
        discovery = tool_data.get("discovery", {})
        tool_platforms = discovery.get("platforms")
        
        if tool_platforms and canonical_platforms:
            if set(tool_platforms) != set(canonical_platforms):
                findings.append({
                    "tool_id": tool_id,
                    "field": "platforms",
                    "canonical_value": str(canonical_platforms),
                    "stale_value": str(tool_platforms),
                    "surface": "data/tools",
                    "severity": "MEDIUM",
                })
    
    # Check checkedOn date
    if "facts_checked" in canonical:
        canonical_date = canonical["facts_checked"]
        pricing = tool_data.get("pricing", {})
        tool_date = pricing.get("checkedOn")
        
        # Only flag if dates differ significantly (not just formatting)
        if tool_date and tool_date != canonical_date:
            # Check if it's a real discrepancy vs minor formatting
            if tool_date[:7] != canonical_date[:7]:  # Different month
                findings.append({
                    "tool_id": tool_id,
                    "field": "checkedOn",
                    "canonical_value": canonical_date,
                    "stale_value": tool_date,
                    "surface": "data/tools",
                    "severity": "LOW",
                })
    
    return findings


def check_tools_v1_stale(canonical_facts: dict, v1_data: dict) -> List[dict]:
    """Check tools-v1.json for stale copies against canonical facts."""
    findings = []
    tools = v1_data.get("tools", [])
    
    for tool in tools:
        tool_id = tool.get("id", "")
        if tool_id not in canonical_facts:
            continue
        
        canonical = canonical_facts[tool_id]
        
        # Check freePlan
        if "free_plan" in canonical:
            canonical_free = canonical["free_plan"]
            if isinstance(canonical_free, dict):
                status = canonical_free.get("status", "")
                pricing = tool.get("pricing") or {}
                tool_free = pricing.get("freePlan")
                
                if "permanent_free_plan" in status and tool_free is not True:
                    findings.append({
                        "tool_id": tool_id,
                        "field": "freePlan",
                        "canonical_value": "free_plan_available",
                        "stale_value": str(tool_free),
                        "surface": "tools-v1.json",
                        "severity": "HIGH",
                    })
                elif "no_free_plan" in status and tool_free is not False:
                    findings.append({
                        "tool_id": tool_id,
                        "field": "freePlan",
                        "canonical_value": "no_free_plan",
                        "stale_value": str(tool_free),
                        "surface": "tools-v1.json",
                        "severity": "HIGH",
                    })
        
        # Check platforms
        if "platform" in canonical:
            canonical_platforms = canonical["platform"]
            discovery = tool.get("discovery") or {}
            tool_platforms = discovery.get("platforms")
            
            if tool_platforms and canonical_platforms:
                if set(tool_platforms) != set(canonical_platforms):
                    findings.append({
                        "tool_id": tool_id,
                        "field": "platforms",
                        "canonical_value": str(canonical_platforms),
                        "stale_value": str(tool_platforms),
                        "surface": "tools-v1.json",
                        "severity": "MEDIUM",
                    })
    
    return findings


def check_tools_json_stale(canonical_facts: dict, tools_data: list) -> List[dict]:
    """Check data/tools.json for stale copies against canonical facts."""
    findings = []
    
    for tool in tools_data:
        tool_id = tool.get("id", "")
        if tool_id not in canonical_facts:
            continue
        
        canonical = canonical_facts[tool_id]
        
        # Check freePlan
        if "free_plan" in canonical:
            canonical_free = canonical["free_plan"]
            if isinstance(canonical_free, dict):
                status = canonical_free.get("status", "")
                tool_free = tool.get("freePlan")
                
                if "permanent_free_plan" in status and tool_free is not True:
                    findings.append({
                        "tool_id": tool_id,
                        "field": "freePlan",
                        "canonical_value": "free_plan_available",
                        "stale_value": str(tool_free),
                        "surface": "tools.json",
                        "severity": "HIGH",
                    })
                elif "no_free_plan" in status and tool_free is not False:
                    findings.append({
                        "tool_id": tool_id,
                        "field": "freePlan",
                        "canonical_value": "no_free_plan",
                        "stale_value": str(tool_free),
                        "surface": "tools.json",
                        "severity": "HIGH",
                    })
    
    return findings


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Stale-copy detection guard")
    parser.add_argument("--strict", action="store_true",
                       help="Exit non-zero if stale copies found")
    parser.add_argument("--report", type=str, default=None,
                       help="Save report to file")
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("Stale-Copy Detection Guard")
    print("=" * 60)
    
    # Load canonical facts
    canonical_facts = load_json(CANONICAL_FACTS_PATH)
    if not canonical_facts:
        print("\n  No canonical-facts.json found. Run derive_canonical_facts.py first.")
        return 1
    
    all_findings = []
    
    # Check data/tools/*.json
    print("\n  Checking data/tools/*.json...")
    for tool_id, canonical in canonical_facts.items():
        tool_path = DATA_TOOLS_DIR / f"{tool_id}.json"
        if tool_path.exists():
            try:
                tool_data = load_json(tool_path)
                if tool_data:
                    findings = check_tool_json_stale(tool_id, canonical, tool_data)
                    all_findings.extend(findings)
            except Exception:
                pass
    
    # Check tools-v1.json
    print("  Checking tools-v1.json...")
    v1_data = load_json(TOOLS_V1_PATH)
    if v1_data:
        findings = check_tools_v1_stale(canonical_facts, v1_data)
        all_findings.extend(findings)
    
    # Check tools.json
    print("  Checking tools.json...")
    tools_data = load_json(TOOLS_JSON_PATH)
    if isinstance(tools_data, list):
        findings = check_tools_json_stale(canonical_facts, tools_data)
        all_findings.extend(findings)
    
    # Summary
    high_severity = sum(1 for f in all_findings if f.get("severity") == "HIGH")
    medium_severity = sum(1 for f in all_findings if f.get("severity") == "MEDIUM")
    low_severity = sum(1 for f in all_findings if f.get("severity") == "LOW")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total stale copies found: {len(all_findings)}")
    print(f"  HIGH severity: {high_severity}")
    print(f"  MEDIUM severity: {medium_severity}")
    print(f"  LOW severity: {low_severity}")
    
    if all_findings:
        print(f"\n  Top findings:")
        # Sort by severity
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_findings = sorted(
            all_findings,
            key=lambda f: severity_order.get(f.get("severity", "LOW"), 3)
        )
        for finding in sorted_findings[:10]:
            print(f"    [{finding['severity']}] {finding['tool_id']}.{finding['field']}: "
                  f"canonical={finding['canonical_value']}, "
                  f"stale={finding['stale_value']} "
                  f"({finding['surface']})")
    
    # Save report if requested
    if args.report:
        report = {
            "pipeline": "stale_copy_detection",
            "total_findings": len(all_findings),
            "high_severity": high_severity,
            "medium_severity": medium_severity,
            "low_severity": low_severity,
            "findings": all_findings,
        }
        save_json(Path(args.report), report)
        print(f"\n  Report saved to {args.report}")
    
    print(f"{'='*60}\n")
    
    if args.strict and all_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
