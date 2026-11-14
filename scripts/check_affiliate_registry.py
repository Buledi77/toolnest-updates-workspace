#!/usr/bin/env python3
"""Validate affiliate registry separation from official destinations and editorial fields."""

from decision_graph_common import ROOT, load_json, load_records, is_date, is_url, print_result

REGISTRY_PATH = ROOT / "data" / "monetization" / "affiliate-registry.json"


def validate_registry():
    registry = load_json(REGISTRY_PATH)
    records = {record["identity"]["id"]: record for record in load_records()}
    errors = []
    seen = set()
    if registry.get("editorial_independence") is not True:
        errors.append("affiliate registry must declare editorial independence")
    for entry in registry.get("entries", []):
        tool_id = entry.get("tool_id")
        if tool_id in seen:
            errors.append(f"duplicate affiliate entry {tool_id}")
        seen.add(tool_id)
        record = records.get(tool_id)
        if record is None:
            errors.append(f"affiliate entry references missing tool {tool_id}")
            continue
        official = entry.get("official_non_affiliate_url")
        if official != record["monetization"]["official_non_affiliate_url"] or not is_url(official):
            errors.append(f"{tool_id}: official URL mismatch")
        status = entry.get("affiliate_status")
        if status not in {"none", "not_applied", "needs_review", "unknown", "active", "expired"}:
            errors.append(f"{tool_id}: invalid affiliate status")
        if entry.get("last_link_check") is not None and not is_date(entry["last_link_check"]):
            errors.append(f"{tool_id}: invalid last_link_check")
        if record["editorial"].get("editorial_tier") not in {"A", "B", "C"}:
            errors.append(f"{tool_id}: editorial tier is invalid")
    if seen != set(records):
        errors.append("affiliate registry is not complete for Decision Graph records")
    return errors


if __name__ == "__main__":
    raise SystemExit(print_result("Affiliate registry validation", validate_registry()))
