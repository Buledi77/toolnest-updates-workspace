#!/usr/bin/env python3
"""Provide deterministic task-first recommendations from the structured catalog."""

from __future__ import annotations

import argparse
import json
import re

from decision_graph_common import ROOT, load_json, load_records

TASK_PATH = ROOT / "data" / "recommendations" / "task-catalog.json"
TOKEN_RE = re.compile(r"[a-z0-9]+")


def recommend(query, records=None, tasks=None):
    records = records if records is not None else load_records()
    tasks = tasks if tasks is not None else load_json(TASK_PATH)["tasks"]
    query_tokens = set(TOKEN_RE.findall(query.lower()))
    record_map = {record["identity"]["id"]: record for record in records}
    recommendations = []
    for task in tasks:
        signal_tokens = set(TOKEN_RE.findall(" ".join(task["required_signals"])))
        score = len(query_tokens & signal_tokens)
        if task["label"].lower() in query.lower():
            score += 3
        if score == 0:
            continue
        candidates = [
            record_map[tool_id]
            for tool_id in task["tool_ids"]
            if tool_id in record_map
        ]
        candidates.sort(
            key=lambda record: (
                record["editorial"]["editorial_tier"],
                record["identity"]["name"].lower(),
            )
        )
        recommendations.append(
            {
                "task_id": task["id"],
                "label": task["label"],
                "guide": task["guide"],
                "score": score,
                "tool_ids": [record["identity"]["id"] for record in candidates],
            }
        )
    return sorted(recommendations, key=lambda item: (-item["score"], item["task_id"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    args = parser.parse_args()
    print(json.dumps(recommend(args.query), indent=2))


if __name__ == "__main__":
    main()
