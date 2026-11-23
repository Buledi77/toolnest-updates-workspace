#!/usr/bin/env python3
"""
Add verified evidence claims for batch 4: LearnWorlds, Salesforce Essentials.

Sources: Official pricing pages, official feature pages, official docs.
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
        "source_id": "learnworlds-pricing",
        "url": "https://www.learnworlds.com/pricing",
        "source_type": "official_pricing",
        "publisher": "LearnWorlds",
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
        "source_id": "learnworlds-features",
        "url": "https://www.learnworlds.com/product/features/flexible-courses",
        "source_type": "official_product",
        "publisher": "LearnWorlds",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "salesforce-pricing",
        "url": "https://www.salesforce.com/small-business/pricing",
        "source_type": "official_pricing",
        "publisher": "Salesforce",
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
        "source_id": "salesforce-affordable",
        "url": "https://www.salesforce.com/pricing/is-salesforce-affordable",
        "source_type": "official_product",
        "publisher": "Salesforce",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    # === LearnWorlds ===
    {
        "claim_id": "learnworlds-pricing-model",
        "tool_id": "learnworlds",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Tiered subscription. Starter $49/mo ($44 annual + $5 per enrollment), Pro Trainer $99/mo ($79 annual, no enrollment fees), Learning Center $299/mo ($194 annual), Corporate custom. White-label mobile app add-on $149/mo.",
        "source_ids": ["learnworlds-pricing", "learnworlds-features"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Starter $49/mo ($44 annual) + $5/enrollment, Pro Trainer $99/mo ($79 annual), Learning Center $299/mo ($194 annual). Blog confirms same pricing.",
        "evidence_note": "Starter plan has per-enrollment fee that can make it more expensive than Pro Trainer at scale.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "learnworlds-free-trial",
        "tool_id": "learnworlds",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "30-day free trial available on all plans.",
        "source_ids": ["learnworlds-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Start for free' on all plans. Blog confirms 30-day free trial.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "learnworlds-free-plan",
        "tool_id": "learnworlds",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a 30-day free trial.",
        "source_ids": ["learnworlds-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows only paid plans with 30-day trial. Blog confirms 'no permanent free plan, only a 30-day trial'.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "learnworlds-capabilities",
        "tool_id": "learnworlds",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Course creation and hosting with AI course builder",
            "Interactive video with quizzes and assessments",
            "SCORM support (up to 20 uploads on Pro Trainer, full on Learning Center)",
            "Course certificates",
            "Live 1:1 and group sessions",
            "Subscriptions, memberships, and payment plans",
            "Unlimited courses and learning paths",
            "50+ built-in integrations",
            "White-label mobile app (add-on)",
            "AI assistant (capped by plan)",
            "Custom domain hosting",
            "Stripe and PayPal payment processing"
        ],
        "source_ids": ["learnworlds-pricing", "learnworlds-features"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Starter: 1,000 learners, 1 admin, AI builder. Pro Trainer: 2,000 learners, 5 admins, no enrollment fees, unlimited courses, certificates, SCORM. Learning Center: white-label, SSO, API.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "learnworlds-platforms",
        "tool_id": "learnworlds",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "White-label mobile app (add-on)"],
        "source_ids": ["learnworlds-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: web-based platform with optional white-label mobile app add-on for $149/mo.",
        "evidence_note": "Mobile app is an expensive add-on, not included by default.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "learnworlds-core-use-case",
        "tool_id": "learnworlds",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Online course creation and eLearning platform for educators, trainers, and businesses to build, host, and sell interactive courses with branded learning experiences.",
        "source_ids": ["learnworlds-pricing", "learnworlds-features"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page targets 'solo trainers and small course businesses'. Product focuses on interactive course creation with AI builder, video, and assessments.",
        "evidence_note": "All-in-one course platform, not just hosting.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "learnworlds-target-user",
        "tool_id": "learnworlds",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Solo course creators, educators, corporate trainers, and businesses selling online courses. Starter for first-time creators, Pro Trainer for growing course businesses, Learning Center for branded academies.",
        "source_ids": ["learnworlds-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Starter for 'launching your first paid course', Pro Trainer for 'solo trainers and small course businesses', Learning Center for 'branded academies'.",
        "evidence_note": "Targets course creators across scales.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "learnworlds-limitations",
        "tool_id": "learnworlds",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Starter plan charges $5 per course enrollment (can exceed base cost at scale)",
            "Starter limited to 1,000 active learners/month and 1 admin",
            "White-label mobile app costs extra ($149/mo add-on)",
            "Interactive video and full SCORM require Learning Center plan",
            "AI assistant capped by plan tier",
            "No perpetual free plan"
        ],
        "source_ids": ["learnworlds-pricing", "learnworlds-features"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows enrollment fees, learner limits, and feature gating. Blog notes mobile app costs extra.",
        "evidence_note": "Starter plan can become expensive with high enrollment volume.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },

    # === Salesforce Essentials (Starter Suite) ===
    {
        "claim_id": "salesforce-pricing-model",
        "tool_id": "salesforce",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-user subscription. Free CRM for up to 2 users. Starter Suite $25/user/mo (monthly or annual). Pro Suite $100/user/mo annual. Enterprise and Unlimited custom. Transaction fees apply on commerce features.",
        "source_ids": ["salesforce-pricing", "salesforce-affordable"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Starter Suite $25/user/mo, Pro Suite $100/user/mo. Affordable page confirms free CRM for up to 2 users and Starter at $25/user/mo.",
        "evidence_note": "Free tier limited to 2 users; Starter includes AI and email marketing.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "salesforce-free-plan",
        "tool_id": "salesforce",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free CRM available for up to 2 users with core features including sales pipeline, service case management, email marketing, and AI (Agentforce).",
        "source_ids": ["salesforce-affordable"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Affordable page: 'Free CRM covers up to 2 users at no cost' with 'sales, service, email marketing, and AI in one place'.",
        "evidence_note": "Genuine free tier, but limited to 2 users.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "salesforce-trial",
        "tool_id": "salesforce",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "30-day free trial available for paid plans. Free CRM also available for up to 2 users.",
        "source_ids": ["salesforce-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Try for free' and '30-day free trial'.",
        "evidence_note": "Both trial and free tier available.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "salesforce-capabilities",
        "tool_id": "salesforce",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "CRM with account, contact, lead, and opportunity management",
            "Sales pipeline and forecast management",
            "Service case management",
            "Email marketing (2,000 emails/mo on Starter)",
            "AI assistant (Agentforce Coworker)",
            "Customizable reports and dashboards",
            "Process automation with Flows",
            "Email integration (Gmail, Outlook)",
            "Connected Slack channels",
            "AppExchange access",
            "Quote creation and management",
            "Knowledge management (Pro Suite+)"
        ],
        "source_ids": ["salesforce-pricing", "salesforce-affordable"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Starter: CRM, sales, service, email marketing, AI, Slack. Pro Suite: custom apps, process automation, knowledge management, macros.",
        "evidence_note": "Comprehensive CRM with AI included at entry tier.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "salesforce-platforms",
        "tool_id": "salesforce",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS app", "Android app"],
        "source_ids": ["salesforce-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Salesforce is a cloud-based CRM with mobile apps for iOS and Android.",
        "evidence_note": "Full-featured mobile CRM apps.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "salesforce-core-use-case",
        "tool_id": "salesforce",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "All-in-one CRM platform for small to enterprise businesses to manage sales, service, marketing, and customer relationships with AI-powered automation.",
        "source_ids": ["salesforce-pricing", "salesforce-affordable"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes CRM for small business. Affordable page positions it as 'all-in-one platform' combining sales, service, and marketing.",
        "evidence_note": "Broad CRM platform, not niche-focused.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "salesforce-target-user",
        "tool_id": "salesforce",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Small to enterprise businesses needing CRM. Free tier for very small teams (2 users), Starter Suite for small businesses, Pro Suite for growing businesses, Enterprise/Unlimited for large organizations.",
        "source_ids": ["salesforce-pricing", "salesforce-affordable"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page targets small business. Affordable page confirms free CRM for 2 users and Starter for small businesses.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "salesforce-limitations",
        "tool_id": "salesforce",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free CRM limited to 2 users",
            "Starter Suite limited to 2,000 email sends/month",
            "Commerce features subject to transaction fees (2.9% + $0.30/transaction)",
            "Advanced features (knowledge management, macros, custom apps) require Pro Suite ($100/user/mo)",
            "Enterprise and Unlimited pricing not publicly disclosed",
            "Add-ons for advanced analytics and marketing automation increase cost"
        ],
        "source_ids": ["salesforce-pricing", "salesforce-affordable"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows feature gating and transaction fees. Affordable page notes add-on costs.",
        "evidence_note": "Total cost can increase significantly with add-ons and higher tiers.",
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
