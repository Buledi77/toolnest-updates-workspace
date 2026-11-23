"""Validate that alternative relationships have evidence basis.

Checks every tools-v2 record's alternatives for:
- Structured alternatives with shared_use_case and major_difference
- Circular references (A lists B, B lists A)
- Missing tool references
- Bare string IDs without evidence_basis

Output: reports/phase2/alternatives-audit.json
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from decision_graph_common import load_json, load_records, ROOT

REPORTS_DIR = ROOT / "reports" / "phase2"


def audit_alternatives():
    records = load_records()
    record_map = {r["identity"]["id"]: r for r in records}

    issues = []
    circular_pairs = set()
    structured_count = 0
    bare_count = 0
    missing_refs = 0

    for record in records:
        tool_id = record["identity"]["id"]
        alternatives = record.get("relationships", {}).get("alternatives", [])

        for alt in alternatives:
            if isinstance(alt, dict):
                structured_count += 1
                alt_id = alt.get("tool_id", "")
                if not alt.get("shared_use_case"):
                    issues.append({
                        "tool_id": tool_id,
                        "alt_id": alt_id,
                        "issue": "missing shared_use_case",
                        "severity": "warning",
                    })
                if not alt.get("major_difference"):
                    issues.append({
                        "tool_id": tool_id,
                        "alt_id": alt_id,
                        "issue": "missing major_difference",
                        "severity": "warning",
                    })
                if not alt.get("evidence_basis"):
                    issues.append({
                        "tool_id": tool_id,
                        "alt_id": alt_id,
                        "issue": "missing evidence_basis",
                        "severity": "info",
                    })
            else:
                bare_count += 1
                alt_id = alt
                issues.append({
                    "tool_id": tool_id,
                    "alt_id": alt_id,
                    "issue": "bare string ID without evidence basis",
                    "severity": "info",
                })

            # Check for missing references
            if alt_id and alt_id not in record_map:
                missing_refs += 1
                issues.append({
                    "tool_id": tool_id,
                    "alt_id": alt_id,
                    "issue": "references missing tool",
                    "severity": "error",
                })

            # Check for circular references
            if alt_id and alt_id in record_map:
                other_alts = record_map[alt_id].get("relationships", {}).get("alternatives", [])
                for other_alt in other_alts:
                    other_alt_id = other_alt.get("tool_id") if isinstance(other_alt, dict) else other_alt
                    if other_alt_id == tool_id:
                        pair = tuple(sorted([tool_id, alt_id]))
                        if pair not in circular_pairs:
                            circular_pairs.add(pair)
                            issues.append({
                                "tool_id": tool_id,
                                "alt_id": alt_id,
                                "issue": "circular alternative relationship",
                                "severity": "warning",
                            })

    report = {
        "generated_at": date.today().isoformat(),
        "schema_version": "alternatives-audit-v1",
        "summary": {
            "total_alternatives": structured_count + bare_count,
            "structured_alternatives": structured_count,
            "bare_string_alternatives": bare_count,
            "circular_pairs": len(circular_pairs),
            "missing_references": missing_refs,
            "total_issues": len(issues),
        },
        "issues": issues,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "alternatives-audit.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Alternatives audit written to {output_path}")
    print(f"Total alternatives: {report['summary']['total_alternatives']}")
    print(f"  Structured: {report['summary']['structured_alternatives']}")
    print(f"  Bare strings: {report['summary']['bare_string_alternatives']}")
    print(f"  Circular pairs: {report['summary']['circular_pairs']}")
    print(f"  Missing references: {report['summary']['missing_references']}")
    print(f"  Total issues: {report['summary']['total_issues']}")

    return report


if __name__ == "__main__":
    audit_alternatives()
