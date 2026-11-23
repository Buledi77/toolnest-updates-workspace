#!/usr/bin/env python3
"""
Add verified evidence claims for batch 25: Zoho CRM.

Sources: Official pricing pages cross-referenced with third-party analysis.
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
        "source_id": "zohocrm-pricing",
        "url": "https://www.zoho.com/crm/pricing.html",
        "source_type": "official_pricing",
        "publisher": "Zoho",
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
        "source_id": "zohocrm-elsner",
        "url": "https://www.elsner.com/zoho-crm-pricing-plans-guide",
        "source_type": "third_party_analysis",
        "publisher": "Elsner",
        "official": False,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "zohocrm-codestringers",
        "url": "https://www.codestringers.com/articles/zoho-crm-pricing",
        "source_type": "third_party_analysis",
        "publisher": "CodeStringers",
        "official": False,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "zohocrm-pricing-model",
        "tool_id": "zohocrm",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-user subscription. Free: up to 3 users. Standard $14/user/mo annual ($20 monthly). Professional $23/user/mo annual ($35 monthly). Enterprise $40/user/mo annual ($50 monthly). Ultimate $52/user/mo annual ($65 monthly). 15-day free trial on paid plans. Monthly billing costs 20-34% more.",
        "source_ids": ["zohocrm-pricing", "zohocrm-elsner", "zohocrm-codestringers"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Multiple sources confirm: Free up to 3 users, Standard $14/mo annual, Professional $23/mo, Enterprise $40/mo, Ultimate $52/mo. 15-day free trial on paid plans.",
        "evidence_note": "Per-user pricing; monthly billing significantly more expensive.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zohocrm-free-plan",
        "tool_id": "zohocrm",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: up to 3 users, 5,000 records, contact management, reminders, workflow automation, 10 email templates, standard reports, mobile apps. No mass email, limited workflow rules (5 per module).",
        "source_ids": ["zohocrm-elsner", "zohocrm-codestringers"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources confirm: Free plan includes contact management, reminders, workflow automation, 10 email templates, standard reports, mobile apps. Limited to 5,000 records and 5 active workflow rules per module.",
        "evidence_note": "Genuine free tier but limited to 3 users and 5,000 records.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zohocrm-trial",
        "tool_id": "zohocrm",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "15-day free trial available on paid plans.",
        "source_ids": ["zohocrm-codestringers"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources confirm 15-day free trial on all paid plans.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zohocrm-capabilities",
        "tool_id": "zohocrm",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "CRM with contact and deal management",
            "Sales pipeline management",
            "Workflow automation",
            "Blueprint process automation (Professional+)",
            "Inventory management (quotes, orders, invoices) (Professional+)",
            "Zia AI assistant and predictive scoring (Enterprise+)",
            "Custom modules and multi-page layouts (Enterprise+)",
            "Territory management (Enterprise+)",
            "Advanced analytics and CommandCenter (Enterprise+)",
            "Zoho Analytics bundle (Ultimate)",
            "Multi-user portals (Enterprise+)",
            "Sandbox environment (Enterprise+)",
            "Webhooks and validation rules (Professional+)",
            "Mass email campaigns",
            "Mobile apps for iOS and Android",
            "Zoho ecosystem integrations (50+ apps)",
            "Custom reporting and dashboards"
        ],
        "source_ids": ["zohocrm-elsner", "zohocrm-codestringers"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources list features per tier. Professional adds blueprint, inventory, webhooks. Enterprise adds Zia AI, custom modules, territory management, sandbox. Ultimate adds advanced analytics.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zohocrm-platforms",
        "tool_id": "zohocrm",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS app", "Android app"],
        "source_ids": ["zohocrm-elsner"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources confirm mobile apps for iOS and Android on all plans.",
        "evidence_note": "Full-featured mobile apps for iOS and Android.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zohocrm-core-use-case",
        "tool_id": "zohocrm",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "CRM platform for small to enterprise businesses to manage sales pipelines, customer relationships, and business processes with automation and AI-powered insights.",
        "source_ids": ["zohocrm-elsner", "zohocrm-codestringers"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources describe CRM for sales tracking, automation, and business process management.",
        "evidence_note": "Broad CRM platform, not niche-focused.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zohocrm-target-user",
        "tool_id": "zohocrm",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to enterprise businesses needing CRM. Free for very small teams (3 users), Standard for small teams, Professional for growing teams, Enterprise for mid-sized orgs, Ultimate for data-heavy teams.",
        "source_ids": ["zohocrm-elsner", "zohocrm-codestringers"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources: Free for 'tiny teams', Standard for 'small teams', Professional for 'growing teams', Enterprise for 'mid-sized orgs', Ultimate for 'data-heavy teams'.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zohocrm-limitations",
        "tool_id": "zohocrm",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan limited to 3 users and 5,000 records",
            "No mass email on free plan",
            "Limited workflow rules (5 per module) on free plan",
            "Zia AI requires Enterprise plan ($40/user/mo)",
            "Custom modules and sandbox require Enterprise plan",
            "Advanced analytics requires Ultimate plan ($52/user/mo)",
            "Monthly billing costs 20-34% more than annual"
        ],
        "source_ids": ["zohocrm-elsner", "zohocrm-codestringers"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources show feature gating and plan limits. Free plan has significant restrictions.",
        "evidence_note": "Free plan is quite limited; AI features gated to Enterprise.",
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
