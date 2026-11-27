#!/usr/bin/env python3
"""Score every indexable page for the Phase B quality gate.

Outputs data/quality/page-scores.csv with:
path, words, unique_facts, sentence_overlap_pct, inbound_links,
ledger_verified_price, passes_gate, reason.

No page is deleted: failing pages are noindexed and removed from the sitemap
by scripts/apply_quality_gate.py, with an entry in docs/indexation-log.md.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from content_metrics import measure  # noqa: E402
from growth_metrics import html_files, sitemap_paths, internal_targets  # noqa: E402

MIN_WORDS = 400
MAX_OVERLAP_PCT = 15.0
# Site infrastructure pages: required for trust and navigation, not thin content.
PROTECTED = {
    "index.html", "about.html", "contact.html", "privacy.html", "terms.html",
    "affiliate-disclosure.html", "editorial-policy.html", "how-we-test.html",
    "corrections.html", "tools/index.html", "category/index.html",
    "compare/index.html", "best/index.html", "goals/index.html",
    "alternatives/index.html", "tools/seo-cost-calculator.html",
    "tools/price-and-limit-changes.html",
    "category/developer-tools.html", "tools/automation-budget-estimator.html",
    "tools/overlap-checker.html", "tools/workflow-explorer.html",
}
SKIP = {"scripts", "tests", "data", "reports", "docs", "node_modules", ".git"}


def sentences(text: str) -> list[str]:
    body = re.search(r"<main[^>]*>(.*?)</main>", text, re.S | re.I)
    body = body.group(1) if body else text
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    parts = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", body).strip())
    return [p.strip() for p in parts if len(p.strip()) > 25]


def ledger_prices() -> set[str]:
    ledger = json.loads((ROOT / "data" / "evidence" / "evidence-ledger.json").read_text(encoding="utf-8"))
    values = set()
    for c in ledger["claims"]:
        if c.get("claim_type") != "pricing":
            continue
        blob = json.dumps(c.get("value"))
        values.update(re.findall(r"\b\d+(?:\.\d+)?\b", blob))
    return values


def main() -> None:
    pages = html_files()
    docs = {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8", errors="replace") for p in pages}
    sitemap = sitemap_paths()
    indexable = sorted(r for r in docs if r in sitemap)  # sitemap == indexable invariant

    sent_by_page = {r: sentences(t) for r, t in docs.items()}
    occurrences = Counter(s for ss in sent_by_page.values() for s in ss)
    # Boilerplate that appears on almost every page (disclosures, checklists)
    # is sitewide navigation/legal text, not duplicated page content.
    boilerplate = {s for s, n in occurrences.items() if n > 20}
    prices = ledger_prices()

    inbound: dict[str, set[str]] = defaultdict(set)
    for src, text in docs.items():
        for tgt in internal_targets(text, src):
            if tgt in docs:
                inbound[tgt].add(src)

    out = ROOT / "data" / "quality" / "page-scores.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["path", "words", "unique_facts", "sentence_overlap_pct",
                         "inbound_links", "ledger_verified_price", "passes_gate", "reason"])
        for rel in indexable:
            ss = [s for s in sent_by_page[rel] if s not in boilerplate]
            overlap = sum(1 for s in ss if occurrences[s] > 1 and s not in boilerplate)
            pct = round(100.0 * overlap / len(ss), 2) if ss else 100.0
            facts = [s for s in ss if re.search(r"\d", s) and occurrences[s] == 1 and s not in boilerplate]
            nums = set(re.findall(r"\$\s?\d+(?:\.\d+)?|\b\d+(?:\.\d+)?\b", docs[rel]))
            has_price = bool({n.lstrip("$").strip() for n in nums} & prices)
            words = measure(docs[rel]).words
            fails = []
            if rel not in PROTECTED:
                if words < MIN_WORDS:
                    fails.append("thin")
                if not facts:
                    fails.append("no_unique_facts")
                if pct > MAX_OVERLAP_PCT:
                    fails.append("repeated_sentences")
            writer.writerow([rel, words, len(facts), pct, len(inbound[rel]),
                             "yes" if has_price else "no", "no" if fails else "yes",
                             ",".join(fails)])
            rows.append((rel, words, len(facts), pct, len(inbound[rel]), has_price, bool(fails)))

    failed = [r for r in rows if r[6]]
    print(f"Wrote {out} ({len(rows)} indexable pages)")
    print(f"Failing gate: {len(failed)} / {len(rows)}")
    print(f"  thin: {sum(1 for r in rows if 'thin' in str(r))}")
    print(f"  no_unique_facts: {sum(1 for r in rows if r[2] == 0)}")
    print(f"  repeated_sentences: {sum(1 for r in rows if r[3] > MAX_OVERLAP_PCT)}")


if __name__ == "__main__":
    main()
