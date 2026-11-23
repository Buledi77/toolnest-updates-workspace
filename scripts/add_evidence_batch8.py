#!/usr/bin/env python3
"""
Add verified evidence claims for batch 8: Closely.

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
        "source_id": "closely-pricing",
        "url": "https://closelyhq.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Closely",
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
        "source_id": "closely-blog-pricing",
        "url": "https://blog.closelyhq.com/closely-pricing-plans-breakdown-vs-competitors",
        "source_type": "official_product",
        "publisher": "Closely",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "closely-pricing-model",
        "tool_id": "closely",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Credit-based tiered subscription. Starter $39/mo annual ($65 monthly, 1 LinkedIn account, 1,000 credits), Growth $95/mo annual ($159 monthly, 3 accounts, 3,000 credits), Essential $205/mo (5 accounts, 5,000 credits), Custom $350/mo (10+ accounts). 40% annual billing discount.",
        "source_ids": ["closely-pricing", "closely-blog-pricing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Starter $39/mo annual, Growth $95/mo annual, Essential $205/mo, Custom $350/mo. Blog confirms credit allocation: emails, phones, or AI personalizations.",
        "evidence_note": "Credit-based model; credits allocated to emails, phone numbers, or AI personalizations.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "closely-free-trial",
        "tool_id": "closely",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Free trial available ('Start free trial' on pricing page).",
        "source_ids": ["closely-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Start free trial' on all plans.",
        "evidence_note": "Trial period length not specified on pricing page.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "closely-free-plan",
        "tool_id": "closely",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a free trial.",
        "source_ids": ["closely-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows only paid plans with free trial. No perpetual free tier.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "closely-capabilities",
        "tool_id": "closely",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "LinkedIn outreach automation with AI personalization",
            "Email campaign sequences (unlimited email accounts)",
            "Multichannel campaigns (LinkedIn + email)",
            "Data enrichment (email finder, phone finder)",
            "AI-powered content personalization",
            "LinkedIn account warmup",
            "Dedicated residential IPs",
            "Smart Inbox for unified responses",
            "CRM integrations",
            "Webhooks",
            "White-label (custom domain, colors, logo)",
            "Advanced analytics and reports",
            "Team management",
            "Conditional sequence builder"
        ],
        "source_ids": ["closely-pricing", "closely-blog-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists all features. Blog confirms data enrichment, AI personalization, white-label, and CRM integrations across all plans.",
        "evidence_note": "All core features available on all tiers; pricing scales by LinkedIn accounts and credits.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "closely-platforms",
        "tool_id": "closely",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["closely-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Closely operates as a web-based platform for LinkedIn and email outreach.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "closely-core-use-case",
        "tool_id": "closely",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "B2B sales engagement platform for automating LinkedIn and email outreach with AI personalization, data enrichment, and multichannel campaigns.",
        "source_ids": ["closely-pricing", "closely-blog-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes LinkedIn and email outreach. Blog positions it for SMB sales teams and agencies.",
        "evidence_note": "LinkedIn-focused B2B outreach with email as secondary channel.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "closely-target-user",
        "tool_id": "closely",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to medium B2B sales teams, agencies, and consultants who need LinkedIn-based outbound outreach. Starter for solo professionals, Growth for small teams, Essential for larger teams, Custom for agencies.",
        "source_ids": ["closely-blog-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Blog: Starter for 'independent recruiters, solo entrepreneurs, or freelance sales professionals', Growth for 'small teams', Essential for 'larger teams'.",
        "evidence_note": "SMB-focused; not designed for enterprise-scale operations.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "closely-limitations",
        "tool_id": "closely",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Credit-based system requires careful management and allocation trade-offs",
            "Limited phone credits compared to email allowances",
            "Significant price jumps between tiers (Starter to Growth: $78 increase)",
            "Custom plan at $350/mo may be out of reach for very small teams",
            "LinkedIn account limits may hinder larger teams",
            "No perpetual free plan"
        ],
        "source_ids": ["closely-blog-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Blog notes credit management challenges, price jumps, and LinkedIn account limits as cons.",
        "evidence_note": "Credit allocation trade-offs and price jumps are notable limitations.",
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
