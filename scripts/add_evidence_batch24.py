#!/usr/bin/env python3
"""
Add verified evidence claims for batch 24: HubSpot.

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
        "source_id": "hubspot-pricing-suite",
        "url": "https://www.hubspot.com/pricing/suite",
        "source_type": "official_pricing",
        "publisher": "HubSpot",
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
        "source_id": "hubspot-pricing-sales",
        "url": "https://www.hubspot.com/pricing/sales",
        "source_type": "official_pricing",
        "publisher": "HubSpot",
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
        "source_id": "hubspot-pricing-marketing",
        "url": "https://www.hubspot.com/pricing/marketing",
        "source_type": "official_pricing",
        "publisher": "HubSpot",
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
        "claim_id": "hubspot-pricing-model",
        "tool_id": "hubspot",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-seat subscription with hub-based pricing. Free CRM for up to 2 users. Starter $7/mo/seat annual ($20 monthly). Professional $90/mo/seat annual. Enterprise $150/mo/seat. Marketing Hub Professional $800/mo (includes 3 seats, 2,000 contacts). Customer Platform bundles available. HubSpot Credits included on paid plans.",
        "source_ids": ["hubspot-pricing-suite", "hubspot-pricing-sales", "hubspot-pricing-marketing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing pages: Free CRM for 2 users, Starter $7/mo/seat annual, Professional $90/mo/seat, Enterprise $150/mo/seat. Marketing Hub Professional $800/mo with 3 seats.",
        "evidence_note": "Per-seat pricing; Marketing Hub Professional is flat-rate with included seats.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hubspot-free-plan",
        "tool_id": "hubspot",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free CRM available: up to 2 users, contact management, deal tracking, email integration, live chat, forms, pop-ups, landing pages, ad management, reporting, 300+ integrations. HubSpot branding on some features.",
        "source_ids": ["hubspot-pricing-suite", "hubspot-pricing-sales"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing pages: Free CRM includes marketing, sales, service, content, data, and revenue tools. Up to 2 users, no credit card required.",
        "evidence_note": "Genuine free tier with broad feature set.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hubspot-trial",
        "tool_id": "hubspot",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available on paid plans with no credit card required.",
        "source_ids": ["hubspot-pricing-marketing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Start 14-day trial' on Professional plan.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hubspot-capabilities",
        "tool_id": "hubspot",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "CRM with contact and deal management",
            "Marketing Hub (email, social, SEO, ads, landing pages)",
            "Sales Hub (pipeline, email sequences, meeting scheduling)",
            "Service Hub (ticketing, knowledge base, customer feedback)",
            "Content Hub (CMS, blogging, design tools)",
            "Data Hub (operations, data sync, workflows)",
            "Revenue Hub (quoting, billing, payments)",
            "AI-powered features (Breeze, Agent Hub, Notetaker)",
            "HubSpot Credits for AI features",
            "300+ integrations",
            "Mobile app for iOS and Android",
            "Custom reporting and dashboards",
            "Automation workflows",
            "Live chat and chatbots",
            "Forms and pop-ups",
            "SSO and advanced security (Enterprise)",
            "Custom objects and sandbox (Enterprise)"
        ],
        "source_ids": ["hubspot-pricing-suite", "hubspot-pricing-sales", "hubspot-pricing-marketing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing pages list all hubs and features. Suite page confirms bundled platform approach.",
        "evidence_note": "Comprehensive platform with multiple hubs; feature gating across tiers.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hubspot-platforms",
        "tool_id": "hubspot",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS app", "Android app"],
        "source_ids": ["hubspot-pricing-sales"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page confirms HubSpot mobile app on all plans.",
        "evidence_note": "Full-featured mobile apps for iOS and Android.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hubspot-core-use-case",
        "tool_id": "hubspot",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "All-in-one CRM and revenue platform for businesses to manage marketing, sales, service, content, data, and revenue operations on a single customer platform.",
        "source_ids": ["hubspot-pricing-suite", "hubspot-pricing-sales"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing pages describe all-in-one customer platform. Suite page confirms bundled approach across all hubs.",
        "evidence_note": "Broad CRM platform, not niche-focused.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hubspot-target-user",
        "tool_id": "hubspot",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to enterprise businesses needing CRM and revenue tools. Free for very small teams, Starter for growing businesses, Professional for scaling teams, Enterprise for large organizations.",
        "source_ids": ["hubspot-pricing-suite"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing pages target businesses across sizes. Suite page describes platform for scaling businesses.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hubspot-limitations",
        "tool_id": "hubspot",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan limited to 2 users",
            "HubSpot branding on some free features",
            "Marketing Hub Professional is expensive ($800/mo flat rate)",
            "Advanced features (custom objects, sandbox, SSO) require Enterprise",
            "Per-seat pricing adds up quickly for larger teams",
            "HubSpot Credits for AI features are limited per plan"
        ],
        "source_ids": ["hubspot-pricing-suite", "hubspot-pricing-sales", "hubspot-pricing-marketing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing pages show feature gating and credit limits. Suite page confirms Enterprise-only features.",
        "evidence_note": "Total cost increases with seats, hubs, and AI usage.",
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
