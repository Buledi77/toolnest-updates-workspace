#!/usr/bin/env python3
"""
Add verified evidence claims for batch 15: Teachable.

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
        "source_id": "teachable-pricing",
        "url": "https://www.teachable.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Teachable",
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
        "source_id": "teachable-online-courses",
        "url": "https://www.teachable.com/online-courses",
        "source_type": "official_product",
        "publisher": "Teachable",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "teachable-support-plans",
        "url": "https://support.teachable.com/en/articles/11682410-new-teachable-plans-in-june-2025",
        "source_type": "official_docs",
        "publisher": "Teachable",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "teachable-pricing-model",
        "tool_id": "teachable",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Product-based tiered subscription. Starter $29/mo annual ($39 monthly, 7.5% transaction fee, 5 products). Builder $69/mo annual ($89 monthly, 0% fee, 10 products). Growth $139/mo annual ($189 monthly, 0% fee, 50 products). Custom for high-volume. Payment processing 2.9% + $0.30 US, 3.9% + $0.30 international.",
        "source_ids": ["teachable-pricing", "teachable-online-courses", "teachable-support-plans"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Starter $29/mo annual, Builder $69/mo, Growth $139/mo. Online courses page confirms 7.5% transaction fee on Starter, 0% on Builder/Growth. Support docs detail plan changes in June 2025.",
        "evidence_note": "Transaction fee on Starter plan; 0% on Builder and Growth. Payment processing fees apply on all plans.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teachable-free-plan",
        "tool_id": "teachable",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a 7-day free trial with 30-day money-back guarantee.",
        "source_ids": ["teachable-pricing", "teachable-online-courses"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: '7-day free trial. 30-day guarantee.' Online courses page confirms no free plan.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teachable-trial",
        "tool_id": "teachable",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "7-day free trial available on all plans with 30-day money-back guarantee.",
        "source_ids": ["teachable-pricing", "teachable-online-courses"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: '7-day free trial. 30-day guarantee.' Online courses page confirms same.",
        "evidence_note": "Short trial period with money-back guarantee.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teachable-capabilities",
        "tool_id": "teachable",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Course creation with AI builder",
            "Memberships and subscriptions",
            "Community (unlimited spaces)",
            "Auto-graded quizzes and short answer assessments",
            "Course certificates and compliance",
            "Drip content and lesson comments",
            "Built-in email marketing",
            "Affiliate program",
            "Coupons, upsells, and order bumps",
            "Abandoned cart emails",
            "Bundles",
            "Student referrals",
            "Custom reporting",
            "iOS and Android student apps",
            "Global payments with VAT/GST handling",
            "Custom domain and branding",
            "Zapier and webhook integrations",
            "Public API access (Growth+)"
        ],
        "source_ids": ["teachable-pricing", "teachable-online-courses", "teachable-support-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Online courses page confirms mobile apps and tax automation. Support docs detail plan features.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teachable-platforms",
        "tool_id": "teachable",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS student app", "Android student app"],
        "source_ids": ["teachable-pricing", "teachable-online-courses"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'iOS & Android student apps' on all plans. Online courses page confirms native mobile apps.",
        "evidence_note": "Mobile apps for students, not creators.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teachable-core-use-case",
        "tool_id": "teachable",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Online course platform for creators, coaches, and educators to build, host, and sell online courses with integrated payments, marketing, and student engagement tools.",
        "source_ids": ["teachable-pricing", "teachable-online-courses"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page targets course creators. Online courses page describes full course creation and selling platform.",
        "evidence_note": "All-in-one course platform, not just hosting.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teachable-target-user",
        "tool_id": "teachable",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Course creators, coaches, and educators selling online courses. Starter for beginners, Builder for growing creators, Growth for established businesses, Custom for high-volume enterprises.",
        "source_ids": ["teachable-online-courses"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Online courses page: 'Creators, coaches, and educators who want full control over their online school'.",
        "evidence_note": "Targets course creators across scales.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teachable-limitations",
        "tool_id": "teachable",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Starter plan charges 7.5% transaction fee on top of subscription",
            "Starter limited to 5 products and 1 admin",
            "Builder limited to 10 products and 3 admins",
            "Growth limited to 50 products and 5 admins",
            "No perpetual free plan",
            "Custom plan pricing not publicly disclosed"
        ],
        "source_ids": ["teachable-pricing", "teachable-online-courses"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows product limits and transaction fees. Online courses page confirms fee structure.",
        "evidence_note": "Transaction fee on Starter can make it more expensive than Builder at scale.",
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
