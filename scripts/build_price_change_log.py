#!/usr/bin/env python3
"""Generate a public price/limit change log from data/changes (real dates only)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "changes" / "tool-change-ledger.json"
OUT = ROOT / "tools" / "price-and-limit-changes.html"


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    rows = []
    for ev in data.get("events", []):
        detected = esc(ev.get("detected_at", "not verified"))
        tool = esc(ev.get("tool_id", "unknown"))
        note = esc(ev.get("correction_note") or ev.get("note", ""))
        status = esc(ev.get("status", "unknown"))
        rows.append(
            f'<article class="p-sec"><h2>{tool}: {status}</h2>'
            f'<p>Detected {detected}. {note}</p></article>'
        )
    newest = max((ev.get("detected_at", "") for ev in data.get("events", [])), default="")
    body = "\n".join(rows) or '<p class="p-note">No recorded changes in the current change ledger.</p>'

    html = f'''<!doctype html>
<html lang="en"><head><title>Price and Limit Change Log | ToolNest</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/assets/site.min.css">
<meta name="description" content="A dated, public record of price and limit changes and disputed claims in the ToolNest evidence ledger.">
<link rel="canonical" href="https://www.toolnestai.tech/tools/price-and-limit-changes.html">
<meta property="og:title" content="Price and Limit Change Log | ToolNest">
<meta property="og:description" content="A dated, public record of price and limit changes and disputed claims in the ToolNest evidence ledger.">
<meta property="og:url" content="https://www.toolnestai.tech/tools/price-and-limit-changes.html">
<meta property="og:image" content="https://www.toolnestai.tech/assets/og-default.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Price and Limit Change Log | ToolNest">
<meta name="twitter:description" content="A dated, public record of price and limit changes and disputed claims in the ToolNest evidence ledger.">
<meta name="twitter:image" content="https://www.toolnestai.tech/assets/og-default.png">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"Price and Limit Change Log","url":"https://www.toolnestai.tech/tools/price-and-limit-changes.html","dateModified":"{newest}"}}</script>
</head><body>
<a class="skip" href="#top">Skip to content</a>
<main id="top" tabindex="-1">
<section class="hero phero"><div class="wrap">
<nav aria-label="Breadcrumb" class="crumbs"><ol><li><a href="/">Home</a></li><li><a href="/tools/index.html">Tools</a></li><li aria-current="page">Price and limit changes</li></ol></nav>
<p class="eyebrow">Editorial record</p><h1>Price and limit change log</h1>
<p class="lede">Vendor prices and limits change. This page records the dated corrections and disputes in the ToolNest evidence ledger. Where official sources conflict, we say so instead of picking a number.</p>
</div></section>
<div class="wrap p-layout"><div class="p-main">{body}
<section class="p-sec"><h2>How to use this log</h2>
<p>Check this page when a price on ToolNest looks out of date. The <a href="/tools/seo-cost-calculator.html">SEO cost and fit calculator</a> uses only the current ledger values, and our <a href="/how-we-test.html">research policy</a> explains how claims are verified.</p>
</section></div><aside class="p-aside"><div class="p-aside-panel"><h3>Related</h3>
<ul><li><a href="/tools/seo-cost-calculator.html">SEO cost calculator</a></li>
<li><a href="/compare/mozpro-vs-semrush.html">Moz Pro vs Semrush</a></li></ul></div></aside></div>
</main></body></html>
'''
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(html)} bytes, {len(data.get('events', []))} events)")


if __name__ == "__main__":
    main()
