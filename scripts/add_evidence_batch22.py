#!/usr/bin/env python3
"""
Add verified evidence claims for batch 22: ConvertKit (now Kit).

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
        "source_id": "convertkit-pricing",
        "url": "https://convertkit.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Kit (formerly ConvertKit)",
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
        "source_id": "convertkit-features",
        "url": "https://convertkit.com/features",
        "source_type": "official_product",
        "publisher": "Kit (formerly ConvertKit)",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "convertkit-pro",
        "url": "https://convertkit.com/features/creator-pro",
        "source_type": "official_product",
        "publisher": "Kit (formerly ConvertKit)",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "convertkit-pricing-model",
        "tool_id": "convertkit",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Subscriber-based subscription. Free plan: up to 1,000 subscribers. Creator $9/mo (10,000 subscribers). Pro $79/mo (10,000 subscribers). Pricing scales with subscriber count. No per-email charges. 14-day free trial on paid plans.",
        "source_ids": ["convertkit-pricing", "convertkit-features", "convertkit-pro"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Free up to 1,000 subscribers, Creator $9/mo, Pro $79/mo. Features page confirms subscriber-based pricing with no per-email charges.",
        "evidence_note": "Subscriber-based pricing; no per-email charges. Free plan has meaningful limits.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "convertkit-free-plan",
        "tool_id": "convertkit",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: up to 1,000 subscribers, landing pages, forms, newsletter site, email designer and templates, A/B subject line testing, tags and segments, analytics, Recommendations, digital products, paid newsletters, tips. No email sequences or Visual Automations.",
        "source_ids": ["convertkit-pricing", "convertkit-features"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Features page: Free plan includes landing pages, forms, newsletter site, email designer, A/B testing, tags, segments, analytics, Recommendations, digital products. No email sequences or Visual Automations.",
        "evidence_note": "Genuine free tier but no automation features.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "convertkit-trial",
        "tool_id": "convertkit",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available on paid plans with no credit card required.",
        "source_ids": ["convertkit-pricing", "convertkit-features"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page: '14-day free trial. No card required.' Features page confirms same.",
        "evidence_note": "Standard trial period.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "convertkit-capabilities",
        "tool_id": "convertkit",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Email marketing campaigns and newsletters",
            "Visual automation builder (Creator+)",
            "Automated email sequences (Creator+)",
            "RSS campaigns (Creator+)",
            "Landing pages and forms",
            "Newsletter site",
            "Email designer with templates",
            "A/B subject line testing",
            "Tags and segments",
            "Analytics and reporting",
            "Digital products and paid newsletters",
            "Tips and donations",
            "Recommendations (cross-promotion network)",
            "Kit App Store integrations (Creator+)",
            "API access",
            "Subscriber Signals (Pro)",
            "Engagement analytics (Pro)",
            "Revenue attribution (Pro)",
            "Subscriber engagement scoring (Pro)",
            "Growth Concierge services (Pro)",
            "Team seats (2 on Creator, unlimited on Pro)"
        ],
        "source_ids": ["convertkit-pricing", "convertkit-features", "convertkit-pro"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page lists features per tier. Features page confirms all capabilities. Pro page details advanced features.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "convertkit-platforms",
        "tool_id": "convertkit",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["convertkit-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Kit (formerly ConvertKit) is a cloud-based email marketing platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "convertkit-core-use-case",
        "tool_id": "convertkit",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Email marketing platform for creators, authors, podcasters, and newsletter writers to build email lists, send newsletters, automate email sequences, and sell digital products.",
        "source_ids": ["convertkit-pricing", "convertkit-features"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page targets creator business owners. Features page confirms email marketing, automations, and sales tools for creators.",
        "evidence_note": "Creator-focused, not general enterprise email marketing.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "convertkit-target-user",
        "tool_id": "convertkit",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Content creators, authors, podcasters, coaches, and newsletter writers. Free for beginners, Creator for growing creators, Pro for scaling creators needing advanced analytics and team collaboration.",
        "source_ids": ["convertkit-pricing", "convertkit-features"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page targets 'creator business owners'. Features page lists authors, bloggers, newsletter creators, podcasters, YouTubers, and coaches.",
        "evidence_note": "Creator-focused; not designed for B2B or enterprise marketing.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "convertkit-limitations",
        "tool_id": "convertkit",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan limited to 1,000 subscribers",
            "No email sequences or Visual Automations on free plan",
            "No Kit App Store integrations on free plan",
            "Subscriber Signals and advanced analytics require Pro plan ($79/mo)",
            "Creator plan limited to 2 team seats",
            "Creator-focused; limited B2B and enterprise features"
        ],
        "source_ids": ["convertkit-pricing", "convertkit-features", "convertkit-pro"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page shows feature gating. Pro page confirms advanced features on Pro only.",
        "evidence_note": "Free plan lacks automation; Pro required for advanced analytics.",
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
