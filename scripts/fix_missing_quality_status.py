#!/usr/bin/env python3
"""Batch fix: set content_quality_status for records missing it."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"


def main():
    fixed = 0
    for record_path in sorted(TOOL_DIR.rglob("*.json")):
        if record_path.name == "README.json":
            continue

        record = json.loads(record_path.read_text(encoding="utf-8"))
        publishing = record.get("publishing", {})

        if "content_quality_status" not in publishing:
            publishing["content_quality_status"] = "assessed"
            record["publishing"] = publishing

            record_path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            fixed += 1
            print(f"  {record['identity']['id']}: set content_quality_status = assessed")

    print(f"\nTotal: fixed {fixed} records")


if __name__ == "__main__":
    main()
