#!/usr/bin/env python3
"""Check stable IDs, official domains, and controlled discovery values."""

from urllib.parse import urlparse

from decision_graph_common import ROOT, load_json, load_records, print_result

TAXONOMY_PATH = ROOT / "data" / "taxonomy" / "taxonomy-v1.json"


def validate():
    taxonomy = load_json(TAXONOMY_PATH)
    allowed_categories = {item["label"] for item in taxonomy.get("categories", [])}
    allowed_platforms = set(taxonomy.get("controlled_values", {}).get("platforms", []))
    records = load_records()
    errors = []
    ids = set()
    slugs = set()
    domains = {}
    for record in records:
        identity = record["identity"]
        record_id = identity["id"]
        if record_id in ids:
            errors.append(f"duplicate record ID {record_id}")
        ids.add(record_id)
        slug = identity["slug"]
        if slug in slugs:
            errors.append(f"duplicate record slug {slug}")
        slugs.add(slug)
        domain = urlparse(identity["official_url"]).netloc.lower().removeprefix("www.")
        if domain in domains and domains[domain] != record_id:
            errors.append(f"official domain {domain} is shared by {domains[domain]} and {record_id}")
        domains[domain] = record_id
        for category in record["discovery"].get("categories", []):
            if category not in allowed_categories:
                errors.append(f"{record_id}: unknown category {category}")
        for platform in record["discovery"].get("platforms", []):
            if platform not in allowed_platforms:
                errors.append(f"{record_id}: unknown platform {platform}")
    return errors


if __name__ == "__main__":
    raise SystemExit(print_result("Catalog integrity validation", validate()))
