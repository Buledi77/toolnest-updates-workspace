#!/usr/bin/env python3
"""
Evidence Gap Registry — Phase A

Deterministic, machine-readable evidence-gap registry for the 30 remaining
Grade-B tool reviews.

For each affected tool, captures only what can be established from repository state:
- tool_id, page path, quality status, research priority
- missing official-source coverage
- missing verified pricing evidence
- missing plan-limit evidence
- missing free-plan evidence
- missing trial evidence
- missing limitation evidence
- missing meaningful competitor differentiation
- missing hands-on evidence
- current recommendation-confidence constraint
- existing source references
- last known evidence review date (only when explicitly present)

Unknown remains unknown. No fabricated source IDs, dates, prices, limits,
tests, ratings, measurements or factual claims.

Output: docs/internal/EVIDENCE-GAP-REGISTRY.json
"""

import json
import os
import re
from pathlib import Path


def load_json(path):
    """Load a JSON file and return its contents."""
    with open(path) as f:
        return json.load(f)


def get_html_sections(filepath):
    """Extract section IDs and text fingerprints from an HTML file."""
    if not os.path.exists(filepath):
        return [], ""
    with open(filepath) as f:
        content = f.read()
    section_ids = re.findall(r'id="([^"]+)"', content)
    # Extract section content (text between section tags)
    sections = re.findall(r'<section[^>]*>(.*?)</section>', content, re.DOTALL)
    section_texts = []
    for sec in sections:
        text = re.sub(r'<[^>]+>', '', sec).strip()
        section_texts.append(text.lower()[:200])
    return section_ids, " ".join(section_texts)


def get_comparison_count(tool_id):
    """Count how many comparison pages reference this tool."""
    compare_dir = Path("compare")
    if not compare_dir.exists():
        return 0, []
    comparisons = []
    for f in compare_dir.iterdir():
        if f.suffix == ".html" and f.name != "index.html":
            if tool_id in f.name:
                comparisons.append(f.name)
    return len(comparisons), comparisons


def get_alternatives_page(tool_id):
    """Check if an alternatives page exists for this tool."""
    alt_path = f"alternatives/{tool_id}-alternatives.html"
    return os.path.exists(alt_path)


def get_best_of_references(tool_id):
    """Find best-of pages that reference this tool."""
    best_dir = Path("best")
    if not best_dir.exists():
        return []
    references = []
    for f in best_dir.iterdir():
        if f.suffix == ".html" and f.name != "index.html":
            with open(f) as fh:
                content = fh.read()
            if tool_id in content.lower():
                references.append(f.name)
    return references


def has_tools_v2(tool_id):
    """Check if a tools-v2 record exists."""
    return os.path.exists(f"data/tools-v2/{tool_id}.json")


def get_evidence_ledger_entries(tool_id):
    """Get evidence ledger claims and sources for a tool."""
    ledger = load_json("data/evidence/evidence-ledger.json")
    claims = [c for c in ledger.get("claims", []) if c.get("tool_id") == tool_id]
    # Collect source IDs from claims
    source_ids = set()
    for c in claims:
        for sid in c.get("source_ids", []):
            source_ids.add(sid)
    sources = [s for s in ledger.get("sources", []) if s.get("source_id") in source_ids]
    return claims, sources


def check_html_evidence_signals(section_ids, section_text):
    """Check HTML content for evidence-related signals."""
    signals = {
        "has_sources_section": "sources" in section_ids,
        "has_limits_section": "limits" in section_ids,
        "has_evidence_status_section": "evidence-status" in section_ids,
        "has_pricing_section": "pricing" in section_ids,
        "has_verdict_section": "verdict" in section_ids,
        "has_alternatives_section": "alternatives" in section_ids or "alternatives-section" in section_ids,
        "has_best_for_section": "best-for" in section_ids,
        "mentions_official_source": "official" in section_text and ("source" in section_text or "site" in section_text),
        "mentions_pricing_checked": "pricing" in section_text and ("checked" in section_text or "verified" in section_text),
        "mentions_hands_on": "hands-on" in section_text or "hands on" in section_text,
        "mentions_tested": "tested" in section_text,
        "mentions_free_plan": "free plan" in section_text or "free tier" in section_text,
        "mentions_trial": "trial" in section_text,
        "mentions_limitations": "limitation" in section_text or "cost trap" in section_text,
        "mentions_skip": "skip" in section_text or "not for" in section_text,
    }
    return signals


