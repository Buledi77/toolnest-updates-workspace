#!/usr/bin/env python3
"""
Add verified evidence claims for batch 7: SoftSync AI.

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
        "source_id": "softsync-pricing",
        "url": "https://softsync.ai/pricing",
        "source_type": "official_pricing",
        "publisher": "SoftSync",
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
        "source_id": "softsync-homepage",
        "url": "https://softsync.ai",
        "source_type": "official_product",
        "publisher": "SoftSync",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "softsync-pricing-model",
        "tool_id": "softsync",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-seat subscription. Pro $29/seat/mo annual ($39 monthly), Business $59/seat/mo annual. Enterprise custom. All plans include AI, MCP, and API access.",
        "source_ids": ["softsync-pricing", "softsync-homepage"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Pro $29/seat/mo billed yearly, $39 monthly. Business $59/seat/mo. Homepage confirms 'plans start at $29 per seat per month, billed yearly'.",
        "evidence_note": "All plans include full CRM features; higher tiers add capacity and support.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "softsync-free-plan",
        "tool_id": "softsync",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan mentioned. Paid plans start at $29/seat/mo.",
        "source_ids": ["softsync-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows only paid plans (Pro, Business, Enterprise). No free tier mentioned.",
        "evidence_note": "No free plan confirmed on pricing page.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "softsync-trial",
        "tool_id": "softsync",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Trial status unclear from official sources. 'Get access' CTA on pricing page.",
        "source_ids": ["softsync-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows 'Get access' CTA but no explicit trial mention.",
        "evidence_note": "Trial status not clearly stated on official pages.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "softsync-capabilities",
        "tool_id": "softsync",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "CRM with flexible records, custom objects, and fields",
            "Table, pipeline, and calendar views",
            "Email sync, campaigns, and templates",
            "Meeting notes and summaries with desktop recorder",
            "Reports and dashboards",
            "AI Assistant",
            "Autopilot workflows",
            "Record and contact enrichment",
            "Integrations and connectors",
            "API and MCP access",
            "Chrome extension",
            "Booking pages and forms",
            "Team roles and group permissions"
        ],
        "source_ids": ["softsync-pricing", "softsync-homepage"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists all features per tier. Homepage describes CRM, booking, forms, meeting notes, and e-signatures in one place.",
        "evidence_note": "All-in-one CRM with AI and automation included on all plans.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "softsync-platforms",
        "tool_id": "softsync",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "Desktop app (Mac/Windows)", "Chrome extension"],
        "source_ids": ["softsync-pricing", "softsync-homepage"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists desktop recorder and Chrome extension. Homepage confirms desktop app for Mac and Windows.",
        "evidence_note": "Multi-platform: web, desktop, and browser extension.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "softsync-core-use-case",
        "tool_id": "softsync",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "All-in-one CRM and sales workspace for growing teams to manage the full customer process: records, email, meetings, AI, and follow-up in one connected app.",
        "source_ids": ["softsync-pricing", "softsync-homepage"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage: 'Your whole business in one app' and 'from $29 per person a month'. Pricing page describes 'complete sales workspace'.",
        "evidence_note": "Positioned as all-in-one CRM alternative to multi-tool stacks.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "softsync-target-user",
        "tool_id": "softsync",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Growing sales teams and businesses needing an all-in-one CRM. Pro for growing teams (up to 25 people), Business for larger teams, Enterprise for custom needs.",
        "source_ids": ["softsync-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Pro 'for growing teams', Business 'for larger teams', Enterprise custom. Pro supports up to 25 people.",
        "evidence_note": "Targets teams replacing multi-tool CRM stacks.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "softsync-limitations",
        "tool_id": "softsync",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "No free plan available",
            "Pro plan limited to 25 team members",
            "Enterprise pricing not publicly disclosed",
            "Data migration is self-served on Pro plan",
            "Priority support only on Business and Enterprise plans"
        ],
        "source_ids": ["softsync-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows plan limits and support tiers. Pro has self-served migration, Business/Enterprise get priority support.",
        "evidence_note": "Support level varies significantly by plan.",
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
