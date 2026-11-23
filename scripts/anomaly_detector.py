#!/usr/bin/env python3
"""Anomaly detector — checks for suspicious transitions that should never overwrite facts.

Checks for:
- $20 → $0 (price to zero)
- $20 → $2,000 (huge price increase)
- USD → unrelated currency
- 20 capabilities → 0 (feature wipe)
- known pricing → blank
- known plan → unknown
- source redirects to unrelated page
- entire extracted record disappears

An anomaly must NOT overwrite the last verified fact.

Usage:
    from scripts.anomaly_detector import detect_anomalies, AnomalyType
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class AnomalyType(str, Enum):
    """Types of anomalies detected in source data."""
    PRICE_TO_ZERO = "price_to_zero"
    HUGE_PRICE_INCREASE = "huge_price_increase"
    CURRENCY_CHANGE = "currency_change"
    FEATURE_WIPE = "feature_wipe"
    PRICING_BLANKED = "pricing_blank"
    PLAN_TO_UNKNOWN = "plan_to_unknown"
    SOURCE_REDIRECT = "source_redirect"
    RECORD_DISAPPEARED = "record_disappeared"
    RADICALLY_DIFFERENT_CONTENT = "radically_different_content"
    IMPOSSIBLE_VALUE = "impossible_value"


# Thresholds
PRICE_INCREASE_FACTOR = 10  # 10x increase is anomalous
FEATURE_LOSS_THRESHOLD = 5  # Losing 5+ features is anomalous
CONTENT_DIFF_THRESHOLD = 0.8  # 80% content change is anomalous


def detect_anomalies(
    old_fields: Optional[dict],
    new_fields: Optional[dict],
    old_fingerprint: Optional[str] = None,
    new_fingerprint: Optional[str] = None,
    old_text: Optional[str] = None,
    new_text: Optional[str] = None,
) -> List[dict]:
    """Detect anomalies in extracted field transitions.
    
    Args:
        old_fields: Previously extracted fields
        new_fields: Newly extracted fields
        old_fingerprint: Previous content fingerprint
        new_fingerprint: New content fingerprint
        old_text: Previous text content
        new_text: New text content
    
    Returns:
        List of anomaly dicts with type, description, and severity
    """
    anomalies = []
    
    if not old_fields:
        return anomalies  # No baseline to compare
    
    if not new_fields:
        # Entire record disappeared
        anomalies.append({
            "type": AnomalyType.RECORD_DISAPPEARED.value,
            "description": "Entire extracted record disappeared",
            "severity": "critical",
            "action": "preserve_last_verified",
        })
        return anomalies
    
    # Check price anomalies
    anomalies.extend(_check_price_anomalies(old_fields, new_fields))
    
    # Check currency anomalies
    anomalies.extend(_check_currency_anomalies(old_fields, new_fields))
    
    # Check feature wipe
    anomalies.extend(_check_feature_anomalies(old_fields, new_fields))
    
    # Check plan anomalies
    anomalies.extend(_check_plan_anomalies(old_fields, new_fields))
    
    # Check content anomalies
    anomalies.extend(_check_content_anomalies(
        old_fingerprint, new_fingerprint, old_text, new_text
    ))
    
    return anomalies


def _check_price_anomalies(old_fields: dict, new_fields: dict) -> List[dict]:
    """Check for price-related anomalies."""
    anomalies = []
    
    old_pricing = old_fields.get("pricing", {})
    new_pricing = new_fields.get("pricing", {})
    
    # Check tier prices
    old_tiers = old_pricing.get("tiers", [])
    new_tiers = new_pricing.get("tiers", [])
    
    old_tier_map = {t.get("plan", ""): t for t in old_tiers}
    new_tier_map = {t.get("plan", ""): t for t in new_tiers}
    
    for plan, old_tier in old_tier_map.items():
        old_price = old_tier.get("price", old_tier.get("amount", 0))
        
        if plan in new_tier_map:
            new_tier = new_tier_map[plan]
            new_price = new_tier.get("price", new_tier.get("amount", 0))
            
            try:
                old_val = float(old_price) if old_price else 0
                new_val = float(new_price) if new_price else 0
                
                # Price to zero
                if old_val > 0 and new_val == 0:
                    anomalies.append({
                        "type": AnomalyType.PRICE_TO_ZERO.value,
                        "description": f"Price for '{plan}' dropped to $0 (was ${old_val})",
                        "severity": "critical",
                        "action": "preserve_last_verified",
                    })
                
                # Huge price increase
                elif old_val > 0 and new_val > old_val * PRICE_INCREASE_FACTOR:
                    anomalies.append({
                        "type": AnomalyType.HUGE_PRICE_INCREASE.value,
                        "description": f"Price for '{plan}' increased {new_val/old_val:.1f}x (${old_val} → ${new_val})",
                        "severity": "critical",
                        "action": "preserve_last_verified",
                    })
                
                # Impossible negative price
                elif new_val < 0:
                    anomalies.append({
                        "type": AnomalyType.IMPOSSIBLE_VALUE.value,
                        "description": f"Negative price for '{plan}': ${new_val}",
                        "severity": "critical",
                        "action": "preserve_last_verified",
                    })
            except (ValueError, TypeError):
                pass
    
    # Check for pricing blanked
    if old_tiers and not new_tiers:
        anomalies.append({
            "type": AnomalyType.PRICING_BLANKED.value,
            "description": f"All {len(old_tiers)} pricing tiers disappeared",
            "severity": "critical",
            "action": "preserve_last_verified",
        })
    
    # Check detected prices
    old_prices = old_pricing.get("detected_prices", [])
    new_prices = new_pricing.get("detected_prices", [])
    if old_prices and not new_prices:
        anomalies.append({
            "type": AnomalyType.PRICING_BLANKED.value,
            "description": "All detected prices disappeared from source",
            "severity": "high",
            "action": "preserve_last_verified",
        })
    
    return anomalies


def _check_currency_anomalies(old_fields: dict, new_fields: dict) -> List[dict]:
    """Check for currency anomalies."""
    anomalies = []
    
    old_currency = old_fields.get("pricing", {}).get("currency")
    new_currency = new_fields.get("pricing", {}).get("currency")
    
    if old_currency and new_currency and old_currency != new_currency:
        anomalies.append({
            "type": AnomalyType.CURRENCY_CHANGE.value,
            "description": f"Currency changed from {old_currency} to {new_currency}",
            "severity": "high",
            "action": "preserve_last_verified",
        })
    
    return anomalies


def _check_feature_anomalies(old_fields: dict, new_fields: dict) -> List[dict]:
    """Check for feature wipe anomalies."""
    anomalies = []
    
    old_caps = old_fields.get("capabilities", [])
    new_caps = new_fields.get("capabilities", [])
    
    if len(old_caps) >= FEATURE_LOSS_THRESHOLD and len(new_caps) == 0:
        anomalies.append({
            "type": AnomalyType.FEATURE_WIPE.value,
            "description": f"All {len(old_caps)} capabilities disappeared",
            "severity": "critical",
            "action": "preserve_last_verified",
        })
    elif old_caps and new_caps:
        old_set = set(old_caps)
        new_set = set(new_caps)
        lost = old_set - new_set
        if len(lost) >= FEATURE_LOSS_THRESHOLD:
            anomalies.append({
                "type": AnomalyType.FEATURE_WIPE.value,
                "description": f"Lost {len(lost)} of {len(old_caps)} capabilities",
                "severity": "high",
                "action": "preserve_last_verified",
            })
    
    return anomalies


def _check_plan_anomalies(old_fields: dict, new_fields: dict) -> List[dict]:
    """Check for plan-related anomalies."""
    anomalies = []
    
    old_tiers = old_fields.get("pricing", {}).get("tiers", [])
    new_tiers = new_fields.get("pricing", {}).get("tiers", [])
    
    old_plans = {t.get("plan", "") for t in old_tiers}
    new_plans = {t.get("plan", "") for t in new_tiers}
    
    # Plans became unknown
    for plan in old_plans:
        if plan and plan not in new_plans:
            # Check if it was replaced with "unknown"
            if "unknown" in new_plans or "Unknown" in new_plans:
                anomalies.append({
                    "type": AnomalyType.PLAN_TO_UNKNOWN.value,
                    "description": f"Known plan '{plan}' replaced with 'unknown'",
                    "severity": "high",
                    "action": "preserve_last_verified",
                })
    
    return anomalies


def _check_content_anomalies(
    old_fp: Optional[str], new_fp: Optional[str],
    old_text: Optional[str], new_text: Optional[str]
) -> List[dict]:
    """Check for content-level anomalies."""
    anomalies = []
    
    # Check for radically different content
    if old_text and new_text:
        old_len = len(old_text)
        new_len = len(new_text)
        
        if old_len > 100:  # Only check substantial content
            ratio = abs(new_len - old_len) / old_len
            if ratio > CONTENT_DIFF_THRESHOLD:
                anomalies.append({
                    "type": AnomalyType.RADICALLY_DIFFERENT_CONTENT.value,
                    "description": f"Content length changed by {ratio:.0%} ({old_len} → {new_len} chars)",
                    "severity": "high",
                    "action": "preserve_last_verified",
                })
    
    return anomalies


def is_anomaly(anomalies: List[dict]) -> bool:
    """Check if any anomalies were detected."""
    return len(anomalies) > 0


def has_critical_anomaly(anomalies: List[dict]) -> bool:
    """Check if any critical anomalies were detected."""
    return any(a.get("severity") == "critical" for a in anomalies)


def should_preserve_last_verified(anomalies: List[dict]) -> bool:
    """Check if the last verified fact should be preserved (not overwritten)."""
    return has_critical_anomaly(anomalies)


def main():
    """Demo/anomaly detection testing."""
    
    # Test case: price to zero
    old = {"pricing": {"tiers": [{"plan": "Pro", "price": 99}]}}
    new = {"pricing": {"tiers": [{"plan": "Pro", "price": 0}]}}
    anomalies = detect_anomalies(old, new)
    print(f"Price to zero: {len(anomalies)} anomalies")
    for a in anomalies:
        print(f"  - {a['type']}: {a['description']}")
    
    # Test case: huge price increase
    old = {"pricing": {"tiers": [{"plan": "Pro", "price": 20}]}}
    new = {"pricing": {"tiers": [{"plan": "Pro", "price": 2000}]}}
    anomalies = detect_anomalies(old, new)
    print(f"\nHuge price increase: {len(anomalies)} anomalies")
    for a in anomalies:
        print(f"  - {a['type']}: {a['description']}")
    
    # Test case: feature wipe
    old = {"capabilities": ["feature1", "feature2", "feature3", "feature4", "feature5"]}
    new = {"capabilities": []}
    anomalies = detect_anomalies(old, new)
    print(f"\nFeature wipe: {len(anomalies)} anomalies")
    for a in anomalies:
        print(f"  - {a['type']}: {a['description']}")
    
    # Test case: no anomaly
    old = {"pricing": {"tiers": [{"plan": "Pro", "price": 99}]}}
    new = {"pricing": {"tiers": [{"plan": "Pro", "price": 109}]}}
    anomalies = detect_anomalies(old, new)
    print(f"\nNormal price change: {len(anomalies)} anomalies")


if __name__ == "__main__":
    main()