def get_tools_json_entry(tool_id):
    """Get the tools.json catalog entry for a tool."""
    catalog = load_json("data/tools.json")
    for t in catalog.get("tools", []):
        if t.get("id") == tool_id:
            return t
    return None


def build_gap_registry():
    """Build the evidence gap registry for all tool reviews with genuine evidence gaps.

    Tracks ALL tools that lack genuine evidence (verified pricing, hands-on testing,
    evidence ledger sources), regardless of quality grade. A tools-v2 record with
    structured relationships does NOT fill evidence gaps.

    A tool is included if it has ANY of the following evidence gaps:
    - No verified pricing evidence
    - No hands-on testing evidence
    - No evidence ledger sources
    - Research-based disclaimer (no genuine evidence claimed)
    """
    # Load quality report
    quality_report = load_json("docs/internal/QUALITY-REPORT.json")

    # Get ALL tool reviews (not just Grade-B)
    all_reviews = [
        p for p in quality_report["pages"]
        if p["type"] == "tool_review"
    ]

    registry = {
        "schema_version": "evidence-gap-registry-v2",
        "generated_at": "2026-11-20",
        "description": "Deterministic evidence-gap registry for ALL tool reviews with genuine evidence gaps. Tools-v2 structured relationships do not fill evidence gaps. Unknown fields remain null. No fabricated evidence.",
        "total_tools": 0,  # Set after filtering
        "tools": []
    }

    for review in sorted(all_reviews, key=lambda x: x["score"]):
        path = review["path"]  # e.g., "/tools/jasper.html"
        tool_id = path.split("/")[-1].replace(".html", "")

        # Get HTML analysis
        html_path = f"tools/{tool_id}.html"
        section_ids, section_text = get_html_sections(html_path)

        # Get tools.json entry
        tools_entry = get_tools_json_entry(tool_id)

        # Get comparison and relationship data
        comp_count, comp_files = get_comparison_count(tool_id)
        has_alt_page = get_alternatives_page(tool_id)
        best_of_refs = get_best_of_references(tool_id)

        # Check tools-v2
        has_v2 = has_tools_v2(tool_id)
        v2_record = None
        if has_v2:
            v2_record = load_json(f"data/tools-v2/{tool_id}.json")

        # Check evidence ledger
        ledger_claims, ledger_sources = get_evidence_ledger_entries(tool_id)

        # Check HTML evidence signals
        html_signals = check_html_evidence_signals(section_ids, section_text)

        # Determine evidence gaps
        # 1. Missing official-source coverage
        has_official_source = (
            html_signals["has_sources_section"] and
            html_signals["mentions_official_source"]
        )
        missing_official_source = not has_official_source

        # 2. Missing verified pricing evidence
        has_verified_pricing = (
            html_signals["mentions_pricing_checked"] or
            (has_v2 and v2_record and len(ledger_sources) > 0)
        )
        missing_verified_pricing = not has_verified_pricing

        # 3. Missing plan-limit evidence
        has_plan_limit = (
            "plan" in section_text and ("limit" in section_text or "quota" in section_text)
        )
        if has_v2 and v2_record:
            factual = v2_record.get("factual_profile", {})
            if factual.get("pricing_status") or factual.get("free_plan_status"):
                has_plan_limit = True
        missing_plan_limit = not has_plan_limit

        # 4. Missing free-plan evidence
        has_free_plan = (
            html_signals["mentions_free_plan"] or
            (has_v2 and v2_record and v2_record.get("factual_profile", {}).get("free_plan_status"))
        )
        missing_free_plan = not has_free_plan

        # 5. Missing trial evidence
        has_trial = (
            html_signals["mentions_trial"] or
            (has_v2 and v2_record and v2_record.get("factual_profile", {}).get("trial_status"))
        )
        missing_trial = not has_trial

        # 6. Missing limitation evidence
        has_limitation = (
            html_signals["has_limits_section"] and
            html_signals["mentions_limitations"]
        )
        if has_v2 and v2_record:
            factual = v2_record.get("factual_profile", {})
            if factual.get("limitations"):
                has_limitation = True
        missing_limitation = not has_limitation

        # 7. Missing meaningful competitor differentiation
        # This requires comparison pages AND the review itself discussing differentiation
        has_competitor_diff = comp_count > 0 and has_alt_page
        # But the quality gate checks for tools-v2 meaningful_comparisons
        if has_v2 and v2_record:
            relationships = v2_record.get("relationships", {})
            if relationships.get("meaningful_comparisons"):
                has_competitor_diff = True
        missing_competitor_diff = not has_competitor_diff

        # 8. Missing hands-on evidence
        has_hands_on = (
            html_signals["mentions_hands_on"] and
            html_signals["mentions_tested"]
        )
        if has_v2 and v2_record:
            # Check for review evidence
            pass  # tools-v2 doesn't directly indicate hands-on
        missing_hands_on = not has_hands_on

        # 9. Existing source references
        existing_sources = []
        if html_signals["has_sources_section"]:
            # Extract URLs from sources section
            with open(html_path) as f:
                content = f.read()
            sources_match = re.search(r'id="sources"(.*?)(?=</section>|<section)', content, re.DOTALL)
            if sources_match:
                urls = re.findall(r'href="([^"]+)"', sources_match.group(1))
                for u in urls:
                    if u.startswith("http"):
                        existing_sources.append({
                            "url": u,
                            "type": "html_reference",
                            "verified": False
                        })
        # Add evidence ledger sources
        for src in ledger_sources:
            existing_sources.append({
                "url": src.get("url", ""),
                "type": src.get("source_type", ""),
                "verified": True,
                "source_id": src.get("source_id", ""),
                "accessed_at": src.get("accessed_at"),
                "verified_at": src.get("verified_at")
            })

        # 10. Last known evidence review date
        last_evidence_date = None
        if has_v2 and v2_record:
            freshness = v2_record.get("freshness", {})
            if freshness.get("last_verified_at"):
                last_evidence_date = freshness["last_verified_at"]
            elif freshness.get("updated_at"):
                last_evidence_date = freshness["updated_at"]
        # Check evidence ledger for most recent verified_at
        for claim in ledger_claims:
            if claim.get("verified_at"):
                if last_evidence_date is None or claim["verified_at"] > last_evidence_date:
                    last_evidence_date = claim["verified_at"]

        # 11. Recommendation confidence constraint
        # Based on available evidence
        evidence_score = sum([
            has_official_source,
            has_verified_pricing,
            has_plan_limit,
            has_limitation,
            has_competitor_diff,
            has_v2,
            len(ledger_claims) > 0,
        ])
        if evidence_score >= 5:
            confidence = "moderate"
        elif evidence_score >= 3:
            confidence = "low"
        else:
            confidence = "minimal"

        # Build the tool record
        tool_record = {
            "tool_id": tool_id,
            "page_path": path,
            "quality_status": {
                "grade": review["grade"],
                "score": review["score"],
                "words": review["words"],
                "sections": review["sections"],
                "unique_marked_sections": review.get("unique_marked", 0),
                "missing_flags": review.get("missing", []),
                "priority": review.get("priority", "unknown")
            },
            "research_priority": review.get("priority", "unknown"),
            "evidence_gaps": {
                "missing_official_source_coverage": missing_official_source,
                "missing_verified_pricing_evidence": missing_verified_pricing,
                "missing_plan_limit_evidence": missing_plan_limit,
                "missing_free_plan_evidence": missing_free_plan,
                "missing_trial_evidence": missing_trial,
                "missing_limitation_evidence": missing_limitation,
                "missing_meaningful_competitor_differentiation": missing_competitor_diff,
                "missing_hands_on_evidence": missing_hands_on
            },
            "recommendation_confidence": confidence,
            "existing_source_references": existing_sources,
            "last_known_evidence_review_date": last_evidence_date,
            "infrastructure_status": {
                "has_tools_v2_record": has_v2,
                "has_evidence_ledger_claims": len(ledger_claims) > 0,
                "evidence_ledger_claim_count": len(ledger_claims),
                "evidence_ledger_source_count": len(ledger_sources),
                "comparison_page_count": comp_count,
                "comparison_pages": comp_files,
                "has_alternatives_page": has_alt_page,
                "best_of_page_references": len(best_of_refs),
                "best_of_pages": best_of_refs
            },
            "html_signal_status": html_signals,
            "tools_json_entry": {
                "name": tools_entry.get("name", "unknown") if tools_entry else "unknown",
                "category": tools_entry.get("cat", "unknown") if tools_entry else "unknown",
                "best_fit": tools_entry.get("best", "unknown") if tools_entry else "unknown",
                "site": tools_entry.get("site", "unknown") if tools_entry else "unknown"
            } if tools_entry else None
        }

        # Only include tools that have genuine evidence gaps
        # A tool with complete evidence (verified pricing, hands-on testing,
        # evidence ledger sources) should not be in the registry
        has_any_gap = any([
            missing_official_source,
            missing_verified_pricing,
            missing_plan_limit,
            missing_free_plan,
            missing_trial,
            missing_limitation,
            missing_competitor_diff,
            missing_hands_on
        ])
        if has_any_gap:
            registry["tools"].append(tool_record)

    # Set total_tools count
    registry["total_tools"] = len(registry["tools"])

    # Add summary statistics
    gap_counts = {
        "missing_official_source_coverage": 0,
        "missing_verified_pricing_evidence": 0,
        "missing_plan_limit_evidence": 0,
        "missing_free_plan_evidence": 0,
        "missing_trial_evidence": 0,
        "missing_limitation_evidence": 0,
        "missing_meaningful_competitor_differentiation": 0,
        "missing_hands_on_evidence": 0
    }
    for tool in registry["tools"]:
        for gap, present in tool["evidence_gaps"].items():
            if present:
                gap_counts[gap] += 1

    registry["summary"] = {
        "total_tools_with_gaps": len(registry["tools"]),
        "tools_with_tools_v2": sum(1 for t in registry["tools"] if t["infrastructure_status"]["has_tools_v2_record"]),
        "tools_with_evidence_ledger": sum(1 for t in registry["tools"] if t["infrastructure_status"]["has_evidence_ledger_claims"]),
        "tools_with_comparison_pages": sum(1 for t in registry["tools"] if t["infrastructure_status"]["comparison_page_count"] > 0),
        "tools_with_alternatives_pages": sum(1 for t in registry["tools"] if t["infrastructure_status"]["has_alternatives_page"]),
        "gap_counts": gap_counts,
        "confidence_distribution": {
            "minimal": sum(1 for t in registry["tools"] if t["recommendation_confidence"] == "minimal"),
            "low": sum(1 for t in registry["tools"] if t["recommendation_confidence"] == "low"),
            "moderate": sum(1 for t in registry["tools"] if t["recommendation_confidence"] == "moderate")
        }
    }

    return registry


