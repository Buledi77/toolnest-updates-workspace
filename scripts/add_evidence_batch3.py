#!/usr/bin/env python3
"""
Add verified evidence claims for batch 3: Sprout Social, Lusha.

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
        "source_id": "sproutsocial-pricing",
        "url": "https://sproutsocial.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Sprout Social",
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
        "source_id": "sproutsocial-plans-guide",
        "url": "https://sproutsocial.com/insights/which-sprout-social-plan-is-right-for-you",
        "source_type": "official_product",
        "publisher": "Sprout Social",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "lusha-pricing",
        "url": "https://www.lusha.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Lusha",
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
        "source_id": "lusha-faq",
        "url": "https://www.lusha.com/faq",
        "source_type": "official_docs",
        "publisher": "Lusha",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "lusha-docs-billing",
        "url": "https://docs.lusha.com/user-guide/billing-and-plans",
        "source_type": "official_docs",
        "publisher": "Lusha",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    # === Sprout Social ===
    {
        "claim_id": "sproutsocial-pricing-model",
        "tool_id": "sproutsocial",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-seat subscription. Essentials $79/seat/mo annual ($99 monthly), Standard $199, Professional $299, Advanced $399. Enterprise custom. Add-ons available for Listening, Premium Analytics, Advocacy.",
        "source_ids": ["sproutsocial-pricing", "sproutsocial-plans-guide"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Essentials $79/seat/mo, Standard $199, Professional $299, Advanced $399. Plans guide confirms same pricing billed annually.",
        "evidence_note": "Per-seat pricing; extra profiles and add-ons increase cost.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "sproutsocial-free-trial",
        "tool_id": "sproutsocial",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "30-day free trial available on all plans, no credit card required.",
        "source_ids": ["sproutsocial-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Try Sprout free for 30 days. No credit card required.'",
        "evidence_note": "Generous trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "sproutsocial-free-plan",
        "tool_id": "sproutsocial",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a 30-day free trial.",
        "source_ids": ["sproutsocial-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows only paid plans with 30-day trial. No perpetual free tier.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "sproutsocial-capabilities",
        "tool_id": "sproutsocial",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Social media publishing and scheduling",
            "Smart Inbox for consolidated messaging",
            "Keyword and location monitoring",
            "Review management",
            "Competitor and paid insights (Professional+)",
            "AI-powered content assistance (AI Assist)",
            "Sentiment analysis (Advanced+)",
            "SproutLink (link management)",
            "Influencer marketing tools",
            "Helpdesk integrations (Salesforce, Zendesk, Advanced+)",
            "Custom reporting and analytics",
            "Mobile app for iOS and Android"
        ],
        "source_ids": ["sproutsocial-pricing", "sproutsocial-plans-guide"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page and plans guide list features per tier. Essentials: publishing, 5 profiles, reporting. Standard: Smart Inbox, monitoring, reviews. Professional: unlimited profiles, competitor insights, AI Assist. Advanced: sentiment, API, helpdesk integrations.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "sproutsocial-platforms",
        "tool_id": "sproutsocial",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS app", "Android app"],
        "source_ids": ["sproutsocial-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page confirms mobile app for iOS and Android included on all plans.",
        "evidence_note": "Full-featured mobile apps, not just notifications.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "sproutsocial-core-use-case",
        "tool_id": "sproutsocial",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Social media management platform for publishing, engagement, listening, and analytics across multiple social networks.",
        "source_ids": ["sproutsocial-pricing", "sproutsocial-plans-guide"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes social media management. Plans guide covers publishing, conversations, monitoring, and reporting.",
        "evidence_note": "Broad social media management, not niche-focused.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "sproutsocial-target-user",
        "tool_id": "sproutsocial",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Social media managers, marketing teams, and customer care teams at small to enterprise organizations. Essentials for solo practitioners, Standard for small teams, Professional for growing teams, Advanced for cross-functional teams.",
        "source_ids": ["sproutsocial-plans-guide"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Plans guide: Essentials for 'solo practitioners, freelancers and small businesses', Standard for 'small teams', Professional for 'growing teams', Advanced for 'cross-functional teams'.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "sproutsocial-limitations",
        "tool_id": "sproutsocial",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Essentials limited to 5 social profiles",
            "Standard limited to 5 social profiles",
            "Competitor insights require Professional plan ($299/seat/mo)",
            "Sentiment analysis and helpdesk integrations require Advanced ($399/seat/mo)",
            "Per-seat pricing adds up quickly for larger teams",
            "Add-ons (Listening, Premium Analytics, Advocacy) increase cost",
            "No perpetual free plan"
        ],
        "source_ids": ["sproutsocial-pricing", "sproutsocial-plans-guide"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows profile limits and feature gating. Support docs confirm add-on costs.",
        "evidence_note": "Total cost scales with seats, profiles, and add-ons.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },

    # === Lusha ===
    {
        "claim_id": "lusha-pricing-model",
        "tool_id": "lusha",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Credit-based subscription. Free plan: 40 credits/month permanent. Starter $37/mo annual ($49.90 monthly), Pro $69.90/mo, Premium $399.90/mo, Scale custom. Credits: 1 per email, 5 per phone number.",
        "source_ids": ["lusha-pricing", "lusha-faq", "lusha-docs-billing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: credit-based system, 1 credit/email, 5 credits/phone. Free plan 40 credits/month. Starter from $37/mo annual. FAQ confirms 5 plans: Free, Starter, Pro, Premium, Scale.",
        "evidence_note": "Credit-based model means actual cost depends on usage patterns.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "lusha-free-plan",
        "tool_id": "lusha",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: 40 credits/month permanent, no credit card required, basic prospecting features, browser extension, CRM integrations.",
        "source_ids": ["lusha-pricing", "lusha-faq"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'Free plan provides up to 40 credits per month' with 'basic prospecting features, browser extension, and CRM integrations'. FAQ confirms 'Free is permanent, with 40 credits a month and no credit card'.",
        "evidence_note": "Genuine perpetual free tier with limited credits.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "lusha-trial",
        "tool_id": "lusha",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "No separate trial — free plan serves as entry point with 40 credits/month permanently.",
        "source_ids": ["lusha-faq"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "FAQ: 'Free to test the data on your own list.' Free plan is permanent, not time-limited.",
        "evidence_note": "Free plan replaces traditional trial model.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "lusha-capabilities",
        "tool_id": "lusha",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Contact data enrichment (email and phone)",
            "B2B contact database (515M+ contacts, 29M+ company profiles)",
            "Browser extension for LinkedIn and web prospecting",
            "CRM integrations (Salesforce, HubSpot, etc.)",
            "Bulk enrichment",
            "Data Waterfall (Pro+)",
            "Buyer intent data signals",
            "AI agent access via MCP",
            "Do Not Call status on phone records",
            "98% email accuracy, 86% phone accuracy (published)"
        ],
        "source_ids": ["lusha-pricing", "lusha-faq", "lusha-docs-billing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes credit system and contact data. FAQ mentions 515M+ contacts, accuracy figures, MCP access, and compliance. Docs confirm credit costs and plan features.",
        "evidence_note": "Data layer separate from sending tools; connects to existing outreach platforms.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "lusha-platforms",
        "tool_id": "lusha",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "Chrome browser extension", "CRM integrations"],
        "source_ids": ["lusha-pricing", "lusha-faq"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page mentions browser extension and CRM integrations. FAQ confirms browser extension on all plans.",
        "evidence_note": "Chrome extension is primary interface; no standalone desktop app.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "lusha-core-use-case",
        "tool_id": "lusha",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "B2B contact data enrichment and lead prospecting, providing verified email addresses and phone numbers for sales and marketing outreach.",
        "source_ids": ["lusha-pricing", "lusha-faq"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: 'credit system is your way to access contact data'. FAQ: 'reveal contacts every week'. Product focuses on contact data, not outreach execution.",
        "evidence_note": "Data enrichment layer, not a full outreach platform.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "lusha-target-user",
        "tool_id": "lusha",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "B2B sales development representatives, recruiters, and marketing teams who need verified contact data for outreach. Free for testing, Starter for individual reps, Pro/Premium for teams, Scale for enterprises.",
        "source_ids": ["lusha-faq"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "FAQ: 'Free to test', 'Starter for one rep', 'Pro or Premium for a team', 'Scale for larger deployments'.",
        "evidence_note": "B2B-focused; strongest in US market.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "lusha-limitations",
        "tool_id": "lusha",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Credit-based pricing means costs vary significantly by usage",
            "Phone numbers cost 5x more than emails (5 credits vs 1)",
            "Free plan limited to 40 credits/month with no rollover",
            "Starter plan credits do not roll over",
            "Smaller database than ZoomInfo for deep US enterprise coverage",
            "EMEA phone coverage still growing compared to Cognism",
            "Not a full outreach platform — data layer only"
        ],
        "source_ids": ["lusha-pricing", "lusha-faq", "lusha-docs-billing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows credit costs. FAQ notes database size comparison. Docs confirm credit rollover rules.",
        "evidence_note": "Credit consumption can be fast, especially for phone-heavy outreach.",
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
