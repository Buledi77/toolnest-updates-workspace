#!/usr/bin/env python3
"""
Add verified evidence claims for batch 20: Wishpond.

Sources: Official pricing pages, official feature pages.
Date: 2026-11-23
"""

import json
from pathlib import Path

LEDGER = Path("data/evidence/evidence-ledger.json")

with open(LEDGER) as f:
    ledger = json.load(f)

today = "2026-11-23"
stale = "2027-02-23"

new_sources = [
    {
        "source_id": "wishpond-homepage",
        "url": "https://wishpond.com",
        "source_type": "official_product",
        "publisher": "Wishpond",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "wishpond-landing-page",
        "url": "https://wishpond.com/landing-page",
        "source_type": "official_product",
        "publisher": "Wishpond",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "wishpond-blog-landing",
        "url": "https://wishpond.com/blog/best-landing-page-builders",
        "source_type": "official_product",
        "publisher": "Wishpond",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "wishpond-pricing-model",
        "tool_id": "wishpond",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Tiered subscription. Starting Out $49/mo, Everything You Need $99/mo, Rapid Growth $199/mo. All plans include access to full suite of marketing tools. Annual billing discount available.",
        "source_ids": ["wishpond-homepage", "wishpond-blog-landing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Blog: Starting Out $49/mo, Everything You Need $99/mo, Rapid Growth $199/mo. Homepage confirms all-in-one pricing model.",
        "evidence_note": "All plans include full suite; pricing scales by features and limits.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wishpond-free-plan",
        "tool_id": "wishpond",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan mentioned. Paid plans start at $49/mo.",
        "source_ids": ["wishpond-homepage"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage shows only paid plans starting at $49/mo. No free plan mentioned.",
        "evidence_note": "No free plan confirmed on official pages.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wishpond-trial",
        "tool_id": "wishpond",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Trial status unclear from official sources. 'Get Started Now' CTA on landing page.",
        "source_ids": ["wishpond-landing-page"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Landing page shows 'Get Started Now' CTA but no explicit trial mention.",
        "evidence_note": "Trial status not clearly stated on official pages.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wishpond-capabilities",
        "tool_id": "wishpond",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Landing page builder with drag-and-drop editor",
            "Contests and giveaways",
            "Popups and forms",
            "Email marketing and automation",
            "SMS marketing",
            "Website builder with AI",
            "A/B testing and AI optimization",
            "Lead generation and capture",
            "Marketing funnels",
            "Appointments scheduling",
            "Outbound sales tools",
            "CRM and email platform integrations (Mailchimp, HubSpot, Salesforce)",
            "Analytics and reporting",
            "Mobile-responsive templates",
            "Custom domains",
            "Dedicated marketing expert support"
        ],
        "source_ids": ["wishpond-homepage", "wishpond-landing-page", "wishpond-blog-landing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage lists all tools: landing pages, popups, forms, email, SMS, website builder, outbound sales. Landing page confirms drag-and-drop editor and AI optimization.",
        "evidence_note": "All-in-one marketing platform with broad tool suite.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wishpond-platforms",
        "tool_id": "wishpond",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["wishpond-homepage"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Wishpond operates as a web-based marketing platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wishpond-core-use-case",
        "tool_id": "wishpond",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "All-in-one marketing platform for small to medium businesses to create landing pages, run contests and giveaways, capture leads, and automate email and SMS marketing campaigns.",
        "source_ids": ["wishpond-homepage", "wishpond-landing-page"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage describes all-in-one marketing platform. Landing page focuses on conversion optimization and lead generation.",
        "evidence_note": "Broad marketing platform, not niche-focused.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wishpond-target-user",
        "tool_id": "wishpond",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to medium businesses needing marketing tools. Starting Out for small businesses, Everything You Need for growing businesses, Rapid Growth for scaling companies.",
        "source_ids": ["wishpond-homepage"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage targets small and medium-sized businesses across various industries.",
        "evidence_note": "SMB-focused; not designed for enterprise-scale operations.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wishpond-limitations",
        "tool_id": "wishpond",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "No free plan available",
            "Starting at $49/mo may be expensive for very small businesses",
            "Feature gating across tiers not fully detailed on public pages",
            "Enterprise pricing not publicly disclosed",
            "Marketing-focused; not a full CRM or analytics platform"
        ],
        "source_ids": ["wishpond-homepage", "wishpond-blog-landing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage shows pricing tiers but limited detail on feature differences. Blog confirms pricing structure.",
        "evidence_note": "Feature gating details not fully transparent on public pages.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
]

# Add sources
existing_source_ids = {s["source_id"] for s in ledger["sources"]}
added_sources = 0
for src in new_sources:
    if src["source_id"] not in existing_source_ids:
        ledger["sources"].append(src)
        added_sources += 1

# Add claims
existing_claim_ids = {c["claim_id"] for c in ledger["claims"]}
added_claims = 0
for claim in new_claims:
    if claim["claim_id"] not in existing_claim_ids:
        ledger["claims"].append(claim)
        added_claims += 1

with open(LEDGER, "w") as f:
    json.dump(ledger, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Added {added_sources} sources and {added_claims} claims")
print(f"Total sources: {len(ledger['sources'])}")
print(f"Total claims: {len(ledger['claims'])}")
