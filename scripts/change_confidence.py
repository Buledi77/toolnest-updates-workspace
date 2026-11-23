#!/usr/bin/env python3
"""Change confidence scorer — classifies detected changes by risk level.

Every detected change needs a confidence/safety classification:
- LOW-RISK / DETERMINISTIC: small price adjustment within expected range
- MEDIUM-RISK: new plan added, feature change
- HIGH-RISK / REQUIRES_REVIEW: price >50% change, free plan disappeared,
  paid → free, free → paid, product discontinued, plan restructured,
  major capability removed, currency changed unexpectedly,
  official sources conflict, parser returns radically different content

No auto-publish for HIGH-RISK changes.

Usage:
    from scripts.change_confidence import classify_change_risk, RiskLevel
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple


class RiskLevel(str, Enum):
    """Risk classification for detected changes."""
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    REQUIRES_REVIEW = "requires_review"


# Changes eligible for automated canonical update
AUTO_PUBLISHABLE = {RiskLevel.LOW_RISK}


def classify_change_risk(
    change_type: str,
    specific_changes: List[str],
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
) -> Tuple[RiskLevel, str]:
    """Classify the risk level of a detected change.
    
    Args:
        change_type: Type of change (from change_detector.py)
        specific_changes: List of specific change descriptions
        old_value: Previous extracted values
        new_value: New extracted values
    
    Returns:
        Tuple of (RiskLevel, explanation)
    """
    # Source-level issues
    if change_type in ("source_unavailable", "source_redirect"):
        return RiskLevel.MEDIUM_RISK, f"Source {change_type} — preserve last verified value"
    
    if change_type == "conflict":
        return RiskLevel.HIGH_RISK, "Conflicting official sources — manual review required"
    
    if change_type == "anomaly":
        return RiskLevel.REQUIRES_REVIEW, "Anomalous change detected — never overwrite last verified fact"
    
    # Cosmetic/layout changes are low risk
    if change_type in ("no_change", "cosmetic_change", "layout_change"):
        return RiskLevel.LOW_RISK, "Non-material change"
    
    # Analyze specific changes for risk
    risk = RiskLevel.LOW_RISK
    reasons = []
    
    for change in specific_changes:
        change_risk, reason = _classify_specific_change(change, old_value, new_value)
        if _risk_greater(change_risk, risk):
            risk = change_risk
        reasons.append(reason)
    
    explanation = "; ".join(reasons) if reasons else change_type
    return risk, explanation


def _classify_specific_change(
    change: str,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
) -> Tuple[RiskLevel, str]:
    """Classify a single specific change."""
    
    # Price changes
    if "price_changed" in change:
        # Parse price change: price_changed:plan:old->new
        match = re.search(r'price_changed:(.+?):(.+?)->(.+)', change)
        if match:
            plan = match.group(1)
            old_str = match.group(2)
            new_str = match.group(3)
            
            try:
                old_price = float(old_str.replace('$', '').replace(',', ''))
                new_price = float(new_str.replace('$', '').replace(',', ''))
                
                if old_price > 0:
                    pct_change = abs(new_price - old_price) / old_price
                    
                    if new_price == 0 and old_price > 0:
                        return RiskLevel.REQUIRES_REVIEW, f"Price dropped to $0 for {plan} — possible anomaly"
                    elif pct_change > 0.5:
                        return RiskLevel.HIGH_RISK, f"Price change >50% for {plan}: ${old_price} → ${new_price}"
                    elif pct_change > 0.2:
                        return RiskLevel.MEDIUM_RISK, f"Price change >20% for {plan}: ${old_price} → ${new_price}"
                    else:
                        return RiskLevel.LOW_RISK, f"Small price adjustment for {plan}: ${old_price} → ${new_price}"
            except (ValueError, TypeError):
                return RiskLevel.MEDIUM_RISK, f"Price change for {plan}: {old_str} → {new_str}"
        
        return RiskLevel.MEDIUM_RISK, f"Price change: {change}"
    
    # Currency changes
    if "currency_changed" in change:
        return RiskLevel.HIGH_RISK, f"Currency changed — {change}"
    
    # Free plan changes
    if "free_plan_changed" in change:
        if "True->False" in change:
            return RiskLevel.HIGH_RISK, "Free plan disappeared — high impact on users"
        elif "False->True" in change:
            return RiskLevel.HIGH_RISK, "Free plan appeared — verify this is accurate"
        return RiskLevel.HIGH_RISK, f"Free plan change: {change}"
    
    # Trial changes
    if "trial_changed" in change:
        return RiskLevel.MEDIUM_RISK, f"Trial information changed"
    
    # Plan changes
    if "plan_removed" in change:
        return RiskLevel.HIGH_RISK, f"Plan removed — {change}"
    if "plan_added" in change:
        return RiskLevel.MEDIUM_RISK, f"New plan added — {change}"
    
    # Billing changes
    if "billing" in change:
        return RiskLevel.MEDIUM_RISK, f"Billing change: {change}"
    
    # Feature changes
    if "features_added" in change:
        return RiskLevel.LOW_RISK, f"Features added"
    if "features_removed" in change:
        return RiskLevel.HIGH_RISK, f"Features removed — {change}"
    
    # Platform changes
    if "platform" in change:
        return RiskLevel.MEDIUM_RISK, f"Platform change: {change}"
    
    # Integration changes
    if "integration" in change:
        return RiskLevel.MEDIUM_RISK, f"Integration change: {change}"
    
    # Default
    return RiskLevel.MEDIUM_RISK, f"Change: {change}"


def _risk_greater(a: RiskLevel, b: RiskLevel) -> bool:
    """Check if risk level a is greater than b."""
    order = {
        RiskLevel.LOW_RISK: 0,
        RiskLevel.MEDIUM_RISK: 1,
        RiskLevel.HIGH_RISK: 2,
        RiskLevel.REQUIRES_REVIEW: 3,
    }
    return order.get(a, 0) > order.get(b, 0)


def is_auto_publishable(risk_level: RiskLevel) -> bool:
    """Check if a change is eligible for automated canonical update."""
    return risk_level in AUTO_PUBLISHABLE


def requires_manual_review(risk_level: RiskLevel) -> bool:
    """Check if a change requires manual review before any update."""
    return risk_level in (RiskLevel.HIGH_RISK, RiskLevel.REQUIRES_REVIEW)


def main():
    """Demo/change confidence testing."""
    
    # Test cases
    test_cases = [
        ("price_change", ["price_changed:Pro:$99->$109"], RiskLevel.LOW_RISK),
        ("price_change", ["price_changed:Pro:$99->$200"], RiskLevel.HIGH_RISK),
        ("price_change", ["price_changed:Pro:$99->$0"], RiskLevel.REQUIRES_REVIEW),
        ("free_plan_change", ["free_plan_changed:True->False"], RiskLevel.HIGH_RISK),
        ("feature_change", ["features_added:AI writing"], RiskLevel.LOW_RISK),
        ("feature_change", ["features_removed:API access"], RiskLevel.HIGH_RISK),
        ("source_unavailable", ["source_unavailable"], RiskLevel.MEDIUM_RISK),
        ("conflict", ["conflicting_sources"], RiskLevel.HIGH_RISK),
    ]
    
    print("\nChange Confidence Tests:")
    print("=" * 60)
    
    for change_type, changes, expected in test_cases:
        risk, explanation = classify_change_risk(change_type, changes)
        status = "PASS" if risk == expected else "FAIL"
        print(f"  [{status}] {change_type}: {risk.value} (expected {expected.value})")
        print(f"         {explanation}")


if __name__ == "__main__":
    main()
