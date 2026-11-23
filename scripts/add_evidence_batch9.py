#!/usr/bin/env python3
"""
Add verified evidence claims for batch 9: Spiky.

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
        "source_id": "spiky-pricing",
        "url": "https://spiky.ai/en/pricing",
        "source_type": "official_pricing",
        "publisher": "Spiky",
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
        "source_id": "spiky-compare",
        "url": "https://spiky.ai/en/compare",
        "source_type": "official_product",
        "publisher": "Spiky",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "spiky-pricing-model",
        "tool_id": "spiky",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-user subscription. Free plan available. Plus $12/mo/user, Pro $24/mo/user (30 meetings/user), Premium $40/mo/user (unlimited meetings), Enterprise custom. No credit card required for paid plans.",
        "source_ids": ["spiky-pricing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Free plan, Plus $12/mo/user, Pro $24/mo/user with 30 meetings/user, Premium $40/mo/user unlimited meetings. No credit card required.",
        "evidence_note": "Published per-user pricing with free tier. Signals scope and pricing separate.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "spiky-free-plan",
        "tool_id": "spiky",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available with limited recording usage and basic meeting intelligence features.",
        "source_ids": ["spiky-pricing", "spiky-compare"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows Free tier. Compare page confirms 'free plan with limited recording usage'.",
        "evidence_note": "Genuine free tier with usage limits.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "spiky-trial",
        "tool_id": "spiky",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Trial equivalent to Premium plan excluding CRM functionality. Free plan also available.",
        "source_ids": ["spiky-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page FAQ: 'Trials are equivalent to the premium plan excluding CRM functionality.'",
        "evidence_note": "Trial provides Premium-level access minus CRM.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "spiky-capabilities",
        "tool_id": "spiky",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Meeting recording and transcription (Zoom, Google Meet, Microsoft Teams)",
            "AI-powered sales coaching and scorecards",
            "Live coaching (Whisper) with real-time guidance",
            "Deal risk and pipeline insights",
            "Revenue forecasting (Signals)",
            "Sentiment analysis and voice emotion analysis",
            "Talk ratio and speaker analytics",
            "CRM and Slack integrations",
            "Keyword tracking",
            "Playbook tracking and battlecards",
            "AI-based coaching and report customization",
            "Custom branding",
            "Bot-free desktop audio capture",
            "People Board and team management"
        ],
        "source_ids": ["spiky-pricing", "spiky-compare"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Compare page confirms meeting intelligence, live coaching, deal insights, and revenue forecasting.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "spiky-platforms",
        "tool_id": "spiky",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "Desktop audio capture"],
        "source_ids": ["spiky-pricing", "spiky-compare"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page and compare page confirm web-based platform with bot-free desktop audio capture.",
        "evidence_note": "Web-based with desktop capture for meetings without bots.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "spiky-core-use-case",
        "tool_id": "spiky",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "AI sales intelligence platform for revenue teams to capture meeting insights, provide live coaching, analyze deal risk, and improve sales performance through behavioral analysis.",
        "source_ids": ["spiky-pricing", "spiky-compare"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page targets 'Revenue Teams of Any Size'. Compare page describes meeting intelligence, live coaching, and revenue insights.",
        "evidence_note": "Sales intelligence and coaching, not general meeting notes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "spiky-target-user",
        "tool_id": "spiky",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Revenue teams, sales managers, and sales enablement professionals. Free for individuals, Plus for small teams, Pro for mid-sized teams, Premium for growing businesses, Enterprise for large organizations.",
        "source_ids": ["spiky-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Plus for 'small teams', Pro for 'mid-sized teams', Premium for 'growing business', Enterprise for 'large organizations'.",
        "evidence_note": "Targets revenue teams across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "spiky-limitations",
        "tool_id": "spiky",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan has limited recording usage",
            "Pro plan limited to 30 meetings/user",
            "CRM integration requires Pro plan or higher",
            "Real-time coaching requires Premium plan",
            "Signals scope and pricing must be confirmed separately",
            "Enterprise pricing not publicly disclosed"
        ],
        "source_ids": ["spiky-pricing", "spiky-compare"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows meeting limits and feature gating. Compare page notes Signals pricing separate.",
        "evidence_note": "Signals is a separate product with separate pricing.",
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
