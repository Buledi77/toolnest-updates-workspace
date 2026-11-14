#!/usr/bin/env python3
"""Create a non-publishing Decision Graph shadow migration from data/tools.json."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from decision_graph_common import ROOT, load_json

LEGACY_PATH = ROOT / "data" / "tools.json"
V2_PATH = ROOT / "data" / "tools-v2"
LEGACY_OUTPUT = ROOT / "data" / "tools-v2" / "legacy"
MAPPING_PATH = ROOT / "data" / "migrations" / "legacy-to-v2-map.json"
BENCHMARK_IDS = {"hostinger", "semrush", "moz-pro"}


def v2_id(legacy_id):
    return "moz-pro" if legacy_id == "mozpro" else legacy_id


def make_record(tool):
    legacy_id = tool["id"]
    record_id = v2_id(legacy_id)
    affiliate_url = tool.get("affiliateUrl") or None
    return {
        "$schema": "https://www.toolnestai.tech/schemas/toolnest-tool-v1.json",
        "schema_version": "toolnest-tool-v1",
        "identity": {
            "id": record_id,
            "name": tool["name"],
            "slug": record_id,
            "official_url": tool["site"],
            "status": "unknown",
            "logo": tool.get("logo"),
            "aliases": []
        },
        "discovery": {
            "categories": [tool["cat"]] if tool.get("cat") else [],
            "use_cases": [],
            "audiences": [],
            "platforms": [],
            "integrations": [],
            "tags": []
        },
        "factual_profile": {
            "capabilities": [],
            "limitations": [],
            "free_plan_status": [],
            "trial_status": [],
            "pricing_status": [],
            "pricing_regions": [],
            "availability_regions": []
        },
        "editorial": {
            "editorial_tier": "C",
            "best_for": [],
            "not_recommended_for": [],
            "review_status": "draft",
            "review_url": None,
            "review_owner": None,
            "editorial_last_reviewed": None
        },
        "relationships": {
            "alternatives": [],
            "meaningful_comparisons": [],
            "related_tools": [],
            "compatible_tools": [],
            "replaces": [],
            "replaced_by": []
        },
        "evidence": {
            "claim_refs": [],
            "source_ids": []
        },
        "monetization": {
            "affiliate_status": "needs_review" if affiliate_url else "unknown",
            "affiliate_network": None,
            "affiliate_url": affiliate_url,
            "official_non_affiliate_url": tool["site"],
            "approved_regions": [],
            "restrictions": [],
            "disclosure_required": True if affiliate_url else None,
            "last_link_check": None
        },
        "publishing": {
            "directory_visibility": "public",
            "standalone_page_status": "none",
            "indexability": "noindex",
            "sitemap_eligible": False,
            "canonical_url": None,
            "template_type": "directory-only",
            "content_quality_status": "unassessed",
            "prepublish_status": "not_ready"
        },
        "freshness": {
            "created_at": None,
            "updated_at": None,
            "last_verified_at": None,
            "next_review_at": None,
            "stale_fields": [
                "identity.status",
                "discovery",
                "factual_profile",
                "relationships",
                "monetization"
            ],
            "change_history_reference": None
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--as-of",
        default=date.today().isoformat(),
        help="Generation date recorded in the migration manifest",
    )
    args = parser.parse_args()
    source = load_json(LEGACY_PATH)
    existing = {
        record["identity"]["id"]: path
        for path in V2_PATH.glob("*.json")
        if path.name not in {"README.json"}
        for record in [load_json(path)]
    }
    LEGACY_OUTPUT.mkdir(parents=True, exist_ok=True)
    MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
    mapping = []
    generated = []
    for tool in source.get("tools", []):
        legacy_id = tool["id"]
        record_id = v2_id(legacy_id)
        entry = {
            "legacy_id": legacy_id,
            "v2_id": record_id,
            "source_fields": [
                "id",
                "name",
                "cat",
                "h",
                "site",
                "badge",
                "featured",
                "best",
                "pros",
                "logo",
                "affiliateUrl"
            ],
            "legacy_editorial_draft": {
                "badge": tool.get("badge", ""),
                "featured": tool.get("featured", False),
                "best": tool.get("best", ""),
                "pros": tool.get("pros", [])
            },
            "presentation_hue": tool.get("h"),
            "affiliate_present": bool(tool.get("affiliateUrl")),
            "migration_status": "benchmark_record_preserved"
            if record_id in BENCHMARK_IDS
            else "tier_c_shadow_record"
        }
        if record_id in BENCHMARK_IDS:
            entry["record_path"] = str(
                Path("data") / "tools-v2" / f"{record_id}.json"
            )
        else:
            output_path = LEGACY_OUTPUT / f"{record_id}.json"
            output_path.write_text(
                json.dumps(make_record(tool), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            generated.append(str(output_path.relative_to(ROOT)))
            entry["record_path"] = str(output_path.relative_to(ROOT))
        mapping.append(entry)
    manifest = {
        "schema_version": "legacy-to-v2-map-v1",
        "generated_at": args.as_of,
        "source_path": "data/tools.json",
        "source_count": len(source.get("tools", [])),
        "benchmark_records_preserved": sorted(BENCHMARK_IDS),
        "generated_shadow_record_count": len(generated),
        "records": mapping
    }
    MAPPING_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"migrated {len(mapping)} legacy records")
    print(f"generated {len(generated)} Tier C shadow records")
    print(f"preserved {len(BENCHMARK_IDS)} benchmark records")
    print(f"wrote {MAPPING_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
