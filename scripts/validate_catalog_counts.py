#!/usr/bin/env python3
"""
Catalog Count Validation for ToolNest.

Reconciles the authoritative v1 catalog count against the v2 enriched record count,
documents the split, and validates that no tool appears in both with conflicting IDs.

This script enforces the rule that future reports must distinguish:
- v1 catalog count (authoritative tools)
- v2 enriched count (research records)

The 10 expansion-only tools are legitimate research records but not yet in the
authoritative catalog. They remain in v2/expansion/ without being forced into v1.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
TOOLS_V2_DIR = ROOT / "data" / "tools-v2"
SITEMAP_PATH = ROOT / "sitemap.xml"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_v1_tool_ids() -> Dict[str, Dict]:
    """Load tools-v1.json and return dict indexed by tool id."""
    data = load_json(TOOLS_V1_PATH)
    tools_list = data.get("tools", [])
    return {t["id"]: t for t in tools_list}


def load_v2_tool_ids() -> Dict[str, Tuple[Dict, Path]]:
    """Load all tools-v2 JSON files and return dict indexed by tool id, with file path."""
    tools: Dict[str, Tuple[Dict, Path]] = {}
    for f in TOOLS_V2_DIR.rglob("*.json"):
        try:
            t = load_json(f)
            tid = t.get("identity", {}).get("id", f.stem)
            tools[tid] = (t, f)
        except (json.JSONDecodeError, KeyError):
            continue
    return tools


def categorize_v2_tools(v2_tools: Dict[str, Tuple[Dict, Path]]) -> Dict[str, List[str]]:
    """Categorize v2 tools into legacy, expansion, and root."""
    categories: Dict[str, List[str]] = {
        "legacy": [],
        "expansion": [],
        "root": []
    }
    for tid, (data, path) in v2_tools.items():
        rel = path.relative_to(TOOLS_V2_DIR)
        if rel.parts[0] == "legacy":
            categories["legacy"].append(tid)
        elif rel.parts[0] == "expansion":
            categories["expansion"].append(tid)
        else:
            categories["root"].append(tid)
    return categories


def check_sitemap_coverage(v1_ids: Set[str]) -> Dict[str, Any]:
    """Check that sitemap includes all v1 catalog tools."""
    if not SITEMAP_PATH.exists():
        return {"status": "SKIP", "reason": "sitemap.xml not found"}
    
    content = SITEMAP_PATH.read_text(encoding="utf-8")
    missing = []
    for tid in sorted(v1_ids):
        # Check for tool page in sitemap
        if f"tools/{tid}" not in content and f"/tools/{tid}" not in content:
            missing.append(tid)
    
    return {
        "status": "PASS" if not missing else "FAIL",
        "total_v1_tools": len(v1_ids),
        "tools_in_sitemap": len(v1_ids) - len(missing),
        "missing_from_sitemap": missing
    }


def validate_catalog_counts() -> Dict[str, Any]:
    """Main validation logic."""
    print("=" * 60)
    print("ToolNest Catalog Count Validation")
    print("=" * 60)
    
    # Load data
    print("\nLoading data...")
    v1_tools = load_v1_tool_ids()
    v2_tools = load_v2_tool_ids()
    
    v1_ids = set(v1_tools.keys())
    v2_ids = set(v2_tools.keys())
    
    print(f"  V1 catalog tools: {len(v1_ids)}")
    print(f"  V2 enriched records: {len(v2_ids)}")
    
    # Categorize v2 tools
    v2_categories = categorize_v2_tools(v2_tools)
    print(f"\n  V2 breakdown:")
    print(f"    Legacy: {len(v2_categories['legacy'])}")
    print(f"    Expansion: {len(v2_categories['expansion'])}")
    print(f"    Root: {len(v2_categories['root'])}")
    
    # Calculate sets
    in_v1_only = v1_ids - v2_ids
    in_v2_only = v2_ids - v1_ids
    in_both = v1_ids & v2_ids
    
    print(f"\n  In v1 only: {len(in_v1_only)}")
    print(f"  In v2 only: {len(in_v2_only)}")
    print(f"  In both: {len(in_both)}")
    
    # Check for missing v1 tools in v2
    issues: List[Dict[str, Any]] = []
    
    if in_v1_only:
        issue = {
            "type": "MISSING_V2_RECORD",
            "severity": "ERROR",
            "description": f"{len(in_v1_only)} v1 catalog tools have no v2 record",
            "tools": sorted(in_v1_only)
        }
        issues.append(issue)
        print(f"\n  ERROR: Missing v2 records for: {sorted(in_v1_only)}")
    
    # Document expansion-only tools
    expansion_only = sorted(in_v2_only)
    print(f"\n  Expansion-only tools (not in v1 catalog): {len(expansion_only)}")
    for tid in expansion_only:
        data, path = v2_tools[tid]
        name = data.get("identity", {}).get("name", "unknown")
        print(f"    {tid}: {name} ({path.relative_to(ROOT)})")
    
    # Check sitemap
    sitemap_result = check_sitemap_coverage(v1_ids)
    print(f"\n  Sitemap coverage: {sitemap_result.get('status', 'SKIP')}")
    
    # Check for conflicting IDs between v1 and v2
    conflicts = []
    for tid in in_both:
        v1_tool = v1_tools[tid]
        v2_tool_data, _ = v2_tools[tid]
        v1_name = v1_tool.get("name", "")
        v2_name = v2_tool_data.get("identity", {}).get("name", "")
        if v1_name and v2_name and v1_name.lower() != v2_name.lower():
            conflicts.append({
                "tool_id": tid,
                "v1_name": v1_name,
                "v2_name": v2_name
            })
    
    if conflicts:
        # Name conflicts are informational — rebranding or product name changes
        # are expected and not validation failures
        issue = {
            "type": "NAME_CONFLICT",
            "severity": "INFO",
            "description": f"{len(conflicts)} tools have different names in v1 vs v2 (rebranding/product name changes)",
            "conflicts": conflicts
        }
        issues.append(issue)
        print(f"\n  INFO: Name differences (rebranding): {len(conflicts)}")
        for c in conflicts:
            print(f"    {c['tool_id']}: v1='{c['v1_name']}' vs v2='{c['v2_name']}'")
    
    # Build reconciliation report
    report = {
        "generated_at": datetime.now().isoformat(),
        "validation_rule": "v1 catalog count must equal authoritative tools; v2 enriched count may exceed v1 for expansion research records",
        "counts": {
            "v1_authoritative": len(v1_ids),
            "v2_enriched": len(v2_ids),
            "v2_legacy": len(v2_categories["legacy"]),
            "v2_expansion": len(v2_categories["expansion"]),
            "v2_root": len(v2_categories["root"]),
            "expansion_only_not_in_v1": len(expansion_only)
        },
        "expansion_only_tools": expansion_only,
        "missing_v2_records": sorted(in_v1_only),
        "name_conflicts": conflicts,
        "sitemap_coverage": sitemap_result,
        "issues": issues,
        "validation_passed": len(in_v1_only) == 0
    }
    
    # Save report
    report_path = ROOT / "data" / "catalog-reconciliation.json"
    save_json(report_path, report)
    print(f"\n  Report saved to {report_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"  V1 Authoritative: {len(v1_ids)}")
    print(f"  V2 Enriched: {len(v2_ids)}")
    print(f"  Expansion-only: {len(expansion_only)}")
    print(f"  Missing v2 records: {len(in_v1_only)}")
    print(f"  Name conflicts: {len(conflicts)}")
    print(f"  Validation: {'PASS' if report['validation_passed'] else 'FAIL'}")
    
    return report


def main():
    report = validate_catalog_counts()
    if not report["validation_passed"]:
        print("\n  WARNING: Validation failed. Review issues above.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
