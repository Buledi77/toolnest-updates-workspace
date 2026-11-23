#!/usr/bin/env python3
"""
Add verified evidence claims for batch 14: SurveyMonkey.

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
        "source_id": "surveymonkey-pricing",
        "url": "https://www.surveymonkey.com/pricing",
        "source_type": "official_pricing",
        "publisher": "SurveyMonkey",
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
        "source_id": "surveymonkey-pricing-details",
        "url": "https://www.surveymonkey.com/pricing/details",
        "source_type": "official_pricing",
        "publisher": "SurveyMonkey",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "region": "global",
        "currency": "EUR",
        "billing_term": "monthly",
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "surveymonkey-help-plans",
        "url": "https://help.surveymonkey.com/en/surveymonkey/billing/surveymonkey-plans",
        "source_type": "official_docs",
        "publisher": "SurveyMonkey",
        "official": True,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "surveymonkey-pricing-model",
        "tool_id": "surveymonkey",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Response-based tiered subscription. Basic (Free) with limited responses. Standard monthly billing available. Advantage €30/user/mo annual (10K responses/year). Premier €75/user/mo annual (100K responses/year). Team plans start at 3 users. Enterprise custom. Overage €0.10/response.",
        "source_ids": ["surveymonkey-pricing", "surveymonkey-pricing-details", "surveymonkey-help-plans"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Pricing page: Team Advantage €30/user/mo, Team Premier €75/user/mo. Help docs confirm Basic (free), Standard, Advantage, Premier, and Enterprise plans. Overage €0.10/response.",
        "evidence_note": "Response-based pricing; overage charges apply. Pricing varies by region.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "surveymonkey-free-plan",
        "tool_id": "surveymonkey",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "Free plan available: create and send surveys, limited responses per survey, 10 questions per survey. No survey logic, no export, no custom reports.",
        "source_ids": ["surveymonkey-help-plans", "surveymonkey-pricing-details"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Help docs: 'Basic (free) plan, you can create and send surveys. You can view a set number of responses per survey.' Pricing details: 'Free users can add up to 10 questions per survey.'",
        "evidence_note": "Genuine free tier but very limited.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "surveymonkey-trial",
        "tool_id": "surveymonkey",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "No separate trial — free plan serves as entry point. Paid plans available with monthly billing.",
        "source_ids": ["surveymonkey-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Help docs describe free plan and paid plans but no separate trial period.",
        "evidence_note": "Free plan replaces traditional trial model.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "surveymonkey-capabilities",
        "tool_id": "surveymonkey",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Survey creation and distribution",
            "Forms and quizzes",
            "500+ expert templates",
            "Survey logic and branching (paid plans)",
            "Question randomization and A/B testing (Advantage+)",
            "Response quotas (Advantage+)",
            "Custom reports and dashboards",
            "Data export (paid plans)",
            "200+ native integrations",
            "7,000+ Zapier integrations",
            "Embed surveys in apps",
            "Custom themes and branding",
            "Team collaboration (Team plans)",
            "Enterprise admin tools and SSO"
        ],
        "source_ids": ["surveymonkey-pricing", "surveymonkey-pricing-details", "surveymonkey-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing pages list features per tier. Help docs confirm plan differences and feature gating.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "surveymonkey-platforms",
        "tool_id": "surveymonkey",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS"],
        "source_ids": ["surveymonkey-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "SurveyMonkey is a cloud-based survey platform accessed via web browser.",
        "evidence_note": "Web-based SaaS; no standalone desktop app mentioned.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "surveymonkey-core-use-case",
        "tool_id": "surveymonkey",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Online survey platform for businesses and individuals to create, distribute, and analyze surveys, forms, and quizzes for market research, customer feedback, and internal polling.",
        "source_ids": ["surveymonkey-pricing", "surveymonkey-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing page describes survey creation and analysis. Help docs confirm survey, form, and quiz capabilities.",
        "evidence_note": "Survey-focused platform, not a general form builder.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "surveymonkey-target-user",
        "tool_id": "surveymonkey",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Individuals, small teams, and enterprises needing online surveys. Free for individuals, Standard for simple needs, Advantage for teams needing advanced logic, Premier for deep analysis, Enterprise for large organizations.",
        "source_ids": ["surveymonkey-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Help docs: individual plans for single users, team plans for collaboration, enterprise for admin tools and security.",
        "evidence_note": "Broad target across organization sizes.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "surveymonkey-limitations",
        "tool_id": "surveymonkey",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "Free plan limited to 10 questions per survey and limited responses",
            "No survey logic, export, or custom reports on free plan",
            "Response limits on paid plans with €0.10 overage per response",
            "Advanced logic (A/B testing, randomization) requires Advantage plan",
            "Team plans require minimum 3 users",
            "Enterprise pricing not publicly disclosed"
        ],
        "source_ids": ["surveymonkey-pricing-details", "surveymonkey-help-plans"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Pricing details show response limits and overage charges. Help docs confirm feature gating.",
        "evidence_note": "Response-based pricing can become expensive at scale.",
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
