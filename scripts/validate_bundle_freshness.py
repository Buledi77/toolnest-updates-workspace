#!/usr/bin/env python3
"""Validate that the decision engine bundle is fresh relative to its inputs.

Checks:
1. The bundle file exists.
2. The SHA-256 hash of tools-v1.json matches the hash stored in bundle metadata.
3. The SHA-256 hash of evidence-ledger.json matches the hash stored in bundle metadata.
4. All tools from tools-v1.json appear exactly once in the bundle.
5. The bundle schema version matches the expected version.

Exit codes:
0 = bundle is fresh
1 = bundle is stale or missing (should rebuild)
2 = validation error (malformed bundle)
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "data" / "tools-v1.json"
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
BUNDLE_PATH = ROOT / "data" / "decision-engine-bundle.json"

EXPECTED_SCHEMA = "decision-engine-bundle-v1"


def sha256_file(path):
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate():
    """Validate bundle freshness. Returns (ok, messages)."""
    messages = []
    ok = True

    # 1. Bundle exists
    if not BUNDLE_PATH.exists():
        return False, ["Bundle file does not exist. Run build_decision_engine_data.py."]

    # 2. Load bundle
    try:
        bundle = load_json(BUNDLE_PATH)
    except json.JSONDecodeError as e:
        return False, [f"Bundle is malformed JSON: {e}"]

    # 3. Schema version check
    schema = bundle.get("schema_version", "")
    if schema != EXPECTED_SCHEMA:
        ok = False
        messages.append(f"Schema mismatch: expected '{EXPECTED_SCHEMA}', got '{schema}'")

    # 4. Tool count check
    tools_data = load_json(TOOLS_PATH)
    expected_tool_count = len(tools_data.get("tools", []))
    bundle_tools = bundle.get("tools", [])
    actual_tool_count = len(bundle_tools)

    if actual_tool_count != expected_tool_count:
        ok = False
        messages.append(
            f"Tool count mismatch: tools-v1.json has {expected_tool_count}, "
            f"bundle has {actual_tool_count}"
        )

    # 5. All tools present exactly once
    v1_ids = {t["id"] for t in tools_data.get("tools", [])}
    bundle_ids = [t.get("id") for t in bundle_tools]
    bundle_id_set = set(bundle_ids)

    if len(bundle_ids) != len(bundle_id_set):
        duplicates = [tid for tid in bundle_id_set if bundle_ids.count(tid) > 1]
        ok = False
        messages.append(f"Duplicate tool IDs in bundle: {duplicates}")

    missing = v1_ids - bundle_id_set
    if missing:
        ok = False
        messages.append(f"Tools missing from bundle: {sorted(missing)}")

    extra = bundle_id_set - v1_ids
    if extra:
        ok = False
        messages.append(f"Extra tools in bundle not in tools-v1.json: {sorted(extra)}")

    # 6. Hash-based freshness check
    metadata = bundle.get("metadata", {})
    stored_tools_hash = metadata.get("tools_v1_hash", "")
    stored_ledger_hash = metadata.get("evidence_ledger_hash", "")

    current_tools_hash = sha256_file(TOOLS_PATH)
    current_ledger_hash = sha256_file(LEDGER_PATH)

    if not stored_tools_hash or not stored_ledger_hash:
        # No hashes stored — bundle was built without freshness tracking
        ok = False
        messages.append(
            "Bundle metadata missing input file hashes. "
            "Rebuild with updated build_decision_engine_data.py."
        )
    else:
        if stored_tools_hash != current_tools_hash:
            ok = False
            messages.append(
                "tools-v1.json has changed since the bundle was built. "
                "Rebuild the bundle."
            )
        if stored_ledger_hash != current_ledger_hash:
            ok = False
            messages.append(
                "evidence-ledger.json has changed since the bundle was built. "
                "Rebuild the bundle."
            )

    return ok, messages


def main():
    ok, messages = validate()

    for msg in messages:
        if ok:
            print(f"  INFO: {msg}")
        else:
            print(f"  FAIL: {msg}")

    if ok:
        print("Bundle freshness: PASS")
        return 0
    else:
        print("Bundle freshness: FAIL — rebuild required")
        return 1


if __name__ == "__main__":
    sys.exit(main())
