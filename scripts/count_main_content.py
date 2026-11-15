#!/usr/bin/env python3
"""Print main-content word counts and unique-section eligibility markers."""

from __future__ import annotations

import sys
from pathlib import Path

from content_metrics import measure, section_name, unique_marked_sections

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"404.html", "googlef7f3d54afb5d5344.html"}


def main() -> int:
    metrics = {}
    for path in sorted(ROOT.rglob("*.html")):
        relative = path.relative_to(ROOT)
        if relative.as_posix() in SKIP:
            continue
        metrics[relative.as_posix()] = measure(path.read_text(encoding="utf-8"))
    unique = unique_marked_sections(metrics)
    print("words\tunique-section\tsection\tpath")
    for path, item in metrics.items():
        print(
            f"{item.words}\t{'yes' if unique[path] else 'no'}\t"
            f"{section_name(Path(path))}\t{path}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
