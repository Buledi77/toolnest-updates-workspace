#!/usr/bin/env python3
"""
Add verified evidence claims for batch 2: CleverTap, Dripify.

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
        "source_id": "clevertap-pricing",
        "url": "https://clevertap.com/pricing",
        "source_type": "official_pricing",
        "publisher": "CleverTap",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "region": "global",
        "currency": "INR",
        "billing_term": "monthly",
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "clevertap-vs-braze",
        "url": "https://clevertap.com/blog/clevertap-vs-braze-customer-engagement-platform",
        "source_type": "official_product",
        "publisher": "CleverTap",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "dripify-pricing",
        "url": "https://dripify.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Dripify",
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
    # === CleverTap ===
    {
        "claim_id": "clevertap-pricing-model",
        "tool_id": "clevertap",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Tiered subscription by MAU (Monthly Active Users). Core plan starts at ₹2,000/month (~$85/mo). Pro and Ultimate are custom-priced. Add-ons available for advanced analytics, premium channels, email, WhatsApp, and promos.",
        "source_ids": ["clevertap-pricing", "clevertap-vs-braze"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page shows Core at ₹2,000/month. Blog states 'published pricing starts at $85/month'. Pro and Ultimate require demo/contact for pricing.",
        "evidence_note": "Core plan has published pricing; higher tiers are quote-based. Add-ons increase cost.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "clevertap-free-trial",
        "tool_id": "clevertap",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "30-day free trial available for apps with MAUs less than 100K.",
        "source_ids": ["clevertap-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: '30-day free trial' on Core plan. Blog confirms '30-day free trial is also offered for apps with MAUs less than 100K'.",
        "evidence_note": "Trial limited to smaller apps.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "clevertap-free-plan",
        "tool_id": "clevertap",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No perpetual free plan. Startup program available with credits. 30-day trial for qualifying apps.",
        "source_ids": ["clevertap-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows only paid plans (Core, Pro, Ultimate). Startup page mentions credits program but no free tier.",
        "evidence_note": "No free forever plan confirmed.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "clevertap-capabilities",
        "tool_id": "clevertap",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Behavioral analytics and real-time segmentation",
            "Omnichannel engagement (push, email, SMS, WhatsApp, RCS, in-app)",
            "Automated user journeys",
            "A/B testing and experimentation",
            "AI-powered personalization (CleverAI)",
            "Predictive analytics and recommendations (Ultimate)",
            "Content creation and image generation",
            "Send time and channel optimization",
            "Loyalty and rewards platform (add-on)",
            "Decisioning agents for 1:1 personalization (Ultimate)"
        ],
        "source_ids": ["clevertap-pricing", "clevertap-vs-braze"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists capabilities across Core, Pro, Ultimate tiers. Core includes behavioral analytics, segmentation, omnichannel engagement, experimentation. Pro adds AI optimization. Ultimate adds agentic orchestration and decisioning.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "clevertap-platforms",
        "tool_id": "clevertap",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS SDK", "Android SDK"],
        "source_ids": ["clevertap-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "CleverTap is a cloud-based platform with SDKs for mobile apps (iOS, Android) and web integration.",
        "evidence_note": "Primarily mobile-first engagement platform.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "clevertap-core-use-case",
        "tool_id": "clevertap",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Customer engagement and retention platform for app and web businesses to drive user activation, retention, and monetization through personalized omnichannel campaigns.",
        "source_ids": ["clevertap-pricing", "clevertap-vs-braze"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes 'Customer Engagement & Retention Platform'. Blog positions it against Braze for customer engagement.",
        "evidence_note": "Focused on mobile app and web customer engagement, not B2B outreach.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "clevertap-target-user",
        "tool_id": "clevertap",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Product and marketing teams at growing to enterprise companies with mobile apps or web products. Core for growing teams, Pro for expanding businesses, Ultimate for enterprise.",
        "source_ids": ["clevertap-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Core for 'growing teams', Pro for 'expanding businesses', Ultimate for 'enterprise teams'.",
        "evidence_note": "Targets companies with significant user bases.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "clevertap-limitations",
        "tool_id": "clevertap",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Core plan limited to basic AI features; advanced AI requires Pro/Ultimate",
            "Pro and Ultimate pricing not publicly disclosed",
            "Add-ons (email, WhatsApp, premium channels, promos) increase cost significantly",
            "30-day trial limited to apps with under 100K MAU",
            "No perpetual free plan"
        ],
        "source_ids": ["clevertap-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows feature gating and add-on costs. Trial limited by MAU. No free tier.",
        "evidence_note": "Total cost of ownership can be higher than base pricing suggests.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },

    # === Dripify ===
    {
        "claim_id": "dripify-pricing-model",
        "tool_id": "dripify",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-user subscription. Basic $59/mo annual ($79 monthly), Pro $79/mo annual ($99 monthly), Advanced $99/mo annual. Enterprise custom. All paid plans include 100 email finder credits/month.",
        "source_ids": ["dripify-pricing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Basic $59/mo billed annually, Pro $79/mo annually, Advanced $99/mo annually. Monthly billing costs $20/mo more per user.",
        "evidence_note": "Per-account pricing — each LinkedIn account needs its own subscription.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "dripify-free-trial",
        "tool_id": "dripify",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "7-day free trial available with no credit card required.",
        "source_ids": ["dripify-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: '7-Day Free Trial, No Credit Card Required' on all plans.",
        "evidence_note": "Short trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "dripify-free-plan",
        "tool_id": "dripify",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a 7-day free trial.",
        "source_ids": ["dripify-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows only paid plans (Basic, Pro, Advanced, Enterprise) with 7-day trial. No perpetual free tier.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "dripify-capabilities",
        "tool_id": "dripify",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "LinkedIn outreach automation (connection requests, messages, follow-ups)",
            "Email campaign sequences",
            "Multi-step drip campaigns",
            "Built-in LinkedIn protection and safety limits",
            "Analytics and reporting",
            "Dedicated inbox for LinkedIn conversations",
            "HubSpot integration",
            "Lead tagging and organization (Advanced+)",
            "A/B testing (Advanced+)",
            "Team management (Advanced+)",
            "Email finder (100 credits/month per user)"
        ],
        "source_ids": ["dripify-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per plan. Basic: 1 campaign, limited quotas. Pro: unlimited campaigns, dedicated inbox, HubSpot. Advanced: team management, A/B testing, lead tagging.",
        "evidence_note": "LinkedIn-focused with email as secondary channel.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "dripify-platforms",
        "tool_id": "dripify",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "LinkedIn (browser extension)"],
        "source_ids": ["dripify-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Dripify operates as a web-based platform with LinkedIn browser integration for automation.",
        "evidence_note": "Requires LinkedIn account; works with Free, Premium, Sales Navigator, and Recruiter Lite.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "dripify-core-use-case",
        "tool_id": "dripify",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "LinkedIn-based B2B outbound prospecting and lead generation through automated connection requests, messaging sequences, and email follow-ups.",
        "source_ids": ["dripify-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page targets 'sellers launching LinkedIn and email campaigns'. Product focuses on LinkedIn automation with email as secondary.",
        "evidence_note": "Primarily LinkedIn-focused; email is secondary channel.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "dripify-target-user",
        "tool_id": "dripify",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "B2B sales development representatives, account executives, and recruiting teams who rely on LinkedIn for outbound prospecting.",
        "source_ids": ["dripify-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: Pro 'for sellers', Advanced 'for sales professionals', Enterprise 'for large teams'.",
        "evidence_note": "B2B-focused, not suitable for B2C or non-LinkedIn strategies.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "dripify-limitations",
        "tool_id": "dripify",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "LinkedIn-only primary focus; email is secondary channel",
            "Per-account pricing — each LinkedIn account needs its own subscription",
            "Basic plan severely limited (1 campaign, 30 messages/day)",
            "A/B testing requires Advanced plan",
            "Only 100 email finder credits/month on self-serve plans",
            "Month-to-month billing costs $20/mo more per user",
            "Risk of LinkedIn account restrictions if safety limits exceeded"
        ],
        "source_ids": ["dripify-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows plan limitations. Third-party reviews note per-account pricing and limited email capabilities.",
        "evidence_note": "LinkedIn automation carries inherent account safety risks.",
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
