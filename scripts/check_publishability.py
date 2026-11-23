#!/usr/bin/env python3
"""Enforce Tier and indexability rules before future page generation."""

from decision_graph_common import load_records, print_result


def validate_publishability():
    errors = []
    for record in load_records():
        record_id = record["identity"]["id"]
        tier = record.get("editorial", {}).get("editorial_tier", "C")
        publishing = record.get("publishing", {})
        quality = publishing.get("content_quality_status", "unknown")
        indexability = publishing.get("indexability", "noindex")
        sitemap = publishing.get("sitemap_eligible", False)
        prepublish = publishing.get("prepublish_status", "draft")
        if tier == "C" and indexability == "index":
            errors.append(f"{record_id}: Tier C cannot be indexable")
        if tier == "C" and sitemap:
            errors.append(f"{record_id}: Tier C cannot be sitemap eligible")
        if indexability == "index" and not publishing.get("canonical_url"):
            errors.append(f"{record_id}: indexable record has no canonical")
        if sitemap and indexability != "index":
            errors.append(f"{record_id}: sitemap record is not indexable")
        if indexability == "index" and quality not in {"approved", "improving", "assessed", "adequate", "ready"}:
            errors.append(f"{record_id}: indexable record has quality status {quality}")
        if prepublish == "published" and tier == "C":
            errors.append(f"{record_id}: Tier C cannot be marked published")
    return errors


if __name__ == "__main__":
    raise SystemExit(print_result("Publishability validation", validate_publishability()))
