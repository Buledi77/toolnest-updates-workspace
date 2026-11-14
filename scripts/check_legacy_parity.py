#!/usr/bin/env python3
"""Check that the shadow migration preserves the current 50-record catalog identity."""

from decision_graph_common import ROOT, load_json, print_result


def validate_parity():
    legacy = load_json(ROOT / "data" / "tools.json")
    manifest = load_json(ROOT / "data" / "migrations" / "legacy-to-v2-map.json")
    errors = []
    if len(legacy.get("tools", [])) != manifest.get("source_count"):
        errors.append("legacy count differs from migration manifest")
    legacy_ids = {tool["id"] for tool in legacy.get("tools", [])}
    mapped_ids = {item["legacy_id"] for item in manifest.get("records", [])}
    if legacy_ids != mapped_ids:
        errors.append("legacy IDs differ from migration manifest")
    if len(manifest.get("records", [])) != len(legacy_ids):
        errors.append("migration manifest contains duplicate or missing records")
    for item in manifest.get("records", []):
        if not item.get("record_path"):
            errors.append(f"{item.get('legacy_id')}: missing record path")
    return errors


if __name__ == "__main__":
    raise SystemExit(print_result("Legacy parity validation", validate_parity()))
