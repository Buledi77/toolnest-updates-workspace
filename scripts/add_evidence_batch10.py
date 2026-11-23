#!/usr/bin/env python3
"""
Add verified evidence claims for batch 10: Apollo IO.

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
        "source_id": "apollo-pricing",
        "url": "https://www.apollo.io/pricing",
        "source_type": "official_pricing",
        "publisher": "Apollo",
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
        "source_id": "apollo-alternatives",
        "url": "https://www.apollo.io/insights/apollo-alternatives",
        "source_type": "official_product",
        "publisher": "Apollo",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "apollo-pricing-model",
        "tool_id": "apollo",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Credit-based tiered subscription. Free: $0 with 900 credits/year. Basic: $49/user/mo annual (30,000 credits/year). Professional: $79/user/mo annual (48,000 credits/year). Organization: $119/user/mo annual (72,000 credits/year, min 3 users). Custom plan available.",
        "source_ids": ["apollo-pricing", "apollo-alternatives"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page and alternatives page: Free $0 with 900 credits/year, Basic $49/user/mo with 30K credits, Professional $79/user/mo with 48K credits, Organization $119/user/mo with 72K credits.",
        "evidence_note": "Credit-based model; 20% annual billing discount. All seats on same plan.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "apollo-free-plan",
        "tool_id": "apollo",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: 900 credits/year (75/month), 2 sequences, basic filters, Gmail-only email connection.",
        "source_ids": ["apollo-pricing", "apollo-alternatives"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Alternatives page: 'Free: $0 per month, 900 credits/year (75/month), 2 sequences, and basic filters'. Pricing page confirms Gmail-only on free plan.",
        "evidence_note": "Genuine free tier with limited credits and Gmail-only.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "apollo-trial",
        "tool_id": "apollo",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Free trial available giving access to most features before committing. Free plan also available.",
        "source_ids": ["apollo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'the free trial gives access to most features before committing'.",
        "evidence_note": "Both trial and free tier available.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "apollo-capabilities",
        "tool_id": "apollo",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "B2B contact database (240M+ contacts, 30M+ companies)",
            "Email sequencing and automation",
            "Multichannel sequences (email, phone, social, tasks)",
            "AI sequence builder and AI research agent",
            "US dialer (Professional+) and international dialer (Organization+)",
            "Power Dialer and Parallel Dialer",
            "Call recording and AI call scripts",
            "CRM integrations (Salesforce, HubSpot, Outreach, SalesLoft)",
            "Lead scoring and automated workflows",
            "Waterfall enrichment",
            "Chrome extension",
            "API access (Custom plans)",
            "SSO and advanced security (Organization+)",
            "Intent data and intent topics"
        ],
        "source_ids": ["apollo-pricing", "apollo-alternatives"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Alternatives page confirms database size, email accuracy, and feature comparison.",
        "evidence_note": "Comprehensive sales engagement platform with data layer.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "apollo-platforms",
        "tool_id": "apollo",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "Chrome extension"],
        "source_ids": ["apollo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Apollo operates as a web-based platform with Chrome extension for prospecting.",
        "evidence_note": "Web-based SaaS with browser extension.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "apollo-core-use-case",
        "tool_id": "apollo",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "B2B sales intelligence and engagement platform combining a contact database with email sequencing, dialer, and AI-powered outreach automation.",
        "source_ids": ["apollo-pricing", "apollo-alternatives"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes sales intelligence platform. Alternatives page positions it for outbound and inbound GTM.",
        "evidence_note": "Combined data + engagement platform, not just a database.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "apollo-target-user",
        "tool_id": "apollo",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "B2B sales teams, from individual reps to enterprise organizations. Free for founders and early-stage teams, Basic for individual sellers, Professional for full-time reps, Organization for teams, Custom for enterprises.",
        "source_ids": ["apollo-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Free for 'founders and early-stage teams', Basic for 'individual sellers', Professional for 'full-time reps', Custom for 'teams needing custom volumes'.",
        "evidence_note": "Broad target across company sizes; used by Fortune 500 companies.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "apollo-limitations",
        "tool_id": "apollo",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan limited to 900 credits/year and Gmail-only",
            "All seats on an account must be on the same plan",
            "US dialer requires Professional plan ($79/user/mo)",
            "International dialer requires Organization plan ($119/user/mo)",
            "API access only on Custom plans",
            "Organization plan requires minimum 3 users"
        ],
        "source_ids": ["apollo-pricing", "apollo-alternatives"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page notes all seats on same plan, dialer requirements, and API access limits.",
        "evidence_note": "Plan-mixing not allowed; dialer features gated by tier.",
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
