#!/usr/bin/env python3
"""Pure structured directory adapter for future public-consumer parity work."""

from __future__ import annotations

import re

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(value):
    return TOKEN_RE.findall(str(value).lower())


def search(records, query):
    words = _tokens(query)
    if not words:
        return list(records)
    ranked = []
    for record in records:
        identity = record["identity"]
        discovery = record["discovery"]
        haystack = _tokens(
            " ".join(
                [
                    identity["name"],
                    *identity.get("aliases", []),
                    *discovery.get("categories", []),
                    *discovery.get("use_cases", []),
                    *discovery.get("tags", []),
                ]
            )
        )
        if not all(word in haystack for word in words):
            continue
        score = sum(word in _tokens(identity["name"]) for word in words) * 10
        ranked.append((score, identity["name"].lower(), record))
    return [item[2] for item in sorted(ranked, key=lambda item: (-item[0], item[1]))]


def query(records, *, text="", category=None, sort="relevance", page=1, per_page=20):
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be positive")
    filtered = list(records)
    if category:
        filtered = [
            record
            for record in filtered
            if category in record["discovery"].get("categories", [])
        ]
    filtered = search(filtered, text)
    if sort == "name":
        filtered.sort(key=lambda record: record["identity"]["name"].lower())
    elif sort == "tier":
        filtered.sort(
            key=lambda record: (
                record["editorial"]["editorial_tier"],
                record["identity"]["name"].lower(),
            )
        )
    elif sort != "relevance":
        raise ValueError(f"unsupported sort: {sort}")
    start = (page - 1) * per_page
    return {
        "items": filtered[start : start + per_page],
        "total": len(filtered),
        "page": page,
        "per_page": per_page,
        "pages": max(1, (len(filtered) + per_page - 1) // per_page),
    }


def public_page_candidates(records):
    """Return only records explicitly eligible for a future public page."""
    return [
        record
        for record in records
        if record["publishing"]["indexability"] == "index"
        and record["publishing"]["sitemap_eligible"] is True
    ]
