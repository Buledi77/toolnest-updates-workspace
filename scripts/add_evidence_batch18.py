#!/usr/bin/env python3
"""
Add verified evidence claims for batch 18: Smartlead.

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
        "source_id": "smartlead-homepage",
        "url": "https://www.smartlead.ai",
        "source_type": "official_product",
        "publisher": "Smartlead",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "smartlead-blog-tools",
        "url": "https://www.smartlead.ai/blog/ai-cold-email-outreach-tools",
        "source_type": "official_product",
        "publisher": "Smartlead",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "smartlead-comparison",
        "url": "https://www.smartlead.ai/comparison/smartlead-vs-snov",
        "source_type": "official_product",
        "publisher": "Smartlead",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "smartlead-pricing-model",
        "tool_id": "smartlead",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Volume-based subscription. Base $39/mo (2,000 contacts, 6,000 emails/mo). Pro $94/mo (30,000 contacts, 90,000 emails/mo, CRM included). Unlimited Smart $174/mo (unlimited contacts, 150,000 emails/mo). Unlimited Prime $379/mo (unlimited contacts, 500,000 emails/mo). All plans include unlimited email accounts. 17% annual billing discount.",
        "source_ids": ["smartlead-homepage", "smartlead-blog-tools", "smartlead-comparison"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Homepage and blog: Base $39/mo, Pro $94/mo, Unlimited Smart $174/mo, Unlimited Prime $379/mo. All plans include unlimited email accounts. Annual billing saves 17%.",
        "evidence_note": "Volume-based pricing; no per-mailbox fees. CRM only on Pro+.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "smartlead-free-plan",
        "tool_id": "smartlead",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a free trial with 50% off first month.",
        "source_ids": ["smartlead-homepage"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage: 'Sign up now and get 50% off on your first month on any plan'. No free plan mentioned.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "smartlead-trial",
        "tool_id": "smartlead",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Free trial available with 50% off first month on any plan.",
        "source_ids": ["smartlead-homepage"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage: 'Start Free Trial' and '50% off on your first month on any plan'.",
        "evidence_note": "Trial period length not specified.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "smartlead-capabilities",
        "tool_id": "smartlead",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Cold email automation and sequences",
            "Unlimited email accounts (mailboxes)",
            "Automated email warmup",
            "Unique IP servers per campaign",
            "Sender reputation protection",
            "Master inbox for unified replies",
            "Custom CRM (Pro+)",
            "Analytics and reporting",
            "Personalization fields and spintax",
            "Automated mailbox rotation",
            "HubSpot, Salesforce, Pipedrive integrations",
            "Webhooks and API access",
            "White-label experience",
            "Subsequences based on lead behavior",
            "AI-powered outreach"
        ],
        "source_ids": ["smartlead-homepage", "smartlead-blog-tools", "smartlead-comparison"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage lists unlimited mailboxes, warmup, IP servers, reputation protection, master inbox. Blog confirms CRM on Pro+. Comparison page confirms integrations.",
        "evidence_note": "All plans include unlimited mailboxes; pricing scales by send volume.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "smartlead-platforms",
        "tool_id": "smartlead",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["smartlead-homepage"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Smartlead operates as a web-based platform for cold email outreach.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "smartlead-core-use-case",
        "tool_id": "smartlead",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Cold email outreach platform for B2B sales teams and agencies to automate email campaigns at scale with unlimited mailboxes, automated warmup, and deliverability optimization.",
        "source_ids": ["smartlead-homepage", "smartlead-blog-tools"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage: 'Cold Email Software for Sales Teams That Run Outbound at Scale'. Blog positions it for cold email outreach.",
        "evidence_note": "Cold email focused, not general marketing automation.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "smartlead-target-user",
        "tool_id": "smartlead",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "B2B sales teams, lead generation agencies, and marketers running cold email outreach. Base for solopreneurs, Pro for growing businesses, Unlimited Smart for agencies, Unlimited Prime for large enterprises.",
        "source_ids": ["smartlead-homepage", "smartlead-blog-tools"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage: Base for 'small businesses and solopreneurs', Pro for 'marketers and growing businesses', Unlimited Smart for 'lead generation agencies', Unlimited Prime for 'large enterprises'.",
        "evidence_note": "B2B cold email focused; not suitable for transactional email.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "smartlead-limitations",
        "tool_id": "smartlead",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "No free plan available",
            "Base plan limited to 2,000 contacts and 6,000 emails/month",
            "Built-in CRM not included on Base plan",
            "Send volume limits may constrain high-volume campaigns",
            "Cold email-only; not suitable for transactional or marketing email",
            "No per-mailbox fees but volume limits apply"
        ],
        "source_ids": ["smartlead-homepage", "smartlead-comparison"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Homepage shows volume limits. Comparison page confirms CRM only on Pro+.",
        "evidence_note": "Volume-based limits are the primary constraint.",
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
