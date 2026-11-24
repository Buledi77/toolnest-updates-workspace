#!/usr/bin/env python3
"""Canonical facts derivation layer.

Reads accepted claims from evidence-ledger.json and writes:
1. data/canonical-facts.json — the single derived build artifact
2. Updates data/tools/*.json pricing sections from canonical facts
3. Updates data/tools-v1.json pricing sections from canonical facts
4. Updates data/tools.json lightweight catalog from canonical facts

This script runs before other generators (regenerate_tool_profiles.py,
build_decision_engine_data.py) in the build pipeline.

Usage:
    python3 scripts/derive_canonical_facts.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
CANONICAL_FACTS_PATH = ROOT / "data" / "canonical-facts.json"
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
TOOLS_JSON_PATH = ROOT / "data" / "tools.json"
DATA_TOOLS_DIR = ROOT / "data" / "tools"

# Accepted claim statuses
ACCEPTED_STATUSES = {"verified", "verified_official", "verified_official_dynamic"}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def extract_pricing_from_claim(claim: dict) -> Optional[dict]:
    """Extract pricing data from a pricing claim.
    
    Returns a dict with plans, billingBasis, currency, checkedOn.
    """
    claim_type = claim.get("claim_type", "")
    if claim_type != "pricing":
        return None
    
    value = claim.get("value", {})
    if isinstance(value, str):
        # Text-based pricing model description
        return {
            "model": value,
            "currency": claim.get("currency", "USD"),
            "billing_term": claim.get("billing_term"),
        }
    
    if isinstance(value, dict):
        pricing = {}
        
        # Extract plans from value
        if "plans" in value:
            pricing["plans"] = value["plans"]
        
        # Extract billing info from claim metadata
        if claim.get("currency"):
            pricing["currency"] = claim["currency"]
        if claim.get("billing_term"):
            pricing["billingBasis"] = claim["billing_term"]
        
        # Extract checked date
        if claim.get("verified_at"):
            pricing["checkedOn"] = claim["verified_at"]
        elif claim.get("accessed_at"):
            pricing["checkedOn"] = claim["accessed_at"]
        
        return pricing if pricing else None
    
    return None


def extract_free_plan_from_claim(claim: dict) -> Optional[dict]:
    """Extract free plan data from a free_plan claim."""
    claim_type = claim.get("claim_type", "")
    if claim_type != "free_plan":
        return None
    
    value = claim.get("value", "")
    if isinstance(value, str):
        # Determine status from text
        has_free = "no free plan" not in value.lower() and "no free" not in value.lower()
        status = "permanent_free_plan" if has_free else "no_free_plan"
        return {
            "status": status,
            "description": value,
            "checkedOn": claim.get("verified_at") or claim.get("accessed_at"),
        }
    elif isinstance(value, dict):
        result = dict(value)
        if claim.get("verified_at"):
            result["checkedOn"] = claim["verified_at"]
        return result
    
    return None


def extract_trial_from_claim(claim: dict) -> Optional[dict]:
    """Extract trial data from a trial claim."""
    claim_type = claim.get("claim_type", "")
    if claim_type != "trial":
        return None
    
    value = claim.get("value", "")
    if isinstance(value, str):
        has_trial = "no trial" not in value.lower() and "no free trial" not in value.lower()
        status = "free_trial" if has_trial else "no_trial"
        return {
            "status": status,
            "description": value,
            "checkedOn": claim.get("verified_at") or claim.get("accessed_at"),
        }
    elif isinstance(value, dict):
        result = dict(value)
        if claim.get("verified_at"):
            result["checkedOn"] = claim["verified_at"]
        return result
    
    return None


def extract_platform_from_claim(claim: dict) -> Optional[List[str]]:
    """Extract platform data from a platform claim."""
    claim_type = claim.get("claim_type", "")
    if claim_type != "platform":
        return None
    
    value = claim.get("value", "")
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        # Parse comma-separated platforms
        return [p.strip() for p in value.split(",") if p.strip()]
    
    return None


def extract_capabilities_from_claim(claim: dict) -> Optional[List[str]]:
    """Extract capabilities from a capability claim."""
    claim_type = claim.get("claim_type", "")
    if claim_type not in ("capability", "feature"):
        return None
    
    value = claim.get("value", "")
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        return [value]
    
    return None


def compute_confidence(claims: list) -> str:
    """Compute confidence level based on claim statuses.
    
    Returns: high, medium, or low
    """
    if not claims:
        return "low"
    
    has_verified_official = any(
        c.get("status") in ("verified_official", "verified_official_dynamic")
        for c in claims
    )
    has_verified = any(c.get("status") == "verified" for c in claims)
    
    if has_verified_official:
        return "high"
    elif has_verified:
        return "medium"
    else:
        return "low"


def derive_canonical_facts() -> dict:
    """Read evidence ledger and derive canonical facts for all tools.
    
    Returns:
        Dict mapping tool_id to canonical fact data.
    """
    ledger = load_json(LEDGER_PATH) if LEDGER_PATH.is_file() else {"claims": []}
    
    # Group accepted claims by tool
    claims_by_tool = defaultdict(list)
    for claim in ledger.get("claims", []):
        if claim.get("status") in ACCEPTED_STATUSES:
            tid = claim.get("tool_id", "")
            if tid:
                claims_by_tool[tid].append(claim)
    
    canonical_facts = {}
    
    for tool_id, claims in claims_by_tool.items():
        fact = {
            "tool_id": tool_id,
            "source_claim_ids": [c.get("claim_id") for c in claims],
        }
        
        # Extract pricing
        pricing_claims = [c for c in claims if c.get("claim_type") == "pricing"]
        if pricing_claims:
            # Use the most recent pricing claim
            latest_pricing = max(
                pricing_claims,
                key=lambda c: c.get("verified_at") or c.get("accessed_at") or "",
            )
            pricing_data = extract_pricing_from_claim(latest_pricing)
            if pricing_data:
                fact["pricing"] = pricing_data
        
        # Extract free plan
        free_plan_claims = [c for c in claims if c.get("claim_type") == "free_plan"]
        if free_plan_claims:
            latest_free = max(
                free_plan_claims,
                key=lambda c: c.get("verified_at") or c.get("accessed_at") or "",
            )
            free_data = extract_free_plan_from_claim(latest_free)
            if free_data:
                fact["free_plan"] = free_data
        
        # Extract trial
        trial_claims = [c for c in claims if c.get("claim_type") == "trial"]
        if trial_claims:
            latest_trial = max(
                trial_claims,
                key=lambda c: c.get("verified_at") or c.get("accessed_at") or "",
            )
            trial_data = extract_trial_from_claim(latest_trial)
            if trial_data:
                fact["trial"] = trial_data
        
        # Extract platform
        platform_claims = [c for c in claims if c.get("claim_type") == "platform"]
        if platform_claims:
            latest_platform = max(
                platform_claims,
                key=lambda c: c.get("verified_at") or c.get("accessed_at") or "",
            )
            platform_data = extract_platform_from_claim(latest_platform)
            if platform_data:
                fact["platform"] = platform_data
        
        # Extract capabilities
        capability_claims = [c for c in claims if c.get("claim_type") in ("capability", "feature")]
        if capability_claims:
            all_caps = []
            for cap_claim in capability_claims:
                cap_data = extract_capabilities_from_claim(cap_claim)
                if cap_data:
                    all_caps.extend(cap_data)
            if all_caps:
                # Deduplicate
                seen = set()
                unique_caps = []
                for cap in all_caps:
                    if cap not in seen:
                        seen.add(cap)
                        unique_caps.append(cap)
                fact["capabilities"] = unique_caps
        
        # Compute facts_checked date from latest verified_at
        all_dates = []
        for c in claims:
            for date_field in ("verified_at", "accessed_at", "checkedOn"):
                d = c.get(date_field)
                if d:
                    all_dates.append(d)
        if all_dates:
            fact["facts_checked"] = max(all_dates)
        
        # Compute confidence
        fact["confidence"] = compute_confidence(claims)
        
        canonical_facts[tool_id] = fact
    
    return canonical_facts


def update_tool_json_from_canonical(tool_id: str, canonical: dict) -> bool:
    """Update a tool's JSON file from canonical facts.
    
    Only updates mutable commercial fields. Preserves all other fields.
    Returns True if any changes were made.
    """
    tool_path = DATA_TOOLS_DIR / f"{tool_id}.json"
    if not tool_path.exists():
        return False
    
    try:
        tool_data = load_json(tool_path)
    except Exception:
        return False
    
    changed = False
    
    # Update pricing section from canonical
    if "pricing" in canonical:
        canonical_pricing = canonical["pricing"]
        
        # Ensure pricing section exists
        if "pricing" not in tool_data:
            tool_data["pricing"] = {}
        
        pricing_section = tool_data["pricing"]
        
        # Update billingBasis
        if "billingBasis" in canonical_pricing:
            if pricing_section.get("billingBasis") != canonical_pricing["billingBasis"]:
                pricing_section["billingBasis"] = canonical_pricing["billingBasis"]
                changed = True
        
        # Update currency
        if "currency" in canonical_pricing:
            if pricing_section.get("currency") != canonical_pricing["currency"]:
                pricing_section["currency"] = canonical_pricing["currency"]
                changed = True
        
        # Update checkedOn from canonical facts_checked
        if "facts_checked" in canonical:
            if pricing_section.get("checkedOn") != canonical["facts_checked"]:
                pricing_section["checkedOn"] = canonical["facts_checked"]
                changed = True
    
    # Update free plan from canonical
    if "free_plan" in canonical:
        canonical_free = canonical["free_plan"]
        pricing_section = tool_data.get("pricing", {})
        
        if isinstance(canonical_free, dict):
            status = canonical_free.get("status", "")
            if "permanent_free_plan" in status:
                if pricing_section.get("freePlan") is not True:
                    pricing_section["freePlan"] = True
                    changed = True
            elif "no_free_plan" in status:
                if pricing_section.get("freePlan") is not False:
                    pricing_section["freePlan"] = False
                    changed = True
    
    # Update trial from canonical
    if "trial" in canonical:
        canonical_trial = canonical["trial"]
        pricing_section = tool_data.get("pricing", {})
        
        if isinstance(canonical_trial, dict):
            status = canonical_trial.get("status", "")
            description = canonical_trial.get("description", "")
            if "free_trial" in status and description:
                if pricing_section.get("trial") != description:
                    pricing_section["trial"] = description
                    changed = True
            elif "no_trial" in status:
                if pricing_section.get("trial") is not None:
                    pricing_section["trial"] = None
                    changed = True
    
    # Update platform from canonical
    if "platform" in canonical:
        canonical_platforms = canonical["platform"]
        discovery = tool_data.get("discovery", {})
        if isinstance(discovery, dict):
            if discovery.get("platforms") != canonical_platforms:
                discovery["platforms"] = canonical_platforms
                changed = True
    
    if changed:
        save_json(tool_path, tool_data)
    
    return changed


def update_tools_v1_from_canonical(canonical_facts: dict) -> bool:
    """Update tools-v1.json pricing sections from canonical facts.
    
    Returns True if any changes were made.
    """
    if not TOOLS_V1_PATH.exists():
        return False
    
    try:
        v1_data = load_json(TOOLS_V1_PATH)
    except Exception:
        return False
    
    tools = v1_data.get("tools", [])
    changed = False
    
    for tool in tools:
        tool_id = tool.get("id", "")
        if tool_id not in canonical_facts:
            continue
        
        canonical = canonical_facts[tool_id]
        tool_changed = False
        
        # Update pricing section
        if "pricing" in canonical:
            canonical_pricing = canonical["pricing"]
            
            if "pricing" not in tool:
                tool["pricing"] = {}
            
            pricing_section = tool["pricing"]
            
            # Update billingBasis
            if "billingBasis" in canonical_pricing:
                if pricing_section.get("billingBasis") != canonical_pricing["billingBasis"]:
                    pricing_section["billingBasis"] = canonical_pricing["billingBasis"]
                    tool_changed = True
            
            # Update currency
            if "currency" in canonical_pricing:
                if pricing_section.get("currency") != canonical_pricing["currency"]:
                    pricing_section["currency"] = canonical_pricing["currency"]
                    tool_changed = True
            
            # Update checkedOn
            if "facts_checked" in canonical:
                if pricing_section.get("checkedOn") != canonical["facts_checked"]:
                    pricing_section["checkedOn"] = canonical["facts_checked"]
                    tool_changed = True
        
        # Update free plan
        if "free_plan" in canonical:
            canonical_free = canonical["free_plan"]
            pricing_section = tool.get("pricing", {})
            
            if isinstance(canonical_free, dict):
                status = canonical_free.get("status", "")
                if "permanent_free_plan" in status:
                    if pricing_section.get("freePlan") is not True:
                        pricing_section["freePlan"] = True
                        tool_changed = True
                elif "no_free_plan" in status:
                    if pricing_section.get("freePlan") is not False:
                        pricing_section["freePlan"] = False
                        tool_changed = True
        
        # Update trial
        if "trial" in canonical:
            canonical_trial = canonical["trial"]
            pricing_section = tool.get("pricing", {})
            
            if isinstance(canonical_trial, dict):
                status = canonical_trial.get("status", "")
                description = canonical_trial.get("description", "")
                if "free_trial" in status and description:
                    if pricing_section.get("trial") != description:
                        pricing_section["trial"] = description
                        tool_changed = True
                elif "no_trial" in status:
                    if pricing_section.get("trial") is not None:
                        pricing_section["trial"] = None
                        tool_changed = True
        
        # Update platforms in discovery
        if "platform" in canonical:
            canonical_platforms = canonical["platform"]
            discovery = tool.get("discovery", {})
            if isinstance(discovery, dict):
                if discovery.get("platforms") != canonical_platforms:
                    discovery["platforms"] = canonical_platforms
                    tool_changed = True
        
        if tool_changed:
            changed = True
    
    if changed:
        save_json(TOOLS_V1_PATH, v1_data)
    
    return changed


def update_tools_json_from_canonical(canonical_facts: dict) -> bool:
    """Update data/tools.json lightweight catalog from canonical facts.
    
    Returns True if any changes were made.
    """
    if not TOOLS_JSON_PATH.exists():
        return False
    
    try:
        tools_data = load_json(TOOLS_JSON_PATH)
    except Exception:
        return False
    
    # tools.json is a list of tool entries
    if not isinstance(tools_data, list):
        return False
    
    changed = False
    for tool in tools_data:
        tool_id = tool.get("id", "")
        if tool_id not in canonical_facts:
            continue
        
        canonical = canonical_facts[tool_id]
        tool_changed = False
        
        # Update free plan
        if "free_plan" in canonical:
            canonical_free = canonical["free_plan"]
            if isinstance(canonical_free, dict):
                status = canonical_free.get("status", "")
                if "permanent_free_plan" in status:
                    if tool.get("freePlan") is not True:
                        tool["freePlan"] = True
                        tool_changed = True
                elif "no_free_plan" in status:
                    if tool.get("freePlan") is not False:
                        tool["freePlan"] = False
                        tool_changed = True
        
        # Update priceFrom if available in canonical pricing
        if "pricing" in canonical:
            canonical_pricing = canonical["pricing"]
            if "plans" in canonical_pricing and canonical_pricing["plans"]:
                # Find the lowest non-free plan price
                prices = []
                for plan in canonical_pricing["plans"]:
                    price = plan.get("monthly_usd") or plan.get("priceMonthly")
                    if price and price > 0:
                        prices.append(price)
                if prices:
                    lowest = min(prices)
                    price_str = f"${lowest}"
                    if tool.get("priceFrom") != price_str:
                        tool["priceFrom"] = price_str
                        tool_changed = True
        
        if tool_changed:
            changed = True
    
    if changed:
        save_json(TOOLS_JSON_PATH, tools_data)
    
    return changed


def main():
    print("\n" + "=" * 60)
    print("Canonical Facts Derivation")
    print("=" * 60)
    
    # Step 1: Derive canonical facts from evidence ledger
    print("\n  Deriving canonical facts from evidence ledger...")
    canonical_facts = derive_canonical_facts()
    
    # Write canonical-facts.json
    save_json(CANONICAL_FACTS_PATH, canonical_facts)
    print(f"  Written {len(canonical_facts)} tool facts to {CANONICAL_FACTS_PATH.relative_to(ROOT)}")
    
    # Step 2: Update data/tools/*.json
    print("\n  Updating data/tools/*.json from canonical facts...")
    tool_json_changes = 0
    for tool_id, canonical in canonical_facts.items():
        if update_tool_json_from_canonical(tool_id, canonical):
            tool_json_changes += 1
    print(f"  Updated {tool_json_changes} tool JSON files")
    
    # Step 3: Update tools-v1.json
    print("\n  Updating tools-v1.json from canonical facts...")
    v1_changed = update_tools_v1_from_canonical(canonical_facts)
    if v1_changed:
        print(f"  Updated {TOOLS_V1_PATH.relative_to(ROOT)}")
    else:
        print(f"  No changes to {TOOLS_V1_PATH.relative_to(ROOT)}")
    
    # Step 4: Update tools.json
    print("\n  Updating tools.json from canonical facts...")
    tools_json_changed = update_tools_json_from_canonical(canonical_facts)
    if tools_json_changed:
        print(f"  Updated {TOOLS_JSON_PATH.relative_to(ROOT)}")
    else:
        print(f"  No changes to {TOOLS_JSON_PATH.relative_to(ROOT)}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Canonical facts derived: {len(canonical_facts)}")
    print(f"  Tool JSONs updated: {tool_json_changes}")
    print(f"  tools-v1.json updated: {v1_changed}")
    print(f"  tools.json updated: {tools_json_changed}")
    print(f"{'='*60}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
