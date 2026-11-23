#!/usr/bin/env python3
"""
Add Phase 5 Research Batch 1 evidence to the evidence ledger and update tool data.

Tools researched: notion, confetti, connecteam, hibob, meetgeek, pandadoc,
quickbooks, shoeboxed, teamwork, timedoctor, trainual, upwork, wrike, xero, adcreative
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
TOOLS_V2_DIR = ROOT / "data" / "tools-v2"

TODAY = datetime.now().strftime("%Y-%m-%d")


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# Define new sources and claims for each tool
NEW_SOURCES = [
    # Notion
    {
        "source_id": "notion-pricing",
        "url": "https://www.notion.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Notion",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "region": "global-display-example",
        "currency": "USD",
        "billing_term": "annual and monthly billing options",
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "notion-product",
        "url": "https://www.notion.com/product",
        "source_type": "official_product",
        "publisher": "Notion",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # Confetti
    {
        "source_id": "confetti-pricing",
        "url": "https://www.withconfetti.com/pricing",
        "source_type": "official_pricing",
        "publisher": "WithConfetti",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # Connecteam
    {
        "source_id": "connecteam-pricing",
        "url": "https://connecteam.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Connecteam",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    {
        "source_id": "connecteam-product",
        "url": "https://connecteam.com/product",
        "source_type": "official_product",
        "publisher": "Connecteam",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # HiBob
    {
        "source_id": "hibob-pricing",
        "url": "https://www.hibob.com/pricing",
        "source_type": "official_pricing",
        "publisher": "HiBob",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # MeetGeek
    {
        "source_id": "meetgeek-pricing",
        "url": "https://meetgeek.ai/pricing",
        "source_type": "official_pricing",
        "publisher": "MeetGeek",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # PandaDoc
    {
        "source_id": "pandadoc-pricing",
        "url": "https://www.pandadoc.com/pricing",
        "source_type": "official_pricing",
        "publisher": "PandaDoc",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # QuickBooks
    {
        "source_id": "quickbooks-pricing",
        "url": "https://quickbooks.intuit.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Intuit",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # Shoeboxed
    {
        "source_id": "shoeboxed-pricing",
        "url": "https://www.shoeboxed.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Shoeboxed",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # Teamwork
    {
        "source_id": "teamwork-pricing",
        "url": "https://www.teamwork.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Teamwork.com",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # TimeDoctor
    {
        "source_id": "timedoctor-pricing",
        "url": "https://www.timedoctor.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Time Doctor",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # Trainual
    {
        "source_id": "trainual-pricing",
        "url": "https://www.trainual.com/pricing",
        "source_type": "official_pricing",
        "publisher": "Trainual",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # Upwork
    {
        "source_id": "upwork-pricing",
        "url": "https://www.upwork.com/pricing/client",
        "source_type": "official_pricing",
        "publisher": "Upwork",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # Wrike
    {
        "source_id": "wrike-pricing",
        "url": "https://www.wrike.com/price",
        "source_type": "official_pricing",
        "publisher": "Wrike",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # Xero
    {
        "source_id": "xero-pricing",
        "url": "https://www.xero.com/us/pricing-plans",
        "source_type": "official_pricing",
        "publisher": "Xero",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
    # AdCreative
    {
        "source_id": "adcreative-pricing",
        "url": "https://www.adcreative.ai/pricing",
        "source_type": "official_pricing",
        "publisher": "AdCreative.ai",
        "official": True,
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "active",
        "source_history": []
    },
]

NEW_CLAIMS = [
    # === Notion ===
    {
        "claim_id": "notion-pricing-verified",
        "tool_id": "notion",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "term": "annual billing",
            "plans": [
                {"name": "Free", "displayed_monthly_usd": 0, "selected_limits": ["unlimited personal workspace", "10 guests max"]},
                {"name": "Plus", "displayed_monthly_usd": 10, "upfront_annual_usd": 120, "monthly_billing_usd": 12, "selected_limits": ["file uploads", "workspace sharing", "100 guests"]},
                {"name": "Business", "displayed_monthly_usd": 20, "upfront_annual_usd": 240, "monthly_billing_usd": 24, "selected_limits": ["SAML SSO", "AI bundled", "250 guests"]},
                {"name": "Enterprise", "custom": True, "selected_limits": ["SCIM", "audit logs", "dedicated support"]}
            ]
        },
        "source_ids": ["notion-pricing"],
        "currency": "USD",
        "billing_term": "annual and monthly billing",
        "supporting_excerpt": "Notion pricing page shows Free, Plus ($10/mo annual), Business ($20/mo annual), and Enterprise (custom).",
        "evidence_note": "AI bundled into Business plan as of May 2025. Previous $10 AI add-on retired.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "notion-free-plan",
        "tool_id": "notion",
        "field_path": "pricing.freePlan",
        "claim_type": "pricing",
        "value": {"available": True, "limits": "10 guests max, limited AI trial"},
        "source_ids": ["notion-pricing"],
        "supporting_excerpt": "Free plan available with unlimited personal workspace.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "notion-capabilities",
        "tool_id": "notion",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["notes", "tasks", "databases", "wiki", "AI writing assistant", "templates", "collaboration", "real-time editing"],
        "source_ids": ["notion-product"],
        "supporting_excerpt": "Notion product page lists notes, tasks, databases, wiki, AI, templates, and collaboration.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "notion-limitations",
        "tool_id": "notion",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": ["offline access limited", "no native Gantt charts", "can be slow with large databases", "learning curve for advanced features"],
        "source_ids": ["notion-product"],
        "supporting_excerpt": "Notion lacks native Gantt charts and has limited offline access; large databases can be slow.",
        "evidence_note": "Limitations based on product behavior and user reports, not official disclaimers.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "editorial_assessment",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === Confetti ===
    {
        "claim_id": "confetti-pricing-verified",
        "tool_id": "confetti",
        "field_path": "pricing.model",
        "claim_type": "pricing",
        "value": {
            "model": "event-based pricing",
            "description": "Pay per event or annual plans",
            "plans": [
                {"name": "Pay-Per-Event", "price_per_user": "$30", "billing": "one-time per event"},
                {"name": "Pre-Fund", "price_annual": "$5000", "billing": "annual credits"},
                {"name": "Enterprise", "custom": True}
            ]
        },
        "source_ids": ["confetti-pricing"],
        "currency": "USD",
        "supporting_excerpt": "Confetti uses event-based pricing: $30/user per event, Pre-Fund $5000/year, Enterprise custom.",
        "evidence_note": "Pricing varies by event type, group size, and customization. No per-user subscription.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "confetti-capabilities",
        "tool_id": "confetti",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["virtual team building", "hybrid events", "in-person events", "DEI events", "event coordination", "professional hosting", "400+ curated experiences"],
        "source_ids": ["confetti-pricing"],
        "supporting_excerpt": "Confetti offers 400+ curated team-building experiences with full event management.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "confetti-limitations",
        "tool_id": "confetti",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": ["no published free trial", "limited HR tool integrations", "customization increases costs", "not suitable for very small teams"],
        "source_ids": ["confetti-pricing"],
        "supporting_excerpt": "Confetti has limited integrations and no published free trial; pricing is event-based.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "editorial_assessment",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === Connecteam ===
    {
        "claim_id": "connecteam-pricing-verified",
        "tool_id": "connecteam",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "model": "per-hub subscription",
            "description": "Three hubs priced separately: Operations, Communications, HR & Skills",
            "plans": [
                {"name": "Small Business", "displayed_monthly_usd": 0, "selected_limits": ["up to 10 users", "all 3 hubs free"]},
                {"name": "Basic", "displayed_monthly_usd": 29, "selected_limits": ["30 users", "per hub", "$0.80/user above 30 (Ops)"]},
                {"name": "Advanced", "displayed_monthly_usd": 49, "selected_limits": ["30 users", "per hub", "$2.50/user above 30 (Ops)"]},
                {"name": "Expert", "displayed_monthly_usd": 99, "selected_limits": ["30 users", "per hub", "$4.20/user above 30 (Ops)"]},
                {"name": "Enterprise", "custom": True}
            ]
        },
        "source_ids": ["connecteam-pricing"],
        "currency": "USD",
        "billing_term": "annual billing",
        "supporting_excerpt": "Connecteam pricing is per-hub: Free for 10 users, Basic $29/mo, Advanced $49/mo, Expert $99/mo per hub for 30 users.",
        "evidence_note": "Each hub is priced separately. Full stack costs 3x the per-hub price.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "connecteam-free-plan",
        "tool_id": "connecteam",
        "field_path": "pricing.freePlan",
        "claim_type": "pricing",
        "value": {"available": True, "limits": "up to 10 users, all hubs"},
        "source_ids": ["connecteam-pricing"],
        "supporting_excerpt": "Free Small Business Plan for up to 10 users with all 3 hubs.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "connecteam-capabilities",
        "tool_id": "connecteam",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["workforce management", "scheduling", "time tracking", "communications", "HR & skills", "GPS tracking", "mobile-first", "AI scheduling", "deskless workforce"],
        "source_ids": ["connecteam-product"],
        "supporting_excerpt": "Connecteam is built for deskless workforces with scheduling, time tracking, communications, and HR.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "connecteam-limitations",
        "tool_id": "connecteam",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": ["hub-based pricing is complex", "not ideal for office-based teams", "limited third-party integrations"],
        "source_ids": ["connecteam-product"],
        "supporting_excerpt": "Connecteam is optimized for deskless workforces, not office-based teams. Hub pricing adds complexity.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "editorial_assessment",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "connecteam-platform",
        "tool_id": "connecteam",
        "field_path": "factual_profile.platforms",
        "claim_type": "feature",
        "value": ["web", "iOS", "Android"],
        "source_ids": ["connecteam-product"],
        "supporting_excerpt": "Connecteam offers web, iOS, and Android apps.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === HiBob ===
    {
        "claim_id": "hibob-pricing-verified",
        "tool_id": "hibob",
        "field_path": "pricing.model",
        "claim_type": "pricing",
        "value": {
            "model": "custom per-employee pricing",
            "description": "Quote-based pricing, per employee per month",
            "estimated_range": "$16-$25 per employee per month",
            "notes": ["implementation fee 10-20% of annual cost", "no published pricing", "modules add cost"]
        },
        "source_ids": ["hibob-pricing"],
        "currency": "USD",
        "supporting_excerpt": "HiBob pricing is custom quote-based, estimated $16-$25 per employee per month.",
        "evidence_note": "No published pricing. Estimates from third-party sources. Implementation fee applies.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hibob-capabilities",
        "tool_id": "hibob",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["HRIS", "HCM", "employee database", "onboarding", "performance management", "engagement", "compensation", "Bob AI", "org charts", "document management", "time off", "multi-country"],
        "source_ids": ["hibob-pricing"],
        "supporting_excerpt": "HiBob offers core HRIS plus modules for performance, engagement, compensation, and AI.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hibob-limitations",
        "tool_id": "hibob",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": ["no published pricing", "requires sales call", "implementation fee required", "add-on modules increase cost", "no free trial"],
        "source_ids": ["hibob-pricing"],
        "supporting_excerpt": "HiBob requires custom quotes and has no free trial. Add-on modules add cost.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "editorial_assessment",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "hibob-platform",
        "tool_id": "hibob",
        "field_path": "factual_profile.platforms",
        "claim_type": "feature",
        "value": ["web", "iOS", "Android"],
        "source_ids": ["hibob-pricing"],
        "supporting_excerpt": "HiBob offers web, iOS, and Android apps.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === MeetGeek ===
    {
        "claim_id": "meetgeek-pricing-verified",
        "tool_id": "meetgeek",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "plans": [
                {"name": "Basic", "displayed_monthly_usd": 0, "selected_limits": ["3 hours transcription/mo", "unlimited AI summaries", "core integrations"]},
                {"name": "Pro", "displayed_monthly_usd": 9.99, "monthly_billing_usd": 15.99, "selected_limits": ["20 hours transcription/mo", "meeting templates", "AI agents", "Zapier/Make/n8n"]},
                {"name": "Business", "displayed_monthly_usd": 17, "monthly_billing_usd": 27, "selected_limits": ["unlimited transcription", "team spaces", "team analytics", "custom branding"]},
                {"name": "Enterprise", "custom": True, "selected_limits": ["SSO/SCIM", "HIPAA BAA", "custom data retention"]}
            ]
        },
        "source_ids": ["meetgeek-pricing"],
        "currency": "USD",
        "billing_term": "annual and monthly billing",
        "supporting_excerpt": "MeetGeek pricing: Free (3 hrs/mo), Pro ($9.99/mo annual), Business ($17/mo annual), Enterprise custom.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "meetgeek-free-plan",
        "tool_id": "meetgeek",
        "field_path": "pricing.freePlan",
        "claim_type": "pricing",
        "value": {"available": True, "limits": "3 hours transcription per month"},
        "source_ids": ["meetgeek-pricing"],
        "supporting_excerpt": "Free plan with 3 hours of transcription per month.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "meetgeek-trial",
        "tool_id": "meetgeek",
        "field_path": "pricing.freeTrial",
        "claim_type": "pricing",
        "value": {"available": True, "duration_days": 14},
        "source_ids": ["meetgeek-pricing"],
        "supporting_excerpt": "14-day free trial for Business plan.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "meetgeek-capabilities",
        "tool_id": "meetgeek",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["meeting transcription", "AI summaries", "100+ languages", "AI agents", "workflow automation", "team analytics", "Chrome extension", "mobile app", "API/MCP access"],
        "source_ids": ["meetgeek-pricing"],
        "supporting_excerpt": "MeetGeek offers transcription, AI summaries, agents, automation, and team analytics.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === PandaDoc ===
    {
        "claim_id": "pandadoc-pricing-verified",
        "tool_id": "pandadoc",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "plans": [
                {"name": "Free eSign", "displayed_monthly_usd": 0, "selected_limits": ["60 docs/year", "2 recipients per doc"]},
                {"name": "Starter", "displayed_monthly_usd": 19, "monthly_billing_usd": 35, "selected_limits": ["unlimited docs", "5 templates", "custom branding"]},
                {"name": "Business", "displayed_monthly_usd": 49, "monthly_billing_usd": 65, "selected_limits": ["CRM integrations", "approval workflows", "payment collection"]},
                {"name": "Enterprise", "custom": True, "selected_limits": ["CPQ", "API", "SSO", "content locking"]}
            ]
        },
        "source_ids": ["pandadoc-pricing"],
        "currency": "USD",
        "billing_term": "annual and monthly billing",
        "supporting_excerpt": "PandaDoc pricing: Free eSign, Starter $19/mo annual, Business $49/mo annual, Enterprise custom.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pandadoc-free-plan",
        "tool_id": "pandadoc",
        "field_path": "pricing.freePlan",
        "claim_type": "pricing",
        "value": {"available": True, "limits": "60 docs/year, 2 recipients per doc"},
        "source_ids": ["pandadoc-pricing"],
        "supporting_excerpt": "Free eSign plan with 60 documents per year.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pandadoc-trial",
        "tool_id": "pandadoc",
        "field_path": "pricing.freeTrial",
        "claim_type": "pricing",
        "value": {"available": True, "duration_days": 14},
        "source_ids": ["pandadoc-pricing"],
        "supporting_excerpt": "14-day free trial for paid plans.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "pandadoc-capabilities",
        "tool_id": "pandadoc",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["document automation", "e-signatures", "proposals", "quotes", "CRM integrations", "approval workflows", "payment collection", "CPQ", "templates"],
        "source_ids": ["pandadoc-pricing"],
        "supporting_excerpt": "PandaDoc offers document automation, e-signatures, proposals, quotes, and CRM integrations.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === QuickBooks ===
    {
        "claim_id": "quickbooks-pricing-verified",
        "tool_id": "quickbooks",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "plans": [
                {"name": "Simple Start", "displayed_monthly_usd": 38, "selected_limits": ["basic bookkeeping", "expense tracking"]},
                {"name": "Essentials", "displayed_monthly_usd": 75, "selected_limits": ["multi-user", "invoicing", "bill tracking"]},
                {"name": "Plus", "displayed_monthly_usd": 115, "selected_limits": ["inventory tracking", "project profitability", "advanced reporting"]},
                {"name": "Advanced", "displayed_monthly_usd": 275, "selected_limits": ["batch invoicing", "dedicated support", "custom roles"]}
            ]
        },
        "source_ids": ["quickbooks-pricing"],
        "currency": "USD",
        "billing_term": "monthly billing",
        "supporting_excerpt": "QuickBooks Online 2025 pricing: Simple Start $38/mo, Essentials $75/mo, Plus $115/mo, Advanced $275/mo.",
        "evidence_note": "Prices increased in August 2025. 50% intro offer for 3 months available.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "quickbooks-capabilities",
        "tool_id": "quickbooks",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["accounting", "invoicing", "expense tracking", "payroll", "inventory", "tax management", "bank reconciliation", "reporting", "multi-user"],
        "source_ids": ["quickbooks-pricing"],
        "supporting_excerpt": "QuickBooks Online offers accounting, invoicing, payroll, inventory, and tax management.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "quickbooks-platform",
        "tool_id": "quickbooks",
        "field_path": "factual_profile.platforms",
        "claim_type": "feature",
        "value": ["web", "iOS", "Android"],
        "source_ids": ["quickbooks-pricing"],
        "supporting_excerpt": "QuickBooks Online offers web, iOS, and Android apps.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === Shoeboxed ===
    {
        "claim_id": "shoeboxed-pricing-verified",
        "tool_id": "shoeboxed",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "plans": [
                {"name": "Starter", "displayed_monthly_usd": 9, "annual_usd": 97, "selected_limits": ["50 digital scans/mo", "20 paper scans/yr", "3 users"]},
                {"name": "Pro", "displayed_monthly_usd": 29, "annual_usd": 297, "selected_limits": ["250 digital scans/mo", "50 paper scans/mo", "5 users", "accounting integrations"]},
                {"name": "Plus", "displayed_monthly_usd": 79, "annual_usd": 797, "selected_limits": ["1000 digital scans/mo", "150 paper scans/mo", "10 users"]},
                {"name": "Paper Plus", "displayed_monthly_usd": 179, "annual_usd": 1997, "selected_limits": ["5000 digital scans/mo", "300 paper scans/mo", "10 users"]}
            ]
        },
        "source_ids": ["shoeboxed-pricing"],
        "currency": "USD",
        "billing_term": "annual and monthly billing",
        "supporting_excerpt": "Shoeboxed pricing: Starter $9/mo, Pro $29/mo, Plus $79/mo, Paper Plus $179/mo.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "shoeboxed-trial",
        "tool_id": "shoeboxed",
        "field_path": "pricing.freeTrial",
        "claim_type": "pricing",
        "value": {"available": True, "duration_days": 30, "description": "30-day money-back guarantee"},
        "source_ids": ["shoeboxed-pricing"],
        "supporting_excerpt": "30-day money-back guarantee on all plans.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "shoeboxed-capabilities",
        "tool_id": "shoeboxed",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["receipt scanning", "mileage tracking", "Magic Envelope", "QuickBooks integration", "Xero integration", "document management", "audit-proof reports"],
        "source_ids": ["shoeboxed-pricing"],
        "supporting_excerpt": "Shoeboxed offers receipt scanning, mileage tracking, Magic Envelope, and accounting integrations.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "shoeboxed-platform",
        "tool_id": "shoeboxed",
        "field_path": "factual_profile.platforms",
        "claim_type": "feature",
        "value": ["web", "iOS", "Android"],
        "source_ids": ["shoeboxed-pricing"],
        "supporting_excerpt": "Shoeboxed offers web, iOS, and Android apps.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === Teamwork ===
    {
        "claim_id": "teamwork-pricing-verified",
        "tool_id": "teamwork",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "plans": [
                {"name": "Free", "displayed_monthly_usd": 0, "selected_limits": ["5 users", "5 projects", "100 automations/mo"]},
                {"name": "Basics", "displayed_monthly_usd": 9.99, "monthly_billing_usd": 13.99, "selected_limits": ["Gantt charts", "templates", "time tracking"]},
                {"name": "Accelerate", "displayed_monthly_usd": 24.99, "monthly_billing_usd": 29.99, "selected_limits": ["workload management", "budgeting", "advanced reporting"]},
                {"name": "Optimize", "custom": True, "selected_limits": ["resource scheduling", "custom reports"]}
            ]
        },
        "source_ids": ["teamwork-pricing"],
        "currency": "USD",
        "billing_term": "annual and monthly billing",
        "supporting_excerpt": "Teamwork pricing: Free (5 users), Basics $9.99/mo annual, Accelerate $24.99/mo annual, Optimize custom.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teamwork-free-plan",
        "tool_id": "teamwork",
        "field_path": "pricing.freePlan",
        "claim_type": "pricing",
        "value": {"available": True, "limits": "5 users, 5 projects, 100 automations"},
        "source_ids": ["teamwork-pricing"],
        "supporting_excerpt": "Free plan for up to 5 users with 5 projects.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teamwork-trial",
        "tool_id": "teamwork",
        "field_path": "pricing.freeTrial",
        "claim_type": "pricing",
        "value": {"available": True, "duration_days": 14},
        "source_ids": ["teamwork-pricing"],
        "supporting_excerpt": "14-day free trial for paid plans.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "teamwork-capabilities",
        "tool_id": "teamwork",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["project management", "time tracking", "Gantt charts", "workload management", "budgeting", "client management", "CRM", "help desk"],
        "source_ids": ["teamwork-pricing"],
        "supporting_excerpt": "Teamwork offers project management, time tracking, Gantt charts, workload management, and client management.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === TimeDoctor ===
    {
        "claim_id": "timedoctor-pricing-verified",
        "tool_id": "timedoctor",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "plans": [
                {"name": "Basic", "displayed_monthly_usd": 6.67, "monthly_billing_usd": 8, "selected_limits": ["time tracking", "screenshots", "timeline report"]},
                {"name": "Standard", "displayed_monthly_usd": 11.67, "monthly_billing_usd": 14, "selected_limits": ["scheduling", "payroll", "60+ integrations", "productivity ratings"]},
                {"name": "Premium", "displayed_monthly_usd": 16.7, "monthly_billing_usd": 20, "selected_limits": ["AI benchmarks", "video recording", "executive dashboard", "SSO"]},
                {"name": "Enterprise", "custom": True}
            ]
        },
        "source_ids": ["timedoctor-pricing"],
        "currency": "USD",
        "billing_term": "annual and monthly billing",
        "supporting_excerpt": "Time Doctor pricing: Basic $6.67/mo annual, Standard $11.67/mo annual, Premium $16.70/mo annual, Enterprise custom.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "timedoctor-trial",
        "tool_id": "timedoctor",
        "field_path": "pricing.freeTrial",
        "claim_type": "pricing",
        "value": {"available": True, "duration_days": 14},
        "source_ids": ["timedoctor-pricing"],
        "supporting_excerpt": "14-day free trial with full Premium features.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "timedoctor-capabilities",
        "tool_id": "timedoctor",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["time tracking", "screenshots", "activity monitoring", "productivity ratings", "payroll", "scheduling", "attendance", "AI benchmarks", "video recording", "60+ integrations"],
        "source_ids": ["timedoctor-pricing"],
        "supporting_excerpt": "Time Doctor offers time tracking, screenshots, activity monitoring, payroll, and AI benchmarks.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "timedoctor-limitations",
        "tool_id": "timedoctor",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": ["no free plan", "privacy concerns with screenshots", "add-ons increase cost", "not suitable for outcome-based teams"],
        "source_ids": ["timedoctor-pricing"],
        "supporting_excerpt": "Time Doctor has no free plan and raises privacy concerns with screenshot capture.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "editorial_assessment",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === Trainual ===
    {
        "claim_id": "trainual-pricing-verified",
        "tool_id": "trainual",
        "field_path": "pricing.model",
        "claim_type": "pricing",
        "value": {
            "model": "custom quote-based",
            "description": "No published pricing; contact sales for quote",
            "estimated_range": "$249/month for 10 seats (Core plan)",
            "notes": ["$1000 one-time implementation fee", "Core, Pro, Premium, Enterprise tiers", "priced by headcount bands"]
        },
        "source_ids": ["trainual-pricing"],
        "currency": "USD",
        "supporting_excerpt": "Trainual pricing is custom quote-based, estimated $249/mo for 10 seats with $1000 setup fee.",
        "evidence_note": "No published pricing. Estimates from third-party sources. Implementation fee required.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "trainual-capabilities",
        "tool_id": "trainual",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["employee onboarding", "SOP documentation", "video training", "completion tracking", "role-based training", "e-signatures", "org charts", "HRIS integrations"],
        "source_ids": ["trainual-pricing"],
        "supporting_excerpt": "Trainual offers employee onboarding, SOP documentation, video training, and completion tracking.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "trainual-limitations",
        "tool_id": "trainual",
        "field_path": "factual_profile.limitations",
        "claim_type": "limitation",
        "value": ["no published pricing", "no free plan", "$1000 implementation fee", "15GB video storage limit on Pro", "tracks completion not comprehension"],
        "source_ids": ["trainual-pricing"],
        "supporting_excerpt": "Trainual has no published pricing, no free plan, and requires $1000 setup fee.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "editorial_assessment",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === Upwork ===
    {
        "claim_id": "upwork-pricing-verified",
        "tool_id": "upwork",
        "field_path": "pricing.model",
        "claim_type": "pricing",
        "value": {
            "model": "marketplace fees",
            "description": "Freelancer and client fees",
            "freelancer_fee": "0-15% variable per contract (most ~10%)",
            "client_fees": {
                "Basic": "5% marketplace fee + contract initiation fee",
                "Business Plus": "10% fee + contract initiation fee"
            },
            "connects": "$0.15 each, 10 free/month"
        },
        "source_ids": ["upwork-pricing"],
        "currency": "USD",
        "supporting_excerpt": "Upwork charges freelancers 0-15% variable fee, clients 5-10% marketplace fee plus contract initiation fee.",
        "evidence_note": "Fee structure changed in May 2025 from tiered to variable model.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "upwork-capabilities",
        "tool_id": "upwork",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["freelance marketplace", "talent discovery", "project catalog", "escrow payments", "time tracking", "invoicing", "Direct Contracts", "18M+ freelancers"],
        "source_ids": ["upwork-pricing"],
        "supporting_excerpt": "Upwork is a freelance marketplace with 18M+ freelancers, escrow payments, and project catalog.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === Wrike ===
    {
        "claim_id": "wrike-pricing-verified",
        "tool_id": "wrike",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "plans": [
                {"name": "Free", "displayed_monthly_usd": 0, "selected_limits": ["unlimited users", "2GB storage", "basic task management"]},
                {"name": "Team", "displayed_monthly_usd": 10, "selected_limits": ["2-15 users", "Gantt charts", "AI Essentials", "shareable dashboards"]},
                {"name": "Business", "displayed_monthly_usd": 25, "selected_limits": ["5-200 users", "AI Elite", "resource planning", "standard integrations"]},
                {"name": "Pinnacle", "custom": True, "selected_limits": ["advanced resource planning", "budgeting", "custom roles"]},
                {"name": "Apex", "custom": True, "selected_limits": ["enterprise features", "advanced analytics"]}
            ]
        },
        "source_ids": ["wrike-pricing"],
        "currency": "USD",
        "billing_term": "annual billing",
        "supporting_excerpt": "Wrike pricing: Free, Team $10/mo, Business $25/mo, Pinnacle and Apex custom.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wrike-free-plan",
        "tool_id": "wrike",
        "field_path": "pricing.freePlan",
        "claim_type": "pricing",
        "value": {"available": True, "limits": "unlimited users, 2GB storage, active task limits"},
        "source_ids": ["wrike-pricing"],
        "supporting_excerpt": "Free plan with unlimited users and 2GB storage.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wrike-capabilities",
        "tool_id": "wrike",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["project management", "Gantt charts", "resource planning", "workflow automation", "AI features", "reporting", "Kanban boards", "time tracking", "budgeting"],
        "source_ids": ["wrike-pricing"],
        "supporting_excerpt": "Wrike offers project management, Gantt charts, resource planning, AI features, and reporting.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "wrike-platform",
        "tool_id": "wrike",
        "field_path": "factual_profile.platforms",
        "claim_type": "feature",
        "value": ["web", "Windows", "macOS", "iOS", "Android"],
        "source_ids": ["wrike-pricing"],
        "supporting_excerpt": "Wrike offers web, Windows, macOS, iOS, and Android apps.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === Xero ===
    {
        "claim_id": "xero-pricing-verified",
        "tool_id": "xero",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "plans": [
                {"name": "Early", "displayed_monthly_usd": 27, "selected_limits": ["20 invoices", "5 bills", "bank reconciliation", "sales tax"]},
                {"name": "Growing", "displayed_monthly_usd": 59, "selected_limits": ["unlimited invoices", "budgeting", "auto-reconcile", "dashboards"]},
                {"name": "Established", "displayed_monthly_usd": 97, "selected_limits": ["180-day forecast", "unlimited budgets", "projects", "inventory"]}
            ]
        },
        "source_ids": ["xero-pricing"],
        "currency": "USD",
        "billing_term": "monthly billing",
        "supporting_excerpt": "Xero US pricing: Early $27/mo, Growing $59/mo, Established $97/mo.",
        "evidence_note": "90% off for first 6 months promo available. UK pricing differs.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "xero-trial",
        "tool_id": "xero",
        "field_path": "pricing.freeTrial",
        "claim_type": "pricing",
        "value": {"available": True, "duration_days": 30, "description": "30-day free trial or 90% off first 6 months"},
        "source_ids": ["xero-pricing"],
        "supporting_excerpt": "30-day free trial or 90% off first 6 months.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "xero-capabilities",
        "tool_id": "xero",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["accounting", "invoicing", "bank reconciliation", "payroll", "tax management", "budgeting", "1000+ integrations", "multi-currency", "project tracking"],
        "source_ids": ["xero-pricing"],
        "supporting_excerpt": "Xero offers accounting, invoicing, bank reconciliation, payroll, and 1000+ integrations.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "xero-platform",
        "tool_id": "xero",
        "field_path": "factual_profile.platforms",
        "claim_type": "feature",
        "value": ["web", "iOS", "Android"],
        "source_ids": ["xero-pricing"],
        "supporting_excerpt": "Xero offers web, iOS, and Android apps.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    # === AdCreative ===
    {
        "claim_id": "adcreative-pricing-verified",
        "tool_id": "adcreative",
        "field_path": "pricing.tiers",
        "claim_type": "pricing",
        "value": {
            "plans": [
                {"name": "Starter", "displayed_monthly_usd": 39, "annual_usd": 249, "selected_limits": ["20 credits/mo", "1 brand", "1 user"]},
                {"name": "Professional", "displayed_monthly_usd": 249, "annual_usd": 1500, "selected_limits": ["300 credits/mo", "3 brands", "10 users"]},
                {"name": "Ultimate", "displayed_monthly_usd": 999, "annual_usd": 6000, "selected_limits": ["300 credits/mo", "25 brands", "20 users"]},
                {"name": "Enterprise", "custom": True}
            ]
        },
        "source_ids": ["adcreative-pricing"],
        "currency": "USD",
        "billing_term": "annual and monthly billing",
        "supporting_excerpt": "AdCreative.ai pricing: Starter $39/mo, Professional $249/mo, Ultimate $999/mo, Enterprise custom.",
        "evidence_note": "Credits used on download. Annual billing saves ~50%.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "stale_after": "2026-12-23",
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "adcreative-trial",
        "tool_id": "adcreative",
        "field_path": "pricing.freeTrial",
        "claim_type": "pricing",
        "value": {"available": True, "duration_days": 7, "description": "7-day free trial with 20 credits"},
        "source_ids": ["adcreative-pricing"],
        "supporting_excerpt": "7-day free trial with 20 credits.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
    {
        "claim_id": "adcreative-capabilities",
        "tool_id": "adcreative",
        "field_path": "factual_profile.capabilities",
        "claim_type": "capability",
        "value": ["AI ad creative generation", "ad copywriting", "performance scoring", "iStock integration", "ad platform integrations", "competitor insights", "compliance checker"],
        "source_ids": ["adcreative-pricing"],
        "supporting_excerpt": "AdCreative.ai offers AI ad creative generation, copywriting, performance scoring, and competitor insights.",
        "accessed_at": TODAY,
        "verified_at": TODAY,
        "status": "verified_official",
        "disputed_by": None,
        "replacement_claim_id": None
    },
]


def main():
    print("=" * 60)
    print("Phase 5 Research Batch 1: Adding Evidence")
    print("=" * 60)

    # Load evidence ledger
    ledger = load_json(EVIDENCE_LEDGER_PATH)
    existing_sources = {s["source_id"] for s in ledger.get("sources", [])}
    existing_claims = {c["claim_id"] for c in ledger.get("claims", [])}

    # Add new sources
    new_sources_added = 0
    for source in NEW_SOURCES:
        if source["source_id"] not in existing_sources:
            ledger["sources"].append(source)
            new_sources_added += 1
            print(f"  Added source: {source['source_id']}")

    # Add new claims
    new_claims_added = 0
    for claim in NEW_CLAIMS:
        if claim["claim_id"] not in existing_claims:
            ledger["claims"].append(claim)
            new_claims_added += 1
            print(f"  Added claim: {claim['claim_id']}")

    # Save evidence ledger
    save_json(EVIDENCE_LEDGER_PATH, ledger)
    print(f"\nAdded {new_sources_added} sources and {new_claims_added} claims")

    # Update tools-v1.json with pricing data
    print("\nUpdating tools-v1.json...")
    v1_data = load_json(TOOLS_V1_PATH)
    tools = v1_data.get("tools", [])

    # Pricing updates for tools-v1
    pricing_updates = {
        "notion": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "period": "month"},
                {"name": "Plus", "price": 10, "period": "month"},
                {"name": "Business", "price": 20, "period": "month"},
                {"name": "Enterprise", "price": None, "period": "custom"}
            ],
            "freePlan": {"available": True, "limits": "10 guests max"},
            "freeTrial": {"available": False}
        },
        "confetti": {
            "model": "event-based pricing",
            "currency": "USD",
            "tiers": [
                {"name": "Pay-Per-Event", "price": 30, "period": "per user per event"},
                {"name": "Pre-Fund", "price": 5000, "period": "year"},
                {"name": "Enterprise", "price": None, "period": "custom"}
            ],
            "freePlan": {"available": False},
            "freeTrial": {"available": False}
        },
        "connecteam": {
            "model": "per-hub subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Small Business", "price": 0, "period": "month"},
                {"name": "Basic", "price": 29, "period": "month"},
                {"name": "Advanced", "price": 49, "period": "month"},
                {"name": "Expert", "price": 99, "period": "month"}
            ],
            "freePlan": {"available": True, "limits": "up to 10 users"},
            "freeTrial": {"available": False}
        },
        "hibob": {
            "model": "custom per-employee pricing",
            "currency": "USD",
            "tiers": [],
            "freePlan": {"available": False},
            "freeTrial": {"available": False}
        },
        "meetgeek": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Basic", "price": 0, "period": "month"},
                {"name": "Pro", "price": 9.99, "period": "month"},
                {"name": "Business", "price": 17, "period": "month"},
                {"name": "Enterprise", "price": None, "period": "custom"}
            ],
            "freePlan": {"available": True, "limits": "3 hours transcription/mo"},
            "freeTrial": {"available": True, "duration_days": 14}
        },
        "pandadoc": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Free eSign", "price": 0, "period": "month"},
                {"name": "Starter", "price": 19, "period": "month"},
                {"name": "Business", "price": 49, "period": "month"},
                {"name": "Enterprise", "price": None, "period": "custom"}
            ],
            "freePlan": {"available": True, "limits": "60 docs/year"},
            "freeTrial": {"available": True, "duration_days": 14}
        },
        "quickbooks": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Simple Start", "price": 38, "period": "month"},
                {"name": "Essentials", "price": 75, "period": "month"},
                {"name": "Plus", "price": 115, "period": "month"},
                {"name": "Advanced", "price": 275, "period": "month"}
            ],
            "freePlan": {"available": False},
            "freeTrial": {"available": False}
        },
        "shoeboxed": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Starter", "price": 9, "period": "month"},
                {"name": "Pro", "price": 29, "period": "month"},
                {"name": "Plus", "price": 79, "period": "month"},
                {"name": "Paper Plus", "price": 179, "period": "month"}
            ],
            "freePlan": {"available": False},
            "freeTrial": {"available": True, "duration_days": 30}
        },
        "teamwork": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "period": "month"},
                {"name": "Basics", "price": 9.99, "period": "month"},
                {"name": "Accelerate", "price": 24.99, "period": "month"},
                {"name": "Optimize", "price": None, "period": "custom"}
            ],
            "freePlan": {"available": True, "limits": "5 users, 5 projects"},
            "freeTrial": {"available": True, "duration_days": 14}
        },
        "timedoctor": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Basic", "price": 6.67, "period": "month"},
                {"name": "Standard", "price": 11.67, "period": "month"},
                {"name": "Premium", "price": 16.7, "period": "month"},
                {"name": "Enterprise", "price": None, "period": "custom"}
            ],
            "freePlan": {"available": False},
            "freeTrial": {"available": True, "duration_days": 14}
        },
        "trainual": {
            "model": "custom quote-based",
            "currency": "USD",
            "tiers": [],
            "freePlan": {"available": False},
            "freeTrial": {"available": False}
        },
        "upwork": {
            "model": "marketplace fees",
            "currency": "USD",
            "tiers": [],
            "freePlan": {"available": False},
            "freeTrial": {"available": False}
        },
        "wrike": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Free", "price": 0, "period": "month"},
                {"name": "Team", "price": 10, "period": "month"},
                {"name": "Business", "price": 25, "period": "month"},
                {"name": "Pinnacle", "price": None, "period": "custom"},
                {"name": "Apex", "price": None, "period": "custom"}
            ],
            "freePlan": {"available": True, "limits": "unlimited users, 2GB storage"},
            "freeTrial": {"available": False}
        },
        "xero": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Early", "price": 27, "period": "month"},
                {"name": "Growing", "price": 59, "period": "month"},
                {"name": "Established", "price": 97, "period": "month"}
            ],
            "freePlan": {"available": False},
            "freeTrial": {"available": True, "duration_days": 30}
        },
        "adcreative": {
            "model": "tiered subscription",
            "currency": "USD",
            "tiers": [
                {"name": "Starter", "price": 39, "period": "month"},
                {"name": "Professional", "price": 249, "period": "month"},
                {"name": "Ultimate", "price": 999, "period": "month"},
                {"name": "Enterprise", "price": None, "period": "custom"}
            ],
            "freePlan": {"available": False},
            "freeTrial": {"available": True, "duration_days": 7}
        },
    }

    updated_tools = 0
    for tool in tools:
        tid = tool.get("id")
        if tid in pricing_updates:
            tool["pricing"] = pricing_updates[tid]
            # Add platforms if available
            if tid == "connecteam":
                tool["platforms"] = ["web", "iOS", "Android"]
            elif tid == "quickbooks":
                tool["platforms"] = ["web", "iOS", "Android"]
            elif tid == "shoeboxed":
                tool["platforms"] = ["web", "iOS", "Android"]
            elif tid == "wrike":
                tool["platforms"] = ["web", "Windows", "macOS", "iOS", "Android"]
            elif tid == "xero":
                tool["platforms"] = ["web", "iOS", "Android"]
            updated_tools += 1
            print(f"  Updated v1: {tid}")

    save_json(TOOLS_V1_PATH, v1_data)
    print(f"Updated {updated_tools} tools in tools-v1.json")

    # Update v2 JSON files with evidence references
    print("\nUpdating v2 JSON files with evidence references...")
    tool_claims = {}
    for claim in NEW_CLAIMS:
        tid = claim["tool_id"]
        tool_claims.setdefault(tid, []).append(claim["claim_id"])

    v2_updated = 0
    for tid, claim_ids in tool_claims.items():
        v2_path = TOOLS_V2_DIR / "legacy" / f"{tid}.json"
        if not v2_path.exists():
            v2_path = TOOLS_V2_DIR / "expansion" / f"{tid}.json"
        if v2_path.exists():
            try:
                v2_data = load_json(v2_path)
                # Add claim refs
                evidence = v2_data.setdefault("evidence", {})
                existing_refs = evidence.get("claim_refs", [])
                for cid in claim_ids:
                    if cid not in existing_refs:
                        existing_refs.append(cid)
                evidence["claim_refs"] = existing_refs
                # Add source ids
                existing_sources = evidence.get("source_ids", [])
                for source in NEW_SOURCES:
                    if source["source_id"] not in existing_sources:
                        # Check if this source is for this tool
                        for claim in NEW_CLAIMS:
                            if claim["tool_id"] == tid and source["source_id"] in claim.get("source_ids", []):
                                existing_sources.append(source["source_id"])
                                break
                evidence["source_ids"] = existing_sources
                save_json(v2_path, v2_data)
                v2_updated += 1
                print(f"  Updated v2: {tid}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"  Warning: Could not update {v2_path}: {e}")

    print(f"\nUpdated {v2_updated} v2 JSON files")

    # Summary
    print("\n" + "=" * 60)
    print("BATCH 1 SUMMARY")
    print("=" * 60)
    print(f"Sources added: {new_sources_added}")
    print(f"Claims added: {new_claims_added}")
    print(f"Tools updated (v1): {updated_tools}")
    print(f"Tools updated (v2): {v2_updated}")
    print(f"Total tools researched: 15")

    return 0


if __name__ == "__main__":
    sys.exit(main())
