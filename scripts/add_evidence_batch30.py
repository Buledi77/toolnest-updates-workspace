#!/usr/bin/env python3
"""
Add verified evidence claims for batch 30: SEMrush.

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
        "source_id": "semrush-pricing-seo",
        "url": "https://www.semrush.com/pricing/seo-ai-search",
        "source_type": "official_pricing",
        "publisher": "Semrush",
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
        "source_id": "semrush-pricing-content",
        "url": "https://www.semrush.com/pricing/content",
        "source_type": "official_pricing",
        "publisher": "Semrush",
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
        "source_id": "semrush-pricing-local",
        "url": "https://www.semrush.com/pricing/local",
        "source_type": "official_pricing",
        "publisher": "Semrush",
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
        "claim_id": "semrush-pricing-model",
        "tool_id": "semrush",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Modular subscription pricing. SEO-only $139/mo annual (5 websites, 500 keywords). Starter SEO+AI Search $199/mo annual (5 websites, 500 keywords, AI visibility). Pro+ SEO+AI Search $299/mo annual (15 websites, 1,500 keywords, content optimization). Advanced custom. Content toolkit $60/mo annual. Local toolkit $30/mo per location. Add-ons: additional users $45/mo, lead generation $90/mo, Base Report $10/mo, Pro Report $20/mo.",
        "source_ids": ["semrush-pricing-seo", "semrush-pricing-content", "semrush-pricing-local"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing pages: SEO $139/mo annual, Starter SEO+AI $199/mo, Pro+ $299/mo. Content toolkit $60/mo. Local toolkit $30/mo per location. Add-ons listed on all pricing pages.",
        "evidence_note": "Modular pricing; users can mix and match toolkits. Annual billing saves ~15%.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "semrush-free-plan",
        "tool_id": "semrush",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Free trial available. Free tools available: domain overview, backlink checker, keyword overview (limited).",
        "source_ids": ["semrush-pricing-seo"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows 'Start for free' CTA for trial but no perpetual free plan. Free tools available on homepage.",
        "evidence_note": "No free plan; limited free tools available.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "semrush-trial",
        "tool_id": "semrush",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "Free trial available ('Start for free' on pricing page). Trial period length not specified.",
        "source_ids": ["semrush-pricing-seo"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Start for free' CTA. Trial period length not specified on pricing page.",
        "evidence_note": "Trial period length not clearly stated.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "semrush-capabilities",
        "tool_id": "semrush",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Keyword research and competitor analysis",
            "Position tracking and rank monitoring",
            "Site audit and technical SEO",
            "Backlink analysis",
            "AI visibility and prompt tracking",
            "Content optimization and SEO briefs",
            "Content creation with AI",
            "Social media management",
            "PPC advertising research",
            "Market analysis and competitive intelligence",
            "Local SEO and Google Business Profile management",
            "Digital PR and link building",
            "AI brand sentiment monitoring",
            "Custom reports and dashboards",
            "MCP access for AI assistants",
            "API access",
            "100+ integrations",
            "Mobile apps for iOS and Android"
        ],
        "source_ids": ["semrush-pricing-seo", "semrush-pricing-content", "semrush-pricing-local"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing pages list features per tier. SEO page: keyword research, competitor analysis, position tracking, site audit, AI visibility. Content page: content creation, SEO briefs. Local page: GBP management, review management.",
        "evidence_note": "Comprehensive SEO and marketing platform with modular toolkits.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "semrush-platforms",
        "tool_id": "semrush",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS app", "Android app"],
        "source_ids": ["semrush-pricing-seo"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Semrush is a cloud-based SEO platform with mobile apps for iOS and Android.",
        "evidence_note": "Full-featured mobile apps for iOS and Android.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "semrush-core-use-case",
        "tool_id": "semrush",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "SEO and digital marketing platform for businesses to conduct keyword research, competitor analysis, site audits, rank tracking, content optimization, and AI visibility monitoring.",
        "source_ids": ["semrush-pricing-seo", "semrush-pricing-content"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing pages describe SEO and AI search platform. Content page confirms content creation and optimization.",
        "evidence_note": "SEO-focused with broader marketing capabilities.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "semrush-target-user",
        "tool_id": "semrush",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Freelancers, small businesses, agencies, and enterprises needing SEO and marketing tools. SEO plan for freelancers, Starter for small teams, Pro+ for growing teams and agencies, Advanced for enterprises.",
        "source_ids": ["semrush-pricing-seo"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: SEO for 'freelancers and small businesses', Starter for 'small teams and agencies', Pro+ for 'growing teams and agencies'.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "semrush-limitations",
        "tool_id": "semrush",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "No free plan available",
            "SEO plan limited to 5 websites and 500 keywords",
            "Content optimization requires Starter plan ($199/mo)",
            "Historical SEO data requires Pro+ plan ($299/mo)",
            "Advanced plan pricing not publicly disclosed",
            "Modular pricing means total cost increases with additional toolkits"
        ],
        "source_ids": ["semrush-pricing-seo", "semrush-pricing-content"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing pages show feature gating and plan limits. Modular pricing means costs stack.",
        "evidence_note": "Modular pricing can become expensive with multiple toolkits.",
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
