#!/usr/bin/env python3
"""
Add verified evidence claims for batch 16: Intercom.

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
        "source_id": "intercom-pricing",
        "url": "https://www.intercom.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Intercom",
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
        "source_id": "intercom-learning-pricing",
        "url": "https://www.intercom.com/learning-center/intercom-pricing",
        "source_type": "official_product",
        "publisher": "Intercom",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "intercom-help-pricing",
        "url": "https://www.intercom.com/help/en/articles/8344190-pricing-faqs",
        "source_type": "official_docs",
        "publisher": "Intercom",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "intercom-pricing-model",
        "tool_id": "intercom",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-seat subscription. Essential $29/seat/mo annual ($39 monthly). Advanced $85/seat/mo annual ($99 monthly, includes 20 Lite seats). Expert $132/seat/mo annual ($139 monthly, includes 50 Lite seats). Fin AI Agent $0.99/outcome on all plans. Proactive Support Plus add-on $99/mo. Copilot add-on $29/agent/mo.",
        "source_ids": ["intercom-pricing", "intercom-learning-pricing", "intercom-help-pricing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Essential $29/seat/mo, Advanced $85, Expert $132. Learning center confirms Fin AI Agent $0.99/outcome. Help docs confirm add-on pricing.",
        "evidence_note": "Per-seat pricing with usage-based AI. No minimum seat requirements.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "intercom-free-plan",
        "tool_id": "intercom",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Early Stage program available for qualifying startups. 14-day free trial available.",
        "source_ids": ["intercom-help-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Help docs: 'If you're a new startup, the Early Stage program may be designed for you. For teams that don't qualify, the Essential plan is $29/seat/month.'",
        "evidence_note": "No perpetual free tier confirmed.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "intercom-trial",
        "tool_id": "intercom",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available with no credit card required.",
        "source_ids": ["intercom-pricing", "intercom-help-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page and help docs confirm 14-day free trial with no credit card required.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "intercom-capabilities",
        "tool_id": "intercom",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Customer messaging (Messenger)",
            "Shared inbox and ticketing system",
            "Fin AI Agent ($0.99/outcome)",
            "Public help center",
            "Pre-built reports",
            "Simple automations",
            "Slack integration",
            "Workflows automation builder (Advanced+)",
            "Multiple team inboxes (Advanced+)",
            "Round-robin assignment (Advanced+)",
            "Private and multilingual help center (Advanced+)",
            "Custom reports (Advanced+)",
            "Salesforce and Marketo integration (Advanced+)",
            "SSO and HIPAA support (Expert)",
            "SLAs and workload management (Expert)",
            "Proactive Support Plus add-on (product tours, surveys, in-app messages)",
            "Copilot AI assistant add-on"
        ],
        "source_ids": ["intercom-pricing", "intercom-learning-pricing", "intercom-help-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Learning center confirms Fin AI Agent and add-ons. Help docs detail feature gating.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "intercom-platforms",
        "tool_id": "intercom",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["intercom-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Intercom is a cloud-based customer communication platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "intercom-core-use-case",
        "tool_id": "intercom",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Customer communication platform for businesses to provide live chat, messaging, help center, and AI-powered support across web and mobile channels.",
        "source_ids": ["intercom-pricing", "intercom-learning-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes customer support platform. Learning center confirms messaging, ticketing, and AI agent capabilities.",
        "evidence_note": "Customer communication focused, not general CRM.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "intercom-target_user",
        "tool_id": "intercom",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Startups, small businesses, and enterprises needing customer support. Essential for small teams, Advanced for growing support teams, Expert for large organizations with security needs.",
        "source_ids": ["intercom-pricing", "intercom-learning-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Essential for 'individuals, startups, and small businesses', Advanced for 'growing support teams', Expert for 'large support teams'.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "intercom-limitations",
        "tool_id": "intercom",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "No free plan available",
            "Fin AI Agent costs $0.99/outcome on top of seat pricing",
            "Workflows automation requires Advanced plan ($85/seat/mo)",
            "Multiple team inboxes require Advanced plan",
            "SSO and HIPAA support require Expert plan ($132/seat/mo)",
            "Proactive Support Plus add-on costs $99/mo extra",
            "Copilot add-on costs $29/agent/mo extra"
        ],
        "source_ids": ["intercom-pricing", "intercom-learning-pricing", "intercom-help-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows feature gating and add-on costs. Learning center confirms AI pricing model.",
        "evidence_note": "Total cost increases with AI usage and add-ons.",
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
