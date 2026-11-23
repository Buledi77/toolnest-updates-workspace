#!/usr/bin/env python3
"""Change detector — classifies changes between source fetches.

Differentiates between:
- NO_CHANGE — fingerprint identical
- COSMETIC_CHANGE — HTML diff < 5%, no field changes
- LAYOUT_CHANGE — structural HTML diff, no field changes
- PARSER-impacting change
- PRICE_CHANGE, PLAN_CHANGE, FREE_PLAN_CHANGE, TRIAL_CHANGE, BILLING_CHANGE
- FEATURE_CHANGE, LIMIT_CHANGE, PLATFORM_CHANGE, INTEGRATION_CHANGE
- PRODUCT_RENAME, SOURCE_REDIRECT, SOURCE_UNAVAILABLE
- CONFLICT, ANOMALY

Only material fact changes should enter the evidence-update pipeline.

Usage:
    python3 scripts/change_detector.py --tool semrush
    python3 scripts/change_detector.py --all
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY_PATH = ROOT / "data" / "sources" / "source-registry.json"
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"


class ChangeType(str, Enum):
    """Types of changes detected between source fetches."""
    NO_CHANGE = "no_change"
    COSMETIC_CHANGE = "cosmetic_change"
    LAYOUT_CHANGE = "layout_change"
    PARSER_CHANGE = "parser_change"
    PRICE_CHANGE = "price_change"
    PLAN_CHANGE = "plan_change"
    FREE_PLAN_CHANGE = "free_plan_change"
    TRIAL_CHANGE = "trial_change"
    BILLING_CHANGE = "billing_change"
    FEATURE_CHANGE = "feature_change"
    LIMIT_CHANGE = "limit_change"
    PLATFORM_CHANGE = "platform_change"
    INTEGRATION_CHANGE = "integration_change"
    PRODUCT_RENAME = "product_rename"
    SOURCE_REDIRECT = "source_redirect"
    SOURCE_UNAVAILABLE = "source_unavailable"
    CONFLICT = "conflict"
    ANOMALY = "anomaly"


# Material changes that should enter the evidence-update pipeline
MATERIAL_CHANGES = {
    ChangeType.PRICE_CHANGE,
    ChangeType.PLAN_CHANGE,
    ChangeType.FREE_PLAN_CHANGE,
    ChangeType.TRIAL_CHANGE,
    ChangeType.BILLING_CHANGE,
    ChangeType.FEATURE_CHANGE,
    ChangeType.LIMIT_CHANGE,
    ChangeType.PLATFORM_CHANGE,
    ChangeType.INTEGRATION_CHANGE,
    ChangeType.PRODUCT_RENAME,
    ChangeType.SOURCE_REDIRECT,
    ChangeType.SOURCE_UNAVAILABLE,
    ChangeType.CONFLICT,
    ChangeType.ANOMALY,
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def html_diff_ratio(old_text: str, new_text: str) -> float:
    """Calculate the ratio of differences between two HTML texts.
    
    Returns a value between 0 (identical) and 1 (completely different).
    """
    if not old_text and not new_text:
        return 0.0
    if not old_text or not new_text:
        return 1.0
    
    # Simple character-level diff ratio
    old_set = set(old_text[:10000])  # Sample for performance
    new_set = set(new_text[:10000])
    
    if not old_set and not new_set:
        return 0.0
    
    union = old_set | new_set
    intersection = old_set & new_set
    similarity = len(intersection) / len(union) if union else 1.0
    return 1.0 - similarity


def detect_price_changes(old_fields: dict, new_fields: dict) -> List[str]:
    """Detect pricing-related changes between old and new extracted fields."""
    changes = []
    
    # Check tier prices
    old_tiers = old_fields.get("pricing", {}).get("tiers", [])
    new_tiers = new_fields.get("pricing", {}).get("tiers", [])
    
    old_tier_map = {t.get("plan", ""): t for t in old_tiers}
    new_tier_map = {t.get("plan", ""): t for t in new_tiers}
    
    all_plans = set(old_tier_map.keys()) | set(new_tier_map.keys())
    
    for plan in all_plans:
        old_tier = old_tier_map.get(plan)
        new_tier = new_tier_map.get(plan)
        
        if old_tier and not new_tier:
            changes.append(f"plan_removed:{plan}")
        elif new_tier and not old_tier:
            changes.append(f"plan_added:{plan}")
        elif old_tier and new_tier:
            old_price = old_tier.get("price", old_tier.get("amount"))
            new_price = new_tier.get("price", new_tier.get("amount"))
            if old_price != new_price:
                changes.append(f"price_changed:{plan}:{old_price}->{new_price}")
            
            old_currency = old_tier.get("currency")
            new_currency = new_tier.get("currency")
            if old_currency and new_currency and old_currency != new_currency:
                changes.append(f"currency_changed:{plan}:{old_currency}->{new_currency}")
            
            old_interval = old_tier.get("billing_interval")
            new_interval = new_tier.get("billing_interval")
            if old_interval and new_interval and old_interval != new_interval:
                changes.append(f"billing_interval_changed:{plan}:{old_interval}->{new_interval}")
    
    # Check free plan
    old_free = old_fields.get("pricing", {}).get("free_plan", False)
    new_free = new_fields.get("pricing", {}).get("free_plan", False)
    if old_free != new_free:
        changes.append(f"free_plan_changed:{old_free}->{new_free}")
    
    # Check trial
    old_trial = old_fields.get("trial", {})
    new_trial = new_fields.get("trial", {})
    if old_trial != new_trial:
        changes.append(f"trial_changed")
    
    return changes


def detect_feature_changes(old_fields: dict, new_fields: dict) -> List[str]:
    """Detect feature/capability changes."""
    changes = []
    
    old_caps = set(old_fields.get("capabilities", []))
    new_caps = set(new_fields.get("capabilities", []))
    
    added = new_caps - old_caps
    removed = old_caps - new_caps
    
    if added:
        changes.append(f"features_added:{','.join(sorted(added))}")
    if removed:
        changes.append(f"features_removed:{','.join(sorted(removed))}")
    
    return changes


def detect_platform_changes(old_fields: dict, new_fields: dict) -> List[str]:
    """Detect platform changes."""
    changes = []
    
    old_platforms = set(old_fields.get("platforms", []))
    new_platforms = set(new_fields.get("platforms", []))
    
    if old_platforms != new_platforms:
        added = new_platforms - old_platforms
        removed = old_platforms - new_platforms
        if added:
            changes.append(f"platforms_added:{','.join(sorted(added))}")
        if removed:
            changes.append(f"platforms_removed:{','.join(sorted(removed))}")
    
    return changes


def detect_integration_changes(old_fields: dict, new_fields: dict) -> List[str]:
    """Detect integration changes."""
    changes = []
    
    old_integrations = set(old_fields.get("integrations", []))
    new_integrations = set(new_fields.get("integrations", []))
    
    if old_integrations != new_integrations:
        added = new_integrations - old_integrations
        removed = old_integrations - old_integrations
        if added:
            changes.append(f"integrations_added:{','.join(sorted(added))}")
        if removed:
            changes.append(f"integrations_removed:{','.join(sorted(removed))}")
    
    return changes


def classify_change(
    old_fingerprint: Optional[str],
    new_fingerprint: Optional[str],
    old_text: Optional[str] = None,
    new_text: Optional[str] = None,
    old_fields: Optional[dict] = None,
    new_fields: Optional[dict] = None,
    fetch_status: Optional[str] = None,
) -> Tuple[ChangeType, List[str]]:
    """Classify the type of change between two source states.
    
    Args:
        old_fingerprint: Previous content fingerprint
        new_fingerprint: Current content fingerprint
        old_text: Previous text content
        new_text: Current text content
        old_fields: Previously extracted fields
        new_fields: Newly extracted fields
        fetch_status: Status of the fetch operation
    
    Returns:
        Tuple of (ChangeType, list of specific change descriptions)
    """
    specific_changes = []
    
    # Handle fetch status
    if fetch_status == "unavailable":
        return ChangeType.SOURCE_UNAVAILABLE, ["source_unavailable"]
    if fetch_status == "redirect":
        return ChangeType.SOURCE_REDIRECT, ["source_redirect"]
    if fetch_status == "conflict":
        return ChangeType.CONFLICT, ["conflicting_sources"]
    
    # Fingerprint comparison
    if old_fingerprint and new_fingerprint:
        if old_fingerprint == new_fingerprint:
            return ChangeType.NO_CHANGE, []
    
    # HTML diff ratio for cosmetic vs layout changes
    if old_text and new_text:
        diff_ratio = html_diff_ratio(old_text, new_text)
        if diff_ratio < 0.05:
            # Very small change — likely cosmetic
            if old_fields and new_fields:
                # Check if any actual fields changed
                field_changes = detect_price_changes(old_fields, new_fields)
                feature_changes = detect_feature_changes(old_fields, new_fields)
                if field_changes or feature_changes:
                    specific_changes.extend(field_changes)
                    specific_changes.extend(feature_changes)
                    if specific_changes:
                        return ChangeType.PRICE_CHANGE if any("price" in c for c in specific_changes) else ChangeType.FEATURE_CHANGE, specific_changes
            return ChangeType.COSMETIC_CHANGE, [f"html_diff_ratio:{diff_ratio:.2%}"]
        elif diff_ratio < 0.2:
            # Moderate change — possibly layout
            pass
        # Large change — continue to field-level analysis
    
    # Field-level change detection
    if old_fields and new_fields:
        price_changes = detect_price_changes(old_fields, new_fields)
        feature_changes = detect_feature_changes(old_fields, new_fields)
        platform_changes = detect_platform_changes(old_fields, new_fields)
        integration_changes = detect_integration_changes(old_fields, new_fields)
        
        specific_changes.extend(price_changes)
        specific_changes.extend(feature_changes)
        specific_changes.extend(platform_changes)
        specific_changes.extend(integration_changes)
        
        # Check for free plan changes
        for change in specific_changes:
            if "free_plan" in change:
                return ChangeType.FREE_PLAN_CHANGE, specific_changes
            if "trial" in change:
                return ChangeType.TRIAL_CHANGE, specific_changes
            if "price" in change or "currency" in change:
                return ChangeType.PRICE_CHANGE, specific_changes
            if "billing" in change:
                return ChangeType.BILLING_CHANGE, specific_changes
            if "plan_removed" in change or "plan_added" in change:
                return ChangeType.PLAN_CHANGE, specific_changes
            if "platform" in change:
                return ChangeType.PLATFORM_CHANGE, specific_changes
            if "integration" in change:
                return ChangeType.INTEGRATION_CHANGE, specific_changes
            if "feature" in change:
                return ChangeType.FEATURE_CHANGE, specific_changes
        
        if specific_changes:
            return ChangeType.FEATURE_CHANGE, specific_changes
    
    # No field-level changes detected but fingerprint changed
    if old_fingerprint and new_fingerprint and old_fingerprint != new_fingerprint:
        return ChangeType.LAYOUT_CHANGE, ["fingerprint_changed_no_field_changes"]
    
    return ChangeType.NO_CHANGE, []


def is_material_change(change_type: ChangeType) -> bool:
    """Check if a change type should enter the evidence-update pipeline."""
    return change_type in MATERIAL_CHANGES


def detect_changes_for_tool(
    tool_id: str,
    fetch_results: dict,
    old_fingerprints: Optional[dict] = None,
    old_fields: Optional[dict] = None,
) -> dict:
    """Detect changes for a specific tool based on fetch results.
    
    Args:
        tool_id: Tool identifier
        fetch_results: Results from source_fetcher.py
        old_fingerprints: Previous fingerprints by source_id
        old_fields: Previously extracted fields
    
    Returns:
        Dict with change detection results
    """
    old_fp = old_fingerprints or {}
    old_f = old_fields or {}
    
    changes = {}
    overall_change = ChangeType.NO_CHANGE
    all_specific = []
    
    for source_id, result in fetch_results.get("sources", {}).items():
        status = result.get("status")
        new_fp = result.get("fingerprint")
        new_text = result.get("text_content")
        
        # Extract fields from text content (simplified — real extraction in extractors/)
        new_f = {}
        if new_text:
            # Simple price extraction
            price_matches = re.findall(r'\$[\d,]+\.?\d*', new_text)
            if price_matches:
                new_f["detected_prices"] = price_matches[:10]
        
        old_fp_val = old_fp.get(source_id)
        
        change_type, specific = classify_change(
            old_fingerprint=old_fp_val,
            new_fingerprint=new_fp,
            old_text=None,  # Would need cached text
            new_text=new_text,
            old_fields=old_f,
            new_fields=new_f,
            fetch_status=status,
        )
        
        changes[source_id] = {
            "change_type": change_type.value,
            "specific_changes": specific,
            "material": is_material_change(change_type),
            "old_fingerprint": old_fp_val,
            "new_fingerprint": new_fp,
        }
        
        if change_type != ChangeType.NO_CHANGE:
            overall_change = change_type
            all_specific.extend(specific)
    
    return {
        "tool_id": tool_id,
        "overall_change": overall_change.value,
        "material_change": is_material_change(overall_change),
        "source_changes": changes,
        "all_specific_changes": all_specific,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Change detector")
    parser.add_argument("--tool", type=str, default=None, help="Check changes for a specific tool")
    parser.add_argument("--all", action="store_true", help="Check all tools")
    args = parser.parse_args()
    
    if not SOURCE_REGISTRY_PATH.is_file():
        print("No source registry found")
        return 1
    
    registry = load_json(SOURCE_REGISTRY_PATH)
    
    if args.tool:
        tool_id = args.tool
        tool_entry = registry.get(tool_id, {})
        sources = tool_entry.get("sources", [])
        
        print(f"\nChange detection for {tool_id}:")
        print(f"  Sources: {len(sources)}")
        
        # Simulate change detection (no actual fetch)
        for source in sources:
            sid = source.get("source_id", "")
            old_fp = source.get("content_fingerprint")
            print(f"  {sid}: fingerprint={'set' if old_fp else 'not set'}")
    
    elif args.all:
        print(f"\nChange detection for all tools:")
        print(f"  Tools in registry: {len(registry)}")
        for tool_id, entry in registry.items():
            sources = entry.get("sources", [])
            print(f"  {tool_id}: {len(sources)} sources")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
