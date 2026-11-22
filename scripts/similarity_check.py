#!/usr/bin/env python3
"""Similarity checker for ToolNest pages.

Uses 5-gram shingle Jaccard similarity to detect duplicate content
across same-type pages.

Usage:
    python3 scripts/similarity_check.py
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

JACCARD_THRESHOLD = 0.30
SENTENCE_THRESHOLD = 0.15


def extract_text(content: str) -> str:
    """Extract text content from HTML, stripping tags."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def shingles(text: str, n: int = 5) -> set[str]:
    """Generate n-gram shingles from text."""
    words = re.findall(r"\b\w+\b", text.lower())
    return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}


def jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def sentence_similarity(text1: str, text2: str) -> float:
    """Calculate shared sentence ratio."""
    sents1 = set(s.strip().lower() for s in re.split(r"[.!?]+", text1) if len(s.strip()) > 20)
    sents2 = set(s.strip().lower() for s in re.split(r"[.!?]+", text2) if len(s.strip()) > 20)
    if not sents1 or not sents2:
        return 0.0
    shared = len(sents1 & sents2)
    total = len(sents1 | sents2)
    return shared / total if total > 0 else 0.0


def get_page_type(path: Path) -> str:
    """Get page type from path."""
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("tools/"):
        return "tool"
    elif rel.startswith("compare/"):
        return "compare"
    elif rel.startswith("alternatives/"):
        return "alternatives"
    elif rel.startswith("best/"):
        return "best"
    elif rel.startswith("category/"):
        return "category"
    elif rel.startswith("goals/"):
        return "goals"
    return "other"


def main() -> None:
    # Collect pages by type
    pages_by_type: dict[str, list[tuple[str, str]]] = {}
    html_files = list(ROOT.rglob("*.html"))
    html_files = [
        p for p in html_files
        if ".git" not in p.parts
        and p.relative_to(ROOT).as_posix() not in {"404.html", "googlef7f3d54afb5d5344.html"}
    ]

    for path in html_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        text = extract_text(content)
        rel = path.relative_to(ROOT).as_posix()
        ptype = get_page_type(path)
        if ptype not in pages_by_type:
            pages_by_type[ptype] = []
        pages_by_type[ptype].append((rel, text))

    # Check similarity within each type
    all_pairs = []
    max_similarity = 0.0
    max_pair = ("", "")

    for ptype, pages in pages_by_type.items():
        if len(pages) < 2:
            continue
        # Compute shingles for all pages
        page_shingles = []
        for rel, text in pages:
            sh = shingles(text)
            page_shingles.append((rel, sh, text))

        # Compare pairs
        for i in range(len(page_shingles)):
            for j in range(i + 1, len(page_shingles)):
                rel1, sh1, text1 = page_shingles[i]
                rel2, sh2, text2 = page_shingles[j]
                jac = jaccard_similarity(sh1, sh2)
                sent = sentence_similarity(text1, text2)
                if jac > max_similarity:
                    max_similarity = jac
                    max_pair = (rel1, rel2)
                if jac > JACCARD_THRESHOLD or sent > SENTENCE_THRESHOLD:
                    all_pairs.append({
                        "type": ptype,
                        "page1": rel1,
                        "page2": rel2,
                        "jaccard": round(jac, 4),
                        "shared_sentences": round(sent, 4),
                    })

    # Write CSV report
    csv_path = REPORTS_DIR / "similarity.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["type", "page1", "page2", "jaccard", "shared_sentences"])
        writer.writeheader()
        writer.writerows(all_pairs)

    # Print summary
    print(f"Similarity check complete")
    print(f"Pages checked: {len(html_files)}")
    print(f"Types: {', '.join(sorted(pages_by_type.keys()))}")
    print(f"Flagged pairs: {len(all_pairs)}")
    print(f"Max Jaccard: {max_similarity:.4f} ({max_pair[0][:40]} vs {max_pair[1][:40]})")
    print()

    if all_pairs:
        print("=== FLAGGED PAIRS ===")
        for pair in all_pairs[:10]:
            print(f"  [{pair['type']}] {pair['page1'][:40]} vs {pair['page2'][:40]}")
            print(f"    Jaccard: {pair['jaccard']}, Shared sentences: {pair['shared_sentences']}")
        if len(all_pairs) > 10:
            print(f"  ... and {len(all_pairs) - 10} more")
        print()
        print("FAIL: Similarity threshold exceeded")
        sys.exit(1)
    else:
        print("PASS: No similarity issues")
        sys.exit(0)


if __name__ == "__main__":
    main()
