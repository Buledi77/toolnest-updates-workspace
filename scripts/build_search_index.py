#!/usr/bin/env python3
"""Build a deterministic, non-publishing search index from Decision Graph records."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from decision_graph_common import ROOT, load_records

OUTPUT = ROOT / "data" / "indexes" / "tool-search-index.json"
TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(value):
    return TOKEN_RE.findall(str(value).lower())


def build(records):
    documents = []
    tools_html_dir = ROOT / "tools"
    for record in records:
        identity = record["identity"]
        slug = identity.get("slug", identity["id"])
        # Exclude records whose HTML page does not exist — prevents dead search results
        if not (tools_html_dir / f"{slug}.html").is_file():
            continue
        discovery = record["discovery"]
        factual = record.get("factual_profile") or record.get("overview", {})
        editorial = record["editorial"]
        fields = [
            identity["name"],
            *identity.get("aliases", []),
            *discovery.get("categories", []),
            *discovery.get("use_cases", []),
            *discovery.get("audiences", []),
            *discovery.get("platforms", []),
            *discovery.get("integrations", []),
            *discovery.get("tags", []),
            factual.get("concise_summary", factual.get("tagline", "")),
            factual.get("primary_purpose", factual.get("description", "")),
            editorial.get("editorial_summary", ""),
        ]
        documents.append(
            {
                "id": identity["id"],
                "name": identity["name"],
                "slug": identity["slug"],
                "tokens": sorted(set(tokens(" ".join(fields)))),
                "categories": discovery.get("categories", []),
                "use_cases": discovery.get("use_cases", []),
                "audiences": discovery.get("audiences", []),
                "editorial_tier": editorial["editorial_tier"],
                "indexability": record["publishing"]["indexability"],
                "evidence_age": record["freshness"].get("last_verified_at"),
                "official_url": identity["official_url"],
            }
        )
    return {
        "schema_version": "toolnest-search-index-v1",
        "source": "data/tools-v2",
        "documents": sorted(documents, key=lambda item: item["id"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    index = build(load_records())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"indexed {len(index['documents'])} records")
    print(f"wrote {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
