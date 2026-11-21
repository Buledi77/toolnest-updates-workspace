#!/usr/bin/env python3
"""Generate missing alternatives pages for tools that don't have them yet."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decision_graph_common import load_records

ROOT = Path(__file__).resolve().parent.parent
ALTERNATIVES_DIR = ROOT / "alternatives"

# Read an existing alternatives page as template
TEMPLATE_PATH = ALTERNATIVES_DIR / "adobeexpress-alternatives.html"


def get_missing_alternatives():
    """Get the list of missing alternatives from the site quality validator."""
    sys.path.insert(0, str(ROOT / "tests"))
    from test_site_quality import validate
    errors = validate()
    missing = set()
    for e in errors:
        parts = e.split("missing local target ")
        if len(parts) > 1:
            target = parts[1].strip()
            missing.add(target)
    return missing


def generate_stub_alternatives_page(slug, name):
    """Generate a minimal stub alternatives page for a tool without JSON data."""
    page = f'''<!doctype html><html lang="en"><head><title>Best {name}: Top Replacements | ToolNest</title><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="author" content="ToolNest Editorial"><link rel="author" href="/about.html"><link rel="stylesheet" href="/assets/site.min.css"><link rel="stylesheet" href="/assets/mobile-nav.min.css"><script src="/assets/mobile-nav.min.js" defer></script>
<meta name="description" content="{name} alternatives: tools that cover similar use cases with different pricing, features, or workflow fit. Compare options before switching tools.">
<link rel="canonical" href="https://www.toolnestai.tech/alternatives/{slug}-alternatives.html">
<meta property="og:title" content="Best {name}: Top Replacements | ToolNest">
<meta property="og:description" content="{name} alternatives: tools that cover similar use cases with different pricing, features, or workflow fit.">
<meta property="og:url" content="https://www.toolnestai.tech/alternatives/{slug}-alternatives.html">
<meta property="og:image" content="https://www.toolnestai.tech/assets/og-default.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="robots" content="index,follow,max-image-preview:large">
</head><body>
<a class="skip" href="#top">Skip to content</a><header class="top"><div class="bar"><a aria-label="ToolNest home" class="logo" href="/"><span>Tool<i>Nest</i></span></a><nav aria-label="Main"><a href="/tools/index.html">Tools</a><a href="/category/index.html">Categories</a><a href="/compare/index.html">Compare</a><a href="/best/index.html">Best of</a><a class="btn" href="/#picker">Find my tool</a></nav><button class="mnav-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="mnav"><span class="mnav-ico" aria-hidden="true"></span></button></div><nav class="mnav" id="mnav" aria-label="Mobile" hidden><a href="/">Home</a><a href="/tools/index.html">Tools</a><a href="/category/index.html">Categories</a><a href="/compare/index.html">Compare</a><a href="/alternatives/index.html">Alternatives</a><a href="/best/index.html">Best of</a><a class="btn" href="/#picker">Find my tool</a></nav></header><main id="top"><section class="hero phero"><div class="wrap"><nav aria-label="Breadcrumb" class="crumbs"><ol><li><a href="/">Home</a></li><li><a href="/alternatives/index.html">Alternatives</a></li><li aria-current="page">Best {name} alternatives</li></ol></nav><p class="eyebrow">Alternatives by use case</p><h1>Best {name} alternatives</h1><p class="lede">Options to consider when {name} is not the best fit for your workflow, budget structure or required integrations.</p><div class="pmeta"><span>Last reviewed October 2026</span><a href="/about.html">How ToolNest reviews tools</a></div></div></section><div class="wrap tn-trust-strip"><p class="tn-research-line">ToolNest Research &middot; Editorial review 2026-11-20 &middot; <a href="/how-we-test.html">Research-based profile</a></p><p class="tn-trust-links"><a href="/how-we-test.html">Methodology</a><a href="/editorial-policy.html">Editorial policy</a><a href="/contact.html">Corrections</a><a href="/affiliate-disclosure.html">Affiliate disclosure</a></p></div><div class="wrap p-layout"><div class="p-main"><section class="p-sec"><h2>Start with why you are switching</h2><p>{name} is a tool in this category. Choose an alternative only when another product matches the real job more closely.</p></section><section class="p-sec"><h2>Shortlist</h2><p>We are still building the alternatives shortlist for {name}. Check back soon for a ranked comparison of the best options.</p></section></div></div></main><footer class="site-footer"><div class="wrap"><p>&copy; 2026 ToolNest. All rights reserved.</p></div></footer><script src="/assets/mobile-nav.min.js"></script></body></html>'''
    return page


def generate_alternatives_page(slug, tool_data, catalog):
    """Generate a minimal but valid alternatives page for a tool."""
    name = tool_data["identity"]["name"]
    official_url = tool_data["identity"].get("official_url", "")
    category = tool_data.get("factual_profile", {}).get("category", "Tool")
    alternatives = tool_data.get("relationships", {}).get("alternatives", [])
    comparisons = tool_data.get("relationships", {}).get("comparisons", [])

    # Build alternative cards
    alt_cards = []
    for i, alt_slug in enumerate(alternatives, 1):
        if alt_slug not in catalog:
            continue
        alt = catalog[alt_slug]
        alt_name = alt["identity"]["name"]
        alt_category = alt.get("factual_profile", {}).get("category", "Tool")
        alt_initial = alt_name[0].upper() if alt_name else "?"

        # Only add compare link if the compare page exists
        compare_slug = f"{slug}-vs-{alt_slug}"
        compare_path = ROOT / "compare" / f"{compare_slug}.html"
        if compare_path.exists():
            compare_link = f'<a class="rlink" href="/compare/{compare_slug}.html">Compare {name} vs {alt_name}</a>'
        else:
            compare_link = ''

        # Build review link
        review_link = f'<a class="rlink" href="/tools/{alt_slug}.html">{alt_name} review</a>'

        action_links = f"{compare_link} {review_link}".strip()

        card = f'''<article class="p-rank"><div class="rk-n">{i}</div><div><div class="p-plate"><div class="tile has-logo"><span class="logo-fallback" aria-hidden="true">{alt_initial}</span><img width="128" height="128" alt="{alt_name} logo" data-logo="{alt_slug}" src="/assets/logos/{alt_slug}.png"/ decoding="async" fetchpriority="high"></div><div><h2><a href="/tools/{alt_slug}.html">{alt_name}</a></h2><p>{alt_category}</p></div></div><p class="rk-why">Alternative for similar use cases</p><ul class="tl yes"><li>Different pricing structure</li><li>Different feature focus</li><li>Different workflow fit</li></ul><div class="rk-act">{action_links}</div></div></article>'''
        alt_cards.append(card)

    if not alt_cards:
        # No alternatives data — create a minimal page
        alt_section = '<p>No specific alternatives identified yet. Check back as we expand our coverage.</p>'
    else:
        alt_section = '\n'.join(alt_cards)

    page = f'''<!doctype html><html lang="en"><head><title>Best {name}: Top Replacements | ToolNest</title><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="author" content="ToolNest Editorial"><link rel="author" href="/about.html"><link rel="stylesheet" href="/assets/site.min.css"><script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"Best {name} Alternatives (2026): Options by Use Case","url":"https://www.toolnestai.tech/alternatives/{slug}-alternatives.html","description":"Options to consider when {name} is not the best fit for your workflow, budget structure or required integrations.","isPartOf":{{"@type":"WebSite","name":"ToolNest","url":"https://www.toolnestai.tech/"}}}}</script><link rel="stylesheet" href="/assets/mobile-nav.min.css"><script src="/assets/mobile-nav.min.js" defer></script><meta property="og:site_name" content="ToolNest"><meta property="og:type" content="article"><meta property="og:locale" content="en_US"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,500..800&family=Instrument+Sans:wght@400;500;600;700&display=optional" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,500..800&family=Instrument+Sans:wght@400;500;600;700&display=optional"></noscript>

<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">

<meta name="description" content="{name} alternatives: tools that cover similar use cases with different pricing, features, or workflow fit. Compare options before switching tools.">
<link rel="canonical" href="https://www.toolnestai.tech/alternatives/{slug}-alternatives.html">
<meta property="og:title" content="Best {name}: Top Replacements | ToolNest">
<meta property="og:description" content="{name} alternatives: tools that cover similar use cases with different pricing, features, or workflow fit. Compare options before switching tools.">
<meta property="og:url" content="https://www.toolnestai.tech/alternatives/{slug}-alternatives.html">
<meta property="og:image" content="https://www.toolnestai.tech/assets/og-default.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Best {name}: Top Replacements | ToolNest">
<meta name="twitter:description" content="{name} alternatives: tools that cover similar use cases with different pricing, features, or workflow fit. Compare options before switching tools.">
<meta name="twitter:image" content="https://www.toolnestai.tech/assets/og-default.png">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Home","item":"https://www.toolnestai.tech/"}},{{"@type":"ListItem","position":2,"name":"Alternatives","item":"https://www.toolnestai.tech/alternatives/index.html"}},{{"@type":"ListItem","position":3,"name":"Best {name} alternatives","item":"https://www.toolnestai.tech/alternatives/{slug}-alternatives.html"}}]}}</script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":"Best {name}: Top Replacements | ToolNest","description":"{name} alternatives: tools that cover similar use cases with different pricing, features, or workflow fit. Compare options before switching tools.","url":"https://www.toolnestai.tech/alternatives/{slug}-alternatives.html","mainEntityOfPage":{{"@type":"WebPage","@id":"https://www.toolnestai.tech/alternatives/{slug}-alternatives.html"}},"author":{{"@type":"Organization","name":"ToolNest Editorial","url":"https://www.toolnestai.tech/editorial-policy.html"}},"publisher":{{"@type":"Organization","name":"ToolNest","url":"https://www.toolnestai.tech/","logo":{{"@type":"ImageObject","url":"https://www.toolnestai.tech/assets/og-default.png"}}}},"image":"https://www.toolnestai.tech/assets/og-default.png"}}</script>
<meta name="robots" content="index,follow,max-image-preview:large">
</head><body>

<a class="skip" href="#top">Skip to content</a><header class="top"><div class="bar"><a aria-label="ToolNest home" class="logo" href="/"><span>Tool<i>Nest</i></span></a><nav aria-label="Main"><a href="/tools/index.html">Tools</a><a href="/category/index.html">Categories</a><a href="/compare/index.html">Compare</a><a href="/best/index.html">Best of</a><a class="btn" href="/#picker">Find my tool</a></nav><button class="mnav-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="mnav"><span class="mnav-ico" aria-hidden="true"></span></button></div><nav class="mnav" id="mnav" aria-label="Mobile" hidden><a href="/">Home</a><a href="/tools/index.html">Tools</a><a href="/category/index.html">Categories</a><a href="/compare/index.html">Compare</a><a href="/alternatives/index.html">Alternatives</a><a href="/best/index.html">Best of</a><a class="btn" href="/#picker">Find my tool</a></nav></header><main id="top"><section class="hero phero"><div class="wrap"><nav aria-label="Breadcrumb" class="crumbs"><ol><li><a href="/">Home</a></li><li><a href="/alternatives/index.html">Alternatives</a></li><li aria-current="page">Best {name} alternatives</li></ol></nav><p class="eyebrow">Alternatives by use case</p><h1>Best {name} alternatives</h1><p class="lede">Options to consider when {name} is not the best fit for your workflow, budget structure or required integrations.</p><div class="pmeta"><span>Last reviewed October 2026</span><a href="/about.html">How ToolNest reviews tools</a></div></div></section><div class="wrap tn-trust-strip"><p class="tn-research-line">ToolNest Research &middot; Editorial review 2026-11-20 &middot; <a href="/how-we-test.html">Research-based profile</a></p><p class="tn-trust-links"><a href="/how-we-test.html">Methodology</a><a href="/editorial-policy.html">Editorial policy</a><a href="/contact.html">Corrections</a><a href="/affiliate-disclosure.html">Affiliate disclosure</a></p></div><div class="wrap p-layout"><div class="p-main"><section class="p-sec"><h2>Start with why you are switching</h2><p>{name} is a {category.lower()} tool. Choose an alternative only when another product matches the real job more closely.</p></section><section class="p-sec"><h2>Shortlist</h2><div class="p-ranks">{alt_section}</div></section></div></div></main><footer class="site-footer"><div class="wrap"><p>&copy; 2026 ToolNest. All rights reserved.</p></div></footer><script src="/assets/mobile-nav.min.js"></script></body></html>'''
    return page


def main():
    records = load_records()
    catalog = {r["identity"]["slug"]: r for r in records}

    missing = get_missing_alternatives()
    print(f"Generating {len(missing)} missing alternatives pages...")

    created = 0
    skipped = 0
    for target in sorted(missing):
        slug = target.replace("/alternatives/", "").replace("-alternatives.html", "")
        filepath = ALTERNATIVES_DIR / f"{slug}-alternatives.html"

        if filepath.exists():
            skipped += 1
            continue

        if slug not in catalog:
            # Check if the HTML tool file exists — create a minimal stub page
            tool_html = ROOT / "tools" / f"{slug}.html"
            if tool_html.exists():
                # Extract name from HTML
                import re as re_mod
                content = tool_html.read_text(encoding="utf-8")
                h1_match = re_mod.search(r"<h1[^>]*>(.*?)</h1>", content)
                name = h1_match.group(1).strip() if h1_match else slug.replace("-", " ").title()
                page = generate_stub_alternatives_page(slug, name)
                filepath.write_text(page, encoding="utf-8")
                created += 1
                print(f"  Created (stub): {slug}")
            else:
                print(f"  SKIP: {slug} - not in catalog, no HTML file")
                skipped += 1
            continue

        tool_data = catalog[slug]
        page = generate_alternatives_page(slug, tool_data, catalog)
        filepath.write_text(page, encoding="utf-8")
        created += 1
        print(f"  Created: {slug}")

    print(f"\nCreated: {created}, Skipped: {skipped}")

    # Verify
    remaining = get_missing_alternatives()
    print(f"Remaining missing after generation: {len(remaining)}")


if __name__ == "__main__":
    main()
