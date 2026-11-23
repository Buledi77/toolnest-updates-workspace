#!/usr/bin/env python3
"""Canonical facts identifier — finds duplicated commercial facts across the site.

Identifies all remaining duplicated commercial facts and reports surfaces with
independent stale copies.

Target architecture:
ONE ACCEPTED VERIFIED FACT
↓
Tool profile, Decision Engine, Stack Analyzer, Comparison, Category, Goals, badges,
commercial-fact timestamp

Classification types:
- CANONICALIZED: Fact is stored only in evidence ledger, derived at build time
- SAFE_DERIVED_COPY: Static copy that matches canonical and is regenerated on build
- EDITORIAL_COPY: Editorial text that references a fact but is not a data source
- REQUIRES_REFACTOR: Manual duplicate that needs to be derived from canonical
- RESEARCH_REQUIRED: Fact surface where evidence is missing or unclear

Usage:
    python3 scripts/canonical_facts.py          # Report duplicated facts
    python3 scripts/canonical_facts.py --fix    # Show what needs fixing
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Set, Optional

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
DECISION_BUNDLE_PATH = ROOT / "data" / "decision-engine-bundle.json"
DEPENDENCY_GRAPH_PATH = ROOT / "data" / "dependency-graph.json"
TOOLS_HTML_DIR = ROOT / "tools"
COMPARE_HTML_DIR = ROOT / "compare"
CATEGORY_HTML_DIR = ROOT / "category"
DATA_TOOLS_DIR = ROOT / "data" / "tools"


class FactClassification(str, Enum):
    """Classification for duplicated fact surfaces.
    
    New granular types replace the flat REQUIRES_REFACTOR:
    - MUTABLE_CANONICAL_FACT: A structured field holding a mutable commercial value
      that MUST derive from the canonical source (evidence ledger).
    - ACTUAL_DUPLICATE: A manual copy of a mutable fact that should be derived.
    - DERIVED_PRESENTATION: Already derived at build time from canonical data.
    - EDITORIAL_REFERENCE: Editorial prose that mentions a fact but is not a data source.
    - SAFE_STATIC_COPY: Static copy with no stale risk (e.g. version labels, names).
    - GENERATOR_OUTPUT: Produced by a build script from canonical data.
    - RESEARCH_REQUIRED: Surface where evidence is missing or unclear.
    
    Legacy types kept for backward compatibility:
    - CANONICALIZED: Fact stored only in evidence ledger.
    - SAFE_DERIVED_COPY: Alias for DERIVED_PRESENTATION.
    - EDITORIAL_COPY: Alias for EDITORIAL_REFERENCE.
    - REQUIRES_REFACTOR: Alias for ACTUAL_DUPLICATE / MUTABLE_CANONICAL_FACT.
    """
    # New granular types
    MUTABLE_CANONICAL_FACT = "MUTABLE_CANONICAL_FACT"
    ACTUAL_DUPLICATE = "ACTUAL_DUPLICATE"
    DERIVED_PRESENTATION = "DERIVED_PRESENTATION"
    EDITORIAL_REFERENCE = "EDITORIAL_REFERENCE"
    SAFE_STATIC_COPY = "SAFE_STATIC_COPY"
    GENERATOR_OUTPUT = "GENERATOR_OUTPUT"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"
    # Legacy types (backward compat)
    CANONICALIZED = "CANONICALIZED"
    SAFE_DERIVED_COPY = "SAFE_DERIVED_COPY"
    EDITORIAL_COPY = "EDITORIAL_COPY"
    REQUIRES_REFACTOR = "REQUIRES_REFACTOR"


# Mutable commercial field paths that indicate a surface carries a mutable fact
MUTABLE_COMMERCIAL_FIELDS = {
    "pricing", "priceFrom", "price_from", "pricingNotes", "pricing_notes",
    "freePlan", "free_plan", "freeLimits", "free_limits",
    "trial", "billingBasis", "billing_basis", "currency",
    "checkedOn", "checked_on", "plans", "priceMonthly", "price_monthly",
    "priceAnnual", "price_annual", "annualDiscount", "annual_discount",
    "priceAnnualMonthlyEquivalent",
}

# Mutable fact types from evidence ledger
MUTABLE_CLAIM_TYPES = {"pricing", "free_plan", "trial", "billing", "plan_limit", "platform", "capability"}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _has_mutable_commercial_fields(tool_data: dict) -> List[str]:
    """Scan a tool JSON dict for mutable commercial fields.
    
    Returns list of field names that carry mutable commercial values.
    """
    found = []
    for key in MUTABLE_COMMERCIAL_FIELDS:
        if key in tool_data:
            found.append(key)
    # Check nested pricing section
    pricing = tool_data.get("pricing", {})
    if isinstance(pricing, dict):
        for key in MUTABLE_COMMERCIAL_FIELDS:
            if key in pricing:
                found.append("pricing." + key)
    return found


def classify_surface(surface: dict, claim: dict) -> FactClassification:
    """Classify a duplicated fact surface with granular classification.
    
    Determines whether a surface is:
    - MUTABLE_CANONICAL_FACT: Structured field holding mutable commercial value
    - ACTUAL_DUPLICATE: Manual copy that should derive from canonical
    - DERIVED_PRESENTATION: Already derived at build time
    - EDITORIAL_REFERENCE: Editorial prose mentioning a fact
    - SAFE_STATIC_COPY: Static copy with no stale risk
    - GENERATOR_OUTPUT: Produced by build script from canonical data
    - RESEARCH_REQUIRED: Evidence missing or unclear
    
    Args:
        surface: Surface dict with type and path
        claim: The canonical claim dict
    
    Returns:
        FactClassification enum value
    """
    surface_type = surface.get("type", "")
    surface_path = surface.get("path", "")
    claim_type = claim.get("claim_type", "")
    
    # Evidence ledger is always the canonical source
    if surface_path and "evidence-ledger" in surface_path:
        return FactClassification.CANONICALIZED
    
    # Tool JSON data files — check if they carry mutable commercial fields
    if surface_type == "tool_json":
        # If the claim is a mutable type, this is an actual duplicate
        if claim_type in MUTABLE_CLAIM_TYPES:
            return FactClassification.ACTUAL_DUPLICATE
        return FactClassification.SAFE_STATIC_COPY
    
    # HTML tool profiles — generated by regenerate_tool_profiles.py
    if surface_type == "tool_profile":
        # Profiles are generator output — they derive from tool JSON
        # The risk is whether tool JSON itself is canonical
        return FactClassification.GENERATOR_OUTPUT
    
    # Decision engine bundle — derived from tools-v1.json + evidence ledger
    if surface_type == "decision_engine":
        # Bundle already merges evidence ledger claims
        # But display fields may still come from tools-v1.json
        if claim_type in MUTABLE_CLAIM_TYPES:
            return FactClassification.DERIVED_PRESENTATION
        return FactClassification.GENERATOR_OUTPUT
    
    # Comparison pages — editorial references
    if surface_type == "comparison":
        return FactClassification.EDITORIAL_REFERENCE
    
    # Category pages — editorial references
    if surface_type == "category":
        return FactClassification.EDITORIAL_REFERENCE
    
    # Stack analyzer — derived from tools-v1.json
    if surface_type == "stack_analyzer":
        return FactClassification.DERIVED_PRESENTATION
    
    # Directory — derived from tools-v1.json
    if surface_type == "directory":
        return FactClassification.DERIVED_PRESENTATION
    
    # Homepage — derived from build_site.py
    if surface_type == "homepage":
        return FactClassification.GENERATOR_OUTPUT
    
    # Goals/Workflows — editorial references
    if surface_type == "goal" or surface_type == "workflow":
        return FactClassification.EDITORIAL_REFERENCE
    
    # Unknown surfaces need research
    return FactClassification.RESEARCH_REQUIRED


def find_canonical_facts() -> dict:
    """Find all commercial facts and their duplication across surfaces.
    
    Uses granular classification to distinguish mutable commercial facts
    from editorial references, safe static copies, and generator outputs.
    
    Returns:
        Report dict with canonical facts and their surfaces, including
        classification for each duplicated surface.
    """
    ledger = load_json(LEDGER_PATH) if LEDGER_PATH.is_file() else {"sources": [], "claims": []}
    v1 = load_json(TOOLS_V1_PATH) if TOOLS_V1_PATH.is_file() else {"tools": []}
    
    tools = v1.get("tools", [])
    tool_map = {t["id"]: t for t in tools}
    
    # Group claims by tool and type
    claims_by_tool = defaultdict(list)
    for claim in ledger.get("claims", []):
        tid = claim.get("tool_id", "")
        if tid:
            claims_by_tool[tid].append(claim)
    
    # All claim types that represent mutable facts
    mutable_types = {"pricing", "free_plan", "trial", "billing", "plan_limit", "platform", "capability"}
    
    canonical_facts = {}
    duplicated_surfaces = []
    classification_counts = {c.value: 0 for c in FactClassification}
    
    # Track field-level mutable facts per tool JSON
    tool_json_mutable_fields = {}
    
    for tool_id, claims in claims_by_tool.items():
        # Scan tool JSON for mutable commercial fields
        tool_json_path = DATA_TOOLS_DIR / f"{tool_id}.json"
        if tool_json_path.exists():
            try:
                tool_data = load_json(tool_json_path)
                mutable_fields = _has_mutable_commercial_fields(tool_data)
                if mutable_fields:
                    tool_json_mutable_fields[tool_id] = mutable_fields
            except Exception:
                pass
        
        # Process all claims (not just commercial types)
        for claim in claims:
            claim_id = claim.get("claim_id", "")
            claim_type = claim.get("claim_type", "")
            claim_status = claim.get("status", "")
            
            # Skip non-accepted claims for canonical fact tracking
            if claim_status not in ("verified", "verified_official", "verified_official_dynamic"):
                continue
            
            canonical_key = f"{tool_id}:{claim_type}"
            
            surfaces = []
            
            # Evidence ledger is the canonical source
            surfaces.append({
                "type": "evidence_ledger",
                "path": str(LEDGER_PATH.relative_to(ROOT)),
                "derived_from_canonical": True,
                "classification": FactClassification.CANONICALIZED.value,
            })
            
            # Check tool JSON data file — scan for mutable commercial fields
            if tool_json_path.exists():
                try:
                    tool_data = load_json(tool_json_path)
                    has_mutable = False
                    matched_fields = []
                    
                    if claim_type == "pricing":
                        has_mutable = bool(
                            tool_data.get("priceFrom") or tool_data.get("price_from")
                            or tool_data.get("pricingNotes") or tool_data.get("pricing")
                        )
                        if "pricing" in tool_data:
                            pricing_section = tool_data["pricing"]
                            if isinstance(pricing_section, dict):
                                for field in MUTABLE_COMMERCIAL_FIELDS:
                                    if field in pricing_section:
                                        matched_fields.append(f"pricing.{field}")
                        for field in MUTABLE_COMMERCIAL_FIELDS:
                            if field in tool_data:
                                matched_fields.append(field)
                    
                    elif claim_type == "free_plan":
                        has_mutable = "free_plan" in tool_data or "freePlan" in tool_data
                        if "free_plan" in tool_data:
                            matched_fields.append("free_plan")
                        if "freePlan" in tool_data:
                            matched_fields.append("freePlan")
                        if "pricing" in tool_data and isinstance(tool_data["pricing"], dict):
                            if "freePlan" in tool_data["pricing"] or "free_plan" in tool_data["pricing"]:
                                matched_fields.append("pricing.freePlan")
                    
                    elif claim_type == "trial":
                        has_mutable = "trial" in tool_data
                        if "trial" in tool_data:
                            matched_fields.append("trial")
                        if "pricing" in tool_data and isinstance(tool_data["pricing"], dict):
                            if "trial" in tool_data["pricing"]:
                                matched_fields.append("pricing.trial")
                    
                    elif claim_type == "platform":
                        has_mutable = False
                        discovery = tool_data.get("discovery", {})
                        if isinstance(discovery, dict) and "platforms" in discovery:
                            has_mutable = True
                            matched_fields.append("discovery.platforms")
                    
                    elif claim_type == "capability":
                        has_mutable = False
                        # Capabilities may be in various fields
                        for field in ["capabilities", "features", "capability"]:
                            if field in tool_data:
                                has_mutable = True
                                matched_fields.append(field)
                    
                    elif claim_type == "billing":
                        has_mutable = False
                        if "pricing" in tool_data and isinstance(tool_data["pricing"], dict):
                            pricing_section = tool_data["pricing"]
                            for field in ["billingBasis", "billing_basis", "currency", "billing_term"]:
                                if field in pricing_section:
                                    has_mutable = True
                                    matched_fields.append(f"pricing.{field}")
                    
                    if has_mutable:
                        surfaces.append({
                            "type": "tool_json",
                            "path": str(tool_json_path.relative_to(ROOT)),
                            "derived_from_canonical": False,
                            "matched_fields": matched_fields,
                            "claim_type": claim_type,
                        })
                except Exception:
                    pass
            
            # Check tool profile HTML (generator output)
            tool_profile = TOOLS_HTML_DIR / f"{tool_id}.html"
            if tool_profile.exists():
                surfaces.append({
                    "type": "tool_profile",
                    "path": str(tool_profile.relative_to(ROOT)),
                    "derived_from_canonical": False,
                    "claim_type": claim_type,
                })
            
            # Check decision engine bundle
            if DECISION_BUNDLE_PATH.is_file():
                try:
                    bundle = load_json(DECISION_BUNDLE_PATH)
                    bundle_tools = bundle.get("tools", {})
                    if tool_id in bundle_tools:
                        surfaces.append({
                            "type": "decision_engine",
                            "path": str(DECISION_BUNDLE_PATH.relative_to(ROOT)),
                            "derived_from_canonical": False,
                            "claim_type": claim_type,
                        })
                except Exception:
                    pass
            
            # Check comparison pages (editorial references)
            if COMPARE_HTML_DIR.is_dir():
                comp_count = 0
                for comp_file in COMPARE_HTML_DIR.glob("*.html"):
                    try:
                        content = comp_file.read_text(encoding="utf-8", errors="replace")
                        if tool_id in content:
                            comp_count += 1
                    except Exception:
                        pass
                if comp_count > 0:
                    surfaces.append({
                        "type": "comparison",
                        "path": "compare/*.html",
                        "derived_from_canonical": False,
                        "classification": FactClassification.EDITORIAL_REFERENCE.value,
                        "count": comp_count,
                        "claim_type": claim_type,
                    })
            
            # Classify all surfaces using granular classification
            classified_surfaces = []
            for surface in surfaces:
                if "classification" not in surface:
                    classification = classify_surface(surface, claim)
                    surface["classification"] = classification.value
                classification_counts[surface["classification"]] = (
                    classification_counts.get(surface["classification"], 0) + 1
                )
                classified_surfaces.append(surface)
            
            # Count non-canonical surfaces as duplicates
            non_canonical = [
                s for s in classified_surfaces
                if s.get("classification") != FactClassification.CANONICALIZED.value
            ]
            
            if len(non_canonical) > 0:
                # Determine stale risk based on new classification
                actual_duplicates = sum(
                    1 for s in non_canonical
                    if s.get("classification") in (
                        FactClassification.ACTUAL_DUPLICATE.value,
                        FactClassification.MUTABLE_CANONICAL_FACT.value,
                    )
                )
                stale_risk = "HIGH" if actual_duplicates > 0 else "LOW"
                
                duplicated_surfaces.append({
                    "canonical_key": canonical_key,
                    "claim_id": claim_id,
                    "tool_id": tool_id,
                    "claim_type": claim_type,
                    "canonical_source": "evidence-ledger.json",
                    "surfaces": classified_surfaces,
                    "non_canonical_surfaces": len(non_canonical),
                    "stale_risk": stale_risk,
                })
            
            canonical_facts[canonical_key] = {
                "claim_id": claim_id,
                "tool_id": tool_id,
                "claim_type": claim_type,
                "value": claim.get("value"),
                "status": claim.get("status"),
                "verified_at": claim.get("verified_at"),
                "surfaces": classified_surfaces,
            }
    
    # Build audit summary with new classification breakdown
    # Count surfaces that truly need refactoring (actual duplicates of mutable facts)
    actual_duplicate_count = sum(
        1 for d in duplicated_surfaces
        if any(
            s.get("classification") in (
                FactClassification.ACTUAL_DUPLICATE.value,
                FactClassification.MUTABLE_CANONICAL_FACT.value,
            )
            for s in d.get("surfaces", [])
        )
    )
    
    report = {
        "pipeline": "canonical_facts",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_canonical_facts": len(canonical_facts),
            "duplicated_surfaces": len(duplicated_surfaces),
            "high_stale_risk": sum(
                1 for d in duplicated_surfaces if d.get("stale_risk") == "HIGH"
            ),
            "medium_stale_risk": sum(
                1 for d in duplicated_surfaces if d.get("stale_risk") == "MEDIUM"
            ),
            "low_stale_risk": sum(
                1 for d in duplicated_surfaces if d.get("stale_risk") == "LOW"
            ),
            "classification_counts": classification_counts,
            "actual_duplicates_needing_refactor": actual_duplicate_count,
            "tool_json_mutable_field_count": len(tool_json_mutable_fields),
        },
        "canonical_facts": canonical_facts,
        "duplicated_surfaces": duplicated_surfaces,
        "tool_json_mutable_fields": tool_json_mutable_fields,
    }
    
    return report


def update_dependency_graph(report: dict) -> dict:
    """Update the dependency graph with canonical→derived relationships.
    
    Adds fact_sources entries to each tool's dependency graph entry
    to show which facts are canonical vs derived.
    
    Args:
        report: The canonical facts report from find_canonical_facts()
    
    Returns:
        Updated dependency graph dict
    """
    if not DEPENDENCY_GRAPH_PATH.is_file():
        return {}
    
    graph = load_json(DEPENDENCY_GRAPH_PATH)
    
    # Group canonical facts by tool
    facts_by_tool = defaultdict(list)
    for key, fact in report.get("canonical_facts", {}).items():
        tool_id = fact.get("tool_id", "")
        if tool_id:
            facts_by_tool[tool_id].append({
                "claim_id": fact.get("claim_id"),
                "claim_type": fact.get("claim_type"),
                "canonical_source": "data/evidence/evidence-ledger.json",
                "status": fact.get("status"),
                "verified_at": fact.get("verified_at"),
            })
    
    # Update each tool's fact_sources in the dependency graph
    for tool_id, facts in facts_by_tool.items():
        if tool_id in graph.get("tools", {}):
            graph["tools"][tool_id]["fact_sources"] = facts
    
    # Add metadata about canonical propagation
    graph["canonical_propagation"] = {
        "enabled": True,
        "canonical_source": "data/evidence/evidence-ledger.json",
        "derived_surfaces": [
            "data/tools/*.json",
            "tools/*.html",
            "data/decision-engine-bundle.json",
        ],
        "classification_types": [c.value for c in FactClassification],
        "summary": report.get("summary", {}),
    }
    
    return graph


def calculate_impacted_outputs(tool_id: str, fact_type: str) -> List[str]:
    """Calculate all outputs impacted by a fact change.
    
    Uses the dependency graph to trace impact.
    
    Args:
        tool_id: The tool with the changed fact
        fact_type: Type of fact (pricing, capability, etc.)
    
    Returns:
        List of impacted output paths
    """
    if not DEPENDENCY_GRAPH_PATH.is_file():
        return []
    
    graph = load_json(DEPENDENCY_GRAPH_PATH)
    tool_deps = graph.get("tools", {}).get(tool_id, {})
    
    impacted = []
    
    # Direct outputs
    if tool_deps.get("tool_profile"):
        impacted.append(tool_deps["tool_profile"])
    if tool_deps.get("decision_engine"):
        impacted.append(tool_deps["decision_engine"])
    if tool_deps.get("category"):
        impacted.append(tool_deps["category"])
    
    # Other outputs
    for other in tool_deps.get("other", []):
        impacted.append(other)
    
    # Comparisons
    for comp in tool_deps.get("comparisons", []):
        impacted.append(comp)
    
    return impacted


def generate_audit_report(report: dict) -> dict:
    """Generate the canonical audit report with detailed classification.
    
    Creates data/canonical-audit-report.json with per-surface classification,
    prioritized by commercial fact type.
    
    Args:
        report: The canonical facts report from find_canonical_facts()
    
    Returns:
        Audit report dict
    """
    summary = report["summary"]
    
    # Count by claim type
    claim_type_counts = defaultdict(int)
    for key, fact in report.get("canonical_facts", {}).items():
        claim_type_counts[fact.get("claim_type", "unknown")] += 1
    
    # Count by stale risk
    stale_risk_counts = defaultdict(int)
    for dup in report.get("duplicated_surfaces", []):
        stale_risk_counts[dup.get("stale_risk", "UNKNOWN")] += 1
    
    # Tools with mutable fields in tool JSON
    tools_with_mutable_fields = report.get("tool_json_mutable_fields", {})
    
    # Prioritized list of actual duplicates
    actual_duplicates = []
    for dup in report.get("duplicated_surfaces", []):
        for surface in dup.get("surfaces", []):
            if surface.get("classification") in (
                FactClassification.ACTUAL_DUPLICATE.value,
                FactClassification.MUTABLE_CANONICAL_FACT.value,
            ):
                actual_duplicates.append({
                    "tool_id": dup.get("tool_id"),
                    "claim_type": dup.get("claim_type"),
                    "claim_id": dup.get("claim_id"),
                    "surface_type": surface.get("type"),
                    "surface_path": surface.get("path"),
                    "matched_fields": surface.get("matched_fields", []),
                    "stale_risk": dup.get("stale_risk"),
                })
    
    audit_report = {
        "pipeline": "canonical_audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_canonical_facts": summary.get("total_canonical_facts", 0),
            "duplicated_surfaces": summary.get("duplicated_surfaces", 0),
            "actual_duplicates_needing_refactor": summary.get("actual_duplicates_needing_refactor", 0),
            "tool_json_mutable_field_count": summary.get("tool_json_mutable_field_count", 0),
            "classification_counts": summary.get("classification_counts", {}),
            "claim_type_counts": dict(claim_type_counts),
            "stale_risk_counts": dict(stale_risk_counts),
        },
        "actual_duplicates": actual_duplicates,
        "tools_with_mutable_fields": {
            tool_id: fields for tool_id, fields in tools_with_mutable_fields.items()
        },
    }
    
    return audit_report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Canonical facts analysis")
    parser.add_argument("--fix", action="store_true", help="Update dependency graph with canonical relationships")
    parser.add_argument("--audit", action="store_true", help="Generate canonical audit report")
    args = parser.parse_args()
    
    report = find_canonical_facts()
    
    summary = report["summary"]
    print(f"\n{'='*60}")
    print(f"Canonical Facts Analysis")
    print(f"{'='*60}")
    print(f"  Total canonical facts: {summary['total_canonical_facts']}")
    print(f"  Duplicated surfaces: {summary['duplicated_surfaces']}")
    print(f"  High stale risk: {summary['high_stale_risk']}")
    print(f"  Medium stale risk: {summary['medium_stale_risk']}")
    print(f"  Low stale risk: {summary.get('low_stale_risk', 0)}")
    print(f"  Actual duplicates needing refactor: {summary.get('actual_duplicates_needing_refactor', 0)}")
    print(f"  Tool JSONs with mutable fields: {summary.get('tool_json_mutable_field_count', 0)}")
    
    # Show classification breakdown
    if "classification_counts" in summary:
        print(f"\n  Classification breakdown:")
        for classification, count in summary["classification_counts"].items():
            if count > 0:
                print(f"    {classification}: {count}")
    
    if report["duplicated_surfaces"]:
        print(f"\n  Top duplicated facts (by stale risk):")
        # Sort by stale risk (HIGH first)
        sorted_dups = sorted(
            report["duplicated_surfaces"],
            key=lambda d: (0 if d.get("stale_risk") == "HIGH" else 1, -d.get("non_canonical_surfaces", 0))
        )
        for dup in sorted_dups[:10]:
            risk = dup.get("stale_risk", "UNKNOWN")
            n_surfaces = dup.get("non_canonical_surfaces", len(dup["surfaces"]))
            print(f"    [{risk}] {dup['canonical_key']}: {n_surfaces} non-canonical surfaces")
    
    # Generate audit report
    if args.audit:
        audit_report = generate_audit_report(report)
        audit_path = ROOT / "data" / "canonical-audit-report.json"
        save_json(audit_path, audit_report)
        print(f"\n  Audit report saved to {audit_path}")
    
    # Update dependency graph if requested
    if args.fix:
        updated_graph = update_dependency_graph(report)
        if updated_graph:
            save_json(DEPENDENCY_GRAPH_PATH, updated_graph)
            print(f"\n  Dependency graph updated with canonical→derived relationships")
    
    return 0


def save_json(path: Path, data: Any) -> None:
    """Save data as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    sys.exit(main())
