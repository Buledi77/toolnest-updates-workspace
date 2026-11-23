#!/usr/bin/env python3
"""
Add verified evidence claims for batch 23: Mailchimp.

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
        "source_id": "mailchimp-pricing",
        "url": "https://mailchimp.com/pricing/marketing",
        "source_type": "official_pricing",
        "publisher": "Mailchimp",
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
        "source_id": "mailchimp-help-plans",
        "url": "https://mailchimp.com/help/about-mailchimp-pricing-plans",
        "source_type": "official_docs",
        "publisher": "Mailchimp",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "mailchimp-compare-plans",
        "url": "https://mailchimp.com/pricing/marketing/compare-plans",
        "source_type": "official_pricing",
        "publisher": "Mailchimp",
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
        "claim_id": "mailchimp-pricing-model",
        "tool_id": "mailchimp",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Contact-based tiered subscription. Free plan: up to 500 contacts, 1,000 emails/mo. Essentials $13/mo annual (500 contacts, 10K emails/mo, 3 seats). Standard $20/mo annual (500 contacts, 12K emails/mo, 5 seats). Premium custom (10K contacts, 150K emails/mo, unlimited seats). Pay As You Go option available. 50% discount for first 12 months on paid plans.",
        "source_ids": ["mailchimp-pricing", "mailchimp-help-plans", "mailchimp-compare-plans"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Essentials $13/mo annual, Standard $20/mo annual. Help docs confirm Free plan limits. Compare page shows feature gating and send limits.",
        "evidence_note": "Contact-based pricing; email sends scale with contacts. Free plan has meaningful limits.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "mailchimp-free-plan",
        "tool_id": "mailchimp",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: up to 500 contacts, 1,000 emails/mo (max 500/mo or 250/day), 1 audience, 1 seat, email support for first 30 days, limited templates, popup forms, 300+ integrations. No email scheduling, automation, or A/B testing.",
        "source_ids": ["mailchimp-pricing", "mailchimp-help-plans", "mailchimp-compare-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page and compare page: Free plan includes 500 contacts, 1,000 emails/mo, 1 audience, 1 seat. No email scheduling, automation, or A/B testing.",
        "evidence_note": "Genuine free tier but very limited.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "mailchimp-trial",
        "tool_id": "mailchimp",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available on paid plans with no credit card required.",
        "source_ids": ["mailchimp-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Free for 14 days' on Standard plan. Help docs confirm no credit card required for free trial.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "mailchimp-capabilities",
        "tool_id": "mailchimp",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Email marketing campaigns",
            "Pre-built email templates",
            "Marketing automation flows (Essentials+)",
            "A/B testing (Essentials+)",
            "Multivariate testing (Standard+)",
            "Email scheduling (Essentials+)",
            "Advanced segmentation (Standard+)",
            "Custom-coded email templates (Standard+)",
            "Generative AI features (Standard+)",
            "SMS and MMS marketing add-on",
            "Popup forms",
            "Landing pages",
            "300+ integrations",
            "Custom reports (Standard+)",
            "Predictive segmentation (Premium)",
            "Enterprise SSO (Premium)",
            "Unlimited audiences (Premium)",
            "Unlimited seats (Premium)",
            "Phone and priority support (Premium)",
            "Pay As You Go option"
        ],
        "source_ids": ["mailchimp-pricing", "mailchimp-help-plans", "mailchimp-compare-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Help docs confirm plan details. Compare page shows feature gating.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "mailchimp-platforms",
        "tool_id": "mailchimp",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["mailchimp-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Mailchimp is a cloud-based email marketing platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "mailchimp-core-use-case",
        "tool_id": "mailchimp",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Email marketing and marketing automation platform for small to large businesses to create email campaigns, automate customer communications, and grow audiences.",
        "source_ids": ["mailchimp-pricing", "mailchimp-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes email marketing platform. Help docs confirm marketing automation capabilities.",
        "evidence_note": "Broad email marketing platform, not niche-focused.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "mailchimp-target-user",
        "tool_id": "mailchimp",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to large businesses needing email marketing. Free for beginners, Essentials for small teams, Standard for growing marketers, Premium for large organizations needing dedicated support.",
        "source_ids": ["mailchimp-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Help docs: Essentials for 'small teams', Standard for 'marketers who want to accelerate business growth', Premium for 'extra large audience' with 'dedicated and extended support'.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "mailchimp-limitations",
        "tool_id": "mailchimp",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan limited to 500 contacts and 1,000 emails/mo (max 250/day)",
            "No email scheduling, automation, or A/B testing on free plan",
            "Email support only for first 30 days on free plan",
            "Generative AI features require Standard plan ($20/mo)",
            "Custom-coded templates can only be sent on Standard+ plan",
            "Enterprise SSO requires Premium plan",
            "Maximum 50,000 contacts on Essentials, 100,000 on Standard"
        ],
        "source_ids": ["mailchimp-pricing", "mailchimp-help-plans", "mailchimp-compare-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows feature gating. Help docs confirm plan limits. Compare page details contact limits.",
        "evidence_note": "Free plan is very limited; paid plans unlock core features.",
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
