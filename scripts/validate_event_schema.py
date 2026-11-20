#!/usr/bin/env python3
"""
Privacy-Safe Event Attribute Schema — normalizes data attributes for future analytics.

This script validates that all event data attributes follow the consistent schema:
  data-page     — page type (tool, comparison, alternatives, best, directory, overlap, workflow)
  data-tool     — tool ID (e.g., "elevenlabs")
  data-pos      — position on page (hero, bottom, dock, result, card)
  data-context  — optional additional context

Event types tracked:
  - tool_visit        — visiting a tool review page
  - affiliate_visit   — clicking an affiliate CTA
  - review_open       — opening a review page
  - comparison_open   — opening a comparison page
  - alternative_open  — opening an alternatives page
  - overlap_completed — completing an overlap check
  - overlap_swap      — swapping tools in overlap checker
  - overlap_reset     — resetting overlap checker
  - workflow_selected  — selecting a workflow
  - workflow_changed   — changing workflow parameters
  - workflow_reset     — resetting workflow explorer

Privacy constraints:
  - No personal data
  - No emails
  - No user IDs
  - No fingerprints
  - No cookies
  - No credentials

Usage:
  python3 scripts/validate_event_schema.py
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Valid event attribute values — matches existing site usage
VALID_DATA_PAGE = {
    "tool", "comparison", "compare", "alternatives", "best", "directory",
    "overlap", "workflow", "category", "homepage", "goal",
}
VALID_DATA_POS = {
    "hero", "bottom", "dock", "result", "card", "list", "filter",
    # Ranking positions in Best pages
    "rank-1", "rank-2", "rank-3", "rank-4", "rank-5", "rank-6",
    "rank-7", "rank-8", "rank-9", "rank-10",
    # Pick positions
    "pick-1", "pick-2", "pick-3", "pick-4", "pick-5", "pick-6",
    # Comparison positions
    "hero-a", "hero-b", "choose-a", "choose-b", "sidebar-a", "sidebar-b",
    # Other positions
    "sidebar", "category", "quick-answer", "mid", "option",
    "step-1", "step-2", "step-3", "step-4", "step-5",
    # Custom positions
    "hosting-review",
}
VALID_DATA_CONTEXT = {
    "tool", "comparison", "alternatives", "best", "directory",
    "overlap", "workflow", "category", "goal",
}

# Pattern for valid tool IDs
TOOL_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class EventAttributeParser(HTMLParser):
    """Parse HTML for data-* event attributes."""

    def __init__(self) -> None:
        super().__init__()
        self.event_elements: list[dict] = []
        self._current_element: dict = {}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        data_attrs = {
            k: v for k, v in attrs_dict.items()
            if k.startswith("data-")
        }
        if data_attrs:
            self.event_elements.append({
                "tag": tag,
                "attrs": data_attrs,
                "line": self.getpos()[0],
            })


def validate_event_attributes(
    elements: list[dict],
    page_path: str,
) -> list[str]:
    """Validate event attributes against the schema."""
    errors: list[str] = []

    for elem in elements:
        attrs = elem["attrs"]
        line = elem["line"]

        # Check data-page
        data_page = attrs.get("data-page")
        if data_page:
            if data_page not in VALID_DATA_PAGE:
                errors.append(
                    f"{page_path}:{line} — invalid data-page '{data_page}' "
                    f"(allowed: {sorted(VALID_DATA_PAGE)})"
                )

        # Check data-tool
        data_tool = attrs.get("data-tool")
        if data_tool:
            if not TOOL_ID_PATTERN.fullmatch(data_tool):
                errors.append(
                    f"{page_path}:{line} — invalid data-tool '{data_tool}' "
                    f"(must be lowercase alphanumeric with hyphens)"
                )

        # Check data-pos
        data_pos = attrs.get("data-pos")
        if data_pos:
            if data_pos not in VALID_DATA_POS:
                errors.append(
                    f"{page_path}:{line} — invalid data-pos '{data_pos}' "
                    f"(allowed: {sorted(VALID_DATA_POS)})"
                )

        # Check data-context
        data_context = attrs.get("data-context")
        if data_context:
            if data_context not in VALID_DATA_CONTEXT:
                errors.append(
                    f"{page_path}:{line} — invalid data-context '{data_context}' "
                    f"(allowed: {sorted(VALID_DATA_CONTEXT)})"
                )

        # Check consistency: if data-page exists, data-tool should too for tool pages
        if data_page == "tool" and not data_tool:
            errors.append(
                f"{page_path}:{line} — data-page='tool' without data-tool"
            )

    return errors


def check_privacy_compliance(content: str, page_path: str) -> list[str]:
    """Check that no personal data patterns appear in data attributes."""
    errors: list[str] = []

    # Check for email patterns in data attributes
    email_pattern = re.compile(
        r'data-\w+\s*=\s*["\'][\w.+-]+@[\w.-]+\.\w+["\']',
        re.IGNORECASE,
    )
    if email_pattern.search(content):
        errors.append(
            f"{page_path} — possible email address in data attribute"
        )

    # Check for obvious PII patterns
    pii_patterns = [
        (r'data-\w+\s*=\s*["\']\d{3}-\d{2}-\d{4}["\']', "SSN-like pattern"),
        (r'data-\w+\s*=\s*["\']\d{10,}["\']', "long numeric ID"),
    ]
    for pattern, description in pii_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            errors.append(
                f"{page_path} — possible {description} in data attribute"
            )

    return errors


def run_validation(html_paths: list[Path] | None = None) -> list[str]:
    """Run the full event schema validation."""
    errors: list[str] = []

    if html_paths is None:
        html_paths = sorted(ROOT.rglob("*.html"))

    for path in html_paths:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        parser = EventAttributeParser()
        parser.feed(content)

        relative = path.relative_to(ROOT).as_posix()

        # Validate event attributes
        errors.extend(validate_event_attributes(parser.event_elements, relative))

        # Check privacy compliance
        errors.extend(check_privacy_compliance(content, relative))

    return errors


def generate_schema_doc() -> str:
    """Generate the event schema documentation."""
    doc = """# ToolNest Event Attribute Schema

