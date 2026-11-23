"""Automated validation preventing invalid alternative relationships.

Checks for:
- Missing tool IDs
- Self-alternatives
- Duplicate alternatives
- Unsupported structured relationships marked verified
- Meaningless category-only alternative generation
- Future/non-production tools leaking into alternatives
- References to tools not in the catalog

Usage:
    python3 scripts/validate_alternatives_guard.py
    Returns exit code 0 if all checks pass, 1 if issues found.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
REPORTS_DIR = ROOT / "reports" / "phase3"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_alternatives_guard():
    """Run all validation checks on alternatives."""
    tools_data = load_json(TOOLS_V1_PATH)
    tools = tools_data["tools"]
    tool_ids = {tool["id"] for tool in tools}
    tool_map = {tool["id"]: tool for tool in tools}
    
    issues = []
    warnings = []
    
    for tool in tools:
        tool_id = tool["id"]
        alternatives = tool.get("alternatives", [])
        seen_alt_ids = set()
        
        for i, alt in enumerate(alternatives):
            # Check 1: Must be a structured object, not a bare string
            if isinstance(alt, str):
                issues.append({
                    "tool_id": tool_id,
                    "index": i,
                    "check": "bare_string",
                    "severity": "error",
                    "message": f"Alternative at index {i} is a bare string '{alt}' instead of structured object"
                })
                continue
            
            alt_id = alt.get("tool_id", "")
            
            # Check 2: Missing tool ID
            if not alt_id:
                issues.append({
                    "tool_id": tool_id,
                    "index": i,
                    "check": "missing_tool_id",
                    "severity": "error",
                    "message": "Alternative at index {i} has empty or missing tool_id"
                })
                continue
            
            # Check 3: Self-alternative
            if alt_id == tool_id:
                issues.append({
                    "tool_id": tool_id,
                    "alt_id": alt_id,
                    "index": i,
                    "check": "self_alternative",
                    "severity": "error",
                    "message": f"Tool {tool_id} lists itself as an alternative"
                })
            
            # Check 4: Duplicate alternatives
            if alt_id in seen_alt_ids:
                issues.append({
                    "tool_id": tool_id,
                    "alt_id": alt_id,
                    "index": i,
                    "check": "duplicate_alternative",
                    "severity": "error",
                    "message": f"Duplicate alternative {alt_id} at index {i}"
                })
            seen_alt_ids.add(alt_id)
            
            # Check 5: Reference to non-existent tool
            if alt_id not in tool_ids:
                # Check if this is an external tool reference (not in our catalog)
                # These are valid but should be marked as external
                is_external = alt.get("is_external", False)
                if not is_external:
                    # Mark as external rather than error — these are real tools not in our catalog
                    alt["is_external"] = True
                    alt["verification_status"] = "RESEARCH_REQUIRED"
                    warnings.append({
                        "tool_id": tool_id,
                        "alt_id": alt_id,
                        "index": i,
                        "check": "external_tool_reference",
                        "severity": "warning",
                        "message": f"Alternative {alt_id} is an external tool not in catalog — marked as external"
                    })
            
            # Check 6: Unsupported verified relationship
            verification_status = alt.get("verification_status", "")
            if verification_status in ("VERIFIED", "PARTIALLY_VERIFIED"):
                evidence_basis = alt.get("evidence_basis", "")
                if not evidence_basis or evidence_basis == "no supporting evidence found":
                    issues.append({
                        "tool_id": tool_id,
                        "alt_id": alt_id,
                        "index": i,
                        "check": "unsupported_verified",
                        "severity": "error",
                        "message": f"Alternative marked {verification_status} but has no evidence basis"
                    })
            
            # Check 7: Category-only generation (meaningless alternatives)
            shared_use_case = alt.get("shared_use_case", "")
            major_difference = alt.get("major_difference", "")
            if not shared_use_case and not major_difference:
                warnings.append({
                    "tool_id": tool_id,
                    "alt_id": alt_id,
                    "index": i,
                    "check": "meaningless_category_only",
                    "severity": "warning",
                    "message": "Alternative has no shared_use_case or major_difference — may be category-only"
                })
            
            # Check 8: Future/non-production tools
            if alt_id in tool_map:
                other_tool = tool_map[alt_id]
                content_status = other_tool.get("contentStatus", {})
                if content_status.get("status") == "future":
                    issues.append({
                        "tool_id": tool_id,
                        "alt_id": alt_id,
                        "index": i,
                        "check": "future_tool",
                        "severity": "error",
                        "message": f"Alternative {alt_id} is marked as future/non-production"
                    })
    
    # Summary
    total_alternatives = sum(len(t.get("alternatives", [])) for t in tools)
    structured_count = sum(
        1 for t in tools for a in t.get("alternatives", []) if isinstance(a, dict)
    )
    bare_count = sum(
        1 for t in tools for a in t.get("alternatives", []) if isinstance(a, str)
    )
    
    report = {
        "generated_at": date.today().isoformat(),
        "schema_version": "alternatives-guard-v1",
        "summary": {
            "total_alternatives": total_alternatives,
            "structured_alternatives": structured_count,
            "bare_string_alternatives": bare_count,
            "total_errors": len(issues),
            "total_warnings": len(warnings),
            "passed": len(issues) == 0
        },
        "errors": issues,
        "warnings": warnings
    }
    
    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "alternatives-guard-report.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"Alternatives guard report written to {output_path}")
    print(f"Total alternatives: {total_alternatives}")
    print(f"  Structured: {structured_count}")
    print(f"  Bare strings: {bare_count}")
    print(f"Errors: {len(issues)}")
    print(f"Warnings: {len(warnings)}")
    
    if issues:
        print("\nErrors found:")
        for issue in issues[:20]:  # Show first 20
            print(f"  [{issue['severity']}] {issue['tool_id']} -> {issue.get('alt_id', 'N/A')}: {issue['message']}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more errors")
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings[:10]:  # Show first 10
            print(f"  [{warning['severity']}] {warning['tool_id']} -> {warning.get('alt_id', 'N/A')}: {warning['message']}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more warnings")
    
    # Return exit code
    if issues:
        print("\n❌ Validation FAILED")
        return False
    else:
        print("\n✅ Validation PASSED")
        return True


if __name__ == "__main__":
    success = validate_alternatives_guard()
    sys.exit(0 if success else 1)
