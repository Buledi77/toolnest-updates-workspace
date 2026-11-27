#!/usr/bin/env python3
"""Apply the Phase B quality gate reversibly.

Failing pages that are not on the enrich-next list get noindex,follow and
leave the sitemap. Nothing is deleted. Every action is logged in
docs/indexation-log.md so it can be reversed.

Sitemap lastmod values come from the evidence ledger for tool/compare pages,
never from build time.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORES = ROOT / "data" / "quality" / "page-scores.csv"
ENRICH = ROOT / "data" / "quality" / "enrich-next.json"
SITEMAP = ROOT / "sitemap.xml"
LOG = ROOT / "docs" / "indexation-log.md"
LEDGER = ROOT / "data" / "evidence" / "evidence-ledger.json"
ROBOTS = b'<meta name="robots" content="noindex,follow">'


def main() -> None:
    rows = list(csv.DictReader(SCORES.open(encoding="utf-8")))
    enrich = set(json.loads(ENRICH.read_text(encoding="utf-8"))["pages"])
    failing = [r for r in rows if r["passes_gate"] == "no" and r["path"] not in enrich]

    changed = []
    for row in failing:
        path = ROOT / row["path"]
        if not path.is_file():
            continue
        b = path.read_bytes()
        if b"noindex" in b:
            continue
        b = re.sub(rb'<meta name="robots" content="[^"]*">\s*', b"", b)
        if b.count(b"</head>") == 1:
            b = b.replace(b"</head>", ROBOTS + b"\n</head>", 1)
        else:
            b = b.replace(b"<body", ROBOTS + b"\n<body", 1)
        path.write_bytes(b)
        changed.append((row["path"], row["reason"], row["words"]))

    # Remove gated pages from the sitemap and set ledger-based lastmod.
    text = SITEMAP.read_text(encoding="utf-8")
    gated = {p for p, _, _ in changed}
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    verified_by_tool: dict[str, str] = {}
    for c in ledger["claims"]:
        tid = c.get("tool_id") or ""
        if c.get("verified_at") and tid:
            verified_by_tool[tid] = max(verified_by_tool.get(tid, ""), c["verified_at"])

    def lastmod_for(rel: str) -> str:
        slug = Path(rel).stem
        if rel.startswith("tools/"):
            return verified_by_tool.get(slug, "2026-11-23")
        if rel.startswith("compare/"):
            ids = slug.split("-vs-")
            dates = [verified_by_tool.get(i) for i in ids]
            return max([d for d in dates if d], default="2026-11-23")
        return "2026-11-23"

    blocks = re.findall(
        r"  <url>\n    <loc>([^<]+)</loc>\n    <lastmod>([^<]+)</lastmod>\n  </url>\n", text)
    kept = []
    for url, old in blocks:
        rel = url.replace("https://www.toolnestai.tech/", "") or "index.html"
        if rel in gated:
            continue
        kept.append(f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{lastmod_for(rel)}</lastmod>\n  </url>\n")
    head = text[:text.index("  <url>")]
    SITEMAP.write_text(head + "".join(kept) + "</urlset>\n", encoding="utf-8")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = [f"\n## {date.today().isoformat()} — Phase B quality gate\n",
             f"- Indexable pages scored: {len(rows)}; gated: {len(changed)}; enrich-next protected: {len(enrich)}\n",
             "- Action: added `noindex,follow` and removed from sitemap (no pages deleted).\n",
             "| Page | Reason | Words |\n|---|---|---|\n"]
    entry += [f"| `{p}` | {r} | {w} |\n" for p, r, w in changed]
    entry.append("\nReversal: remove the `noindex,follow` meta tag and re-add the URL to the sitemap.\n")
    with LOG.open("a", encoding="utf-8") as fh:
        fh.writelines(entry)

    print(f"gated {len(changed)} pages; sitemap URLs now {len(kept)}; log: {LOG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
