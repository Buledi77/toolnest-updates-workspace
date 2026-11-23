#!/usr/bin/env python3
"""
Add verified evidence claims for batch 27: Zendesk.

Sources: Official pricing page cross-referenced with third-party analysis.
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
        "source_id": "zendesk-pricing",
        "url": "https://www.zendesk.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Zendesk",
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
        "source_id": "zendesk-intercom-pricing",
        "url": "https://www.intercom.com/learning-center/zendesk-pricing",
        "source_type": "third_party_analysis",
        "publisher": "Intercom",
        "official": False,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "zendesk-helpdesk-pricing",
        "url": "https://www.helpdesk.com/blog/zendesk-pricing",
        "source_type": "third_party_analysis",
        "publisher": "HelpDesk",
        "official": False,
        "accessed_at": today,
        "verified_at": today,
        "status": "active",
        "source_history": []
    },
]

new_claims = [
    {
        "claim_id": "zendesk-pricing-model",
        "tool_id": "zendesk",
        "field_path": "factual_profile.pricing_model",
        "claim_type": "pricing",
        "value": "Per-agent subscription. Support Team $19/agent/mo annual ($25 monthly, email ticketing only). Suite Team $55/agent/mo annual ($69 monthly, multichannel). Suite Professional $115/agent/mo annual ($149 monthly). Suite Enterprise + Copilot quote-only. AI agent resolutions billed separately at $1.50-$2.00 per resolution beyond included allowance. Add-ons: Copilot $50/agent/mo, QA $35, WFM $25.",
        "source_ids": ["zendesk-pricing", "zendesk-intercom-pricing", "zendesk-helpdesk-pricing"],
        "region": "global",
        "currency": "USD",
        "billing_term": "monthly",
        "supporting_excerpt": "Multiple sources confirm: Support Team $19/agent/mo annual, Suite Team $55, Suite Professional $115, Suite Enterprise quote-only. AI agent resolutions $1.50-$2.00 per resolution.",
        "evidence_note": "Per-agent pricing; AI usage billed separately. Enterprise pricing not public.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zendesk-free-plan",
        "tool_id": "zendesk",
        "field_path": "factual_profile.free_plan_status",
        "claim_type": "free_plan",
        "value": "No free plan. Only a 14-day free trial available.",
        "source_ids": ["zendesk-helpdesk-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources confirm no free plan exists. Only 14-day free trial.",
        "evidence_note": "Confirmed no free plan exists.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zendesk-trial",
        "tool_id": "zendesk",
        "field_path": "factual_profile.trial_status",
        "claim_type": "trial",
        "value": "14-day free trial available on Suite Professional level features.",
        "source_ids": ["zendesk-helpdesk-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources confirm 14-day free trial built on Suite Professional level capabilities.",
        "evidence_note": "Trial provides Professional-level access.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zendesk-capabilities",
        "tool_id": "zendesk",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": [
            "Ticketing and shared inbox",
            "Multichannel support (email, chat, messaging, voice, social)",
            "Knowledge base and help center",
            "AI agents with automated resolutions",
            "Skills-based routing (Professional+)",
            "Advanced analytics and reporting",
            "SLA policies (Growth+)",
            "CSAT surveys (Growth+)",
            "Multiple ticket forms (Growth+)",
            "Light agents (Growth+)",
            "IVR and App Builder (Professional+)",
            "Side conversations (Professional+)",
            "Custom roles (Enterprise)",
            "Sandbox environment (Enterprise)",
            "Approval workflows (Enterprise)",
            "HIPAA enablement add-on (Professional+)",
            "Data residency add-on (Professional+)",
            "Copilot AI assistant add-on ($50/agent/mo)",
            "QA add-on ($35/agent/mo)",
            "WFM add-on ($25/agent/mo)",
            "1,800+ marketplace integrations",
            "Mobile apps for iOS and Android"
        ],
        "source_ids": ["zendesk-pricing", "zendesk-intercom-pricing", "zendesk-helpdesk-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources list features per tier. Support Team: email ticketing. Suite Team: multichannel. Suite Professional: skills-based routing, analytics. Enterprise: custom roles, sandbox, approval workflows.",
        "evidence_note": "Feature gating across tiers is clearly documented.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zendesk-platforms",
        "tool_id": "zendesk",
        "field_path": "factual_profile.platforms",
        "claim_type": "platform",
        "value": ["Web-based SaaS", "iOS app", "Android app"],
        "source_ids": ["zendesk-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Zendesk is a cloud-based customer support platform with mobile apps for iOS and Android.",
        "evidence_note": "Full-featured mobile apps for iOS and Android.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zendesk-core-use-case",
        "tool_id": "zendesk",
        "field_path": "factual_profile.core_use_case",
        "claim_type": "use_case",
        "value": "Customer support platform for mid-market and enterprise teams to manage customer inquiries through ticketing, multichannel support, knowledge base, and AI-powered automation.",
        "source_ids": ["zendesk-intercom-pricing", "zendesk-helpdesk-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources describe Zendesk for mid-market and enterprise teams with deep reporting, omnichannel routing, and 1,800+ integrations.",
        "evidence_note": "Mid-market and enterprise focused; overkill for small teams.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zendesk-target-user",
        "tool_id": "zendesk",
        "field_path": "factual_profile.target_user",
        "claim_type": "target_user",
        "value": "Mid-market and enterprise customer support teams. Support Team for email-only teams, Suite Team for multichannel teams, Suite Professional for scaling teams, Suite Enterprise for large organizations with compliance needs.",
        "source_ids": ["zendesk-intercom-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources: Zendesk is strong for mid-market and enterprise teams. Consistently described as overkill for teams under 10 agents.",
        "evidence_note": "Mid-market and enterprise focused; not ideal for very small teams.",
        "accessed_at": today,
        "verified_at": today,
        "stale_after": stale,
        "status": "verified",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "zendesk-limitations",
        "tool_id": "zendesk",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": [
            "No free plan available",
            "Support Team limited to email ticketing only (no messaging, voice, or help center)",
            "AI agent resolutions billed separately at $1.50-$2.00 per resolution beyond included allowance",
            "Copilot add-on costs $50/agent/mo extra",
            "QA and WFM add-ons add $60/agent/mo combined",
            "Suite Enterprise pricing not publicly disclosed",
            "Overkill for teams under 10 agents"
        ],
        "source_ids": ["zendesk-intercom-pricing", "zendesk-helpdesk-pricing"],
        "region": None,
        "currency": None,
        "billing_term": None,
        "supporting_excerpt": "Sources show feature gating, add-on costs, and AI resolution billing. 10-agent team on Suite Professional with Copilot, QA, and WFM pays ~$3,300/month.",
        "evidence_note": "Total cost increases significantly with add-ons and AI usage.",
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
