#!/usr/bin/env python3
"""
Add verified evidence claims for batch 26: Freshdesk.

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
        "source_id": "freshdesk-pricing",
        "url": "https://freshdesk.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Freshdesk",
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
        "source_id": "freshdesk-support-pricing",
        "url": "https://support.freshdesk.com/support/solutions/articles/50000011778-understanding-freshdesk-pricing-plans",
        "source_type": "official_docs",
        "publisher": "Freshdesk",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "freshdesk-support-free",
        "url": "https://support.freshdesk.com/support/solutions/articles/50000010099-explore-freshdesk-free-program-freshdesk-only",
        "source_type": "official_docs",
        "publisher": "Freshdesk",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "freshdesk-pricing-model",
        "tool_id": "freshdesk",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-agent subscription. Two product lines: Freshdesk Omni (multichannel) and Freshdesk (email-first). Growth $19/agent/mo annual, Pro $55/agent/mo annual, Enterprise $89/agent/mo annual. Free program for 6 months (2 agents max). Freddy AI Agent included (500 sessions). Add-ons: Freddy AI Copilot $29/agent/mo, additional AI sessions $49/100 sessions.",
        "source_ids": ["freshdesk-pricing", "freshdesk-support-pricing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Growth $19/agent/mo, Pro $55/agent/mo, Enterprise $89/agent/mo. Support docs confirm two product lines and free program for 6 months.",
        "evidence_note": "Per-agent pricing; AI add-ons increase cost.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "freshdesk-free-plan",
        "tool_id": "freshdesk",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free program available for 6 months: up to 2 agents, ticketing, knowledge base, ticket dispatch, analytics, team collaboration, 24x5 email support. After 6 months, must upgrade or reduce to 2 agents permanently.",
        "source_ids": ["freshdesk-support-free", "freshdesk-support-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Support docs: Free program for 6 months with ticketing, knowledge base, analytics, team collaboration. After trial, reduce to 2 agents or upgrade.",
        "evidence_note": "Time-limited free program, not perpetual.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "freshdesk-trial",
        "tool_id": "freshdesk",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available with full feature access and no credit card required.",
        "source_ids": ["freshdesk-support-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Support docs: 14-day free trial with full feature access, no credit card required.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "freshdesk-capabilities",
        "tool_id": "freshdesk",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Ticketing and shared inbox",
            "Customer portal and knowledge base",
            "Automation rules and workflows",
            "Freddy AI Agent (500 sessions included)",
            "Freddy AI Copilot add-on ($29/agent/mo)",
            "Freddy AI Insights (Enterprise)",
            "Advanced ticket routing (Pro+)",
            "Custom roles and permissions (Pro+)",
            "Analytics dashboards and reporting",
            "Multiple SLA policies (Enterprise)",
            "Skill-based routing (Enterprise)",
            "Sandbox environment (Enterprise)",
            "Audit logs (Enterprise)",
            "IP whitelisting (Enterprise)",
            "WhatsApp campaigns (Pro+)",
            "Multilingual helpdesk (Pro+)",
            "Voice add-on available",
            "Marketplace integrations",
            "Mobile apps for iOS and Android"
        ],
        "source_ids": ["freshdesk-pricing", "freshdesk-support-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Support docs confirm plan differences and feature gating.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "freshdesk-platforms",
        "tool_id": "freshdesk",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS app", "Android app"],
        "source_ids": ["freshdesk-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page confirms mobile apps for iOS and Android.",
        "evidence_note": "Full-featured mobile apps for iOS and Android.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "freshdesk-core-use-case",
        "tool_id": "freshdesk",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Customer support platform for businesses to manage customer inquiries through ticketing, knowledge base, and multichannel support with AI-powered assistance.",
        "source_ids": ["freshdesk-pricing", "freshdesk-support-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes customer support platform. Support docs confirm ticketing, knowledge base, and multichannel support.",
        "evidence_note": "Customer support focused, not general CRM.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "freshdesk-target-user",
        "tool_id": "freshdesk",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to large businesses needing customer support. Free for very small teams (2 agents), Growth for small teams, Pro for scaling businesses, Enterprise for large organizations.",
        "source_ids": ["freshdesk-pricing", "freshdesk-support-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Growth for 'small teams', Pro for 'scaling businesses', Enterprise for 'large organizations'.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "freshdesk-limitations",
        "tool_id": "freshdesk",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free program limited to 6 months, then 2 agents permanently",
            "Advanced ticket routing requires Pro plan ($55/agent/mo)",
            "Freddy AI Copilot costs $29/agent/mo extra",
            "Enterprise features (sandbox, audit logs, IP whitelisting) require Enterprise plan ($89/agent/mo)",
            "Voice add-on costs extra ($15-$69/mo depending on plan)",
            "WhatsApp campaigns require Pro plan"
        ],
        "source_ids": ["freshdesk-pricing", "freshdesk-support-pricing", "freshdesk-support-free"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows feature gating and add-on costs. Support docs confirm free program limitations.",
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
