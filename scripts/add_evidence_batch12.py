#!/usr/bin/env python3
"""
Add verified evidence claims for batch 12: PhantomBuster.

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
        "source_id": "phantombuster-support-plans",
        "url": "https://support.phantombuster.com/hc/en-us/articles/4494623647250-What-Each-PhantomBuster-Plan-Includes-Features-Limits-and-Pricing",
        "source_type": "official_docs",
        "publisher": "PhantomBuster",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "phantombuster-blog-pricing",
        "url": "https://phantombuster.com/blog/ai-automation/phantombuster-pricing-explained",
        "source_type": "official_product",
        "publisher": "PhantomBuster",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "phantombuster-pricing-model",
        "tool_id": "phantombuster",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Workspace-based subscription. Start $69/mo ($56 annual, 20h execution, 5 slots, 10K AI credits, 500 email credits). Grow $159/mo ($128 annual, 80h, 15 slots, 30K AI, 2,500 email). Scale $439/mo ($352 annual, 300h, 50 slots, 90K AI, 10K email). Free plan: 30 min/month, 1 slot, 50 MB storage.",
        "source_ids": ["phantombuster-support-plans", "phantombuster-blog-pricing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Support docs and blog: Start $69/mo ($56 annual), Grow $159/mo ($128 annual), Scale $439/mo ($352 annual). Free plan 30 min/month with 1 slot.",
        "evidence_note": "Workspace-based pricing — no per-user charges. Up to 100 workspace members.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "phantombuster-free-plan",
        "tool_id": "phantombuster",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: 30 min/month execution time, 1 slot, 50 MB storage. No AI, email, URL Finder, or CAPTCHA credits. Exports limited to 10 rows.",
        "source_ids": ["phantombuster-support-plans", "phantombuster-blog-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Blog: 'Free includes 30 minutes per month of execution time, 1 slot, and 50 MB of storage. It does not include monthly AI, email discovery, URL Finder, or CAPTCHA credits. Exports and API output are limited to 10 rows.'",
        "evidence_note": "Very limited free tier — mainly for light validation.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "phantombuster-trial",
        "tool_id": "phantombuster",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available with no credit card required. 2 hours total execution time, 5 slots, 1,000 AI credits, 50 email credits.",
        "source_ids": ["phantombuster-support-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Support docs: Free trial 14 days with 2 hours total execution, 5 slots, 1,000 AI credits, 50 email credits, 50 CAPTCHA credits.",
        "evidence_note": "Generous trial with full platform access.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "phantombuster-capabilities",
        "tool_id": "phantombuster",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "130+ automation Phantoms for LinkedIn and other platforms",
            "LinkedIn data extraction (profiles, companies, posts, groups)",
            "Email discovery and verification",
            "AI-powered data enrichment",
            "Workflow automation (multi-step Flows)",
            "URL Finder for website discovery",
            "CAPTCHA-solving credits",
            "CRM integrations (HubSpot bi-directional)",
            "Google Sheets, n8n, Zapier, Make integrations",
            "LinkedIn Sales Navigator integration",
            "Unlimited CSV/JSON exports (paid plans)",
            "API access",
            "Up to 100 workspace members"
        ],
        "source_ids": ["phantombuster-support-plans", "phantombuster-blog-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Support docs list all features. Blog confirms 130+ automations, CRM integrations, and workspace-based pricing.",
        "evidence_note": "All Phantoms available on all plans; pricing scales by execution time and slots.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "phantombuster-platforms",
        "tool_id": "phantombuster",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["phantombuster-support-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "PhantomBuster operates as a cloud-based platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "phantombuster-core-use-case",
        "tool_id": "phantombuster",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Web automation and data extraction platform for B2B prospecting, lead generation, and social media intelligence, primarily focused on LinkedIn data extraction and enrichment.",
        "source_ids": ["phantombuster-support-plans", "phantombuster-blog-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Support docs describe automation Phantoms for LinkedIn and other platforms. Blog positions it for prospecting workflows.",
        "evidence_note": "Data extraction and automation, not outreach execution.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "phantombuster-target-user",
        "tool_id": "phantombuster",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "B2B sales teams, recruiters, marketers, and agencies who need to extract and enrich data from LinkedIn and other platforms. Start for individuals, Grow for small teams, Scale for agencies and large teams.",
        "source_ids": ["phantombuster-blog-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Blog: Grow fits 'consultants, SDRs, and small teams'. Scale for 'agencies managing multiple client campaigns'.",
        "evidence_note": "Targets teams needing data extraction at scale.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "phantombuster-limitations",
        "tool_id": "phantombuster",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan very limited: 30 min/month, 1 slot, 10-row export limit, no credits",
            "Start plan limited to 20 hours/month execution time",
            "Execution time is shared across all workspace members",
            "Credits (AI, email, URL, CAPTCHA) do not roll over between months",
            "LinkedIn automation carries account safety risks",
            "Complex workflows consume slots quickly"
        ],
        "source_ids": ["phantombuster-support-plans", "phantombuster-blog-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Support docs note shared resources and no rollover. Blog notes slot consumption for complex workflows.",
        "evidence_note": "Shared workspace resources can be consumed quickly by complex workflows.",
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
