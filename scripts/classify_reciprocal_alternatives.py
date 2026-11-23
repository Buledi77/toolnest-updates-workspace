"""Classify all reciprocal alternative pairs.

A ↔ B is NOT automatically an error. This script classifies each reciprocal pair as:
- VALID_RECIPROCAL: both directions have different when_preferable conditions
- WEAK_RELATIONSHIP: reciprocal but with little meaningful differentiation
- REMOVE: should not be reciprocal (one direction is invalid)
- RESEARCH_REQUIRED: insufficient data to classify

Outputs:
- reports/phase3/reciprocal-classification.json
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
REPORTS_DIR = ROOT / "reports" / "phase3"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_alternative_map(tools):
    """Build a map of tool_id -> list of structured alternatives."""
    alt_map = {}
    for tool in tools:
        tool_id = tool["id"]
        alts = tool.get("alternatives", [])
        if alts:
            alt_map[tool_id] = alts
    return alt_map


def find_reciprocal_pairs(alt_map):
    """Find all reciprocal pairs in the alternative map."""
    reciprocal = set()
    for tool_id, alts in alt_map.items():
        for alt in alts:
            alt_id = alt.get("tool_id", "") if isinstance(alt, dict) else alt
            if alt_id in alt_map:
                for other_alt in alt_map[alt_id]:
                    other_id = other_alt.get("tool_id", "") if isinstance(other_alt, dict) else other_alt
                    if other_id == tool_id:
                        pair = tuple(sorted([tool_id, alt_id]))
                        reciprocal.add(pair)
    return reciprocal


def get_alt_detail(alt_map, tool_id, target_id):
    """Get the structured alternative detail for tool_id -> target_id."""
    for alt in alt_map.get(tool_id, []):
        if isinstance(alt, dict) and alt.get("tool_id") == target_id:
            return alt
    return None


def classify_pair(tool_a, tool_b, alt_map):
    """Classify a reciprocal pair."""
    alt_a_to_b = get_alt_detail(alt_map, tool_a, tool_b)
    alt_b_to_a = get_alt_detail(alt_map, tool_b, tool_a)
    
    # Get when_preferable for both directions
    when_a_prefers_b = alt_a_to_b.get("when_preferable", "") if alt_a_to_b else ""
    when_b_prefers_a = alt_b_to_a.get("when_preferable", "") if alt_b_to_a else ""
    
    # Get verification status
    status_a = alt_a_to_b.get("verification_status", "RESEARCH_REQUIRED") if alt_a_to_b else "RESEARCH_REQUIRED"
    status_b = alt_b_to_a.get("verification_status", "RESEARCH_REQUIRED") if alt_b_to_a else "RESEARCH_REQUIRED"
    
    # Get evidence basis
    evidence_a = alt_a_to_b.get("evidence_basis", "") if alt_a_to_b else ""
    evidence_b = alt_b_to_a.get("evidence_basis", "") if alt_b_to_a else ""
    
    # Classification logic
    classification = "RESEARCH_REQUIRED"
    reasoning = []
    
    # Check if both have meaningful when_preferable
    if when_a_prefers_b and when_b_prefers_a:
        if when_a_prefers_b != when_b_prefers_a:
            classification = "VALID_RECIPROCAL"
            reasoning.append("Both directions have different when_preferable conditions")
        else:
            classification = "WEAK_RELATIONSHIP"
            reasoning.append("Both directions have identical when_preferable conditions")
    elif not when_a_prefers_b and not when_b_prefers_a:
        # Check evidence
        if status_a in ("VERIFIED", "PARTIALLY_VERIFIED") and status_b in ("VERIFIED", "PARTIALLY_VERIFIED"):
            classification = "VALID_RECIPROCAL"
            reasoning.append("Both directions have verified evidence despite missing when_preferable")
        else:
            classification = "RESEARCH_REQUIRED"
            reasoning.append("No when_preferable and insufficient evidence")
    else:
        # One has when_preferable, the other doesn't
        if status_a in ("VERIFIED", "PARTIALLY_VERIFIED") or status_b in ("VERIFIED", "PARTIALLY_VERIFIED"):
            classification = "WEAK_RELATIONSHIP"
            reasoning.append("Asymmetric when_preferable with some evidence")
        else:
            classification = "RESEARCH_REQUIRED"
            reasoning.append("Asymmetric when_preferable with insufficient evidence")
    
    return {
        "tool_a": tool_a,
        "tool_b": tool_b,
        "classification": classification,
        "reasoning": "; ".join(reasoning),
        "when_a_prefers_b": when_a_prefers_b,
        "when_b_prefers_a": when_b_prefers_a,
        "verification_status_a": status_a,
        "verification_status_b": status_b,
        "evidence_basis_a": evidence_a,
        "evidence_basis_b": evidence_b
    }


def classify_reciprocal_alternatives():
    """Main classification function."""
    tools_data = load_json(TOOLS_V1_PATH)
    tools = tools_data["tools"]
    alt_map = build_alternative_map(tools)
    
    # Find reciprocal pairs
    reciprocal_pairs = find_reciprocal_pairs(alt_map)
    
    # Classify each pair
    classifications = []
    valid_count = 0
    weak_count = 0
    remove_count = 0
    research_count = 0
    
    for pair in sorted(reciprocal_pairs):
        classification = classify_pair(pair[0], pair[1], alt_map)
        classifications.append(classification)
        
        if classification["classification"] == "VALID_RECIPROCAL":
            valid_count += 1
        elif classification["classification"] == "WEAK_RELATIONSHIP":
            weak_count += 1
        elif classification["classification"] == "REMOVE":
            remove_count += 1
        else:
            research_count += 1
    
    # Build report
    report = {
        "generated_at": date.today().isoformat(),
        "schema_version": "reciprocal-classification-v1",
        "summary": {
            "total_reciprocal_pairs": len(reciprocal_pairs),
            "valid_reciprocal": valid_count,
            "weak_relationship": weak_count,
            "remove": remove_count,
            "research_required": research_count
        },
        "classifications": classifications
    }
    
    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "reciprocal-classification.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"Reciprocal classification written to {output_path}")
    print(f"Total reciprocal pairs: {len(reciprocal_pairs)}")
    print(f"  Valid reciprocal: {valid_count}")
    print(f"  Weak relationship: {weak_count}")
    print(f"  Remove: {remove_count}")
    print(f"  Research required: {research_count}")
    print()
    print("Classifications:")
    for c in classifications:
        print(f"  {c['tool_a']} <-> {c['tool_b']}: {c['classification']}")
        print(f"    Reasoning: {c['reasoning']}")
    
    return report


if __name__ == "__main__":
    classify_reciprocal_alternatives()
