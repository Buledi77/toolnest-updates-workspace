#!/usr/bin/env python3
"""Production scope validator — guards against expansion-only tool leakage.

Ensures that the 10 expansion-only tools never appear in any production surface:
- tools/ HTML files
- category/ pages
- compare/ pages
- best/ pages
- goals/ pages
- sitemap.xml
- data/decision-engine-bundle.json
- index.html (homepage)

Usage:
    python3 scripts/validate_production_scope.py          # Run all checks
    python3 scripts/validate_production_scope.py --fix     # Report what needs fixing
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
CATALOG_RECON_PATH = ROOT / "data" / "catalog-reconciliation.json"
DECISION_BUNDLE_PATH = ROOT / "data" / "decision-engine-bundle.json"
SITEMAP_PATH = ROOT / "sitemap.xml"
INDEX_PATH = ROOT / "index.html"
TOOLS_HTML_DIR = ROOT / "tools"
CATEGORY_HTML_DIR = ROOT / "category"
COMPARE_HTML_DIR = ROOT / "compare"
BEST_HTML_DIR = ROOT / "best"
GOALS_HTML_DIR = ROOT / "goals"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_production_tool_ids() -> Set[str]:
    """Get the set of 153 production tool IDs from tools-v1.json."""
    v1 = load_json(TOOLS_V1_PATH)
    tools = v1.get("tools", []) if isinstance(v1, dict) else v1
    return {t["id"] for t in tools}


def get_expansion_only_ids() -> Set[str]:
    """Get the set of expansion-only tool IDs that must not leak into production."""
    if not CATALOG_RECON_PATH.is_file():
        return set()
    recon = load_json(CATALOG_RECON_PATH)
    return set(recon.get("expansion_only_tools", []))


def check_html_file(path: Path, expansion_ids: Set[str]) -> List[dict]:
    """Check an HTML file for references to expansion-only tool IDs."""
    issues = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return issues
    
    for eid in expansion_ids:
        # Check for tool_id references in various formats
        patterns = [
            rf'\b{re.escape(eid)}\b',  # Direct ID match
            rf'href=["\'].*?/{re.escape(eid)}',  # Link to tool
            rf'data-tool=["\']?{re.escape(eid)}',  # Data attribute
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append({
                    "file": str(path.relative_to(ROOT)),
                    "expansion_tool": eid,
                    "pattern": pattern,
                    "severity": "HIGH",
                })
                break  # One issue per tool per file
    
    return issues


def check_json_data(path: Path, expansion_ids: Set[str]) -> List[dict]:
    """Check a JSON file for expansion-only tool IDs."""
    issues = []
    try:
        data = load_json(path)
    except Exception:
        return issues
    
    def check_value(obj, path_prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                check_value(v, f"{path_prefix}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_value(item, f"{path_prefix}[{i}]")
        elif isinstance(obj, str):
            for eid in expansion_ids:
                if eid in obj:
                    issues.append({
                        "file": str(path.relative_to(ROOT)),
                        "expansion_tool": eid,
                        "json_path": path_prefix,
                        "severity": "HIGH",
                    })
    
    check_value(data)
    return issues


def check_sitemap(path: Path, expansion_ids: Set[str]) -> List[dict]:
    """Check sitemap.xml for expansion-only tool URLs."""
    issues = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return issues
    
    for eid in expansion_ids:
        if f"/tools/{eid}" in content:
            issues.append({
                "file": str(path.relative_to(ROOT)),
                "expansion_tool": eid,
                "severity": "HIGH",
            })
    
    return issues


def check_tools_html_directory(expansion_ids: Set[str]) -> List[dict]:
    """Check if expansion-only tools have HTML files in tools/ directory."""
    issues = []
    if not TOOLS_HTML_DIR.is_dir():
        return issues
    
    for eid in expansion_ids:
        html_path = TOOLS_HTML_DIR / f"{eid}.html"
        if html_path.exists():
            issues.append({
                "file": str(html_path.relative_to(ROOT)),
                "expansion_tool": eid,
                "issue": "expansion-only tool has HTML file in tools/ directory",
                "severity": "HIGH",
            })
    
    return issues


def validate_production_scope() -> dict:
    """Run all production scope validation checks.
    
    Returns:
        Report dict with validation results
    """
    production_ids = get_production_tool_ids()
    expansion_ids = get_expansion_only_ids()
    
    all_issues = []
    checks = {}
    
    # Check 1: tools/ HTML directory
    issues = check_tools_html_directory(expansion_ids)
    checks["tools_html_directory"] = {
        "passed": len(issues) == 0,
        "issues": len(issues),
    }
    all_issues.extend(issues)
    
    # Check 2: Decision engine bundle
    if DECISION_BUNDLE_PATH.is_file():
        issues = check_json_data(DECISION_BUNDLE_PATH, expansion_ids)
        checks["decision_engine_bundle"] = {
            "passed": len(issues) == 0,
            "issues": len(issues),
        }
        all_issues.extend(issues)
    
    # Check 3: Sitemap
    if SITEMAP_PATH.is_file():
        issues = check_sitemap(SITEMAP_PATH, expansion_ids)
        checks["sitemap"] = {
            "passed": len(issues) == 0,
            "issues": len(issues),
        }
        all_issues.extend(issues)
    
    # Check 4: Homepage
    if INDEX_PATH.is_file():
        issues = check_html_file(INDEX_PATH, expansion_ids)
        checks["homepage"] = {
            "passed": len(issues) == 0,
            "issues": len(issues),
        }
        all_issues.extend(issues)
    
    # Check 5: Category pages
    category_issues = []
    if CATEGORY_HTML_DIR.is_dir():
        for html_file in CATEGORY_HTML_DIR.glob("*.html"):
            issues = check_html_file(html_file, expansion_ids)
            category_issues.extend(issues)
    checks["category_pages"] = {
        "passed": len(category_issues) == 0,
        "issues": len(category_issues),
    }
    all_issues.extend(category_issues)
    
    # Check 6: Comparison pages
    compare_issues = []
    if COMPARE_HTML_DIR.is_dir():
        for html_file in COMPARE_HTML_DIR.glob("*.html"):
            issues = check_html_file(html_file, expansion_ids)
            compare_issues.extend(issues)
    checks["compare_pages"] = {
        "passed": len(compare_issues) == 0,
        "issues": len(compare_issues),
    }
    all_issues.extend(compare_issues)
    
    # Check 7: Best pages
    best_issues = []
    if BEST_HTML_DIR.is_dir():
        for html_file in BEST_HTML_DIR.glob("*.html"):
            issues = check_html_file(html_file, expansion_ids)
            best_issues.extend(issues)
    checks["best_pages"] = {
        "passed": len(best_issues) == 0,
        "issues": len(best_issues),
    }
    all_issues.extend(best_issues)
    
    # Check 8: Goals pages
    goals_issues = []
    if GOALS_HTML_DIR.is_dir():
        for html_file in GOALS_HTML_DIR.glob("*.html"):
            issues = check_html_file(html_file, expansion_ids)
            goals_issues.extend(issues)
    checks["goals_pages"] = {
        "passed": len(goals_issues) == 0,
        "issues": len(goals_issues),
    }
    all_issues.extend(goals_issues)
    
    # Check 9: V1 count verification
    v1_count = len(production_ids)
    v1_check = {
        "passed": v1_count == 153,
        "expected": 153,
        "actual": v1_count,
    }
    checks["v1_count"] = v1_check
    if v1_count != 153:
        all_issues.append({
            "file": str(TOOLS_V1_PATH.relative_to(ROOT)),
            "issue": f"V1 count mismatch: expected 153, got {v1_count}",
            "severity": "HIGH",
        })
    
    # Overall pass/fail
    all_passed = all(c.get("passed", False) for c in checks.values())
    
    report = {
        "pipeline": "validate_production_scope",
        "summary": {
            "production_tools": len(production_ids),
            "expansion_only_tools": len(expansion_ids),
            "total_issues": len(all_issues),
            "all_checks_passed": all_passed,
        },
        "checks": checks,
        "issues": all_issues,
        "expansion_only_tool_ids": sorted(expansion_ids),
    }
    
    return report


def main():
    report = validate_production_scope()
    
    summary = report["summary"]
    print(f"\n{'='*60}")
    print(f"Production Scope Validation")
    print(f"{'='*60}")
    print(f"  Production tools: {summary['production_tools']}")
    print(f"  Expansion-only tools: {summary['expansion_only_tools']}")
    print(f"  Total issues: {summary['total_issues']}")
    print(f"  All checks passed: {summary['all_checks_passed']}")
    
    print(f"\n  Check results:")
    for check_name, result in report["checks"].items():
        status = "PASS" if result.get("passed") else "FAIL"
        issues = result.get("issues", 0)
        print(f"    [{status}] {check_name} ({issues} issues)")
    
    if report["issues"]:
        print(f"\n  Issues found:")
        for issue in report["issues"][:20]:  # Show first 20
            severity = issue.get("severity", "UNKNOWN")
            file_path = issue.get("file", "unknown")
            tool = issue.get("expansion_tool", issue.get("issue", ""))
            print(f"    [{severity}] {file_path}: {tool}")
        if len(report["issues"]) > 20:
            print(f"    ... and {len(report['issues']) - 20} more")
    
    return 0 if summary["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
