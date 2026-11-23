#!/usr/bin/env python3
"""
Add verified evidence claims for batch 28: Pipedrive.

Sources: Official pricing page cross-referenced with third-party analysis.
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
        "source_id": "pipedrive-pricing",
        "url": "https://www.pipedrive.com/en/pricing",
        "source_type": "official_pricing",
        "publisher": "Pipedrive",
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
        "source_id": "pipedrive-axis",
        "url": "https://axisconsulting.io/pipedrive-pricing-plans",
        "source_type": "third_party_analysis",
        "publisher": "Axis Consulting",
        "official": False,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "pipedrive-forbes",
        "url": "https://www.forbes.com/advisor/business/software/pipedrive-pricing",
        "source_type": "third_party_analysis",
        "publisher": "Forbes Advisor",
        "official": False,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "pipedrive-pricing-model",
        "tool_id": "pipedrive",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-seat subscription. Lite $14/seat/mo annual ($24 monthly). Growth $39/seat/mo annual ($49 monthly). Premium $59/seat/mo annual ($79 monthly). Ultimate $79/seat/mo annual ($99 monthly). 20% annual billing discount. Add-ons: LeadBooster, Projects, Smart Docs, Campaigns, Web Visitors.",
        "source_ids": ["pipedrive-pricing", "pipedrive-axis", "pipedrive-forbes"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Multiple sources confirm: Lite $14/seat/mo annual, Growth $39, Premium $59, Ultimate $79. 20% annual billing discount. Add-ons available on all plans.",
        "evidence_note": "Per-seat pricing; add-ons increase cost. No free plan.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pipedrive-free-plan",
        "tool_id": "pipedrive",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a 14-day free trial available with no credit card required.",
        "source_ids": ["pipedrive-axis", "pipedrive-forbes"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources confirm no free plan exists. Only 14-day free trial with no credit card required.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pipedrive-trial",
        "tool_id": "pipedrive",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available with no credit card required.",
        "source_ids": ["pipedrive-axis", "pipedrive-forbes"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources confirm 14-day free trial with no credit card required.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pipedrive-capabilities",
        "tool_id": "pipedrive",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Visual sales pipeline management",
            "Contact and deal management",
            "Activity and task management",
            "Workflow automation (Growth+)",
            "Two-way email sync (Growth+)",
            "Revenue forecasting (Growth+)",
            "LeadBooster lead capture (Premium+)",
            "Projects management (Premium+)",
            "Smart Docs (Premium+)",
            "Campaigns add-on (all plans)",
            "Web Visitors tracking add-on (all plans)",
            "Custom fields and reports",
            "Meeting scheduler (Growth+)",
            "Email tracking (Growth+)",
            "Products catalog (Growth+)",
            "500+ integrations",
            "Mobile apps for iOS and Android",
            "SSO and advanced security (Ultimate)"
        ],
        "source_ids": ["pipedrive-pricing", "pipedrive-axis", "pipedrive-forbes"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources list features per tier. Lite: core pipeline. Growth: automation, email sync, forecasting. Premium: LeadBooster, Projects, Smart Docs. Ultimate: SSO, advanced security.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pipedrive-platforms",
        "tool_id": "pipedrive",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS app", "Android app"],
        "source_ids": ["pipedrive-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pipedrive is a cloud-based CRM with mobile apps for iOS and Android.",
        "evidence_note": "Full-featured mobile apps for iOS and Android.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pipedrive-core-use-case",
        "tool_id": "pipedrive",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Sales-focused CRM for small to medium sales teams to manage pipelines, automate sales tasks, and track deals from lead to close with visual pipeline management.",
        "source_ids": ["pipedrive-axis", "pipedrive-forbes"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources describe Pipedrive as sales-focused CRM for pipeline management and deal tracking.",
        "evidence_note": "Sales pipeline focused, not general CRM.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pipedrive-target-user",
        "tool_id": "pipedrive",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to medium sales teams. Lite for solopreneurs, Growth for small teams needing automation, Premium for scaling teams, Ultimate for larger organizations with security needs.",
        "source_ids": ["pipedrive-forbes"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Forbes: Lite for 'self-employed or solopreneurs', Growth for 'teams needing to set up client consults', Premium for 'lead generation and task management'.",
        "evidence_note": "Sales team focused; not designed for non-sales use cases.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pipedrive-limitations",
        "tool_id": "pipedrive",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "No free plan available",
            "Lite plan lacks email sync, automation, and forecasting",
            "Two-way email sync requires Growth plan ($39/seat/mo)",
            "LeadBooster, Projects, and Smart Docs require Premium plan ($59/seat/mo)",
            "Add-ons (Campaigns, Web Visitors) cost extra on all plans",
            "SSO and advanced security require Ultimate plan ($79/seat/mo)"
        ],
        "source_ids": ["pipedrive-axis", "pipedrive-forbes"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources show feature gating and add-on costs. Lite is quite limited without email sync or automation.",
        "evidence_note": "Lite plan is quite limited; Growth is the entry point for most teams.",
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
