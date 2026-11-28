#!/usr/bin/env python3
"""Build the press page and owner-only outreach list (nothing is sent)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "evidence" / "evidence-ledger.json"
OUT = ROOT / "docs"
OUT.mkdir(parents=True, exist_ok=True)

ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
claims = len(ledger["claims"])
sources = len(ledger["sources"])
vendors = len({c.get("tool_id") for c in ledger["claims"] if c.get("tool_id")})

press = f"""# Press and citation page

ToolNest publishes research-based software comparisons. All commercial figures below come from the
[evidence ledger](../data/evidence/evidence-ledger.json) with a dated official source. No hands-on testing is claimed
unless a page says so.

## Citation-ready statistics

- The evidence ledger contains {claims} claims from {sources} sources covering {vendors} tools.
- `tools/state-of-seo-pricing-2026.html` lists published entry prices for four SEO tools with verification dates.
- `data/price-and-limit-changes/pricing.csv` and `.json` provide downloadable, source-linked plan data.
- `tools/seo-cost-calculator.html` estimates the cheapest fitting plan from those published limits.

## Suggested citation

> ToolNest Editorial (2026). State of SEO tool pricing 2026. https://www.toolnestai.tech/tools/state-of-seo-pricing-2026.html

## Embedding

An embeddable calculator snippet with a visible attribution link is published at
`/data/price-and-limit-changes/embed/seo-calculator.html`. Please keep the attribution link.

## Contact

Use the site contact page for corrections and interview requests.
"""
(OUT / "press-page.md").write_text(press, encoding="utf-8")

targets = [
 ("Search Engine Land", "SEO news outlet", "state-of-seo-pricing-2026.html"),
 ("Search Engine Journal", "SEO news outlet", "state-of-seo-pricing-2026.html"),
 ("Moz Blog", "SEO practitioner blog", "mozpro-vs-semrush.html"),
 ("Ahrefs Blog", "SEO research blog", "state-of-seo-pricing-2026.html"),
 ("Semrush Blog", "SEO platform blog", "mozpro-vs-semrush.html"),
 ("Backlinko", "SEO education blog", "seo-cost-calculator.html"),
 ("Neil Patel Blog", "Marketing blog", "seo-cost-calculator.html"),
 ("Search Engine Roundtable", "SEO news", "price-and-limit-changes.html"),
 ("Sistrix Blog", "European SEO blog", "state-of-seo-pricing-2026.html"),
 ("Screaming Frog Blog", "Technical SEO blog", "tools/screamingfrog.html"),
 ("Aleyda Solis / Orainti", "International SEO consultant", "state-of-seo-pricing-2026.html"),
 ("Bigfoot29 SEO newsletter", "SEO newsletter", "seo-cost-calculator.html"),
 ("SEO FMO newsletter", "SEO newsletter", "price-and-limit-changes.html"),
 ("The SEO Newsletter (Growth Bar)", "SEO newsletter", "seo-cost-calculator.html"),
 ("Optimize newsletter", "SEO newsletter", "state-of-seo-pricing-2026.html"),
 ("Last Week in SEO", "SEO newsletter", "price-and-limit-changes.html"),
 ("iloveSEO newsletter", "European SEO newsletter", "state-of-seo-pricing-2026.html"),
 ("Marie Haynes Consulting", "SEO consultant", "mozpro-vs-semrush.html"),
 ("Dr. Pete Meyers", "SEO columnist", "price-and-limit-changes.html"),
 ("Roger Montti", "SEO journalist", "state-of-seo-pricing-2026.html"),
 ("SaaStr", "SaaS community", "seo-cost-calculator.html"),
 ("Indie Hackers", "Founder community", "seo-cost-calculator.html"),
 ("GrowthHackers", "Growth community", "seo-cost-calculator.html"),
 ("Product Hunt", "Product discovery", "seo-cost-calculator.html"),
 ("Hacker News", "Technical community", "state-of-seo-pricing-2026.html"),
 ("Reddit r/SEO", "SEO community", "mozpro-vs-semrush.html"),
 ("Reddit r/SaaS", "SaaS community", "seo-cost-calculator.html"),
 ("LinkedIn SEO groups", "Professional community", "price-and-limit-changes.html"),
 ("Ahrefs Community", "Tool community", "mozpro-vs-semrush.html"),
 ("Moz Community", "Tool community", "mozpro-vs-semrush.html"),
 ("WebmasterWorld", "Webmaster forum", "state-of-seo-pricing-2026.html"),
 ("SEO Chat forums", "SEO forum", "seo-cost-calculator.html"),
 ("Digital Marketing Institute", "Marketing education", "state-of-seo-pricing-2026.html"),
 ("HubSpot Blog", "Marketing blog", "seo-cost-calculator.html"),
 ("Zapier Blog", "Automation blog", "seo-cost-calculator.html"),
 ("ClickUp Blog", "Productivity blog", "monday-vs-notion.html"),
 ("Notion Blog", "Productivity blog", "monday-vs-notion.html"),
 ("monday.com Blog", "Work management blog", "monday-vs-notion.html"),
 ("ProductLedger", "SaaS data blog", "state-of-seo-pricing-2026.html"),
 ("OpenView SaaS benchmarks", "SaaS research", "state-of-seo-pricing-2026.html"),
]
lines = ["# Outreach list (owner-only — nothing has been sent)", "",
         "| Target | Why relevant | Asset to pitch |", "|---|---|---|"]
lines += [f"| {t} | {why} | `{asset}` |" for t, why, asset in targets]
lines += ["", "Email template: cite the dated dataset, offer the CSV/JSON and calculator embed, ",
          "and ask whether a short data note would be useful. Do not ask for a link directly.", ""]
(OUT / "outreach-list.md").write_text("\n".join(lines), encoding="utf-8")
print(f"wrote press page and {len(targets)} outreach targets")