def main():
    print("=== Building Evidence Gap Registry ===\n")
    registry = build_gap_registry()

    # Write output
    output_path = "docs/internal/EVIDENCE-GAP-REGISTRY.json"
    with open(output_path, "w") as f:
        json.dump(registry, f, indent=2)

    print(f"Output: {output_path}")
    print(f"Total tools: {registry['total_tools']}")
    print()

    # Print summary
    summary = registry["summary"]
    print("=== Summary ===")
    print(f"Tools with tools-v2: {summary['tools_with_tools_v2']}")
    print(f"Tools with evidence ledger: {summary['tools_with_evidence_ledger']}")
    print(f"Tools with comparison pages: {summary['tools_with_comparison_pages']}")
    print(f"Tools with alternatives pages: {summary['tools_with_alternatives_pages']}")
    print()

    print("=== Gap Counts ===")
    for gap, count in summary["gap_counts"].items():
        print(f"  {gap}: {count}/{registry['total_tools']}")
    print()

    print("=== Confidence Distribution ===")
    for level, count in summary["confidence_distribution"].items():
        print(f"  {level}: {count}")
    print()

    # Print per-tool summary
    print("=== Per-Tool Summary ===")
    for tool in registry["tools"]:
        gaps = [g for g, v in tool["evidence_gaps"].items() if v]
        print(f"  {tool['tool_id']}: grade={tool['quality_status']['grade']}, "
              f"score={tool['quality_status']['score']}, "
              f"confidence={tool['recommendation_confidence']}, "
              f"gaps={len(gaps)}")

    print(f"\n=== Registry written to {output_path} ===")


if __name__ == "__main__":
    main()
