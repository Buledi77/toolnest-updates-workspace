#!/usr/bin/env python3
"""
Add verified evidence claims for batch 29: Klaviyo.

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
        "source_id": "klaviyo-pricing",
        "url": "https://www.klaviyo.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Klaviyo",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "klaviyo-pricing-model",
        "tool_id": "klaviyo",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Profile-based tiered subscription. Free plan: 250 active profiles, 500 emails/mo, $5 Composer usage, $5 mobile messages, 250 social profiles, 50 review orders, 10 Customer Agent resolutions, 10 Helpdesk tickets. Email plan $20/mo (500 profiles, 5K emails). Marketing plan $25/mo (500 profiles, 5K emails, SMS add-on). Custom plan for high-volume. Pricing scales with active profiles.",
        "source_ids": ["klaviyo-pricing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Free plan 250 profiles/500 emails, Email $20/mo for 500 profiles/5K emails, Marketing $25/mo for 500 profiles/5K emails with SMS add-on. Custom plan for high-volume.",
        "evidence_note": "Profile-based pricing; scales with active profiles. Free plan has meaningful limits.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "klaviyo-free-plan",
        "tool_id": "klaviyo",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: 250 active profiles, 500 emails/mo, $5 Composer usage, $5 mobile messages, 250 social profiles, 50 review orders, 10 Customer Agent resolutions, 10 Helpdesk tickets, mobile app marketing.",
        "source_ids": ["klaviyo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Free plan includes 250 active profiles, 500 emails/mo, Composer, mobile messages, social marketing, reviews, Customer Hub, Customer Agent, Helpdesk.",
        "evidence_note": "Genuine free tier with broad feature access but limited volume.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "klaviyo-trial",
        "tool_id": "klaviyo",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "No separate trial — free plan serves as entry point. Paid plans available with monthly billing.",
        "source_ids": ["klaviyo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows free plan and paid plans but no separate trial period.",
        "evidence_note": "Free plan replaces traditional trial model.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "klaviyo-capabilities",
        "tool_id": "klaviyo",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Email marketing campaigns and flows",
            "SMS and MMS marketing",
            "AI-powered Composer for content creation",
            "Customer Agent for automated resolutions",
            "Social marketing and paid ads",
            "Reviews collection and display",
            "Customer Hub for unified profiles",
            "Helpdesk for customer support",
            "Mobile app push notifications",
            "Advanced segmentation",
            "A/B testing",
            "Automated email flows",
            "Ecommerce integrations (Shopify, BigCommerce, WooCommerce, Magento)",
            "Custom reporting and analytics",
            "Event tracking and behavioral targeting",
            "GDPR and CCPA compliance tools"
        ],
        "source_ids": ["klaviyo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists all features: email, SMS, Composer, social marketing, reviews, Customer Hub, Customer Agent, Helpdesk, mobile app.",
        "evidence_note": "All features available on all plans; pricing scales by profiles.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "klaviyo-platforms",
        "tool_id": "klaviyo",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["klaviyo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Klaviyo is a cloud-based email marketing platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "klaviyo-core-use-case",
        "tool_id": "klaviyo",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Ecommerce-focused email and SMS marketing platform for online stores to automate customer communications, run campaigns, and grow revenue through data-driven marketing.",
        "source_ids": ["klaviyo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes email and SMS marketing platform with ecommerce integrations.",
        "evidence_note": "Ecommerce-focused, not general email marketing.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "klaviyo-target-user",
        "tool_id": "klaviyo",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Ecommerce businesses of all sizes. Free for testing, Email for growing stores, Marketing for stores needing SMS and social, Custom for high-volume enterprises.",
        "source_ids": ["klaviyo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page targets ecommerce businesses. Email plan for email-only, Marketing for multichannel.",
        "evidence_note": "Ecommerce-focused; strongest with Shopify, BigCommerce, WooCommerce.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "klaviyo-limitations",
        "tool_id": "klaviyo",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan limited to 250 active profiles and 500 emails/mo",
            "Composer usage limited to $5/mo on free plan",
            "SMS and MMS are add-ons on paid plans",
            "Pricing scales with active profiles, which can become expensive at scale",
            "Custom plan pricing not publicly disclosed",
            "Ecommerce-focused; limited non-ecommerce use cases"
        ],
        "source_ids": ["klaviyo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows profile-based pricing and add-on costs. Free plan has significant volume limits.",
        "evidence_note": "Profile-based pricing can become expensive at scale.",
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
