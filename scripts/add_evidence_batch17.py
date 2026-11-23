#!/usr/bin/env python3
"""
Add verified evidence claims for batch 17: Help Scout.

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
        "source_id": "helpscout-pricing",
        "url": "https://www.helpscout.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Help Scout",
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
        "source_id": "helpscout-compare-gorgias",
        "url": "https://www.helpscout.com/compare/gorgias",
        "source_type": "official_product",
        "publisher": "Help Scout",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "helpscout-compare-zendesk",
        "url": "https://www.helpscout.com/compare/zendesk",
        "source_type": "official_product",
        "publisher": "Help Scout",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "helpscout-pricing-model",
        "tool_id": "helpscout",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-user subscription. Free plan for up to 5 users (email only, 1 help center). Standard $25/user/mo (live chat, SMS, WhatsApp, Instagram, Messenger, 2 help centers). Plus $45/user/mo (advanced workflows, 3 help centers, AI Drafts, Salesforce/Jira/HubSpot). Pro $75/user/mo (SSO/SAML, HIPAA, 5 help centers, unlimited workflows). Envoy AI agent add-on $0.75/resolution.",
        "source_ids": ["helpscout-pricing", "helpscout-compare-gorgias", "helpscout-compare-zendesk"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Free up to 5 users, Standard $25/user/mo, Plus $45/user/mo, Pro $75/user/mo. Compare pages confirm same pricing and feature gating.",
        "evidence_note": "Free plan is email-only; paid plans add channels. Envoy AI agent is usage-based add-on.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "helpscout-free-plan",
        "tool_id": "helpscout",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: up to 5 users, 1 shared inbox (email only), 1 help center, 10 tags, 10 saved replies, basic reporting. No live chat, SMS, or social channels.",
        "source_ids": ["helpscout-compare-gorgias", "helpscout-compare-zendesk"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Compare pages: Free plan includes shared inbox, knowledge base, reporting, 10 tags, 10 saved replies. Email only, no live chat or social.",
        "evidence_note": "Genuine free tier but email-only.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "helpscout-trial",
        "tool_id": "helpscout",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Free trial available on paid plans ('Try for Free' on pricing page). Envoy AI agent has 3-month free trial.",
        "source_ids": ["helpscout-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Try for Free' on Standard and Plus plans. Envoy add-on: '3-month free trial'.",
        "evidence_note": "Trial period length not specified on pricing page.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "helpscout-capabilities",
        "tool_id": "helpscout",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Shared inbox for email support",
            "Live chat, SMS, WhatsApp, Instagram, Facebook Messenger",
            "Knowledge base (help center)",
            "AI Inbox assistant (all paid plans)",
            "AI Assist and Topics (all paid plans)",
            "AI Summarize and AI Drafts (Plus and Pro)",
            "Multiple inboxes",
            "Basic workflows (Standard), advanced (Plus), unlimited (Pro)",
            "SLA policies",
            "Round robin routing (Plus+)",
            "Salesforce, Jira, HubSpot integrations (Plus+)",
            "SSO/SAML (Pro)",
            "HIPAA compliance (Pro)",
            "Envoy AI agent add-on ($0.75/resolution)",
            "Light users (view-only seats)"
        ],
        "source_ids": ["helpscout-pricing", "helpscout-compare-gorgias", "helpscout-compare-zendesk"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Compare pages confirm channel support and AI features.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "helpscout-platforms",
        "tool_id": "helpscout",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["helpscout-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Help Scout is a cloud-based customer support platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "helpscout-core-use-case",
        "tool_id": "helpscout",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Customer support platform for businesses to provide multi-channel support (email, chat, SMS, social) with shared inbox, knowledge base, and AI-powered assistance.",
        "source_ids": ["helpscout-pricing", "helpscout-compare-gorgias"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes customer support platform. Compare pages confirm multi-channel support and knowledge base.",
        "evidence_note": "Customer support focused, not general CRM.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "helpscout-target-user",
        "tool_id": "helpscout",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to large businesses needing customer support. Free for very small teams (5 users), Standard for growing teams, Plus for teams managing higher volume, Pro for teams needing scale and security.",
        "source_ids": ["helpscout-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Standard for 'growing teams', Plus for 'teams managing higher volume', Pro for 'teams that need the highest level of scale and security'.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "helpscout-limitations",
        "tool_id": "helpscout",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan limited to email only (no live chat, SMS, or social)",
            "Free plan limited to 10 tags and 10 saved replies",
            "Advanced workflows require Plus plan ($45/user/mo)",
            "SSO/SAML and HIPAA compliance require Pro plan ($75/user/mo)",
            "Envoy AI agent costs $0.75/resolution on top of seat pricing",
            "Additional help centers cost $20/mo each"
        ],
        "source_ids": ["helpscout-pricing", "helpscout-compare-gorgias"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows feature gating. Compare pages confirm free plan limitations and add-on costs.",
        "evidence_note": "Free plan is email-only; paid plans add channels.",
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
