#!/usr/bin/env python3
"""
Add verified evidence claims for batch 6: SimpleTexting.

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
        "source_id": "simpletexting-pricing",
        "url": "https://simpletexting.com/pricing",
        "source_type": "official_pricing",
        "publisher": "SimpleTexting",
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
        "source_id": "simpletexting-plan-guide",
        "url": "https://simpletexting.com/blog/what-simpletexting-plan-should-you-choose",
        "source_type": "official_product",
        "publisher": "SimpleTexting",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "simpletexting-pricing-model",
        "tool_id": "simpletexting",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Credit-based tiered subscription. $29/mo for 500 SMS credits (toll-free number), $39/mo (local number). Scales to $899/mo for 50,000 messages. Extra credits $0.055 each. MMS costs 3 credits per message. Additional users $20/mo, additional numbers $10/mo.",
        "source_ids": ["simpletexting-pricing", "simpletexting-plan-guide"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: $29 for 500 credits toll-free, $39 local number. Plan guide: $109/mo for 3,000 credits, $549/mo for 25,000 credits. Extra credits 5.5 cents each.",
        "evidence_note": "Credit-based model; MMS costs 3x SMS. No contracts, 20% annual billing discount.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "simpletexting-free-trial",
        "tool_id": "simpletexting",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available.",
        "source_ids": ["simpletexting-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Try it free'. Blog confirms 14-day free trial.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "simpletexting-free-plan",
        "tool_id": "simpletexting",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a 14-day free trial.",
        "source_ids": ["simpletexting-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows only paid plans with trial. No perpetual free tier.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "simpletexting-capabilities",
        "tool_id": "simpletexting",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Mass SMS texting and two-way messaging",
            "MMS (picture messaging)",
            "Auto-replies and drip campaigns",
            "AI Assist message generator",
            "API access",
            "Reporting and analytics",
            "Unlimited contacts",
            "Advanced audience segments",
            "Unlimited text-to-join keywords",
            "Mailchimp and Zapier integrations",
            "Opt-in forms and pop-ups",
            "10DLC registration guidance",
            "Enterprise-grade deliverability",
            "Live support 7 days/week"
        ],
        "source_ids": ["simpletexting-pricing", "simpletexting-plan-guide"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists all messaging features, contact management, and support. Plan guide confirms all features available on all tiers.",
        "evidence_note": "All features available on all tiers; pricing scales by volume only.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "simpletexting-platforms",
        "tool_id": "simpletexting",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["simpletexting-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "SimpleTexting is a cloud-based SMS marketing platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "simpletexting-core-use-case",
        "tool_id": "simpletexting",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "SMS and MMS marketing platform for businesses to send mass text messages, run two-way conversations, and automate drip campaigns for customer engagement.",
        "source_ids": ["simpletexting-pricing", "simpletexting-plan-guide"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes SMS marketing. Plan guide covers mass texting, internal communications, and marketing use cases.",
        "evidence_note": "SMS-focused marketing platform, not a general messaging tool.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "simpletexting-target-user",
        "tool_id": "simpletexting",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to large businesses using SMS for marketing, customer engagement, and internal communications. Churches and nonprofits get 15% discount.",
        "source_ids": ["simpletexting-plan-guide"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Plan guide describes use cases from mid-sized businesses to large organizations. Blog notes 15% discount for churches and nonprofits.",
        "evidence_note": "Broad target across business sizes and sectors.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "simpletexting-limitations",
        "tool_id": "simpletexting",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Credit-based pricing means costs scale with message volume",
            "MMS costs 3 credits per message (3x SMS cost)",
            "Additional team members cost $20/mo each (3 included)",
            "Additional phone numbers cost $10/mo each",
            "No perpetual free plan",
            "Drip campaigns require manual setup (not out-of-the-box)"
        ],
        "source_ids": ["simpletexting-pricing", "simpletexting-plan-guide"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows credit costs and add-on fees. Comparison notes drip campaigns need manual setup.",
        "evidence_note": "Total cost increases with volume, team size, and additional numbers.",
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
