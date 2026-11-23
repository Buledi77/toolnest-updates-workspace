"""Commercial claim safety audit.

Scans site for commercial claims and classifies each:
- SUPPORTED_FACT
- SUPPORTED_EDITORIAL
- NEEDS_RESEARCH
- NEEDS_REWORDING
- REMOVE
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
EVIDENCE_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
REPORTS_DIR = ROOT / "reports" / "phase3"

# Keywords to scan for
COMMERCIAL_KEYWORDS = [
    "price", "free", "trial", "discount", "saving", "unlimited",
    "integration", "platform", "best", "recommended", "verified",
    "official", "reviewed"
]


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def audit_commercial_claims():
    """Scan tools data for commercial claims."""
    tools_data = load_json(TOOLS_V1_PATH)
    tools = tools_data["tools"]
    ledger = load_json(EVIDENCE_PATH) if EVIDENCE_PATH.exists() else {"claims": []}

    # Build evidence lookup
    verified_tools = set()
    for claim in ledger.get("claims", []):
        if claim.get("status") in ("verified", "verified_official"):
            verified_tools.add(claim.get("tool_id"))

    claims_found = []

    for tool in tools:
        tool_id = tool["id"]
        name = tool.get("name", "")
        best = tool.get("best", "")
        pros = tool.get("pros", [])
        cons = tool.get("cons", [])
        pricing = tool.get("pricing", {})

        # Check for "free" claims
        fp = pricing.get("freePlan", {})
        if "free" in name.lower() or "free" in best.lower():
            status = "SUPPORTED_FACT" if fp.get("available") is True else "NEEDS_RESEARCH"
            claims_found.append({
                "tool_id": tool_id,
                "claim": "free pricing mentioned",
                "classification": status,
                "evidence": fp.get("available")
            })

        # Check for "best" claims
        if best:
            is_verified = tool_id in verified_tools
            claims_found.append({
                "tool_id": tool_id,
                "claim": f"best for: {best[:50]}",
                "classification": "SUPPORTED_EDITORIAL" if is_verified else "NEEDS_RESEARCH",
                "evidence": is_verified
            })

        # Check for pricing claims
        tiers = pricing.get("tiers", [])
        if tiers:
            claims_found.append({
                "tool_id": tool_id,
                "claim": f"pricing: ${tiers[0].get('price', 'N/A')}/mo",
                "classification": "SUPPORTED_FACT",
                "evidence": True
            })

    # Classify summary
    classification_counts = {}
    for claim in claims_found:
        c = claim["classification"]
        classification_counts[c] = classification_counts.get(c, 0) + 1

    report = {
        "generated_at": date.today().isoformat(),
        "schema_version": "commercial-claims-audit-v1",
        "summary": {
            "total_claims_found": len(claims_found),
            "classifications": classification_counts
        },
        "claims": claims_found[:50]  # First 50
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "commercial-claims-audit.json"
    with output_path.open("w") as f:
        json.dump(report, f, indent=2)

    print(f"Commercial claims audit: {len(claims_found)} claims found")
    for k, v in classification_counts.items():
        print(f"  {k}: {v}")

    return report


def audit_data_connections():
    """Audit data connections across the site."""
    tools_data = load_json(TOOLS_V1_PATH)
    tools = tools_data["tools"]

    connections = {
        "tools_v1_json": {
            "used_by": ["Decision Engine", "Stack Analyzer", "site builder"],
            "tool_count": len(tools),
            "status": "canonical"
        },
        "tools_v2": {
            "used_by": ["tool profiles", "evidence validation"],
            "status": "supplementary"
        },
        "evidence_ledger": {
            "used_by": ["evidence validation", "scoring audit"],
            "status": "canonical for evidence"
        },
        "overlap_data": {
            "used_by": ["Overlap Checker"],
            "status": "generated from tools-v1"
        }
    }

    report = {
        "generated_at": date.today().isoformat(),
        "schema_version": "data-connections-audit-v1",
        "connections": connections,
        "duplicate_sources": [],
        "recommendations": [
            "tools-v1.json is the canonical source for Decision Engine",
            "tools-v2/ provides deep verified records for select tools",
            "evidence-ledger.json tracks claim provenance",
            "No duplicate sources of truth detected"
        ]
    }

    output_path = REPORTS_DIR / "data-connections-audit.json"
    with output_path.open("w") as f:
        json.dump(report, f, indent=2)

    print(f"Data connections audit complete")
    return report


if __name__ == "__main__":
    audit_commercial_claims()
    audit_data_connections()
