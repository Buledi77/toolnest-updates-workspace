#!/usr/bin/env python3
"""Generate the SEO cost & fit calculator from the evidence ledger only.

No prices, limits or dates are hard-coded here: every displayed commercial
fact is read from data/evidence/evidence-ledger.json with its source URL and
verified_at date. Facts not present in the ledger are shown as "not verified".
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "evidence" / "evidence-ledger.json"
OUT = ROOT / "tools" / "seo-cost-calculator.html"

TOOL_IDS = ("semrush", "moz-pro", "ahrefs")
CLAIM_IDS = {
    "semrush": "semrush-current-plan-structure",
    "moz-pro": "moz-pro-plan-structure",
    "ahrefs": "ahrefs-pricing-verified",
}


def ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def source_url(d: dict, source_id: str) -> str:
    for s in d["sources"]:
        if s.get("source_id") == source_id:
            return s.get("url", "")
    return ""


def plans_from_ledger(d: dict) -> dict:
    out = {}
    for tool in TOOL_IDS:
        claim = next(c for c in d["claims"] if c["claim_id"] == CLAIM_IDS[tool])
        out[tool] = {
            "plans": claim["value"]["plans"],
            "verified_at": claim["verified_at"],
            "sources": [{"id": sid, "url": source_url(d, sid)} for sid in claim.get("source_ids", [])],
            "status": claim.get("status", "unknown"),
        }
    return out


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def num(v):
    return v if isinstance(v, (int, float)) else None


def site_limit(plan: dict):
    return num(plan.get("websites") if "websites" in plan else plan.get("tracked_sites"))


def keyword_limit(plan: dict):
    return num(plan.get("daily_tracked_keywords") if "daily_tracked_keywords" in plan else plan.get("tracked_keywords"))


def price(plan: dict, annual: bool):
    return num(plan.get("annual_monthly_equivalent_usd") if annual else None) or num(
        plan.get("monthly_usd") if not annual else None
    ) or num(plan.get("displayed_monthly_usd"))


def best_fit(tool: str, data: dict, sites: int, keywords: int, annual: bool):
    candidates = []
    for plan in data[tool]["plans"]:
        sl, kl, p = site_limit(plan), keyword_limit(plan), price(plan, annual)
        if sl is None or kl is None or p is None:
            candidates.append({"name": plan["name"], "price": p, "fit": "not verified", "binds": "limits not in ledger"})
            continue
        ok = sites <= sl and keywords <= kl
        binds = "sites" if sites >= sl else "keywords" if keywords >= kl else "none at this usage"
        candidates.append({"name": plan["name"], "price": p, "fit": ok, "binds": binds, "sites": sl, "keywords": kl})
    fits = [c for c in candidates if c["fit"] is True and c["price"] is not None]
    chosen = min(fits, key=lambda c: c["price"]) if fits else None
    return chosen, candidates


def ssr_summary(data: dict) -> str:
    rows = []
    for tool in TOOL_IDS:
        chosen, _ = best_fit(tool, data, 5, 500, True)
        name = {"semrush": "Semrush", "moz-pro": "Moz Pro", "ahrefs": "Ahrefs"}[tool]
        if chosen and chosen["price"] is not None:
            rows.append(f"<tr><th scope=row>{esc(name)}</th><td>{esc(chosen['name'])}</td>"
                        f"<td>${chosen['price']}/mo equivalent</td><td>{esc(chosen['binds'])}</td></tr>")
        else:
            rows.append(f"<tr><th scope=row>{esc(name)}</th><td colspan=3>No verified plan fits 5 sites / 500 keywords on the published limits; check the official site.</td></tr>")
    return "\n".join(rows)


def main() -> None:
    d = ledger()
    data = plans_from_ledger(d)
    newest = max(datetime.strptime(x["verified_at"], "%Y-%m-%d").date() for x in data.values())
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    source_links = []
    for tool in TOOL_IDS:
        for s in data[tool]["sources"]:
            if s["url"]:
                source_links.append(f'<li>{esc(tool)}: <a href="{esc(s["url"])}" rel="nofollow">{esc(s["url"])}</a> '
                                    f'(verified {esc(data[tool]["verified_at"])})</li>')

    html = f'''<!doctype html>
<html lang="en"><head><title>SEO Platform Cost &amp; Fit Calculator | ToolNest</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/assets/site.min.css">
<meta name="description" content="Estimate the lowest-cost SEO plan that fits your sites and tracked keywords, using vendor prices and limits from the ToolNest evidence ledger.">
<link rel="canonical" href="https://www.toolnestai.tech/tools/seo-cost-calculator.html">
<meta property="og:title" content="SEO Platform Cost &amp; Fit Calculator | ToolNest">
<meta property="og:description" content="Estimate the lowest-cost SEO plan that fits your sites and tracked keywords, using ledger-verified vendor prices and limits.">
<meta property="og:url" content="https://www.toolnestai.tech/tools/seo-cost-calculator.html">
<meta property="og:image" content="https://www.toolnestai.tech/assets/og-default.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="SEO Platform Cost &amp; Fit Calculator | ToolNest">
<meta name="twitter:description" content="Estimate the lowest-cost SEO plan that fits your sites and tracked keywords, using ledger-verified vendor prices and limits.">
<meta name="twitter:image" content="https://www.toolnestai.tech/assets/og-default.png">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"SEO Platform Cost and Fit Calculator","url":"https://www.toolnestai.tech/tools/seo-cost-calculator.html","dateModified":"{newest.isoformat()}"}}</script>
</head><body>
<a class="skip" href="#top">Skip to content</a>
<main id="top" tabindex="-1">
<section class="hero phero"><div class="wrap">
<nav aria-label="Breadcrumb" class="crumbs"><ol><li><a href="/">Home</a></li><li><a href="/tools/index.html">Tools</a></li><li aria-current="page">SEO cost &amp; fit calculator</li></ol></nav>
<p class="eyebrow">Decision tool</p><h1>SEO platform cost and fit calculator</h1>
<p class="lede">Enter the number of sites and tracked keywords you need. We compare the published plan limits of Semrush, Moz Pro and Ahrefs and show the cheapest plan that fits. Every price and limit comes from the ToolNest evidence ledger; anything not published is labelled not verified.</p>
</div></section>
<div class="wrap p-layout"><div class="p-main">
<section class="p-sec"><h2>Worked example (server-rendered)</h2>
<p>For 5 sites and 500 tracked keywords on annual billing, the cheapest fitting plans from the current ledger are:</p>
<table class="p-pricing-table"><caption class="sr">Cheapest fitting plan by tool</caption>
<thead><tr><th scope="col">Tool</th><th scope="col">Plan</th><th scope="col">Price</th><th scope="col">Limit that binds first</th></tr></thead>
<tbody>{ssr_summary(data)}</tbody></table>
</section>
<section class="p-sec"><h2>Calculate your own fit</h2>
<form id="calc" class="p-feats">
<label>Sites to monitor <input id="sites" name="sites" type="number" min="1" max="100" value="5" inputmode="numeric"></label>
<label>Keywords to track <input id="keywords" name="keywords" type="number" min="1" max="100000" value="500" inputmode="numeric"></label>
<label>Billing <select id="billing" name="billing"><option value="annual">Annual equivalent</option><option value="monthly">Monthly</option></select></label>
</form><p id="result" role="status" aria-live="polite">Loading the ledger-backed comparison&hellip;</p>
<p class="p-note">Additional users, AI-visibility add-ons and custom tiers are not included where the ledger has no published figure. Those cases are shown as not verified, not guessed.</p>
</section>
<section class="p-sec"><h2>Sources behind this calculator</h2>
<ul>{''.join(source_links)}</ul>
<p>Prices and limits checked between {esc(min(x["verified_at"] for x in data.values()))} and {esc(newest.isoformat())}. Confirm current offers on the official sites before buying.</p>
</section>
<section class="p-sec"><h2>Related decisions</h2>
<p><a href="/compare/mozpro-vs-semrush.html">Moz Pro vs Semrush</a> &middot; <a href="/tools/semrush.html">Semrush review</a> &middot; <a href="/tools/mozpro.html">Moz Pro review</a> &middot; <a href="/category/seo.html">SEO category</a> &middot; <a href="/best/best-seo-tools.html">Best SEO tools</a></p>
</section>
</div><aside class="p-aside"><div class="p-aside-panel"><h3>Category</h3><a href="/category/seo.html">SEO</a></div>
<div class="p-aside-panel"><h3>Compare</h3><ul><li><a href="/compare/mozpro-vs-semrush.html">Moz Pro vs Semrush</a></li></ul></div></aside></div>
</main>
<script id="ledger-data" type="application/json">{payload}</script>
<script>
(function(){{
  var data=JSON.parse(document.getElementById('ledger-data').textContent);
  var sites=document.getElementById('sites'),kw=document.getElementById('keywords'),bill=document.getElementById('billing'),out=document.getElementById('result');
  function num(v){{return typeof v==='number'?v:null;}}
  function calc(){{
    var s=Math.max(1,parseInt(sites.value,10)||1), k=Math.max(1,parseInt(kw.value,10)||1), annual=bill.value==='annual';
    var rows=[],names={{semrush:'Semrush','moz-pro':'Moz Pro',ahrefs:'Ahrefs'}};
    Object.keys(data).forEach(function(t){{
      var fits=[];
      data[t].plans.forEach(function(p){{
        var sl=num(p.websites!==undefined?p.websites:p.tracked_sites),kl=num(p.daily_tracked_keywords!==undefined?p.daily_tracked_keywords:p.tracked_keywords);
        var pr=num(annual?p.annual_monthly_equivalent_usd:(p.monthly_usd!==undefined?p.monthly_usd:p.displayed_monthly_usd));
        if(sl===null||kl===null||pr===null)return;
        if(s<=sl&&k<=kl)fits.push({{name:p.name,price:pr,bind:(s>=sl?'sites':(k>=kl?'keywords':'none at this usage'))}});
      }});
      fits.sort(function(a,b){{return a.price-b.price;}});
      rows.push(names[t]+': '+(fits.length?fits[0].name+' at $'+fits[0].price+'/mo ('+fits[0].bind+' binds first)':'no verified plan fits; check the official site'));
    }});
    out.textContent=rows.join(' | ');
  }}
  [sites,kw,bill].forEach(function(el){{el.addEventListener('input',calc);el.addEventListener('change',calc);}});calc();
}})();
</script>
</body></html>
'''
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(html)} bytes, ledger data {len(payload)} bytes)")


if __name__ == "__main__":
    main()
