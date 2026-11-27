#!/usr/bin/env python3
"""Year in titles comes from one constant; shown facts must be ledger-backed and fresh."""

import json
import re
import sys
import unittest
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from content_constants import FACT_MAX_AGE_DAYS, SHOW_YEAR  # noqa: E402

LEDGER = ROOT / "data" / "evidence" / "evidence-ledger.json"
SKIP_DIRS = {"scripts", "tests", "data", "reports", "docs", "node_modules", ".git"}
PRIORITY = [
    "tools/semrush.html", "tools/mozpro.html",
    "compare/mozpro-vs-semrush.html", "compare/claude-vs-gemini.html",
    "compare/monday-vs-notion.html", "best/best-sales-tools.html",
]


class ContentFreshnessTests(unittest.TestCase):
    def test_years_in_titles_use_single_constant(self):
        for p in ROOT.rglob("*.html"):
            if set(p.relative_to(ROOT).parts) & SKIP_DIRS:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"<title>([^<]+)</title>", text)
            if not m:
                continue
            for year in re.findall(r"\b(20\d\d)\b", m.group(1)):
                self.assertEqual(
                    int(year), SHOW_YEAR,
                    f"{p.relative_to(ROOT)} title has stale year {year}",
                )

    def test_priority_dates_are_ledger_backed_and_fresh(self):
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        verified = {
            datetime.strptime(c["verified_at"], "%Y-%m-%d").date()
            for c in ledger["claims"] if c.get("verified_at")
        }
        today = date.today()
        for rel in PRIORITY:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for raw in re.findall(r"\b2026-\d\d-\d\d\b", text):
                shown = datetime.strptime(raw, "%Y-%m-%d").date()
                self.assertIn(shown, verified, f"{rel} shows {raw} absent from ledger")
                self.assertLessEqual((today - shown).days, FACT_MAX_AGE_DAYS,
                                     f"{rel} shows stale date {raw}")


if __name__ == "__main__":
    unittest.main()
