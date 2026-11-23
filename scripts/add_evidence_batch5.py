#!/usr/bin/env python3
"""
Add verified evidence claims for batch 5: Reply.io.

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
        "source_id": "replyio-pricing",
        "url": "https://reply.io",
        "source_type": "official_pricing",
        "publisher": "Reply.io",
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
        "claim_id": "replyio-pricing-model",
        "tool_id": "replyio",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Tiered subscription by contacts. Email Volume $49/user/mo annual (1,000 active contacts), Multichannel $89/user/mo annual (unlimited contacts). AI SDR Starter $500/mo. LinkedIn automation $69/mo/account add-on. Calls & SMS $29/mo/account add-on.",
        "source_ids": ["replyio-pricing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Official site: Email Volume $49/user/mo billed annually starting at 1,000 active contacts. Multichannel $89/user/mo annual with unlimited contacts. AI SDR $500/mo. LinkedIn $69/mo/acct, Calls & SMS $29/mo/acct.",
        "evidence_note": "Pricing scales by active contacts on Email Volume plan; Multichannel is flat-rate unlimited.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "replyio-free-trial",
        "tool_id": "replyio",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available.",
        "source_ids": ["replyio-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Official site: 'Start 14-day trial' on Multichannel plan.",
        "evidence_note": "Short trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "replyio-free-plan",
        "tool_id": "replyio",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a 14-day free trial.",
        "source_ids": ["replyio-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Official site shows only paid plans with 14-day trial. No perpetual free tier.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "replyio-capabilities",
        "tool_id": "replyio",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Multichannel sales outreach (email, LinkedIn, SMS, calls)",
            "Email automation with sequences",
            "Email warmup included with every mailbox",
            "Unlimited emails to active contacts",
            "LinkedIn automation ($69/mo/account add-on)",
            "Calls & SMS automation ($29/mo/account add-on)",
            "AI-powered personalization",
            "Live data credits (50/month) from 1B+ B2B contacts",
            "Anti-spam and deliverability suite",
            "Reply management and meeting scheduling",
            "Contact enrichment",
            "Team performance and channel efficiency reports"
        ],
        "source_ids": ["replyio-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Official site lists email automation, LinkedIn, calls, SMS, warmup, unlimited emails, live data credits, anti-spam suite, and AI features.",
        "evidence_note": "Multichannel platform with email as primary channel.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "replyio-platforms",
        "tool_id": "replyio",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "Chrome extension"],
        "source_ids": ["replyio-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Reply.io operates as a web-based platform with Chrome extension for LinkedIn automation.",
        "evidence_note": "Web-based with browser extension for LinkedIn.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "replyio-core-use-case",
        "tool_id": "replyio",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "B2B sales engagement platform for automating multichannel outbound outreach (email, LinkedIn, SMS, calls) to scale prospecting and book more meetings.",
        "source_ids": ["replyio-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Official site describes 'AI Sales Outreach & Cold Email Platform' for SDR and sales teams.",
        "evidence_note": "B2B outbound-focused, not inbound marketing.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "replyio-target-user",
        "tool_id": "replyio",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "B2B sales development representatives, sales teams, and lead generation agencies who need to scale outbound outreach across multiple channels.",
        "source_ids": ["replyio-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Official site targets SDRs and sales teams. Third-party reviews confirm B2B sales teams and agencies.",
        "evidence_note": "B2B sales-focused, not suitable for B2C or non-outbound use cases.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "replyio-limitations",
        "tool_id": "replyio",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Email Volume plan limited by active contacts per month",
            "LinkedIn automation is a paid add-on ($69/mo/account)",
            "Calls & SMS automation is a paid add-on ($29/mo/account)",
            "Only 50 live data credits/month on base plans",
            "No perpetual free plan",
            "Some users report usability issues and support concerns"
        ],
        "source_ids": ["replyio-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Official site shows add-on costs for LinkedIn and calls/SMS. Third-party reviews note usability concerns.",
        "evidence_note": "Total cost increases with add-ons and higher contact volumes.",
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
