#!/usr/bin/env python3
"""Extract main-content metrics used by the static-site indexability gate."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

WORD_RE = re.compile(r"\b[\w'-]+\b")
EXCLUDED_TAGS = {"header", "nav", "footer", "script", "style", "aside"}
EXCLUDED_MARKERS = {
    "related",
    "newsletter",
    "subscribe",
    "tn-ecosystem",
    "tn-complete-map",
}
UNIQUE_MARKERS = (
    "verdict",
    "quick answer",
    "who should skip",
    "skip ",
    "not for",
    "pricing",
    "price",
    "cost",
    "plans",
    "billing",
    "hands-on",
    "hands on",
    "tested",
    "testing",
)


@dataclass
class Section:
    identifier: str
    text: str = ""

    @property
    def fingerprint(self) -> str:
        return " ".join(self.text.split()).lower()

    @property
    def has_unique_marker(self) -> bool:
        text = self.fingerprint
        return any(marker in text for marker in UNIQUE_MARKERS)


@dataclass
class ContentMetrics:
    words: int
    sections: list[Section] = field(default_factory=list)

    @property
    def marked_fingerprints(self) -> set[str]:
        return {
            section.fingerprint
            for section in self.sections
            if section.has_unique_marker and len(section.fingerprint) >= 40
        }


class MainContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.main_depth = 0
        self.excluded_depth = 0
        self.excluded_tags: list[str] = []
        self.sections: list[Section] = []
        self.section_stack: list[Section] = []
        self.words: list[str] = []

    @staticmethod
    def is_excluded(attrs: dict[str, str | None]) -> bool:
        values = " ".join(
            value or "" for key, value in attrs.items() if key in {"id", "class"}
        ).lower()
        return any(marker in values for marker in EXCLUDED_MARKERS)

    def handle_starttag(self, tag: str, attrs_list) -> None:
        attrs = dict(attrs_list)
        if tag == "main":
            self.main_depth += 1
        if self.main_depth and (tag in EXCLUDED_TAGS or self.is_excluded(attrs)):
            self.excluded_depth += 1
            self.excluded_tags.append(tag)
            return
        if self.main_depth and not self.excluded_depth and tag == "section":
            section = Section(attrs.get("id") or attrs.get("class") or "section")
            self.sections.append(section)
            self.section_stack.append(section)

    def handle_endtag(self, tag: str) -> None:
        if self.main_depth and self.excluded_tags and tag == self.excluded_tags[-1]:
            self.excluded_tags.pop()
            self.excluded_depth -= 1
            return
        if tag == "section" and self.section_stack:
            self.section_stack.pop()
        if tag == "main":
            self.main_depth = max(0, self.main_depth - 1)

    def handle_data(self, data: str) -> None:
        if self.main_depth and not self.excluded_depth:
            self.words.extend(WORD_RE.findall(data))
            for section in self.section_stack:
                section.text += f" {data}"


def measure(content: str) -> ContentMetrics:
    parser = MainContentParser()
    parser.feed(content)
    return ContentMetrics(words=len(parser.words), sections=parser.sections)


def unique_marked_sections(metrics_by_page: dict[str, ContentMetrics]) -> dict[str, set[str]]:
    fingerprints = Counter(
        fingerprint
        for metrics in metrics_by_page.values()
        for fingerprint in metrics.marked_fingerprints
    )
    return {
        page: {
            fingerprint
            for fingerprint in metrics.marked_fingerprints
            if fingerprints[fingerprint] == 1
        }
        for page, metrics in metrics_by_page.items()
    }


def section_name(path: Path) -> str:
    parts = path.parts
    if len(parts) == 1:
        return "root"
    return parts[0]


def page_route(relative: str) -> str:
    return "/" if relative == "index.html" else f"/{relative}"
