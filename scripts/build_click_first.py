#!/usr/bin/env python3
"""Add answer-first, ledger-sourced content to the enrich-next pages.

Every number and date comes from data/evidence/evidence-ledger.json. Pages with
no ledger fact say "not verified" rather than inventing a figure.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "evidence" / "evidence-ledger.json"
ENRICH = ROOT / "data" / "quality" / "enrich-next.json"


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def facts_for(tool_id: str, ledger: dict) -> dict:
    claims = [c for c in ledger["claims"] if c.get("tool_id") == tool_id]
    pricing = [c for c in claims if c.get("claim_type") == "pricing" and isinstance(c.get("value"), dict) and "plans" in c["value"]]
    limitations = [c for c in claims if c.get("claim_type") == "limitation"]
    sources = []
    for c in claims:
        for sid in c.get("source_ids", []):
            for s in ledger["sources"]:
                if s.get("source_id") == sid and s.get("url") and s["url"] not in [x[1] for x in sources]:
                    sources.append((s["url"], c.get("verified_at", "")))
    return {"pricing": pricing, "limitations": limitations, "sources": sources}


def plan_rows(data: dict) -> str:
    rows = []
    for claim in data["pricing"]:
        for plan in claim["value"]["plans"]:
            price = plan.get("monthly_usd", plan.get("displayed_monthly_usd", "custom"))
            annual = plan.get("annual_monthly_equivalent_usd")
            limits = ", ".join(
                f"{k.replace('_', ' ')}: {v}" for k, v in plan.items()
                if k not in ("name", "monthly_usd", "displayed_monthly_usd", "annual_monthly_equivalent_usd", "price")
            )
            rows.append(
                f"<tr><th scope=row>{esc(plan['name'])}</th>"
                f"<td>${esc(price)}/mo{(' or $'+str(annual)+'/mo annual equivalent') if annual else ''}</td>"
                f"<td>{esc(limits) if limits else 'Not verified'}</td></tr>"
            )
    return "\n".join(rows)


def build(rel: str, ledger: dict) -> str | None:
    stem = Path(rel).stem
    if rel.startswith("compare/"):
        tool_ids = stem.split("-vs-")
    elif rel.startswith(("tools/", "alternatives/")):
        tool_ids = [stem.replace("-alternatives", "")]
    else:
        tool_ids = []
    tool_ids = [t for t in tool_ids if t]
    all_data = {t: facts_for(t, ledger) for t in tool_ids}
    priced = [(t, d) for t, d in all_data.items() if d["pricing"]]

    names = []
    for t in tool_ids:
        names.append(t.replace("-", " ").title())

    if not priced:
        src = []
        for t, d in all_data.items():
            for url, verified in d["sources"][:2]:
                src.append(f'<li><a href="{esc(url)}" rel="nofollow">{esc(url)}</a> (verified {esc(verified or "not verified")})</li>')
        return (f'<section class="p-sec" id="click-first"><h2>Price and limits for {esc(" ".join(names))}: not verified</h2>'
                f'<p>ToolNest has no ledger-verified price for {esc(" ".join(names))}. '
                f'We do not publish a number until it can be traced to a dated official source, so the answer here is '
                f'<strong>not verified</strong>. Check the official site before you buy.</p>'
                f'<h3>Official sources checked</h3><ul>{"".join(src) or "<li>Not verified</li>"}</ul>'
                f'<p class="p-note">Switching note: confirm current plan limits, cancellation and export terms '
                f'with the vendor; ToolNest does not guess them.</p></section>\n')

    first = priced[0][1]["pricing"][0]["value"]["plans"][0]
    first_price = first.get("monthly_usd", first.get("displayed_monthly_usd", "not verified"))
    answer = (f"{names[0]} starts at ${esc(first_price)}/mo on the official plan published in the ToolNest evidence ledger. "
              f"That figure is the entry point, not the total cost of a team workflow: the table below shows the published limits "
              f"that decide which plan you actually need.")
    rows = plan_rows(priced[0][1])
    skip_items = []
    for t, d in all_data.items():
        for c in d["limitations"][:2]:
            v = c.get("value")
            if isinstance(v, list):
                skip_items.extend(str(x) for x in v[:2])
            elif isinstance(v, str):
                skip_items.append(v[:120])
    skip_html = ("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in dict.fromkeys(skip_items[:4])) + "</ul>") if skip_items else "<p>Not verified from official pages.</p>"
    src = []
    for t, d in all_data.items():
        for url, verified in d["sources"][:2]:
            src.append(f'<li><a href="{esc(url)}" rel="nofollow">{esc(url)}</a> (verified {esc(verified or "not verified")})</li>')
    switching = ("Switching note: compare the published site and keyword limits below against what you use today, "
                 "then check cancellation and export terms on the official site. ToolNest does not publish a number "
                 "that the vendor does not state.")
    verified_dates = sorted({v for _, d in all_data.items() for _, v in d["sources"] if v})
    when = verified_dates[-1] if verified_dates else "not verified"

    return (f'<section class="p-sec" id="click-first"><h2>Plan limits and fit for {esc(" ".join(names))}</h2>'
            f'<p>{answer}</p>'
            f'<table class="p-pricing-table"><caption class="sr">Ledger-verified plans for {esc(" ".join(names))}</caption>'
            f'<thead><tr><th scope=col>Plan</th><th scope=col>Published price</th><th scope=col>Published limits</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>'
            f'<h3>Who should skip</h3>{skip_html}'
            f'<h3>{esc(switching)}</h3>'
            f'<h3>Official sources</h3><ul>{"".join(src) or "<li>Not verified</li>"}</ul>'
            f'<p class="p-note">Checked against the evidence ledger on {esc(when)}. '
            f'Where the vendor does not publish a figure, this page says not verified.</p></section>\n')


def main() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    pages = json.loads(ENRICH.read_text(encoding="utf-8"))["pages"]
    added = 0
    for rel in pages:
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if 'id="click-first"' in text:
            continue
        block = build(rel, ledger)
        if not block:
            print("no ledger data:", rel)
            continue
        idx = text.find('<div class="wrap p-layout">')
        if idx < 0:
            idx = text.find("</main>")
        if idx < 0:
            continue
        path.write_text(text[:idx] + block + text[idx:], encoding="utf-8")
        added += 1
    print(f"added click-first sections to {added} pages")


if __name__ == "__main__":
    main()
