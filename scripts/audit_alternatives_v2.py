"""Audit all alternative relationships in tools-v1.json and convert bare strings to structured objects.

For every relationship, checks whether available evidence actually supports meaningful substitutability:
- Shared category
- Shared use case tags
- Existing comparison page
- Evidence ledger claims
- Overlap data relationships

Outputs:
- reports/phase3/alternatives-audit.json (full audit report)
- Updated data/tools-v1.json with structured alternatives
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
EVIDENCE_LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
OVERLAP_DATA_PATH = ROOT / "data" / "overlap-data.json"
REPORTS_DIR = ROOT / "reports" / "phase3"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_tool_map(tools):
    """Build a map of tool_id -> tool record."""
    return {tool["id"]: tool for tool in tools}


def build_overlap_lookup(overlap_data):
    """Build lookup structures from overlap data."""
    # Tool pairs with comparison evidence
    comparison_pairs = set()
    shared_job_pairs = set()
    category_pairs = {}
    
    for pair in overlap_data.get("overlap_pairs", []):
        a, b = pair["tool_a"], pair["tool_b"]
        pair_key = tuple(sorted([a, b]))
        if pair.get("has_comparison"):
            comparison_pairs.add(pair_key)
        if pair.get("shared_job"):
            shared_job_pairs.add(pair_key)
        cat = pair.get("shared_category")
        if cat:
            category_pairs[pair_key] = cat
    
    # Alternatives from overlap data
    overlap_alts = overlap_data.get("alternatives", {})
    
    return comparison_pairs, shared_job_pairs, category_pairs, overlap_alts


def build_evidence_lookup(ledger):
    """Build lookup from evidence ledger claims."""
    tool_claims = {}
    for claim in ledger.get("claims", []):
        tid = claim.get("tool_id")
        if tid:
            tool_claims.setdefault(tid, []).append(claim)
    return tool_claims


def find_evidence_for_pair(tool_a, tool_b, tool_map, comparison_pairs, shared_job_pairs, 
                           category_pairs, overlap_alts, evidence_claims):
    """Find all evidence supporting an alternative relationship between two tools."""
    evidence = []
    pair_key = tuple(sorted([tool_a, tool_b]))
    
    tool_a_data = tool_map.get(tool_a, {})
    tool_b_data = tool_map.get(tool_b, {})
    
    # 1. Check shared category
    cat_a = tool_a_data.get("cat", "")
    cat_b = tool_b_data.get("cat", "")
    if cat_a and cat_b and cat_a == cat_b:
        evidence.append({
            "type": "shared_category",
            "detail": f"Both in {cat_a}",
            "strength": "moderate"
        })
    
    # 2. Check overlap data comparison
    if pair_key in comparison_pairs:
        evidence.append({
            "type": "comparison_page",
            "detail": "Has dedicated comparison page",
            "strength": "strong"
        })
    
    # 3. Check shared job from overlap data
    if pair_key in shared_job_pairs:
        evidence.append({
            "type": "shared_job",
            "detail": "Overlap data confirms shared job-to-be-done",
            "strength": "strong"
        })
    
    # 4. Check overlap category
    if pair_key in category_pairs:
        evidence.append({
            "type": "overlap_category",
            "detail": f"Overlap data: {category_pairs[pair_key]}",
            "strength": "moderate"
        })
    
    # 5. Check if B is in A's overlap alternatives
    if tool_a in overlap_alts and tool_b in overlap_alts[tool_a]:
        evidence.append({
            "type": "overlap_alternative",
            "detail": "Listed in overlap data alternatives",
            "strength": "moderate"
        })
    
    # 6. Check shared use case tags
    tags_a = set(tool_a_data.get("useCaseTags", []))
    tags_b = set(tool_b_data.get("useCaseTags", []))
    shared_tags = tags_a & tags_b
    if shared_tags:
        evidence.append({
            "type": "shared_use_case_tags",
            "detail": f"Shared tags: {', '.join(sorted(shared_tags))}",
            "strength": "strong"
        })
    
    # 7. Check evidence ledger claims
    claims_a = evidence_claims.get(tool_a, [])
    claims_b = evidence_claims.get(tool_b, [])
    verified_a = [c for c in claims_a if c.get("status") in ("verified", "verified_official")]
    verified_b = [c for c in claims_b if c.get("status") in ("verified", "verified_official")]
    if verified_a and verified_b:
        evidence.append({
            "type": "both_verified",
            "detail": f"Tool A has {len(verified_a)} verified claims, Tool B has {len(verified_b)}",
            "strength": "moderate"
        })
    
    return evidence


def derive_shared_use_case(tool_a, tool_b, tool_map, evidence_list):
    """Derive the shared use case from available evidence."""
    tool_a_data = tool_map.get(tool_a, {})
    tool_b_data = tool_map.get(tool_b, {})
    
    # Check for shared category
    cat_a = tool_a_data.get("cat", "")
    cat_b = tool_b_data.get("cat", "")
    if cat_a and cat_b and cat_a == cat_b:
        return f"Both serve the {cat_a} use case"
    
    # Check for shared use case tags
    tags_a = set(tool_a_data.get("useCaseTags", []))
    tags_b = set(tool_b_data.get("useCaseTags", []))
    shared_tags = tags_a & tags_b
    if shared_tags:
        return f"Both address: {', '.join(sorted(shared_tags))}"
    
    # Check best_for fields
    best_a = tool_a_data.get("best", "")
    best_b = tool_b_data.get("best", "")
    if best_a and best_b:
        return f"Tool A: {best_a[:50]}... | Tool B: {best_b[:50]}..."
    
    return None


def derive_major_difference(tool_a, tool_b, tool_map):
    """Derive the major difference between two tools."""
    tool_a_data = tool_map.get(tool_a, {})
    tool_b_data = tool_map.get(tool_b, {})
    
    diffs = []
    
    # Check pricing differences
    pricing_a = tool_a_data.get("pricing", {})
    pricing_b = tool_b_data.get("pricing", {})
    free_a = pricing_a.get("freePlan", {}).get("available")
    free_b = pricing_b.get("freePlan", {}).get("available")
    if free_a is not None and free_b is not None and free_a != free_b:
        if free_a:
            diffs.append(f"{tool_a_data.get('name', tool_a)} offers a free plan")
        else:
            diffs.append(f"{tool_b_data.get('name', tool_b)} offers a free plan")
    
    # Check category differences
    cat_a = tool_a_data.get("cat", "")
    cat_b = tool_b_data.get("cat", "")
    if cat_a and cat_b and cat_a != cat_b:
        diffs.append(f"{tool_a_data.get('name', tool_a)} is {cat_a}, {tool_b_data.get('name', tool_b)} is {cat_b}")
    
    # Check best_for differences
    best_a = tool_a_data.get("best", "")
    best_b = tool_b_data.get("best", "")
    if best_a and best_b and best_a != best_b:
        diffs.append(f"Different strengths: {tool_a_data.get('name', tool_a)} excels at {best_a[:40]}, {tool_b_data.get('name', tool_b)} at {best_b[:40]}")
    
    if diffs:
        return "; ".join(diffs[:2])
    
    return None


def derive_when_preferable(tool_a, tool_b, tool_map, evidence_list):
    """Derive when tool_b is preferable over tool_a."""
    tool_a_data = tool_map.get(tool_a, {})
    tool_b_data = tool_map.get(tool_b, {})
    
    # Check if B has free plan and A doesn't
    pricing_a = tool_a_data.get("pricing", {})
    pricing_b = tool_b_data.get("pricing", {})
    free_a = pricing_a.get("freePlan", {}).get("available")
    free_b = pricing_b.get("freePlan", {}).get("available")
    if free_b is True and free_a is False:
        return f"When a free plan is required"
    
    # Check best_for
    best_b = tool_b_data.get("best", "")
    if best_b:
        return f"When {best_b.lower()[:60]} is the priority"
    
    return None


def determine_verification_status(evidence_list):
    """Determine verification status based on evidence strength."""
    if not evidence_list:
        return "RESEARCH_REQUIRED"
    
    strong_count = sum(1 for e in evidence_list if e.get("strength") == "strong")
    moderate_count = sum(1 for e in evidence_list if e.get("strength") == "moderate")
    
    if strong_count >= 2:
        return "VERIFIED"
    elif strong_count >= 1 or moderate_count >= 2:
        return "PARTIALLY_VERIFIED"
    else:
        return "RESEARCH_REQUIRED"


def audit_alternatives():
    """Main audit function."""
    # Load data
    tools_data = load_json(TOOLS_V1_PATH)
    tools = tools_data["tools"]
    tool_map = build_tool_map(tools)
    
    # Load evidence sources
    ledger = load_json(EVIDENCE_LEDGER_PATH) if EVIDENCE_LEDGER_PATH.exists() else {"claims": []}
    overlap = load_json(OVERLAP_DATA_PATH) if OVERLAP_DATA_PATH.exists() else {}
    
    comparison_pairs, shared_job_pairs, category_pairs, overlap_alts = build_overlap_lookup(overlap)
    evidence_claims = build_evidence_lookup(ledger)
    
    # Audit results
    audit_results = []
    structured_count = 0
    research_required_count = 0
    verified_count = 0
    partially_verified_count = 0
    reciprocal_pairs = set()
    
    # First pass: find reciprocal pairs
    for tool in tools:
        tool_id = tool["id"]
        for alt in tool.get("alternatives", []):
            alt_id = alt if isinstance(alt, str) else alt.get("tool_id", "")
            if alt_id in tool_map:
                other_alts = tool_map[alt_id].get("alternatives", [])
                for other_alt in other_alts:
                    other_alt_id = other_alt if isinstance(other_alt, str) else other_alt.get("tool_id", "")
                    if other_alt_id == tool_id:
                        pair = tuple(sorted([tool_id, alt_id]))
                        reciprocal_pairs.add(pair)
    
    # Second pass: convert and audit
    for tool in tools:
        tool_id = tool["id"]
        old_alts = tool.get("alternatives", [])
        new_alts = []
        
        for alt in old_alts:
            alt_id = alt if isinstance(alt, str) else alt.get("tool_id", "")
            
            # Find evidence
            evidence = find_evidence_for_pair(
                tool_id, alt_id, tool_map, comparison_pairs, shared_job_pairs,
                category_pairs, overlap_alts, evidence_claims
            )
            
            # Derive fields
            shared_use_case = derive_shared_use_case(tool_id, alt_id, tool_map, evidence)
            major_difference = derive_major_difference(tool_id, alt_id, tool_map)
            when_preferable = derive_when_preferable(tool_id, alt_id, tool_map, evidence)
            
            # Determine verification status
            verification_status = determine_verification_status(evidence)
            
            # Build evidence basis string
            evidence_types = [e["type"] for e in evidence]
            evidence_basis = "; ".join(evidence_types) if evidence_types else "no supporting evidence found"
            
            # Build structured alternative
            structured_alt = {
                "tool_id": alt_id,
                "shared_use_case": shared_use_case,
                "major_difference": major_difference,
                "when_preferable": when_preferable,
                "evidence_basis": evidence_basis,
                "verification_status": verification_status
            }
            new_alts.append(structured_alt)
            
            # Track stats
            if verification_status == "VERIFIED":
                verified_count += 1
            elif verification_status == "PARTIALLY_VERIFIED":
                partially_verified_count += 1
            else:
                research_required_count += 1
            
            # Record audit result
            audit_results.append({
                "tool_id": tool_id,
                "alt_id": alt_id,
                "verification_status": verification_status,
                "evidence_count": len(evidence),
                "evidence_types": evidence_types,
                "shared_use_case": shared_use_case,
                "major_difference": major_difference,
                "when_preferable": when_preferable,
                "is_reciprocal": tuple(sorted([tool_id, alt_id])) in reciprocal_pairs
            })
        
        # Update tool with structured alternatives
        tool["alternatives"] = new_alts
        structured_count += len(new_alts)
    
    # Save updated tools-v1.json
    with TOOLS_V1_PATH.open("w", encoding="utf-8") as f:
        json.dump(tools_data, f, indent=2, ensure_ascii=False)
    
    # Build report
    report = {
        "generated_at": date.today().isoformat(),
        "schema_version": "alternatives-audit-v2",
        "summary": {
            "total_alternatives": structured_count,
            "structured_alternatives": structured_count,
            "bare_string_alternatives": 0,
            "verified": verified_count,
            "partially_verified": partially_verified_count,
            "research_required": research_required_count,
            "reciprocal_pairs": len(reciprocal_pairs),
            "tools_with_alternatives": sum(1 for t in tools if t.get("alternatives")),
            "tools_without_alternatives": sum(1 for t in tools if not t.get("alternatives"))
        },
        "reciprocal_pairs": [list(p) for p in sorted(reciprocal_pairs)],
        "audit_results": audit_results
    }
    
    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "alternatives-audit.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"Alternatives audit written to {output_path}")
    print(f"Total alternatives: {structured_count}")
    print(f"  Verified: {verified_count}")
    print(f"  Partially verified: {partially_verified_count}")
    print(f"  Research required: {research_required_count}")
    print(f"  Reciprocal pairs: {len(reciprocal_pairs)}")
    print(f"Tools with alternatives: {report['summary']['tools_with_alternatives']}")
    print(f"Tools without alternatives: {report['summary']['tools_without_alternatives']}")
    print(f"\nUpdated {TOOLS_V1_PATH} with structured alternatives")
    
    return report


if __name__ == "__main__":
    audit_alternatives()
