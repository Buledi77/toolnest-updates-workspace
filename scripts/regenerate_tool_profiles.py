#!/usr/bin/env python3
"""Regenerate all tool profile HTML pages from data/tools/*.json.

Reads each tool's JSON data file and generates a complete HTML profile page
following the ToolNest information hierarchy:
- Tool identity, Quick verdict, Best for, Pricing snapshot, Key capabilities,
  Important limitations, Who should choose, Who should skip, Alternatives,
  Comparisons, Evidence/Sources, Affiliate disclosure.

Usage:
    python3 scripts/regenerate_tool_profiles.py [--dry-run] [--tool slug]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS_JSON_DIR = ROOT / "data" / "tools"
TOOLS_HTML_DIR = ROOT / "tools"
PUBLIC_HOST = "https://www.toolnestai.tech"


def load_tool(slug: str) -> dict:
    path = TOOLS_JSON_DIR / f"{slug}.json"
    if not path.exists():
        print(f"  SKIP {slug}: no JSON data file")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def esc(text: str) -> str:
    return html.escape(str(text))


def first_non_empty(*values: str) -> str:
    for v in values:
        if v and str(v).strip():
            return str(v).strip()
    return ""


def list_items(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def render_ul(items: list[str], css_class: str = "") -> str:
    if not items:
        return ""
    cls = f' class="{css_class}"' if css_class else ""
    return '<ul' + cls + '>' + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def category_label(data: dict) -> str:
    discovery = data.get("discovery", {})
    cats = discovery.get("categories", [])
    if cats:
        cat = str(cats[0])
        # Normalize category names for URL slugs
        return cat
    identity = data.get("identity", {})
    return identity.get("category", "Software")


def category_slug(cat: str) -> str:
    """Convert category name to URL slug."""
    slug = cat.lower().replace(" & ", "-and-").replace(" ", "-")
    return slug


def tool_slug_for_id(tool_id: str) -> str:
    """Map tool IDs to their HTML slugs (handles moz-pro -> mozpro)."""
    if tool_id == "moz-pro":
        return "mozpro"
    return tool_id


def tool_route(tool_id: str) -> str:
    slug = tool_slug_for_id(tool_id)
    return f"/tools/{slug}.html"


def comparison_route(slug: str) -> str | None:
    """Find the comparison page route for a given slug like 'adobeexpress-vs-canva'."""
    compare_dir = ROOT / "compare"
    if not compare_dir.exists():
        return None
    path = compare_dir / f"{slug}.html"
    if path.exists():
        return f"/compare/{slug}.html"
    return None


def render_identity_section(data: dict) -> str:
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))
    cat = esc(category_label(data))
    official_url = esc(identity.get("official_url", ""))
    logo = identity.get("logo", "")

    discovery = data.get("discovery", {})
    use_cases = list_items(discovery.get("use_cases", []))
    lede = first_non_empty(
        use_cases[0] if use_cases else "",
    )

    editorial = data.get("editorial", {})
    best_for = list_items(editorial.get("best_for", []))
    best_for_text = best_for[0] if best_for else ""

    monetization = data.get("monetization", {})
    cta_url = esc(monetization.get("official_non_affiliate_url", official_url))

    # Last reviewed
    freshness = data.get("freshness", {})
    last_reviewed = data.get("lastReviewed", "")
    if not last_reviewed:
        last_reviewed = freshness.get("updated_at", "")
    reviewed_month = ""
    if last_reviewed:
        # Extract month year
        match = re.match(r"(\d{4})-(\d{2})", str(last_reviewed))
        if match:
            year = match.group(1)
            month_num = int(match.group(2))
            months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            reviewed_month = f"Last reviewed {months[month_num - 1]} {year}"

    lines = []
    lines.append('<section class="p-sec" id="overview">')
    lines.append(f"<h2>{name} overview</h2>")

    # Overview paragraph
    if lede:
        lines.append(f"<p>{esc(name)} is a tool for {esc(lede)}.</p>")

    # Why it may be a good fit
    if best_for_text:
        lines.append(f'<div class="p-why"><b>Why it may be a good fit</b><p>{esc(best_for_text)}</p></div>')

    # Glance box
    glance_parts = []
    glance_parts.append(f'<div><small>Category</small><b>{cat}</b></div>')
    if best_for_text:
        glance_parts.append(f'<div><small>Best for</small><b>{esc(best_for_text)}</b></div>')
    if official_url:
        glance_parts.append(f'<div><small>Official site</small><b><a href="{official_url}" rel="sponsored nofollow noopener" target="_blank">Visit {name}</a></b></div>')
    if glance_parts:
        lines.append(f'<div class="p-glance">{"".join(glance_parts)}</div>')

    lines.append("</section>")
    return "\n".join(lines)


def render_best_for_section(data: dict) -> str:
    editorial = data.get("editorial", {})
    factual = data.get("factual_profile", {})

    best_for = list_items(editorial.get("best_for", []))
    not_recommended = list_items(editorial.get("not_recommended_for", []))

    # If not_recommended_for is empty, try to derive from limitations
    if not not_recommended:
        limitations = list_items(factual.get("limitations", []))
        if limitations:
            not_recommended = limitations[:3]

    # If still empty, skip section
    if not best_for and not not_recommended:
        return ""

    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))

    lines = []
    lines.append(f'<section class="p-sec" id="best-for">')
    lines.append(f"<h2>Who {name} is best for, and who should skip it</h2>")
    lines.append('<div class="two">')

    if best_for:
        lines.append(f'<div class="box"><h3>Best for</h3>{render_ul(best_for, "tl yes")}</div>')

    if not_recommended:
        lines.append(f'<div class="box"><h3>Not best for</h3>{render_ul(not_recommended, "tl no")}</div>')

    lines.append("</div></section>")
    return "\n".join(lines)


def render_pricing_section(data: dict) -> str:
    pricing = data.get("pricing", {})
    factual = data.get("factual_profile", {})
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))

    # Pricing status from factual_profile as fallback
    pricing_status = first_non_empty(
        pricing.get("pricing_status", ""),
        factual.get("pricing_status", ""),
    )

    free_plan_status = first_non_empty(
        factual.get("free_plan_status", ""),
    )
    trial_status = first_non_empty(
        factual.get("trial_status", ""),
    )

    plans = pricing.get("plans", [])
    checked_on = pricing.get("checkedOn", "")
    source_urls = list_items(pricing.get("sourceUrls", []))

    # Determine pricing verification state
    verified = bool(checked_on) and bool(plans)
    verification_label = ""
    if verified:
        verification_label = f"Pricing checked {esc(checked_on)}"
    elif pricing_status and ("not verified" in pricing_status.lower() or "pending" in pricing_status.lower()):
        verification_label = "Pricing verification pending"
    elif not pricing_status and not plans:
        verification_label = "Official pricing not publicly confirmed"

    # Find first paid plan price
    first_paid_price = ""
    for plan in plans:
        if isinstance(plan, dict):
            price = plan.get("priceMonthly")
            if price and price > 0:
                first_paid_price = f"${int(price)}/mo"
                break

    # Build pricing summary
    pricing_summary = ""
    if first_paid_price:
        if free_plan_status or pricing.get("freePlan"):
            pricing_summary = f"Free + paid plans from {first_paid_price}"
        else:
            pricing_summary = f"From {first_paid_price}"
    elif pricing_status:
        pricing_summary = esc(pricing_status)
    elif free_plan_status:
        pricing_summary = "Free plan available"

    lines = []
    lines.append(f'<section class="p-sec" id="pricing">')
    lines.append(f"<h2>{name} pricing</h2>")

    if pricing_summary:
        lines.append(f'<p class="p-pricing-summary">{esc(pricing_summary)}</p>')

    if verification_label:
        cls = "p-verified" if verified else "p-unverified"
        lines.append(f'<p class="p-evidence-strip {cls}">{esc(verification_label)}</p>')

    # Free plan details
    if free_plan_status:
        lines.append(f'<div class="p-free-note"><b>Free plan:</b> {esc(free_plan_status)}</div>')

    # Trial details
    if trial_status:
        lines.append(f'<div class="p-trial-note"><b>Trial:</b> {esc(trial_status)}</div>')

    # Plans table
    if plans:
        lines.append('<table class="p-pricing-table"><caption class="sr">Pricing plans</caption>')
        lines.append("<thead><tr><th scope=\"col\">Plan</th><th scope=\"col\">Price</th><th scope=\"col\">Details</th></tr></thead>")
        lines.append("<tbody>")
        for plan in plans:
            if not isinstance(plan, dict):
                continue
            plan_name = esc(plan.get("name", ""))
            price_m = plan.get("priceMonthly")
            price_a = plan.get("priceAnnualMonthlyEquivalent")
            notes = esc(plan.get("notes", ""))
            limits = plan.get("limits", {})

            if price_m is not None:
                if price_m > 0:
                    price_str = f"${int(price_m)}/mo"
                    if price_a is not None and price_a > 0:
                        price_str += f" or ${int(price_a)}/mo billed annually"
                else:
                    price_str = "Free"
            else:
                price_str = "Custom"

            details_parts = []
            if notes:
                details_parts.append(notes)
            if limits:
                limit_strs = []
                for k, v in limits.items():
                    limit_strs.append(f"{esc(str(k))}: {esc(str(v))}")
                if limit_strs:
                    details_parts.append("; ".join(limit_strs))

            details_str = "; ".join(details_parts) if details_parts else "—"
            lines.append(f"<tr><th scope=\"row\">{plan_name}</th><td>{price_str}</td><td>{details_str}</td></tr>")
        lines.append("</tbody></table>")

    # Source links
    if source_urls:
        lines.append('<div class="p-pricing-sources">')
        for url in source_urls:
            lines.append(f'<p><a href="{esc(url)}" target="_blank" rel="nofollow">Check current pricing</a></p>')
        lines.append("</div>")

    lines.append("</section>")
    return "\n".join(lines)


def render_capabilities_section(data: dict) -> str:
    factual = data.get("factual_profile", {})
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))

    capabilities = factual.get("capabilities", [])
    items = []
    for cap in capabilities:
        if isinstance(cap, dict):
            desc = cap.get("description", "")
            if desc:
                items.append(str(desc))
            elif "claim_id" in cap:
                # Skip claim_id-only capabilities with no description
                continue
        elif isinstance(cap, str) and cap.strip():
            items.append(cap.strip())

    if not items:
        return ""

    lines = []
    lines.append(f'<section class="p-sec" id="capabilities">')
    lines.append(f"<h2>{name} key capabilities</h2>")
    lines.append(render_ul(items))
    lines.append("</section>")
    return "\n".join(lines)


def render_limitations_section(data: dict) -> str:
    factual = data.get("factual_profile", {})
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))

    limitations = list_items(factual.get("limitations", []))
    if not limitations:
        return ""

    lines = []
    lines.append(f'<section class="p-sec" id="limitations">')
    lines.append(f"<h2>{name} important limitations</h2>")
    lines.append('<div class="p-limitation-area">')
    lines.append(render_ul(limitations, "tl no"))
    lines.append("</div></section>")
    return "\n".join(lines)


def render_who_sections(data: dict) -> str:
    """Render 'Who should choose' and 'Who should skip' sections."""
    editorial = data.get("editorial", {})
    factual = data.get("factual_profile", {})
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))

    # Who should choose — from audiences or best_for
    audiences = list_items(factual.get("audiences", []))
    best_for = list_items(editorial.get("best_for", []))
    choose_items = audiences if audiences else best_for

    # Who should skip — from not_recommended_for
    skip_items = list_items(editorial.get("not_recommended_for", []))

    if not choose_items and not skip_items:
        return ""

    lines = []
    lines.append('<section class="p-sec" id="who-should-choose">')

    if choose_items:
        lines.append(f"<h2>Who should choose {name}</h2>")
        lines.append(render_ul(choose_items, "tl yes"))

    if skip_items:
        lines.append(f'<h2 id="who-should-skip">Who should skip {name}</h2>')
        lines.append(render_ul(skip_items, "tl no"))

    lines.append("</section>")
    return "\n".join(lines)


def render_alternatives_section(data: dict) -> str:
    relationships = data.get("relationships", {})
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))

    alternatives = list_items(relationships.get("alternatives", []))
    if not alternatives:
        return ""

    lines = []
    lines.append(f'<section class="p-sec" id="alternatives">')
    lines.append(f"<h2>{name} alternatives</h2>")
    lines.append('<div class="p-alt-grid">')

    for alt_id in alternatives[:6]:
        alt_slug = tool_slug_for_id(alt_id)
        alt_route = tool_route(alt_id)
        alt_name = alt_id.replace("-", " ").title()
        lines.append(f'<div class="p-alt-card">')
        lines.append(f'<a href="{alt_route}" class="p-alt-link">')
        lines.append(f"<b>{esc(alt_name)}</b>")
        lines.append(f'<span class="p-alt-action">View profile →</span>')
        lines.append("</a></div>")

    lines.append("</div></section>")
    return "\n".join(lines)


def render_comparisons_section(data: dict) -> str:
    relationships = data.get("relationships", {})
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))

    comparisons = list_items(relationships.get("meaningful_comparisons", []))
    comparisons = comparisons + list_items(relationships.get("comparisons", []))
    # Deduplicate
    seen = set()
    unique_comparisons = []
    for c in comparisons:
        if c not in seen:
            seen.add(c)
            unique_comparisons.append(c)
    comparisons = unique_comparisons

    if not comparisons:
        return ""

    lines = []
    lines.append(f'<section class="p-sec" id="comparisons">')
    lines.append(f"<h2>Compare {name} with</h2>")
    lines.append('<div class="p-comp-list">')

    for comp_slug in comparisons[:5]:
        route = comparison_route(comp_slug)
        if route:
            comp_name = comp_slug.replace("-vs-", " vs ").replace("-", " ").title()
            lines.append(f'<a href="{route}" class="p-comp-link"><b>{esc(comp_name)}</b></a>')

    lines.append("</div></section>")
    return "\n".join(lines)


def render_evidence_section(data: dict) -> str:
    evidence = data.get("evidence", {})
    claims = data.get("claims", [])
    pricing = data.get("pricing", {})
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))

    source_urls = list_items(pricing.get("sourceUrls", []))
    checked_on = pricing.get("checkedOn", "")
    confidence = evidence.get("confidence", "")
    test_status = evidence.get("test_status", "")

    # Build evidence items
    evidence_items = []
    if checked_on and source_urls:
        evidence_items.append(f"Pricing verified from official source on {esc(checked_on)}")
    elif checked_on:
        evidence_items.append(f"Information last checked {esc(checked_on)}")

    if confidence == "unverified":
        evidence_items.append("Research-backed assessment — pricing not yet verified")
    elif confidence == "verified":
        evidence_items.append("Verified from official sources")

    if test_status == "research_only":
        evidence_items.append("Research-based assessment")

    # Claims
    claim_items = []
    for claim in claims:
        if isinstance(claim, dict):
            text = claim.get("text", "")
            source = claim.get("sourceUrl", "")
            if text:
                claim_items.append(f"{esc(text)}")

    if not evidence_items and not claim_items and not source_urls:
        return ""

    lines = []
    lines.append(f'<section class="p-sec" id="evidence">')
    lines.append(f"<h2>Sources &amp; evidence</h2>")

    if evidence_items:
        lines.append('<div class="p-evidence-strip">')
        for item in evidence_items:
            lines.append(f"<p>{item}</p>")
        lines.append("</div>")

    if claim_items:
        lines.append("<h3>Verified claims</h3>")
        lines.append(render_ul(claim_items))

    if source_urls:
        lines.append("<h3>Official sources</h3>")
        for url in source_urls:
            lines.append(f'<p><a href="{esc(url)}" target="_blank" rel="nofollow">{esc(url)}</a></p>')

    lines.append("</section>")
    return "\n".join(lines)


def render_faq_section(data: dict) -> str:
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))
    editorial = data.get("editorial", {})
    best_for = list_items(editorial.get("best_for", []))
    best_for_text = best_for[0] if best_for else ""

    lines = []
    lines.append(f'<section class="p-sec" id="questions">')
    lines.append(f"<h2>{name} FAQ</h2>")
    lines.append('<div class="faqlist">')

    # FAQ 1: Who should start
    if best_for_text:
        lines.append('<div class="qa">')
        lines.append(f'<button aria-controls="fa1" aria-expanded="false" id="fq1" type="button"><span>Who should start with {name}?</span><i aria-hidden="true" class="pm"></i></button>')
        lines.append(f'<div aria-labelledby="fq1" class="ans" id="fa1" role="region"><div><p>Start with it if your main need is {esc(best_for_text)}.</p></div></div>')
        lines.append("</div>")

    # FAQ 2: Check pricing
    lines.append('<div class="qa">')
    lines.append(f'<button aria-controls="fa2" aria-expanded="false" id="fq2" type="button"><span>Should I check the current plan before buying?</span><i aria-hidden="true" class="pm"></i></button>')
    lines.append('<div aria-labelledby="fq2" class="ans" id="fa2" role="region"><div><p>Yes. Features, limits and prices change, so confirm the latest details on the official site.</p></div></div>')
    lines.append("</div>")

    lines.append("</div></section>")
    return "\n".join(lines)


def render_affiliate_disclosure(data: dict) -> str:
    monetization = data.get("monetization", {})
    affiliate_status = monetization.get("affiliate_status", "")

    lines = []
    if affiliate_status == "active":
        lines.append('<p class="p-note"><span class="t">Some links may become affiliate links.</span> If a link is monetized, ToolNest may receive a commission at no extra cost to the buyer. <a href="/affiliate-disclosure.html">Read the disclosure</a>.</p>')
    else:
        lines.append('<p class="p-note">ToolNest is independent. We may earn a commission from qualifying purchases at no extra cost to you. <a href="/affiliate-disclosure.html">Read the disclosure</a>.</p>')
    return "\n".join(lines)


def render_aside(data: dict) -> str:
    """Render the sidebar (p-aside) with pricing panel and related links."""
    identity = data.get("identity", {})
    name = esc(identity.get("name", ""))
    official_url = esc(identity.get("official_url", ""))
    monetization = data.get("monetization", {})
    cta_url = esc(monetization.get("official_non_affiliate_url", official_url))
    cat = esc(category_label(data))
    pricing = data.get("pricing", {})
    factual = data.get("factual_profile", {})

    # Pricing summary for sidebar
    plans = pricing.get("plans", [])
    first_paid = ""
    for plan in plans:
        if isinstance(plan, dict):
            p = plan.get("priceMonthly")
            if p and p > 0:
                first_paid = f"${int(p)}/mo"
                break

    pricing_summary = ""
    if first_paid:
        if pricing.get("freePlan") or factual.get("free_plan_status"):
            pricing_summary = f"Free + from {first_paid}"
        else:
            pricing_summary = f"From {first_paid}"
    elif factual.get("free_plan_status"):
        pricing_summary = "Free plan available"
    elif pricing.get("pricing_status"):
        pricing_summary = esc(pricing.get("pricing_status", ""))

    # Related tools
    relationships = data.get("relationships", {})
    related = list_items(relationships.get("related_tools", []))

    lines = []
    lines.append('<aside class="p-aside">')

    # Pricing panel
    lines.append('<div class="p-aside-panel">')
    lines.append(f"<h3>{name} pricing</h3>")
    if pricing_summary:
        lines.append(f'<p class="p-aside-price">{esc(pricing_summary)}</p>')
    if cta_url:
        lines.append(f'<a class="btn" href="{cta_url}" rel="sponsored nofollow noopener" target="_blank">Visit {name}</a>')
    lines.append("</div>")

    # Category link
    lines.append('<div class="p-aside-panel">')
    lines.append(f"<h3>Category</h3>")
    cat_slug = category_slug(cat)
    lines.append(f'<a href="/category/{esc(cat_slug)}.html">{esc(cat)}</a>')
    lines.append("</div>")

    # Related tools
    if related:
        lines.append('<div class="p-aside-panel">')
        lines.append("<h3>Related tools</h3>")
        lines.append("<ul>")
        for rel_id in related[:5]:
            rel_slug = tool_slug_for_id(rel_id)
            rel_name = rel_id.replace("-", " ").title()
            lines.append(f'<li><a href="/tools/{rel_slug}.html">{esc(rel_name)}</a></li>')
        lines.append("</ul>")
        lines.append("</div>")

    lines.append("</aside>")
    return "\n".join(lines)


def generate_page(data: dict) -> str:
    """Generate a complete HTML page for a tool."""
    identity = data.get("identity", {})
    name = identity.get("name", "")
    slug = identity.get("slug", identity.get("id", ""))
    official_url = identity.get("official_url", "")
    logo = identity.get("logo", "")
    cat = category_label(data)

    discovery = data.get("discovery", {})
    use_cases = list_items(discovery.get("use_cases", []))
    lede = first_non_empty(use_cases[0] if use_cases else "")

    editorial = data.get("editorial", {})
    best_for = list_items(editorial.get("best_for", []))
    best_for_text = best_for[0] if best_for else ""

    monetization = data.get("monetization", {})
    cta_url = monetization.get("official_non_affiliate_url", official_url)

    freshness = data.get("freshness", {})
    last_reviewed = data.get("lastReviewed", "")
    if not last_reviewed:
        last_reviewed = freshness.get("updated_at", "")
    reviewed_month = ""
    if last_reviewed:
        match = re.match(r"(\d{4})-(\d{2})", str(last_reviewed))
        if match:
            year = match.group(1)
            month_num = int(match.group(2))
            months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
            reviewed_month = f"Last reviewed {months[month_num - 1]} {year}"

    # Build description
    desc_parts = []
    if lede:
        desc_parts.append(esc(lede))
    desc_parts.append("This review explains the strengths, trade-offs and ideal use cases in plain English.")
    description = ". ".join(desc_parts) if desc_parts else "Editorial review covering strengths, trade-offs, pricing, and who should choose or skip this tool."

    # Title
    title = f"{esc(name)} Review: {esc(cat)} Platform | ToolNest"

    # H1
    h1 = f"{esc(name)} review: who it is for and who should skip it"

    # Canonical
    canonical = f"{PUBLIC_HOST}/tools/{slug}.html"

    # Logo HTML
    logo_html = ""
    if logo:
        logo_html = f'<img alt="{esc(name)}" class="wm" data-logo="{esc(slug)}" height="40" src="{esc(logo)}" style="height:40px" width="149" decoding="async"/ fetchpriority="high">'

    # CTA button
    cta_html = ""
    if cta_url:
        cta_html = f'<a class="btn big" data-page="tool" data-pos="hero" data-tool="{esc(slug)}" href="{esc(cta_url)}" rel="sponsored nofollow noopener" target="_blank"><span class="sr">Visit {esc(name)}</a>'

    # Build main content sections
    sections = []
    sections.append(render_identity_section(data))
    sections.append(render_best_for_section(data))
    sections.append(render_pricing_section(data))
    sections.append(render_capabilities_section(data))
    sections.append(render_limitations_section(data))
    sections.append(render_who_sections(data))
    sections.append(render_alternatives_section(data))
    sections.append(render_comparisons_section(data))
    sections.append(render_evidence_section(data))
    sections.append(render_faq_section(data))
    sections.append(render_affiliate_disclosure(data))

    main_content = "\n".join(s for s in sections if s)

    # Build aside
    aside_html = render_aside(data)

    # Structured data
    breadcrumb_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": str(PUBLIC_HOST)},
            {"@type": "ListItem", "position": 2, "name": esc(cat), "item": f"{PUBLIC_HOST}/category/{cat.lower().replace(' ', '-')}.html"},
            {"@type": "ListItem", "position": 3, "name": h1, "item": canonical}
        ]
    }, separators=(",", ":"))

    article_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"{esc(name)} Review: {esc(cat)} Platform | ToolNest",
        "description": description,
        "url": canonical,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "author": {"@type": "Organization", "name": "ToolNest Editorial", "url": f"{PUBLIC_HOST}/editorial-policy.html"},
        "publisher": {"@type": "Organization", "name": "ToolNest", "url": str(PUBLIC_HOST), "logo": {"@type": "ImageObject", "url": f"{PUBLIC_HOST}/assets/og-default.png"}},
        "image": f"{PUBLIC_HOST}/assets/og-default.png"
    }, separators=(",", ":"))

    webpage_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"{esc(name)} Review: Pros, Cons, Features & Best For (2026)",
        "url": canonical,
        "description": description,
        "isPartOf": {"@type": "WebSite", "name": "ToolNest", "url": str(PUBLIC_HOST)}
    }, separators=(",", ":"))

    software_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": esc(name),
        "url": canonical,
        "publisher": {"@type": "Organization", "name": "ToolNest", "url": str(PUBLIC_HOST)}
    }, separators=(",", ":"))

    # Build the full HTML
    html_parts = []
    html_parts.append('<!doctype html><html lang="en"><head>')
    html_parts.append(f'<title>{title}</title>')
    html_parts.append('<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    html_parts.append('<meta name="author" content="ToolNest Editorial"><link rel="author" href="/about.html">')
    html_parts.append('<link rel="stylesheet" href="/assets/site.min.css">')
    html_parts.append(f'<script type="application/ld+json">{webpage_json}</script>')
    html_parts.append('<link rel="stylesheet" href="/assets/mobile-nav.min.css">')
    html_parts.append('<script src="/assets/mobile-nav.min.js" defer></script>')
    html_parts.append('<meta property="og:site_name" content="ToolNest">')
    html_parts.append('<meta property="og:type" content="article">')
    html_parts.append('<meta property="og:locale" content="en_US">')
    html_parts.append('<meta property="og:image:width" content="1200">')
    html_parts.append('<meta property="og:image:height" content="630">')
    html_parts.append(f'<script type="application/ld+json" id="tn-software-application">{software_json}</script>')
    html_parts.append('')
    html_parts.append('<link rel="preconnect" href="https://fonts.googleapis.com">')
    html_parts.append('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    html_parts.append('<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,500..800&family=Instrument+Sans:wght@400;500;600;700&display=optional" onload="this.onload=null;this.rel=\'stylesheet\'">')
    html_parts.append('<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,500..800&family=Instrument+Sans:wght@400;500;600;700&display=optional"></noscript>')
    html_parts.append('')
    html_parts.append('<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">')
    html_parts.append('')
    html_parts.append(f'<meta name="description" content="{description}">')
    html_parts.append(f'<link rel="canonical" href="{canonical}">')
    html_parts.append(f'<meta property="og:title" content="{title}">')
    html_parts.append(f'<meta property="og:description" content="{description}">')
    html_parts.append(f'<meta property="og:url" content="{canonical}">')
    html_parts.append(f'<meta property="og:image" content="{PUBLIC_HOST}/assets/og-default.png">')
    html_parts.append('<meta name="twitter:card" content="summary_large_image">')
    html_parts.append(f'<meta name="twitter:title" content="{title}">')
    html_parts.append(f'<meta name="twitter:description" content="{description}">')
    html_parts.append(f'<meta name="twitter:image" content="{PUBLIC_HOST}/assets/og-default.png">')
    html_parts.append('<script async src="https://www.googletagmanager.com/gtag/js?id=G-VS0TB85N2G"></script>')
    html_parts.append('<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","G-VS0TB85N2G");</script>')
    html_parts.append(f'<script type="application/ld+json">{breadcrumb_json}</script>')
    html_parts.append(f'<script type="application/ld+json">{article_json}</script>')
    html_parts.append('<meta name="robots" content="index,follow,max-image-preview:large">')
    html_parts.append('</head><body>')
    html_parts.append('')
    html_parts.append('<a class="skip" href="#top">Skip to content</a>')

    # Header
    html_parts.append('<header class="top"><div class="bar"><a aria-label="ToolNest home" class="logo" href="/"><span>Tool<i>Nest</i></span></a>')
    html_parts.append('<nav aria-label="Main"><a href="/tools/index.html" aria-current="page">Tools</a><a href="/category/index.html">Categories</a><a href="/compare/index.html">Compare</a><a href="/best/index.html">Best of</a><a class="btn" href="/#picker">Find my tool</a></nav>')
    html_parts.append('<button class="mnav-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="mnav"><span class="mnav-ico" aria-hidden="true"></span></button></div>')
    html_parts.append('<nav class="mnav" id="mnav" aria-label="Mobile" hidden><a href="/">Home</a><a href="/tools/index.html">Tools</a><a href="/category/index.html">Categories</a><a href="/compare/index.html">Compare</a><a href="/alternatives/index.html">Alternatives</a><a href="/best/index.html">Best of</a><a class="btn" href="/#picker">Find my tool</a></nav></header>')

    # Main
    html_parts.append('<main id="top" tabindex="-1">')

    # Hero
    cat_slug = category_slug(cat)
    html_parts.append(f'<section class="hero phero"><div aria-hidden="true" class="hero-bg"><i class="blob b1"></i><i class="blob b2"></i><div class="gridlines"></div></div>')
    html_parts.append(f'<div class="wrap"><nav aria-label="Breadcrumb" class="crumbs"><ol><li><a href="/">Home</a></li><li><a href="/category/{esc(cat_slug)}.html">{esc(cat)}</a></li><li aria-current="page">{h1}</li></ol></nav>')
    html_parts.append(f'<div class="p-plate"><div class="plate">{logo_html}</div><span class="badge">{esc(cat)}</span></div>')
    html_parts.append(f'<p class="eyebrow">Tool review   {esc(cat)}</p>')
    html_parts.append(f'<h1>{h1}</h1>')
    if lede:
        html_parts.append(f'<p class="lede">{esc(lede)}. This review explains the strengths, trade-offs and ideal use cases in plain English.</p>')
    html_parts.append(f'<div class="s-cta">{cta_html}<a class="lnk" href="#best-for">Who it is for</a></div>')
    if reviewed_month:
        html_parts.append(f'<div class="pmeta"><span>{esc(reviewed_month)}</span><a href="/about.html">How we research and choose tools</a></div>')
    html_parts.append("</div></section>")

    # Trust strip
    html_parts.append('<div class="wrap tn-trust-strip"><p class="tn-research-line">ToolNest Research &middot; Editorial review 2026-11-23 &middot; <a href="/how-we-test.html">Research-based profile</a></p><p class="tn-trust-links"><a href="/how-we-test.html">Methodology</a><a href="/editorial-policy.html">Editorial policy</a><a href="/contact.html">Corrections</a><a href="/affiliate-disclosure.html">Affiliate disclosure</a></p></div>')

    # Content layout
    html_parts.append('<div class="wrap p-layout"><div class="p-main">')
    html_parts.append(main_content)
    html_parts.append("</div>")
    html_parts.append(aside_html)
    html_parts.append("</div>")
    html_parts.append("</main>")

    # Footer
    html_parts.append('<footer><div class="wrap"><div class="f-grid"><nav aria-label="About this site" class="f-col"><h2>About</h2>')
    html_parts.append('<a href="/about.html">How we research and choose tools</a>')
    html_parts.append('<a href="/affiliate-disclosure.html">Disclosure</a>')
    html_parts.append('<a href="/privacy.html">Privacy policy</a>')
    html_parts.append('<a href="/terms.html">Terms of use</a>')
    html_parts.append('<a href="/contact.html">Contact</a>')
    html_parts.append('<a href="/how-we-test.html">How we test</a>')
    html_parts.append('<a href="/editorial-policy.html">Editorial policy</a>')
    html_parts.append('</nav></div><div class="f-base"><p><strong>Disclosure.</strong> Some links may be affiliate links. Product names belong to their owners. Verify current features and prices on the official site.</p>')
    html_parts.append('<div class="f-end"><p>© 2026 ToolNest</p><a class="totop" href="#top">Back to top</a></div></div></div></footer>')
    html_parts.append("</body></html>")

    return "\n".join(html_parts)


def main():
    parser = argparse.ArgumentParser(description="Regenerate tool profile HTML pages")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without writing")
    parser.add_argument("--tool", type=str, help="Regenerate only a specific tool by slug")
    args = parser.parse_args()

    # Get all tool JSON files
    json_files = sorted(TOOLS_JSON_DIR.glob("*.json"))
    if args.tool:
        json_files = [TOOLS_JSON_DIR / f"{args.tool}.json"]

    count = 0
    skipped = 0
    for json_path in json_files:
        slug = json_path.stem
        data = load_tool(slug)
        if not data:
            skipped += 1
            continue

        html_content = generate_page(data)
        html_path = TOOLS_HTML_DIR / f"{slug}.html"

        if args.dry_run:
            print(f"  Would write: {html_path} ({len(html_content)} chars)")
        else:
            html_path.write_text(html_content, encoding="utf-8", newline="\n")
            print(f"  Written: {html_path}")

        count += 1

    print(f"\nDone: {count} profiles generated, {skipped} skipped")


if __name__ == "__main__":
    main()
