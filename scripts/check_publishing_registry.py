#!/usr/bin/env python3
"""Validate page-intent uniqueness and alignment with protected benchmark URLs."""

from decision_graph_common import ROOT, load_json, load_records, is_url, print_result
import re

INTENT_PATH = ROOT / "data" / "publishing" / "page-intents.json"
SITEMAP_PATH = ROOT / "sitemap.xml"


def validate_registry():
    registry = load_json(INTENT_PATH)
    records = {record["identity"]["id"]: record for record in load_records()}
    errors = []
    sitemap_text = SITEMAP_PATH.read_text(encoding="utf-8")
    sitemap_urls = set(re.findall(r"<loc>([^<]+)</loc>", sitemap_text))
    paths = []
    canonicals = []
    for intent in registry.get("intents", []):
        intent_id = intent.get("intent_id")
        tool_id = intent.get("tool_id")
        path = intent.get("path")
        canonical = intent.get("canonical_url")
        if tool_id not in records:
            errors.append(f"{intent_id}: missing tool {tool_id}")
        if not path or not path.startswith("/"):
            errors.append(f"{intent_id}: invalid path")
        if not is_url(canonical):
            errors.append(f"{intent_id}: invalid canonical")
        if intent.get("status") == "published" and canonical not in sitemap_urls:
            errors.append(f"{intent_id}: published canonical is absent from sitemap")
        paths.append(path)
        canonicals.append(canonical)
        if (
            tool_id in records
            and intent.get("status") == "published"
            and intent.get("template_type") == "premium-review"
        ):
            publishing = records[tool_id]["publishing"]
            if publishing["indexability"] != "index":
                errors.append(f"{intent_id}: published intent is not indexable")
            if publishing.get("canonical_url") and publishing["canonical_url"] != canonical:
                errors.append(f"{intent_id}: canonical differs from tool record")
    if len(paths) != len(set(paths)):
        errors.append("page-intent paths are duplicated")
    if len(canonicals) != len(set(canonicals)):
        errors.append("page-intent canonicals are duplicated")
    return errors


if __name__ == "__main__":
    raise SystemExit(print_result("Publishing registry validation", validate_registry()))
