#!/usr/bin/env python3
"""
Add verified evidence claims for batch 21: ActiveCampaign.

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
        "source_id": "activecampaign-pricing",
        "url": "https://www.activecampaign.com/pricing",
        "source_type": "official_pricing",
        "publisher": "ActiveCampaign",
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
        "source_id": "activecampaign-compare-marketo",
        "url": "https://www.activecampaign.com/compare/marketo",
        "source_type": "official_product",
        "publisher": "ActiveCampaign",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "activecampaign-help-plans",
        "url": "https://help.activecampaign.com/hc/en-us/articles/14251311251356-Overview-of-ActiveCampaign-plans",
        "source_type": "official_docs",
        "publisher": "ActiveCampaign",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "activecampaign-pricing-model",
        "tool_id": "activecampaign",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Contact-based tiered subscription. Starter $29/mo (1,000 contacts, 10K emails/mo, 1 user, 5 actions/automation). Plus $49/mo (1,000 contacts, 10K emails, 1 user, unlimited automation actions, landing pages, generative AI). Pro $79/mo (1,000 contacts, 12K emails, 3 users, predictive sending, conditional content). Enterprise $145/mo (1,000 contacts, 15K emails, 5 users, SSO, HIPAA). No free plan.",
        "source_ids": ["activecampaign-pricing", "activecampaign-compare-marketo", "activecampaign-help-plans"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page and compare pages: Starter $29/mo, Plus $49/mo, Pro $79/mo, Enterprise $145/mo for 1,000 contacts. Help docs confirm plan details and feature gating.",
        "evidence_note": "Contact-based pricing; email sends scale with contacts. No free plan.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "activecampaign-free-plan",
        "tool_id": "activecampaign",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a free trial available.",
        "source_ids": ["activecampaign-pricing", "activecampaign-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows only paid plans. Help docs confirm no free tier.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "activecampaign-trial",
        "tool_id": "activecampaign",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Free trial available. Trial period length not specified on pricing page.",
        "source_ids": ["activecampaign-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Start free trial' CTA. Trial period length not specified.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "activecampaign-capabilities",
        "tool_id": "activecampaign",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Email marketing campaigns with 250+ templates",
            "Multi-step marketing automation",
            "AI-powered automation and campaign builders",
            "Marketing CRM",
            "Landing pages and site messages (Plus+)",
            "Generative AI for content and images (Plus+)",
            "Predictive sending (Pro+)",
            "Conditional content (Pro+)",
            "Advanced segmentation (Pro+)",
            "Attribution and conversion tracking (Pro+)",
            "A/B testing on emails and automations",
            "Web forms and inline forms",
            "Website tracking",
            "950+ integrations including Shopify, WooCommerce, Salesforce",
            "Prospecting and retargeting ads (Plus+)",
            "Revenue reporting (Plus+)",
            "SSO and HIPAA support (Enterprise)",
            "Dedicated account team (Enterprise)",
            "Active Intelligence Credits (500 on all plans)"
        ],
        "source_ids": ["activecampaign-pricing", "activecampaign-compare-marketo", "activecampaign-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Compare pages confirm feature gating. Help docs detail plan differences.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "activecampaign-platforms",
        "tool_id": "activecampaign",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["activecampaign-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "ActiveCampaign is a cloud-based marketing automation platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "activecampaign-core-use-case",
        "tool_id": "activecampaign",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Email marketing and marketing automation platform for businesses to automate customer communications, segment audiences, and personalize messaging at scale.",
        "source_ids": ["activecampaign-pricing", "activecampaign-compare-marketo"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes email marketing and automation. Compare pages position it against Marketo for marketing automation.",
        "evidence_note": "Marketing automation focused, not general CRM.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "activecampaign-target-user",
        "tool_id": "activecampaign",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to enterprise businesses needing email marketing and automation. Starter for individuals, Plus for growing teams, Pro for marketers needing AI optimization, Enterprise for organizations needing security and dedicated support.",
        "source_ids": ["activecampaign-pricing", "activecampaign-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Starter for 'individuals', Plus for 'growing teams', Pro for 'marketers', Enterprise for 'organizations'. Help docs confirm target audiences.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "activecampaign-limitations",
        "tool_id": "activecampaign",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "No free plan available",
            "Starter plan limited to 5 actions per automation",
            "Starter plan limited to 1 user seat",
            "Cross-channel marketing not included on Starter",
            "Landing pages and generative AI require Plus plan ($49/mo)",
            "Predictive sending and conditional content require Pro plan ($79/mo)",
            "SSO and HIPAA support require Enterprise plan ($145/mo)",
            "Maximum 25,000 contacts on Starter plan"
        ],
        "source_ids": ["activecampaign-pricing", "activecampaign-compare-marketo", "activecampaign-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows feature gating. Compare pages confirm Starter limitations. Help docs detail plan restrictions.",
        "evidence_note": "Feature gating across tiers is significant; Starter is quite limited.",
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
