#!/usr/bin/env python3
"""Fact history manager — versioned history for commercial facts.

Maintains enough history to explain:
- old value
- new candidate value
- source
- detected date
- verified date
- decision
- impact

Does not destructively overwrite commercial facts.
Avoids uncontrolled ledger duplication.

Usage:
    from scripts.fact_history import add_fact_change, get_fact_history
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def add_fact_change(
    claim_id: str,
    old_value: Any,
    new_candidate: Any,
    source: str,
    impact: str,
    detected_date: Optional[str] = None,
) -> dict:
    """Add a fact change entry to a claim's fact_history.
    
    Args:
        claim_id: The claim identifier
        old_value: Previous verified value
        new_candidate: New candidate value from source
        source: Source identifier
        impact: Impact description (e.g., "pricing_increase")
        detected_date: Date detected (defaults to now)
    
    Returns:
        The new fact_history entry
    """
    if detected_date is None:
        detected_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    entry = {
        "old_value": old_value,
        "new_candidate": new_candidate,
        "source": source,
        "detected_date": detected_date,
        "verified_date": None,
        "decision": "pending_review",
        "impact": impact,
    }
    
    # Update the ledger
    if LEDGER_PATH.is_file():
        ledger = load_json(LEDGER_PATH)
        for claim in ledger.get("claims", []):
            if claim.get("claim_id") == claim_id:
                if "fact_history" not in claim:
                    claim["fact_history"] = []
                claim["fact_history"].append(entry)
                # Keep only last 20 entries to avoid uncontrolled growth
                claim["fact_history"] = claim["fact_history"][-20:]
                save_json(LEDGER_PATH, ledger)
                break
    
    return entry


def get_fact_history(claim_id: str) -> List[dict]:
    """Get the fact history for a claim.
    
    Args:
        claim_id: The claim identifier
    
    Returns:
        List of fact_history entries
    """
    if not LEDGER_PATH.is_file():
        return []
    
    ledger = load_json(LEDGER_PATH)
    for claim in ledger.get("claims", []):
        if claim.get("claim_id") == claim_id:
            return claim.get("fact_history", [])
    
    return []


def update_fact_decision(claim_id: str, decision: str, verified_date: Optional[str] = None) -> bool:
    """Update the decision for the most recent pending fact change.
    
    Args:
        claim_id: The claim identifier
        decision: New decision (e.g., "approved", "rejected", "auto_applied")
        verified_date: Date verified (defaults to now)
    
    Returns:
        True if updated, False if not found
    """
    if verified_date is None:
        verified_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if not LEDGER_PATH.is_file():
        return False
    
    ledger = load_json(LEDGER_PATH)
    for claim in ledger.get("claims", []):
        if claim.get("claim_id") == claim_id:
            history = claim.get("fact_history", [])
            # Update the most recent pending entry
            for entry in reversed(history):
                if entry.get("decision") == "pending_review":
                    entry["decision"] = decision
                    entry["verified_date"] = verified_date
                    save_json(LEDGER_PATH, ledger)
                    return True
    
    return False


def get_pending_changes() -> List[dict]:
    """Get all claims with pending fact changes.
    
    Returns:
        List of dicts with claim_id, tool_id, and pending changes
    """
    if not LEDGER_PATH.is_file():
        return []
    
    ledger = load_json(LEDGER_PATH)
    pending = []
    
    for claim in ledger.get("claims", []):
        history = claim.get("fact_history", [])
        pending_entries = [e for e in history if e.get("decision") == "pending_review"]
        if pending_entries:
            pending.append({
                "claim_id": claim.get("claim_id"),
                "tool_id": claim.get("tool_id"),
                "claim_type": claim.get("claim_type"),
                "pending_changes": pending_entries,
            })
    
    return pending


def main():
    """Demo/fact history testing."""
    
    print("\nFact History Demo:")
    print("=" * 60)
    
    # Show pending changes
    pending = get_pending_changes()
    print(f"Pending fact changes: {len(pending)}")
    
    # Show history for a sample claim
    if LEDGER_PATH.is_file():
        ledger = load_json(LEDGER_PATH)
        claims_with_history = [
            c for c in ledger.get("claims", [])
            if c.get("fact_history")
        ]
        print(f"Claims with fact history: {len(claims_with_history)}")


if __name__ == "__main__":
    main()
