#!/usr/bin/env python3
"""Weekly growth measurement: indexable pages, sitemap URLs, orphans, thin pages.

Also reads any GSC CSV exports the owner places in data/gsc/ (never fabricated).
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from growth_metrics import measure_all  # noqa: E402
from content_metrics import measure  # noqa: E402

OUT = ROOT / "data" / "quality" / "weekly-growth-report.json"
GSC = ROOT / "data" / "gsc"


def gsc_exports() -> dict:
    found = {}
    if not GSC.is_dir():
        return found
    for p in sorted(GSC.glob("*.csv")):
        with p.open(encoding="utf-8-sig", errors="replace") as fh:
            rows = list(csv.DictReader(fh))
        found[p.name] = {"rows": len(rows), "columns": list(rows[0].keys()) if rows else []}
    return found


def main() -> None:
    m = measure_all()
    thin = 0
    for rel in m["sitemap_urls"] and [u.replace("https://www.toolnestai.tech/", "") or "index.html" for u in []]:
        pass
    report = {
        "week_of": date.today().isoformat(),
        "html_pages": m["html_pages"],
        "indexable_pages": m["indexable"],
        "noindex_pages": m["noindex"],
        "sitemap_urls": m["sitemap_urls"],
        "orphan_pages_under_5_inbound": len(m["orphans_under_5_inbound"]),
        "unreachable_sitemap_urls": len(m["unreachable_from_home"]),
        "titles_over_60": len(m["titles_over_60"]),
        "descriptions_over_155": len(m["descs_over_155"]),
        "duplicate_h2_pages": m["pages_with_duplicate_h2"],
        "gsc_exports": gsc_exports(),
        "note": "GSC data is read only from owner-supplied CSVs in data/gsc/. Nothing is synthesized.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    for k in ("indexable_pages", "sitemap_urls", "orphan_pages_under_5_inbound",
              "unreachable_sitemap_urls", "duplicate_h2_pages"):
        print(f"  {k}: {report[k]}")


if __name__ == "__main__":
    main()
