#!/usr/bin/env python3
"""
Add verified evidence claims for batch 11: TextMagic.

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
        "source_id": "textmagic-pricing",
        "url": "https://www.textmagic.com/pricing",
        "source_type": "official_pricing",
        "publisher": "TextMagic",
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
        "source_id": "textmagic-ai",
        "url": "https://www.textmagic.com/ai",
        "source_type": "official_product",
        "publisher": "TextMagic",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "textmagic-support-billing",
        "url": "https://support.textmagic.com/article/textmagic-billing-plans",
        "source_type": "official_docs",
        "publisher": "TextMagic",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "textmagic-pricing-model",
        "tool_id": "textmagic",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Pay-as-you-go credit-based. US outbound SMS $0.049/msg standard. Professional monthly plans $0.02-$0.04/msg depending on volume. Toll-free number $10/mo, local 10DLC number $10/mo + $10/mo campaign registration. MMS $0.08/msg. Email $0.006/email. No contracts, credits never expire.",
        "source_ids": ["textmagic-pricing", "textmagic-ai", "textmagic-support-billing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: $0.049/SMS pay-as-you-go, Professional plans $0.02-$0.04. AI page confirms pricing model. Support docs detail Essential (pay-as-you-go) vs Professional (monthly) plans.",
        "evidence_note": "Prepaid model; no monthly minimums. Volume discounts on Professional plans.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "textmagic-free-trial",
        "tool_id": "textmagic",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Free trial available with no credit card required.",
        "source_ids": ["textmagic-ai"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "AI page: 'Free trial: Yes, no credit card required'.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "textmagic-free-plan",
        "tool_id": "textmagic",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No perpetual free plan. Only a free trial. Inbound SMS is free on all plans.",
        "source_ids": ["textmagic-pricing", "textmagic-ai"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows pay-as-you-go model. AI page confirms prepaid model with no free tier. Inbound SMS is free.",
        "evidence_note": "Confirmed no free plan exists; inbound SMS is free.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "textmagic-capabilities",
        "tool_id": "textmagic",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Mass SMS texting and two-way messaging",
            "MMS (multimedia messaging)",
            "Automation workflows",
            "Shared team inbox",
            "Omnichannel chat widget",
            "Email campaigns",
            "AI writing and templates",
            "Unlimited contacts and users",
            "Delivery reporting",
            "Integrations and API access",
            "Compliance tools",
            "Dedicated numbers and Sender IDs",
            "Global SMS to 200+ countries",
            "Voice call forwarding"
        ],
        "source_ids": ["textmagic-pricing", "textmagic-ai"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists all features. AI page confirms SMS, email, and global coverage.",
        "evidence_note": "All features available regardless of spend level.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "textmagic-platforms",
        "tool_id": "textmagic",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["textmagic-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "TextMagic is a cloud-based SMS platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "textmagic-core-use-case",
        "tool_id": "textmagic",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "SMS and email marketing platform for businesses to send mass text messages, run two-way conversations, and automate customer engagement workflows.",
        "source_ids": ["textmagic-pricing", "textmagic-ai"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes SMS marketing. AI page confirms 20,000+ businesses worldwide using the platform.",
        "evidence_note": "SMS-focused with email as secondary channel.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "textmagic-target-user",
        "tool_id": "textmagic",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to large businesses using SMS for marketing, notifications, and customer engagement. Pay-as-you-go for occasional use, Professional for regular high-volume messaging.",
        "source_ids": ["textmagic-support-billing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Support docs: Essential (pay-as-you-go) for 'occasional use', Professional (monthly) for 'regular, higher-volume messaging'.",
        "evidence_note": "Broad target across business sizes and use cases.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "textmagic-limitations",
        "tool_id": "textmagic",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Pay-as-you-go pricing means costs scale with message volume",
            "Toll-free and local numbers cost $10/mo each",
            "10DLC campaign registration adds $10/mo for local US numbers",
            "MMS costs $0.08/msg (more than SMS)",
            "No perpetual free plan",
            "Longer messages (over 160 chars) billed by part"
        ],
        "source_ids": ["textmagic-pricing", "textmagic-support-billing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows number costs and MMS pricing. Support docs confirm 10DLC fees.",
        "evidence_note": "Total cost increases with volume, numbers, and message length.",
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
