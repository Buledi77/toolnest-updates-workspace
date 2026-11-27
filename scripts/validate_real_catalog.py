#!/usr/bin/env python3
"""Validate the real catalog data and report errors by severity."""

import re

from decision_graph_common import (
    ROOT,
    LEDGER_PATH,
    load_json,
    load_legacy_ids,
    load_records,
    print_result,
    validate_tool_records,
)


def validate_real_catalog():
    """Run validation against the production catalog and categorize errors.

    Expansion-only records (data/tools-v2/expansion) are not production pages;
    they are governed by validate_production_scope.py and must not be counted
    as production catalog defects.
    """
    errors = validate_tool_records()

    expansion_path = ROOT / "data" / "catalog-reconciliation.json"
    expansion_ids = set()
    if expansion_path.is_file():
        expansion_ids = set(load_json(expansion_path).get("expansion_only_tools", []))
    if expansion_ids:
        errors = [
            err for err in errors
            if not any(re.search(rf"\b{re.escape(tid)}\b", err) for tid in expansion_ids)
        ]

    high = []
    medium = []
    low = []

    for err in errors:
        if "references missing tool" in err:
            high.append(err)
        elif "references missing claim" in err or "references missing source" in err:
            medium.append(err)
        elif "omits claim" in err:
            low.append(err)
        else:
            medium.append(err)

    return {
        "high": high,
        "medium": medium,
        "low": low,
        "total": len(high) + len(medium) + len(low),
    }


def check_evidence_consistency():
    """Check that no record claims moderate confidence without backing evidence."""
    records = load_records()
    ledger = load_json(LEDGER_PATH)
    source_ids = {s.get("source_id") for s in ledger.get("sources", [])}
    claim_ids = {c.get("claim_id") for c in ledger.get("claims", [])}

    errors = []
    for record in records:
        rid = record["identity"]["id"]
        evidence = record.get("evidence", {})
        confidence = evidence.get("confidence", "")
        if confidence in ("moderate", "high"):
            # Accept either the new ledger-based format (source_ids + claim_refs)
            # or the older inline sources array as valid backing evidence
            has_ledger_sources = bool(evidence.get("source_ids"))
            has_ledger_claims = bool(evidence.get("claim_refs"))
            has_inline_sources = bool(
                isinstance(evidence.get("sources"), list)
                and len(evidence["sources"]) > 0
            )
            if not (has_ledger_sources and has_ledger_claims) and not has_inline_sources:
                errors.append(
                    f"{rid} claims {confidence} confidence but has no backing evidence"
                )
            # Check that referenced sources and claims actually exist
            for sid in evidence.get("source_ids", []):
                if sid not in source_ids:
                    errors.append(
                        f"{rid} references missing source {sid} with {confidence} confidence"
                    )
            for cr in evidence.get("claim_refs", []):
                if cr.get("claim_id") not in claim_ids:
                    errors.append(
                        f"{rid} references missing claim {cr.get('claim_id')} with {confidence} confidence"
                    )
    return errors


def check_new_catalog_records():
    """Verify the 6 new catalog records exist and are structurally valid."""
    records = load_records()
    record_ids = {r["identity"]["id"] for r in records}

    expected = {"circle", "deel", "nutshell", "quo", "survicate", "tidio"}
    errors = []

    for tid in sorted(expected):
        if tid not in record_ids:
            errors.append(f"missing expected catalog record: {tid}")
        else:
            record = next(r for r in records if r["identity"]["id"] == tid)
            tier = record.get("editorial", {}).get("editorial_tier")
            if tier != "C":
                errors.append(f"{tid} should be Tier C, got {tier}")
            confidence = record.get("evidence", {}).get("confidence")
            if confidence != "unverified":
                errors.append(f"{tid} should have unverified confidence, got {confidence}")

    return errors


def check_preserved_evidence():
    """Verify that Hostinger, Semrush, and Moz Pro evidence is preserved."""
    records = load_records()
    record_map = {r["identity"]["id"]: r for r in records}

    preserved = {"hostinger", "semrush", "mozpro"}
    errors = []

    for tid in sorted(preserved):
        if tid not in record_map:
            errors.append(f"preserved record {tid} not found in catalog")
        else:
            record = record_map[tid]
            evidence = record.get("evidence", {})
            # These records should not have been cleared
            if evidence.get("confidence") == "unverified" and not evidence.get("source_ids"):
                errors.append(
                    f"{tid} evidence was cleared but should have been preserved"
                )

    return errors


def main():
    results = validate_real_catalog()
    consistency = check_evidence_consistency()
    new_records = check_new_catalog_records()
    preserved = check_preserved_evidence()

    print("=== Real Catalog Validation ===")
    print(f"Total structural errors: {results['total']}")
    print(f"  HIGH (broken links): {len(results['high'])}")
    print(f"  MEDIUM (evidence issues): {len(results['medium'])}")
    print(f"  LOW (research backlog): {len(results['low'])}")

    if results["high"]:
        print("\nHIGH severity:")
        for e in results["high"]:
            print(f"  {e}")
    if results["medium"]:
        print("\nMEDIUM severity:")
        for e in results["medium"]:
            print(f"  {e}")
    if results["low"]:
        print("\nLOW severity:")
        for e in results["low"]:
            print(f"  {e}")

    print(f"\nEvidence consistency errors: {len(consistency)}")
    for e in consistency:
        print(f"  {e}")

    print(f"\nNew catalog record errors: {len(new_records)}")
    for e in new_records:
        print(f"  {e}")

    print(f"\nPreserved evidence errors: {len(preserved)}")
    for e in preserved:
        print(f"  {e}")

    total = results["total"] + len(consistency) + len(new_records) + len(preserved)
    print(f"\nTotal issues: {total}")
    return total


if __name__ == "__main__":
    count = main()
    raise SystemExit(print_result("Real catalog validation", [] if count == 0 else [f"{count} issues found"]))
