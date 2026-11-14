#!/usr/bin/env python3
"""Build explainable AI Stack Builder candidates from structured records."""

from __future__ import annotations

import argparse
import json
import re

from decision_graph_common import ROOT, load_json, load_records

REQUIREMENTS_PATH = ROOT / "data" / "stack" / "stack-builder-v1.json"
TOKEN_RE = re.compile(r"[a-z0-9]+")


def build_stack(requirement_id, records=None, requirements=None):
    records = records if records is not None else load_records()
    requirements = requirements if requirements is not None else load_json(REQUIREMENTS_PATH)["requirements"]
    requirement = next((item for item in requirements if item["id"] == requirement_id), None)
    if requirement is None:
        raise ValueError(f"unknown stack requirement: {requirement_id}")
    signals = set(TOKEN_RE.findall(" ".join(requirement["signals"])))
    categories = set(requirement["preferred_categories"])
    ranked = []
    for record in records:
        discovery = record["discovery"]
        haystack = set(
            TOKEN_RE.findall(
                " ".join(
                    discovery.get("categories", [])
                    + discovery.get("tags", [])
                    + discovery.get("use_cases", [])
                )
            )
        )
        score = len(signals & haystack)
        if discovery.get("categories", []) and categories.intersection(discovery["categories"]):
            score += 2
        if score:
            ranked.append(
                {
                    "tool_id": record["identity"]["id"],
                    "name": record["identity"]["name"],
                    "score": score,
                    "editorial_tier": record["editorial"]["editorial_tier"],
                    "indexability": record["publishing"]["indexability"],
                }
            )
    ranked.sort(key=lambda item: (-item["score"], item["editorial_tier"], item["name"].lower()))
    return {
        "requirement_id": requirement_id,
        "tools": ranked[: requirement["max_tools"]],
        "explanation": "Matches are based only on structured discovery fields; no popularity, rating, or affiliate signal is used.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("requirement_id")
    args = parser.parse_args()
    print(json.dumps(build_stack(args.requirement_id), indent=2))


if __name__ == "__main__":
    main()
