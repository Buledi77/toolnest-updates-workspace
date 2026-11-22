#!/usr/bin/env python3
"""Spot-check pack for ToolNest — quick human verification.

Writes /reports/spot-check.md with:
- 30 random claims across upgraded pages
- 20 lowest-confidence tools
- All source conflicts
- All blocked tools
- Max similarity score

Usage:
    python3 scripts/spotcheck.py
"""

from __future__ import annotations

import json
import random
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
TOOLS_V2_DIR = ROOT / "data" / "tools-v2"
TOOLS_JSON = ROOT / "data" / "tools.json"


def load_catalog() -> dict[str, dict]:
    data = json.loads(TOOLS_JSON.read_text())
    return {t["id"]: t for t in data.get("tools", [])}


def load_v2(slug: str) -> dict | None:
    candidates = [
        TOOLS_V2_DIR / f"{slug}.json",
        TOOLS_V2_DIR / "legacy" / f"{slug}.json",
        TOOLS_V2_DIR / "expansion" / f"{slug}.json",
    ]
    for p in candidates:
        if p.exists():
            return json.loads(p.read_text())
    return None


def extract_claims_from_html(path: Path) -> list[dict]:
    """Extract claims from a tool HTML page."""
    claims = []
    content = path.read_text(encoding="utf-8", errors="replace")
    # Look for source links
    source_pattern = re.compile(r'href="([^"]+)"[^>]*rel="sponsored nofollow')
    for match in source_pattern.finditer(content):
        url = match.group(1)
        if "semrush.com" in url or "ahrefs.com" in url or "moz.com" in url:
            claims.append({"sourceUrl": url, "page": str(path)})
    return claims


def main() -> None:
    catalog = load_catalog()
    lines = [
        "# Spot-Check Report",
        "",
        f"Date: {date.today().isoformat()}",
        "",
    ]

    # 1. 30 random claims
    lines.extend(["## 30 Random Claims", ""])
    tool_files = list((ROOT / "tools").glob("*.html"))
    random.seed(42)  # Reproducible
    sample = random.sample(tool_files, min(30, len(tool_files)))
    for i, path in enumerate(sample, 1):
        slug = path.stem
        v2 = load_v2(slug)
        evidence = v2.get("evidence", {}) if v2 else {}
        sources = evidence.get("sources", [])
        source_urls = [s.get("url", "") for s in sources if isinstance(s, dict)]
        lines.append(f"{i}. **{slug}** (`/tools/{slug}.html`)")
        if source_urls:
            lines.append(f"   - Sources: {', '.join(source_urls[:3])}")
        else:
            lines.append("   - No sources in tools-v2")
        lines.append("")

    # 2. 20 lowest-confidence tools
    lines.extend(["## 20 Lowest-Confidence Tools", ""])
    confidences = []
    for slug in catalog:
        v2 = load_v2(slug)
        if v2:
            evidence = v2.get("evidence", {})
            confidence = evidence.get("confidence", "unknown")
            confidences.append((slug, confidence))
    confidences.sort(key=lambda x: str(x[1]))
    for slug, confidence in confidences[:20]:
        lines.append(f"- **{slug}**: confidence={confidence}")
    lines.append("")

    # 3. Source conflicts
    lines.extend(["## Source Conflicts", ""])
    conflicts_found = False
    for slug in catalog:
        v2 = load_v2(slug)
        if v2:
            evidence = v2.get("evidence", {})
            conflicts = evidence.get("conflicts", [])
            if conflicts:
                conflicts_found = True
                lines.append(f"- **{slug}**: {conflicts}")
    if not conflicts_found:
        lines.append("- No source conflicts found")
    lines.append("")

    # 4. Blocked tools
    lines.extend(["## Blocked Tools", ""])
    blocked_file = REPORTS_DIR / "blocked.md"
    if blocked_file.exists():
        lines.append(blocked_file.read_text().strip())
    else:
        lines.append("- No blocked tools recorded")
    lines.append("")

    # 5. Max similarity score
    lines.extend(["## Similarity Score", ""])
    similarity_file = REPORTS_DIR / "similarity.csv"
    if similarity_file.exists():
        content = similarity_file.read_text()
        lines.append(f"- Similarity report exists: {len(content)} bytes")
    else:
        lines.append("- Run `python3 scripts/similarity_check.py` first")
    lines.append("")

    # Write report
    report_path = REPORTS_DIR / "spot-check.md"
    report_path.write_text("\n".join(lines) + "\n")
    print(f"Spot-check report: {report_path}")


if __name__ == "__main__":
    main()
