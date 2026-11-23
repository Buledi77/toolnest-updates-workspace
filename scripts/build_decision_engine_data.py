#!/usr/bin/env python3
"""Build a decision-ready JSON bundle for the Decision Engine.

Merges tools-v1.json with evidence-ledger.json claims so that each tool
record carries its evidence claims with verification statuses.

The output is embedded directly into decision-engine.html as a <script>
block, avoiding client-side JSON fetching.

Evidence status mapping for scoring:
  verified_official  -> VERIFIED_MATCH (highest confidence)
  verified           -> VERIFIED_MATCH
  editorial_assessment -> EDITORIAL_ASSESSMENT (moderate confidence)
  research_required  -> UNKNOWN (lowers confidence, no disqualification)
  official_source_conflict -> CONFLICTING_SOURCES (lowers confidence significantly)
  official_source_unavailable -> UNKNOWN
  disputed           -> CONFLICTING_SOURCES
  needs_review       -> EDITORIAL_ASSESSMENT (treated as moderate until reviewed)
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "data" / "tools-v1.json"
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
OUTPUT_PATH = ROOT / "data" / "decision-engine-bundle.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_evidence_map(ledger):
    """Build a dict: tool_id -> list of claim summaries for scoring."""
    claims = ledger.get("claims", [])
    evidence_map = {}

    for claim in claims:
        tool_id = claim.get("tool_id")
        if not tool_id:
            continue

        status = claim.get("status", "needs_review")
        field_path = claim.get("field_path", "")
        claim_type = claim.get("claim_type", "")
        claim_id = claim.get("claim_id", "")
        source_ids = claim.get("source_ids", [])
        stale_after = claim.get("stale_after", "")

        # Map ledger status to scoring state
        if status in ("verified_official", "verified"):
            scoring_state = "VERIFIED_MATCH"
        elif status == "editorial_assessment":
            scoring_state = "EDITORIAL_ASSESSMENT"
        elif status in ("research_required", "official_source_unavailable"):
            scoring_state = "UNKNOWN"
        elif status in ("official_source_conflict", "disputed"):
            scoring_state = "CONFLICTING_SOURCES"
        elif status == "needs_review":
            scoring_state = "EDITORIAL_ASSESSMENT"
        else:
            scoring_state = "UNKNOWN"

        summary = {
            "claim_id": claim_id,
            "field_path": field_path,
            "claim_type": claim_type,
            "status": status,
            "scoring_state": scoring_state,
            "source_ids": source_ids,
            "stale_after": stale_after,
        }

        if tool_id not in evidence_map:
            evidence_map[tool_id] = []
        evidence_map[tool_id].append(summary)

    return evidence_map


def detect_conflicts(evidence_list):
    """Check if a tool has conflicting claims for the same field_path."""
    field_claims = {}
    for claim in evidence_list:
        fp = claim["field_path"]
        if fp not in field_claims:
            field_claims[fp] = []
        field_claims[fp].append(claim)

    has_conflict = False
    for fp, claims in field_claims.items():
        states = set(c["scoring_state"] for c in claims)
        if "CONFLICTING_SOURCES" in states:
            has_conflict = True
            break
        # Multiple different statuses for same field is also a conflict signal
        if len(claims) > 1:
            statuses = set(c["status"] for c in claims)
            if len(statuses) > 1 and "disputed" in statuses:
                has_conflict = True
                break

    return has_conflict


def compute_evidence_confidence(evidence_list):
    """Compute evidence confidence from actual claim verification status.

    Returns a dict with:
      - level: "strong", "moderate", or "limited"
      - verified_count: number of VERIFIED_MATCH claims
      - editorial_count: number of EDITORIAL_ASSESSMENT claims
      - unknown_count: number of UNKNOWN claims
      - conflict_count: number of CONFLICTING_SOURCES claims
      - has_conflict: boolean
    """
    if not evidence_list:
        return {
            "level": "limited",
            "verified_count": 0,
            "editorial_count": 0,
            "unknown_count": 0,
            "conflict_count": 0,
            "has_conflict": False,
        }

    verified = 0
    editorial = 0
    unknown = 0
    conflict = 0

    for claim in evidence_list:
        state = claim.get("scoring_state", "UNKNOWN")
        if state == "VERIFIED_MATCH":
            verified += 1
        elif state == "EDITORIAL_ASSESSMENT":
            editorial += 1
        elif state == "UNKNOWN":
            unknown += 1
        elif state == "CONFLICTING_SOURCES":
            conflict += 1

    has_conflict = detect_conflicts(evidence_list)

    # Confidence level based on verified claims
    # Strong: 3+ verified claims
    # Moderate: 1+ verified or 2+ editorial claims
    # Limited: everything else
    if verified >= 3:
        level = "strong"
    elif verified >= 1 or editorial >= 2:
        level = "moderate"
    else:
        level = "limited"

    # Conflicts downgrade confidence
    if has_conflict or conflict > 0:
        if level == "strong":
            level = "moderate"
        elif level == "moderate":
            level = "limited"

    return {
        "level": level,
        "verified_count": verified,
        "editorial_count": editorial,
        "unknown_count": unknown,
        "conflict_count": conflict,
        "has_conflict": has_conflict,
    }


def build_bundle():
    """Build the decision engine data bundle."""
    tools_data = load_json(TOOLS_PATH)
    ledger = load_json(LEDGER_PATH)

    tools = tools_data.get("tools", [])
    evidence_map = build_evidence_map(ledger)

    bundle_tools = []
    for tool in tools:
        tool_id = tool.get("id", "")
        evidence_list = evidence_map.get(tool_id, [])
        evidence_confidence = compute_evidence_confidence(evidence_list)

        # Create a merged tool record with evidence data
        merged = dict(tool)
        merged["evidence_claims"] = evidence_list
        merged["evidence_confidence"] = evidence_confidence

        bundle_tools.append(merged)

    bundle = {
        "schema_version": "decision-engine-bundle-v1",
        "tools": bundle_tools,
        "metadata": {
            "total_tools": len(bundle_tools),
            "tools_with_evidence": sum(
                1 for t in bundle_tools if t["evidence_claims"]
            ),
            "total_claims": sum(
                len(t["evidence_claims"]) for t in bundle_tools
            ),
            "ledger_sources": len(ledger.get("sources", [])),
            # Freshness hashes for validate_bundle_freshness.py
            "tools_v1_hash": sha256_file(TOOLS_PATH),
            "evidence_ledger_hash": sha256_file(LEDGER_PATH),
        },
    }

    return bundle


def main():
    bundle = build_bundle()

    # Write to JSON file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)

    meta = bundle["metadata"]
    print(f"Decision engine bundle built:")
    print(f"  Total tools: {meta['total_tools']}")
    print(f"  Tools with evidence: {meta['tools_with_evidence']}")
    print(f"  Total claims: {meta['total_claims']}")
    print(f"  Ledger sources: {meta['ledger_sources']}")
    print(f"  Output: {OUTPUT_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
