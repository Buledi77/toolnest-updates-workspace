#!/usr/bin/env python3
"""
Add verified evidence claims for batch 13: Streak.

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
        "source_id": "streak-pricing",
        "url": "https://www.streak.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Streak",
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
        "source_id": "streak-sales-crm",
        "url": "https://www.streak.com/sales-crm",
        "source_type": "official_product",
        "publisher": "Streak",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "streak-support",
        "url": "https://support.streak.com/en/articles/2542950-what-is-streak",
        "source_type": "official_docs",
        "publisher": "Streak",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "streak-pricing-model",
        "tool_id": "streak",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-user subscription. Free plan available. Pro $49/user/mo annual ($59 monthly, 20 AI credits). Pro+ $69/user/mo annual ($89 monthly, 150 AI credits, integrations, automations). Enterprise $129/user/mo annual ($159 monthly, custom roles, dedicated support). 20% annual billing discount.",
        "source_ids": ["streak-pricing", "streak-sales-crm"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Pro $49/user/mo annual, Pro+ $69/user/mo annual, Enterprise $129/user/mo annual. Monthly billing $10 more per user. 20% annual discount.",
        "evidence_note": "Per-user pricing; all team members must be on same plan.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "streak-free-plan",
        "tool_id": "streak",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: email tracking, link tracking, email snippets, 50 mail merge sends/day, Streak Share, thread splitter. No CRM pipelines on free plan.",
        "source_ids": ["streak-pricing", "streak-support"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'free plan works inside Gmail at no cost and includes email and link tracking, email snippets, 50 mail merge sends per day, Streak Share, and thread splitter. The free plan does not include CRM pipelines.'",
        "evidence_note": "Genuine free tier but no CRM pipelines.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "streak-trial",
        "tool_id": "streak",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial of Pro+ plan available, including integrations, automation, unlimited contacts and CRM records, and 1,000 AI credits.",
        "source_ids": ["streak-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'free 14-day trial of the Pro+ plan, which includes integrations, automation, unlimited contacts and CRM records, and 1,000 AI credits.'",
        "evidence_note": "Trial provides Pro+ level access.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "streak-capabilities",
        "tool_id": "streak",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Gmail-native CRM with visual pipelines",
            "Unlimited contacts, pipelines, and records",
            "Shared pipelines and real-time collaboration",
            "Mail merge (50/day free, unlimited on paid)",
            "Email tracking and link tracking",
            "Email snippets and templates",
            "AI-powered features (20 credits Pro, 150 Pro+)",
            "Integrations and automations (Pro+)",
            "Advanced report dashboards (Pro+)",
            "Custom roles and permissions (Enterprise)",
            "Data validation rules (Enterprise)",
            "Mobile apps for iOS and Android",
            "Thread splitter and Streak Share"
        ],
        "source_ids": ["streak-pricing", "streak-sales-crm", "streak-support"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Sales CRM page confirms Gmail-native experience. Support docs describe Boxes, Sidebar, and CRM functionality.",
        "evidence_note": "All CRM features on paid plans; free plan has email tools only.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "streak-platforms",
        "tool_id": "streak",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Gmail (Chrome extension)", "iOS app", "Android app"],
        "source_ids": ["streak-pricing", "streak-sales-crm"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows iOS and Android app logos. Product is Gmail-native via Chrome extension.",
        "evidence_note": "Gmail-native with mobile apps for pipeline management.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "streak-core-use-case",
        "tool_id": "streak",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Gmail-native CRM for sales teams who want to manage pipelines, contacts, and deals directly inside Gmail without switching to a separate CRM application.",
        "source_ids": ["streak-pricing", "streak-sales-crm"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'full CRM in Gmail'. Sales CRM page: 'all CRM functionality is embedded in Gmail, not an external app'.",
        "evidence_note": "Gmail-native CRM, not a standalone CRM.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "streak-target-user",
        "tool_id": "streak",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to medium sales teams and solo operators who work primarily in Gmail. Free for individuals, Pro for small teams, Pro+ for teams needing automations, Enterprise for larger organizations.",
        "source_ids": ["streak-pricing", "streak-sales-crm"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Pro for 'teams who want a full CRM in Gmail', Pro+ for 'teams who need automations'. Sales CRM page targets 'Gmail-heavy small teams and solo operators'.",
        "evidence_note": "Gmail-dependent; not suitable for Outlook-heavy teams.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "streak-limitations",
        "tool_id": "streak",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan does not include CRM pipelines",
            "All team members must be on the same plan",
            "Gmail-only — does not work with Outlook or other email clients",
            "Mail merge limited to 50/day on free plan, 400/day for personal Gmail",
            "Integrations and automations require Pro+ plan ($69/user/mo)",
            "Enterprise plan requires minimum 10 users"
        ],
        "source_ids": ["streak-pricing", "streak-sales-crm"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page notes same-plan requirement and free plan limitations. Sales CRM page confirms Gmail-only and mail merge limits.",
        "evidence_note": "Gmail dependency is the primary limitation.",
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
