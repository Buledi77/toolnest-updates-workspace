#!/usr/bin/env python3
"""Enforce Tier and indexability rules before future page generation."""

from decision_graph_common import load_records, print_result


def validate_publishability():
    errors = []
    for record in load_records():
        record_id = record["identity"]["id"]
        tier = record["editorial"]["editorial_tier"]
        publishing = record["publishing"]
        quality = publishing["content_quality_status"]
        if tier == "C" and publishing["indexability"] == "index":
            errors.append(f"{record_id}: Tier C cannot be indexable")
        if tier == "C" and publishing["sitemap_eligible"]:
            errors.append(f"{record_id}: Tier C cannot be sitemap eligible")
        if publishing["indexability"] == "index" and not publishing.get("canonical_url"):
            errors.append(f"{record_id}: indexable record has no canonical")
        if publishing["sitemap_eligible"] and publishing["indexability"] != "index":
            errors.append(f"{record_id}: sitemap record is not indexable")
        if publishing["indexability"] == "index" and quality not in {"approved", "improving"}:
            errors.append(f"{record_id}: indexable record has quality status {quality}")
        if publishing["prepublish_status"] == "published" and tier == "C":
            errors.append(f"{record_id}: Tier C cannot be marked published")
    return errors


if __name__ == "__main__":
    raise SystemExit(print_result("Publishability validation", validate_publishability()))
