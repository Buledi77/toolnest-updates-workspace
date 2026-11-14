#!/usr/bin/env python3
"""Verify and ingest a bounded catalog batch as non-publishing Tier C records."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from decision_graph_common import ROOT, is_url, load_json, load_records, print_result

INTAKE_PATH = ROOT / "data" / "intake" / "catalog-expansion-v1.json"
OUTPUT_DIR = ROOT / "data" / "tools-v2" / "expansion"


def verify_url(url):
    request = Request(url, method="HEAD", headers={"User-Agent": "ToolNestCatalogVerifier/1.0"})
    try:
        with urlopen(request, timeout=15) as response:
            return response.status
    except HTTPError as exc:
        return exc.code
    except URLError:
        request = Request(url, headers={"User-Agent": "ToolNestCatalogVerifier/1.0"})
        try:
            with urlopen(request, timeout=15) as response:
                return response.status
        except HTTPError as exc:
            return exc.code
        except URLError:
            return None


def validate_candidates(candidates, existing_ids, check_network=True):
    errors = []
    seen = set(existing_ids)
    verified = {}
    for candidate in candidates:
        candidate_id = candidate.get("id")
        if not candidate_id or candidate_id in seen:
            errors.append(f"{candidate_id or '<missing>'}: duplicate or missing ID")
            continue
        seen.add(candidate_id)
        if not is_url(candidate.get("official_url")):
            errors.append(f"{candidate_id}: invalid official URL")
            continue
        if not candidate.get("source_note"):
            errors.append(f"{candidate_id}: missing source note")
            continue
        status = verify_url(candidate["official_url"]) if check_network else 200
        if status is None or status >= 500 or status == 404:
            errors.append(f"{candidate_id}: official URL check failed ({status})")
            continue
        verified[candidate_id] = status
    return errors, verified


def make_record(candidate, as_of):
    return {
        "$schema": "https://www.toolnestai.tech/schemas/toolnest-tool-v1.json",
        "schema_version": "toolnest-tool-v1",
        "identity": {
            "id": candidate["id"],
            "name": candidate["name"],
            "slug": candidate["id"],
            "official_url": candidate["official_url"],
            "status": "active",
            "logo": None,
            "aliases": []
        },
        "discovery": {
            "categories": [candidate["category"]],
            "use_cases": [],
            "audiences": [],
            "platforms": ["web"],
            "integrations": [],
            "tags": candidate.get("tags", [])
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
        "evidence": {"claim_refs": [], "source_ids": []},
        "monetization": {
            "affiliate_status": "unknown",
            "affiliate_network": None,
            "affiliate_url": None,
            "official_non_affiliate_url": candidate["official_url"],
            "approved_regions": [],
            "restrictions": [],
            "disclosure_required": None,
            "last_link_check": as_of[:10]
        },
        "publishing": {
            "directory_visibility": "private",
            "standalone_page_status": "none",
            "indexability": "noindex",
            "sitemap_eligible": False,
            "canonical_url": None,
            "template_type": "directory-only",
            "content_quality_status": "unassessed",
            "prepublish_status": "not_ready"
        },
        "freshness": {
            "created_at": as_of,
            "updated_at": as_of,
            "last_verified_at": as_of,
            "next_review_at": None,
            "stale_fields": [
                "factual_profile",
                "editorial",
                "relationships",
                "monetization"
            ],
            "change_history_reference": None
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    intake = load_json(INTAKE_PATH)
    candidate_ids = {candidate.get("id") for candidate in intake.get("candidates", [])}
    existing_ids = {
        record["identity"]["id"]
        for record in load_records()
        if record["identity"]["id"] not in candidate_ids
        or not (OUTPUT_DIR / f"{record['identity']['id']}.json").exists()
    }
    errors, verified = validate_candidates(
        intake.get("candidates", []), existing_ids, check_network=not args.offline
    )
    if errors:
        return print_result("Catalog intake validation", errors)
    if not args.apply:
        print(f"Catalog intake validation: PASS ({len(verified)} candidates)")
        print("Dry run only; use --apply after reviewing the verified batch.")
        return 0
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for candidate in intake["candidates"]:
        path = OUTPUT_DIR / f"{candidate['id']}.json"
        path.write_text(
            json.dumps(make_record(candidate, args.as_of), indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"Catalog intake applied: {len(verified)} Tier C records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
