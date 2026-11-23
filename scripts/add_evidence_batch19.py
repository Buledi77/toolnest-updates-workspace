#!/usr/bin/env python3
"""
Add verified evidence claims for batch 19: Omnisend.

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
        "source_id": "omnisend-pricing",
        "url": "https://www.omnisend.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Omnisend",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "omnisend-support-pricing",
        "url": "https://support.omnisend.com/en/articles/3533018-omnisend-pricing-plans-2026",
        "source_type": "official_docs",
        "publisher": "Omnisend",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "omnisend-blog-email",
        "url": "https://www.omnisend.com/blog/cheap-email-marketing",
        "source_type": "official_product",
        "publisher": "Omnisend",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "omnisend-pricing-model",
        "tool_id": "omnisend",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Contact-based tiered subscription. Free plan: 500 emails/mo, 250 contacts, 500 web push notifications. Standard $16/mo (500 contacts, 6,000 emails/mo). Pro $59/mo (unlimited emails, SMS included at $0.007/SMS). SMS rates vary by country and volume. Email credits on Standard = contacts × 12.",
        "source_ids": ["omnisend-pricing", "omnisend-support-pricing", "omnisend-blog-email"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Free 500 emails/250 contacts, Standard $16/mo, Pro $59/mo. Support docs confirm email credits = contacts × 12 on Standard. Blog confirms SMS rates from $0.007.",
        "evidence_note": "Contact-based pricing; email credits scale with contacts on Standard.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "omnisend-free-plan",
        "tool_id": "omnisend",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: 500 emails/mo, 250 contacts, 500 web push notifications/mo, pre-built ecommerce workflows, segmentation, A/B testing, pop-ups, landing pages, 24/7 support. Omnisend branding on emails and forms.",
        "source_ids": ["omnisend-pricing", "omnisend-support-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Free plan includes workflows, segmentation, A/B testing, pop-ups, landing pages, 24/7 support. Support docs confirm 500 emails/250 contacts.",
        "evidence_note": "Genuine free tier with ecommerce features.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "omnisend-trial",
        "tool_id": "omnisend",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "No separate trial — free plan serves as entry point. Paid plans available with monthly billing.",
        "source_ids": ["omnisend-pricing"],
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
        "claim_id": "omnisend-capabilities",
        "tool_id": "omnisend",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Email marketing campaigns",
            "SMS marketing (Pro plan)",
            "Web push notifications",
            "Pre-built ecommerce workflows and automations",
            "Segmentation and A/B testing",
            "Pop-ups and landing pages",
            "AI features (subject line, copywriting, segment builder, Forms AI)",
            "Personalized product recommendations (Pro)",
            "Dynamic content (Pro)",
            "Customer lifecycle stages and RFM analysis",
            "Churn prediction",
            "Omnisend MCP connection to ChatGPT and Claude",
            "Shopify, WooCommerce, BigCommerce integrations",
            "24/7 live chat and email support",
            "Advanced reporting (Pro)"
        ],
        "source_ids": ["omnisend-pricing", "omnisend-support-pricing", "omnisend-blog-email"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Support docs confirm plan differences. Blog confirms AI features and MCP connections.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "omnisend-platforms",
        "tool_id": "omnisend",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["omnisend-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Omnisend is a cloud-based email marketing platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "omnisend-core-use-case",
        "tool_id": "omnisend",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Ecommerce-focused email and SMS marketing platform for online stores to automate customer communications, run campaigns, and grow revenue through multichannel marketing.",
        "source_ids": ["omnisend-pricing", "omnisend-blog-email"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes ecommerce marketing platform. Blog positions it for ecommerce stores of all sizes.",
        "evidence_note": "Ecommerce-focused, not general email marketing.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "omnisend-target-user",
        "tool_id": "omnisend",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Ecommerce businesses of all sizes. Free for testing, Standard for growing stores, Pro for high-volume senders needing SMS and advanced features.",
        "source_ids": ["omnisend-pricing", "omnisend-blog-email"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Standard for 'growing and medium-sized businesses', Pro for 'high-volume senders'. Blog confirms ecommerce focus.",
        "evidence_note": "Ecommerce-focused; strongest with Shopify, WooCommerce, BigCommerce.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "omnisend-limitations",
        "tool_id": "omnisend",
        "field_path": "factual_profile.limitations",
        "value": [
            "Free plan limited to 500 emails/mo and 250 contacts",
            "Omnisend branding on emails and forms for free plan",
            "SMS marketing only available on Pro plan",
            "Advanced AI features (dynamic content, product recommendations) require Pro plan",
            "Standard plan email credits limited to contacts × 12",
            "Exceeding email limits on Standard blocks campaigns until renewal"
        ],
        "source_ids": ["omnisend-pricing", "omnisend-support-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows plan limits. Support docs confirm email credit calculation and blocking behavior.",
        "evidence_note": "Email credit limits on Standard can be restrictive for high-frequency sending.",
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
