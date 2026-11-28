#!/usr/bin/env python3
"""Build Phase D link-worthy assets strictly from the evidence ledger."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "evidence" / "evidence-ledger.json"
CHANGES = ROOT / "data" / "changes" / "tool-change-ledger.json"
OUT = ROOT / "assets" / "price-and-limit-changes"
TOOLS = ROOT / "tools"


def esc(v) -> str:
    return html.escape(str(v), quote=True)


def ledger_rows(ledger: dict) -> list[dict]:
    rows = []
    for c in ledger["claims"]:
        if c.get("claim_type") != "pricing" or not isinstance(c.get("value"), dict):
            continue
        for plan in c["value"].get("plans", []):
            price = plan.get("monthly_usd", plan.get("displayed_monthly_usd", ""))
            rows.append({
                "tool_id": c.get("tool_id", ""), "claim_id": c["claim_id"],
                "plan": plan.get("name", ""), "monthly_usd": price,
                "annual_monthly_equivalent_usd": plan.get("annual_monthly_equivalent_usd", ""),
                "limits": json.dumps({k: v for k, v in plan.items()
                                      if k not in ("name", "monthly_usd", "displayed_monthly_usd",
                                                   "annual_monthly_equivalent_usd")}, ensure_ascii=False),
                "verified_at": c.get("verified_at", ""),
                "source_urls": " | ".join(
                    s.get("url", "") for s in ledger["sources"]
                    if s.get("source_id") in c.get("source_ids", []) and s.get("url")),
            })
    return rows


def main() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    changes = json.loads(CHANGES.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ledger_rows(ledger)

    (OUT / "pricing.json").write_text(
        json.dumps({"generated_from": "data/evidence/evidence-ledger.json",
                    "claims": rows, "changes": changes.get("events", [])},
                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (OUT / "pricing.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # simple SVG bar chart of entry prices by tool (USD only)
    by_tool = {}
    for r in rows:
        try:
            price = float(r["monthly_usd"])
        except (TypeError, ValueError):
            continue
        tid = r["tool_id"]
        if price > 0 and (tid not in by_tool or price < by_tool[tid]):
            by_tool[tid] = price
    items = sorted(by_tool.items(), key=lambda x: x[1])[:12]
    maxp = max((v for _, v in items), default=1)
    bars = []
    for i, (tid, v) in enumerate(items):
        y = 10 + i * 28
        w = int(360 * v / maxp)
        bars.append(f'<text x="8" y="{y+14}" font-size="12" fill="#1A1D21">{esc(tid)}</text>'
                    f'<rect x="150" y="{y+2}" width="{w}" height="16" rx="4" fill="#1B5E4B"/>'
                    f'<text x="{160+w}" y="{y+14}" font-size="12" fill="#1A1D21">${v:g}</text>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="620" height="' + str(20 + len(items) * 28) +
           '" viewBox="0 0 620 ' + str(20 + len(items) * 28) + '" role="img" aria-label="Entry monthly price by tool">'
           + "".join(bars) + "</svg>")
    (OUT / "entry-price-chart.svg").write_text(svg, encoding="utf-8")

    # State of SEO tool pricing 2026 page — all numbers from ledger
    seo_rows = [r for r in rows if r["tool_id"] in ("semrush", "moz-pro", "ahrefs", "screamingfrog")]
    table = "\n".join(
        f"<tr><th scope=row>{esc(r['tool_id'])}</th><td>{esc(r['plan'])}</td>"
        f"<td>${esc(r['monthly_usd'])}/mo</td><td>{esc(r['annual_monthly_equivalent_usd'])}</td>"
        f"<td>{esc(r['verified_at'])}</td></tr>" for r in seo_rows[:20])
    page = f'''<!doctype html><html lang="en"><head><title>State of SEO Tool Pricing 2026 | ToolNest</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/assets/site.min.css">
<meta name="description" content="Published entry prices for Semrush, Moz Pro, Ahrefs and Screaming Frog, each traced to a dated official source in the ToolNest evidence ledger.">
<link rel="canonical" href="https://www.toolnestai.tech/tools/state-of-seo-pricing-2026.html">
<meta property="og:title" content="State of SEO Tool Pricing 2026 | ToolNest">
<meta property="og:description" content="Published SEO tool prices with dates and official sources, from the ToolNest evidence ledger.">
<meta property="og:url" content="https://www.toolnestai.tech/tools/state-of-seo-pricing-2026.html">
<meta property="og:image" content="https://www.toolnestai.tech/assets/og-default.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="State of SEO Tool Pricing 2026 | ToolNest">
<meta name="twitter:description" content="Published SEO tool prices with dates and official sources, from the ToolNest evidence ledger.">
<meta name="twitter:image" content="https://www.toolnestai.tech/assets/og-default.png">
</head><body><a class="skip" href="#top">Skip to content</a><main id="top" tabindex="-1">
<section class="hero phero"><div class="wrap"><nav aria-label="Breadcrumb" class="crumbs"><ol><li><a href="/">Home</a></li><li><a href="/tools/index.html">Tools</a></li><li aria-current="page">State of SEO tool pricing 2026</li></ol></nav>
<p class="eyebrow">Ledger data</p><h1>State of SEO tool pricing 2026</h1>
<p class="lede">Entry prices for four SEO tools, each with the date it was verified and the official source. Numbers come only from the ToolNest evidence ledger; where a vendor publishes no figure, none is shown.</p></div></section>
<div class="wrap p-layout"><div class="p-main"><section class="p-sec"><h2>Published entry prices</h2>
<table class="p-pricing-table"><caption class="sr">Ledger-verified SEO tool prices</caption><thead><tr><th scope=col>Tool</th><th scope=col>Plan</th><th scope=col>Monthly USD</th><th scope=col>Annual monthly equivalent</th><th scope=col>Verified</th></tr></thead><tbody>{table}</tbody></table>
<p>Download the underlying data as <a href="/assets/price-and-limit-changes/pricing.csv">CSV</a> or <a href="/assets/price-and-limit-changes/pricing.json">JSON</a>. Method: each value is copied from the cited official pricing page into the evidence ledger with its verification date; nothing is inferred or estimated.</p>
<p><img src="/assets/price-and-limit-changes/entry-price-chart.svg" alt="Bar chart of entry monthly prices by SEO tool" width="620"></p></section>
<section class="p-sec"><h2>How to cite this data</h2><p>ToolNest Editorial (2026). State of SEO tool pricing 2026. https://www.toolnestai.tech/tools/state-of-seo-pricing-2026.html. Figures verified as dated in the linked ledger sources.</p>
<p>Related: <a href="/tools/seo-cost-calculator.html">SEO cost and fit calculator</a> and <a href="/tools/price-and-limit-changes.html">price and limit change log</a>.</p></section></div></main></body></html>
'''
    (TOOLS / "state-of-seo-pricing-2026.html").write_text(page, encoding="utf-8")

    # embeddable snippet with visible attribution
    embed_dir = OUT / "embed"
    embed_dir.mkdir(parents=True, exist_ok=True)
    (embed_dir / "seo-calculator.html").write_text(
        '<div style="max-width:640px;margin:0 auto;border:1px solid #E2E6EB;border-radius:16px;padding:16px">'
        '<iframe title="ToolNest SEO cost calculator" src="/tools/seo-cost-calculator.html" '
        'style="width:100%;height:420px;border:0"></iframe>'
        '<p style="font:14px system-ui;text-align:center">Calculator by '
        '<a href="https://www.toolnestai.tech/tools/seo-cost-calculator.html">ToolNest</a> '
        '&middot; data from the ToolNest evidence ledger</p></div>', encoding="utf-8")

    print(f"wrote {len(rows)} pricing rows, chart, pricing page and embed snippet")


if __name__ == "__main__":
    main()
