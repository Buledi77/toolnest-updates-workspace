#!/usr/bin/env python3
"""
Alternative Template Repetition Detector for ToolNest.

Scans verified alternative relationships for repeated phrasing in:
- shared_use_case
- major_difference
- when_preferable

Detects generic, template-like text that may have been copy-pasted
across unrelated products rather than being genuinely researched.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip, collapse whitespace."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    # Remove common punctuation for comparison
    text = re.sub(r'[.,;:]', '', text)
    return text


def similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings."""
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def collect_alternative_text() -> List[Dict[str, Any]]:
    """Collect all alternative relationship text from v1 catalog (dict-style alternatives)."""
    relationships: List[Dict[str, Any]] = []
    
    v1_data = load_json(TOOLS_V1_PATH)
    tools = v1_data.get("tools", [])
    
    for tool in tools:
        tool_id = tool.get("id", "")
        alts = tool.get("alternatives", [])
        
        for alt in alts:
            if isinstance(alt, dict):
                relationships.append({
                    "source_tool": tool_id,
                    "target_tool": alt.get("tool_id", ""),
                    "shared_use_case": alt.get("shared_use_case", ""),
                    "major_difference": alt.get("major_difference", ""),
                    "when_preferable": alt.get("when_preferable", ""),
                    "status": alt.get("verification_status", "RESEARCH_REQUIRED"),
                    "evidence_basis": alt.get("evidence_basis", "")
                })
    
    return relationships


def detect_template_repetition(
    relationships: List[Dict[str, Any]],
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Detect repeated phrasing across alternative relationships.
    
    Returns groups of similar text that may indicate template repetition.
    """
    # Group by field type
    field_groups: Dict[str, List[Tuple[str, str, str]]] = {
        "shared_use_case": [],
        "major_difference": [],
        "when_preferable": []
    }
    
    for rel in relationships:
        for field in ["shared_use_case", "major_difference", "when_preferable"]:
            text = rel.get(field, "")
            if text and len(text) > 20:  # Skip very short text
                field_groups[field].append((
                    rel["source_tool"],
                    rel["target_tool"],
                    text
                ))
    
    # Find similar pairs
    repetition_groups: Dict[str, List[List[Dict]]] = {
        "shared_use_case": [],
        "major_difference": [],
        "when_preferable": []
    }
    
    for field, entries in field_groups.items():
        seen_groups: List[List[Dict]] = []
        used_indices = set()
        
        for i in range(len(entries)):
            if i in used_indices:
                continue
            
            group = [{
                "source_tool": entries[i][0],
                "target_tool": entries[i][1],
                "text": entries[i][2]
            }]
            used_indices.add(i)
            
            for j in range(i + 1, len(entries)):
                if j in used_indices:
                    continue
                
                sim = similarity(entries[i][2], entries[j][2])
                if sim >= threshold:
                    group.append({
                        "source_tool": entries[j][0],
                        "target_tool": entries[j][1],
                        "text": entries[j][2],
                        "similarity": round(sim, 3)
                    })
                    used_indices.add(j)
            
            if len(group) > 1:
                repetition_groups[field].append(group)
    
    return repetition_groups


def detect_generic_phrases(
    relationships: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Detect generic, non-specific phrases that indicate template text.
    """
    generic_patterns = [
        r"both tools are used for",
        r"both platforms provide",
        r"both solutions offer",
        r"both tools help users",
        r"the main difference is",
        r"key difference between",
        r"choose .* if you need",
        r"consider .* when",
        r"better suited for",
        r"ideal for users who",
        r"provides a comprehensive",
        r"offers advanced",
        r"designed for",
        r"enables users to",
        r"allows teams to",
    ]
    
    generic_findings: List[Dict[str, Any]] = []
    
    for rel in relationships:
        for field in ["shared_use_case", "major_difference", "when_preferable"]:
            text = rel.get(field, "")
            if not text:
                continue
            
            for pattern in generic_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    generic_findings.append({
                        "source_tool": rel["source_tool"],
                        "target_tool": rel["target_tool"],
                        "field": field,
                        "text": text[:100],
                        "matched_pattern": pattern
                    })
                    break  # One match per field is enough
    
    return generic_findings


def main():
    print("=" * 60)
    print("Alternative Template Repetition Detector")
    print("=" * 60)
    
    # Collect all alternative text
    print("\nCollecting alternative relationships...")
    relationships = collect_alternative_text()
    
    verified = [r for r in relationships if r.get("status") in ("VERIFIED", "verified")]
    print(f"  Total relationships: {len(relationships)}")
    print(f"  Verified relationships: {len(verified)}")
    
    if not relationships:
        print("\n  No alternative relationships found.")
        return 0
    
    # Detect template repetition
    print("\nDetecting template repetition...")
    repetition_groups = detect_template_repetition(relationships, threshold=0.7)
    
    total_repetitions = 0
    for field, groups in repetition_groups.items():
        if groups:
            total_repetitions += len(groups)
            print(f"\n  {field}: {len(groups)} repetition groups")
            for i, group in enumerate(groups[:5]):  # Show first 5
                print(f"\n    Group {i+1}:")
                for entry in group:
                    sim = entry.get("similarity", "N/A")
                    print(f"      {entry['source_tool']} → {entry['target_tool']} (sim={sim})")
                    print(f"        \"{entry['text'][:80]}...\"")
                if len(groups) > 5:
                    print(f"    ... and {len(groups) - 5} more groups")
    
    # Detect generic phrases
    print("\nDetecting generic phrases...")
    generic_findings = detect_generic_phrases(relationships)
    print(f"  Generic phrase matches: {len(generic_findings)}")
    
    if generic_findings:
        for finding in generic_findings[:10]:
            print(f"    {finding['source_tool']} → {finding['target_tool']}")
            print(f"      Field: {finding['field']}")
            print(f"      Pattern: {finding['matched_pattern']}")
            print(f"      Text: \"{finding['text']}...\"")
        if len(generic_findings) > 10:
            print(f"    ... and {len(generic_findings) - 10} more")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total relationships analyzed: {len(relationships)}")
    print(f"  Verified relationships: {len(verified)}")
    print(f"  Repetition groups found: {total_repetitions}")
    print(f"  Generic phrase matches: {len(generic_findings)}")
    
    if total_repetitions > 0 or len(generic_findings) > 10:
        print("\n  WARNING: Template repetition detected.")
        print("  Review these relationships for genuine research vs. copy-paste.")
    else:
        print("\n  No significant template repetition detected.")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