## Overview
Privacy-safe data attributes for future analytics on meaningful user actions.

## Attributes

| Attribute | Description | Example Values |
|-----------|-------------|----------------|
| data-page | Page type | tool, comparison, alternatives, best, directory, overlap, workflow |
| data-tool | Tool ID | elevenlabs, chatgpt, claude |
| data-pos | Position on page | hero, bottom, dock, result, card |
| data-context | Additional context | tool, comparison, alternatives |

## Event Types

| Event | Description |
|-------|-------------|
| tool_visit | Visiting a tool review page |
| affiliate_visit | Clicking an affiliate CTA |
| review_open | Opening a review page |
| comparison_open | Opening a comparison page |
| alternative_open | Opening an alternatives page |
| overlap_completed | Completing an overlap check |
| overlap_swap | Swapping tools in overlap checker |
| overlap_reset | Resetting overlap checker |
| workflow_selected | Selecting a workflow |
| workflow_changed | Changing workflow parameters |
| workflow_reset | Resetting workflow explorer |

## Privacy Constraints
- No personal data
- No emails
- No user IDs
- No fingerprints
- No cookies
- No credentials

## Implementation
Data attributes are placed on interactive elements (buttons, links) that represent
meaningful user actions. They are passive markers — no JavaScript tracking is
installed. Future analytics can read these attributes when needed.
"""
    return doc


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Event Attribute Schema for ToolNest"
    )
    parser.add_argument(
        "--doc",
        action="store_true",
        help="Print the event schema documentation",
    )
    args = parser.parse_args()

    if args.doc:
        print(generate_schema_doc())
        return 0

    errors = run_validation()

    if errors:
        print(f"Event Schema Validation: FAIL ({len(errors)} issue(s))")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Event Schema Validation: PASS")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
