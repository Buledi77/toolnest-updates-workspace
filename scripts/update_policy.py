#!/usr/bin/env python3
"""Safe update policy — three-tier update classification.

Tiers:
- TIER 1: deterministic low-risk → eligible for automated canonical update
- TIER 2: update candidate automatically, require approval before publish
- TIER 3: manual review required

No direct production deployment enabled.

Usage:
    from scripts.update_policy import classify_update, UpdateTier
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]


class UpdateTier(str, Enum):
    """Update policy tiers."""
    TIER_1 = "tier_1_auto"
    TIER_2 = "tier_2_approval"
    TIER_3 = "tier_3_manual"


def classify_update(
    change_type: str,
    risk_level: str,
    anomaly_detected: bool = False,
    source_official: bool = False,
    claim_type: str = "",
) -> Tuple[UpdateTier, str]:
    """Classify an update into a policy tier.
    
    Args:
        change_type: Type of change (from change_detector.py)
        risk_level: Risk level (from change_confidence.py)
        anomaly_detected: Whether anomaly detection flagged this
        source_official: Whether the source is first-party official
        claim_type: Type of claim (pricing, capability, etc.)
    
    Returns:
        Tuple of (UpdateTier, explanation)
    """
    # Anomalies always go to TIER 3
    if anomaly_detected:
        return UpdateTier.TIER_3, "Anomaly detected — manual review required"
    
    # High risk always goes to TIER 3
    if risk_level in ("high_risk", "requires_review"):
        return UpdateTier.TIER_3, f"High risk ({risk_level}) — manual review required"
    
    # Medium risk goes to TIER 2
    if risk_level == "medium_risk":
        return UpdateTier.TIER_2, f"Medium risk — approval required before publish"
    
    # Low risk with official source can be TIER 1
    if risk_level == "low_risk" and source_official:
        return UpdateTier.TIER_1, "Low risk with official source — eligible for auto-update"
    
    # Low risk without official source goes to TIER 2
    if risk_level == "low_risk":
        return UpdateTier.TIER_2, "Low risk but non-official source — approval required"
    
    # Default to TIER 2 for safety
    return UpdateTier.TIER_2, "Default to approval-required for safety"


def is_auto_publishable(tier: UpdateTier) -> bool:
    """Check if an update tier is eligible for automated canonical update."""
    return tier == UpdateTier.TIER_1


def requires_approval(tier: UpdateTier) -> bool:
    """Check if an update tier requires approval before publish."""
    return tier == UpdateTier.TIER_2


def requires_manual_review(tier: UpdateTier) -> bool:
    """Check if an update tier requires manual review."""
    return tier == UpdateTier.TIER_3


def create_update_request(
    tool_id: str,
    claim_id: str,
    old_value: Any,
    new_value: Any,
    tier: UpdateTier,
    source: str,
    change_type: str,
) -> dict:
    """Create an update request record.
    
    Args:
        tool_id: Tool identifier
        claim_id: Claim identifier
        old_value: Current verified value
        new_value: New candidate value
        tier: Update policy tier
        source: Source identifier
        change_type: Type of change
    
    Returns:
        Update request dict
    """
    return {
        "tool_id": tool_id,
        "claim_id": claim_id,
        "old_value": old_value,
        "new_value": new_value,
        "tier": tier.value,
        "source": source,
        "change_type": change_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending" if tier != UpdateTier.TIER_1 else "auto_approved",
        "approved_by": None,
        "approved_at": None,
        "published": False,
    }


def main():
    """Demo/update policy testing."""
    
    test_cases = [
        ("price_change", "low_risk", False, True, "pricing", UpdateTier.TIER_1),
        ("price_change", "low_risk", False, False, "pricing", UpdateTier.TIER_2),
        ("price_change", "medium_risk", False, True, "pricing", UpdateTier.TIER_2),
        ("price_change", "high_risk", False, True, "pricing", UpdateTier.TIER_3),
        ("price_change", "low_risk", True, True, "pricing", UpdateTier.TIER_3),
    ]
    
    print("\nUpdate Policy Tests:")
    print("=" * 60)
    
    for change_type, risk, anomaly, official, claim_type, expected in test_cases:
        tier, explanation = classify_update(change_type, risk, anomaly, official, claim_type)
        status = "PASS" if tier == expected else "FAIL"
        print(f"  [{status}] {change_type}/{risk}: {tier.value} (expected {expected.value})")
        print(f"         {explanation}")


if __name__ == "__main__":
    main()
