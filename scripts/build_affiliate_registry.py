#!/usr/bin/env python3
"""Build a centralized affiliate registry without changing public destinations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from decision_graph_common import ROOT, load_records

OUTPUT = ROOT / "data" / "monetization" / "affiliate-registry.json"


def build(records):
    entries = []
    for record in records:
        identity = record["identity"]
        monetization = record["monetization"]
        entries.append(
            {
                "tool_id": identity["id"],
                "official_non_affiliate_url": monetization["official_non_affiliate_url"],
                "affiliate_status": monetization["affiliate_status"],
                "affiliate_network": monetization.get("affiliate_network"),
                "affiliate_url": monetization.get("affiliate_url"),
                "approved_regions": monetization.get("approved_regions", []),
                "restrictions": monetization.get("restrictions", []),
                "disclosure_required": monetization.get("disclosure_required"),
                "last_link_check": monetization.get("last_link_check"),
            }
        )
    return {
        "schema_version": "toolnest-affiliate-registry-v1",
        "editorial_independence": True,
        "entries": sorted(entries, key=lambda item: item["tool_id"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    registry = build(load_records())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(registry['entries'])} affiliate entries")


if __name__ == "__main__":
    main()
