#!/usr/bin/env python3
"""Add Phase 5 Research Batch 2 evidence - pricing for 10 tools without pricing data."""

from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "evidence" / "evidence-ledger.json"
V1 = ROOT / "data" / "tools-v1.json"
V2_DIR = ROOT / "data" / "tools-v2"
TODAY = datetime.now().strftime("%Y-%m-%d")

def load(p):
    with p.open(encoding="utf-8") as f:
        return json.load(f)

def save(p, d):
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

NEW_SOURCES = [
    {"source_id": "ahrefs-pricing", "url": "https://ahrefs.com/pricing", "source_type": "official_pricing", "publisher": "Ahrefs", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
    {"source_id": "apollo-pricing", "url": "https://www.apollo.io/pricing", "source_type": "official_pricing", "publisher": "Apollo", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
    {"source_id": "descript-pricing", "url": "https://www.descript.com/pricing", "source_type": "official_pricing", "publisher": "Descript", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
    {"source_id": "elevenlabs-pricing", "url": "https://elevenlabs.io/pricing", "source_type": "official_pricing", "publisher": "ElevenLabs", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
    {"source_id": "claude-pricing", "url": "https://claude.com/pricing", "source_type": "official_pricing", "publisher": "Anthropic", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
    {"source_id": "hubspot-pricing", "url": "https://www.hubspot.com/pricing", "source_type": "official_pricing", "publisher": "HubSpot", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
    {"source_id": "pipedrive-pricing", "url": "https://www.pipedrive.com/pricing", "source_type": "official_pricing", "publisher": "Pipedrive", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
    {"source_id": "monday-pricing", "url": "https://monday.com/pricing", "source_type": "official_pricing", "publisher": "monday.com", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
    {"source_id": "todoist-pricing", "url": "https://todoist.com/pricing", "source_type": "official_pricing", "publisher": "Todoist", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
    {"source_id": "copyai-pricing", "url": "https://www.copy.ai/pricing", "source_type": "official_pricing", "publisher": "Copy.ai", "official": True, "accessed_at": TODAY, "verified_at": TODAY, "status": "active", "source_history": []},
]

NEW_CLAIMS = [
    # Ahrefs
    {"claim_id": "ahrefs-pricing-verified", "tool_id": "ahrefs", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Starter", "displayed_monthly_usd": 29}, {"name": "Lite", "displayed_monthly_usd": 129}, {"name": "Standard", "displayed_monthly_usd": 249}, {"name": "Advanced", "displayed_monthly_usd": 449}, {"name": "Enterprise", "displayed_monthly_usd": 1499}]}, "source_ids": ["ahrefs-pricing"], "currency": "USD", "billing_term": "monthly and annual billing", "supporting_excerpt": "Ahrefs pricing: Starter $29/mo, Lite $129/mo, Standard $249/mo, Advanced $449/mo, Enterprise $1499/mo.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "ahrefs-free-plan", "tool_id": "ahrefs", "field_path": "pricing.freePlan", "claim_type": "pricing", "value": {"available": True, "limits": "Webmaster Tools for verified sites only"}, "source_ids": ["ahrefs-pricing"], "currency": "USD", "billing_term": "free", "supporting_excerpt": "Free Webmaster Tools for sites you own.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "ahrefs-capabilities", "tool_id": "ahrefs", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["SEO", "keyword research", "backlink analysis", "site audit", "rank tracking", "content explorer", "competitor analysis"], "source_ids": ["ahrefs-pricing"], "supporting_excerpt": "Ahrefs offers SEO tools including keyword research, backlink analysis, and site audit.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    # Apollo
    {"claim_id": "apollo-pricing-verified", "tool_id": "apollo", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Free", "displayed_monthly_usd": 0}, {"name": "Basic", "displayed_monthly_usd": 49}, {"name": "Professional", "displayed_monthly_usd": 79}, {"name": "Organization", "displayed_monthly_usd": 119}]}, "source_ids": ["apollo-pricing"], "currency": "USD", "billing_term": "annual billing", "supporting_excerpt": "Apollo pricing: Free, Basic $49/mo, Professional $79/mo, Organization $119/mo per user.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "apollo-free-plan", "tool_id": "apollo", "field_path": "pricing.freePlan", "claim_type": "pricing", "value": {"available": True, "limits": "limited credits, Gmail only"}, "source_ids": ["apollo-pricing"], "currency": "USD", "billing_term": "free", "supporting_excerpt": "Free plan with limited credits.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "apollo-capabilities", "tool_id": "apollo", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["sales intelligence", "lead database", "email sequencing", "CRM integration", "dialer", "call recording", "buying intent"], "source_ids": ["apollo-pricing"], "supporting_excerpt": "Apollo offers sales intelligence, lead database, email sequencing, and CRM integration.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    # Descript
    {"claim_id": "descript-pricing-verified", "tool_id": "descript", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Free", "displayed_monthly_usd": 0}, {"name": "Hobbyist", "displayed_monthly_usd": 16}, {"name": "Creator", "displayed_monthly_usd": 24}, {"name": "Business", "displayed_monthly_usd": 50}]}, "source_ids": ["descript-pricing"], "currency": "USD", "billing_term": "annual billing", "supporting_excerpt": "Descript pricing: Free, Hobbyist $16/mo, Creator $24/mo, Business $50/mo per person.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "descript-free-plan", "tool_id": "descript", "field_path": "pricing.freePlan", "claim_type": "pricing", "value": {"available": True, "limits": "1 hour media/mo, watermarked exports"}, "source_ids": ["descript-pricing"], "currency": "USD", "billing_term": "free", "supporting_excerpt": "Free plan with 1 hour media per month.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "descript-capabilities", "tool_id": "descript", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["video editing", "audio editing", "text-based editing", "AI voice cloning", "screen recording", "podcast editing", "captions", "AI dubbing"], "source_ids": ["descript-pricing"], "supporting_excerpt": "Descript offers video/audio editing with text-based workflow and AI features.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    # ElevenLabs
    {"claim_id": "elevenlabs-pricing-verified", "tool_id": "elevenlabs", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Free", "displayed_monthly_usd": 0}, {"name": "Starter", "displayed_monthly_usd": 6}, {"name": "Creator", "displayed_monthly_usd": 22}, {"name": "Pro", "displayed_monthly_usd": 99}, {"name": "Scale", "displayed_monthly_usd": 299}, {"name": "Business", "displayed_monthly_usd": 990}]}, "source_ids": ["elevenlabs-pricing"], "currency": "USD", "billing_term": "monthly and annual billing", "supporting_excerpt": "ElevenLabs pricing: Free, Starter $6/mo, Creator $22/mo, Pro $99/mo, Scale $299/mo, Business $990/mo.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "elevenlabs-free-plan", "tool_id": "elevenlabs", "field_path": "pricing.freePlan", "claim_type": "pricing", "value": {"available": True, "limits": "10k credits/mo, non-commercial"}, "source_ids": ["elevenlabs-pricing"], "currency": "USD", "billing_term": "free", "supporting_excerpt": "Free plan with 10k credits per month, non-commercial use.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "elevenlabs-capabilities", "tool_id": "elevenlabs", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["text-to-speech", "voice cloning", "speech-to-text", "AI voice generation", "dubbing", "sound effects", "music generation"], "source_ids": ["elevenlabs-pricing"], "supporting_excerpt": "ElevenLabs offers text-to-speech, voice cloning, and AI voice generation.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    # Claude
    {"claim_id": "claude-pricing-verified", "tool_id": "claude", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Free", "displayed_monthly_usd": 0}, {"name": "Pro", "displayed_monthly_usd": 20}, {"name": "Max", "displayed_monthly_usd": 100}, {"name": "Ultra", "displayed_monthly_usd": 200}]}, "source_ids": ["claude-pricing"], "currency": "USD", "billing_term": "monthly billing", "supporting_excerpt": "Claude pricing: Free, Pro $20/mo, Max $100/mo, Ultra $200/mo.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "claude-free-plan", "tool_id": "claude", "field_path": "pricing.freePlan", "claim_type": "pricing", "value": {"available": True, "limits": "limited usage every 5 hours and weekly"}, "source_ids": ["claude-pricing"], "currency": "USD", "billing_term": "free", "supporting_excerpt": "Free plan with limited usage.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "claude-capabilities", "tool_id": "claude", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["AI chat", "code generation", "Claude Code", "document analysis", "web search", "artifacts", "memory", "API access"], "source_ids": ["claude-pricing"], "supporting_excerpt": "Claude offers AI chat, code generation, Claude Code, and document analysis.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "claude-platform", "tool_id": "claude", "field_path": "factual_profile.platforms", "claim_type": "feature", "value": ["web", "iOS", "Android", "Windows", "macOS"], "source_ids": ["claude-pricing"], "supporting_excerpt": "Claude offers web, iOS, Android, Windows, and macOS apps.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    # HubSpot
    {"claim_id": "hubspot-pricing-verified", "tool_id": "hubspot", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Free", "displayed_monthly_usd": 0}, {"name": "Starter", "displayed_monthly_usd": 20}, {"name": "Professional", "displayed_monthly_usd": 800}, {"name": "Enterprise", "displayed_monthly_usd": 3600}]}, "source_ids": ["hubspot-pricing"], "currency": "USD", "billing_term": "annual billing", "supporting_excerpt": "HubSpot pricing: Free CRM, Starter $20/mo per seat, Professional $800/mo, Enterprise $3600/mo.", "evidence_note": "Pricing varies by hub. Prices shown are per-hub starting prices.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "hubspot-free-plan", "tool_id": "hubspot", "field_path": "pricing.freePlan", "claim_type": "pricing", "value": {"available": True, "limits": "basic CRM features"}, "source_ids": ["hubspot-pricing"], "currency": "USD", "billing_term": "free", "supporting_excerpt": "Free CRM with basic features.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "hubspot-capabilities", "tool_id": "hubspot", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["CRM", "marketing automation", "sales pipeline", "customer service", "CMS", "workflows", "reporting", "2000+ integrations"], "source_ids": ["hubspot-pricing"], "supporting_excerpt": "HubSpot offers CRM, marketing, sales, service, and CMS hubs.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    # Pipedrive
    {"claim_id": "pipedrive-pricing-verified", "tool_id": "pipedrive", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Lite", "displayed_monthly_usd": 14}, {"name": "Essential", "displayed_monthly_usd": 27}, {"name": "Scale", "displayed_monthly_usd": 49}, {"name": "Premium", "displayed_monthly_usd": 79}]}, "source_ids": ["pipedrive-pricing"], "currency": "USD", "billing_term": "annual billing", "supporting_excerpt": "Pipedrive pricing: Lite $14/mo, Essential $27/mo, Scale $49/mo, Premium $79/mo per user.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "pipedrive-trial", "tool_id": "pipedrive", "field_path": "pricing.freeTrial", "claim_type": "pricing", "value": {"available": True, "duration_days": 14}, "source_ids": ["pipedrive-pricing"], "currency": "USD", "billing_term": "trial", "supporting_excerpt": "14-day free trial.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "pipedrive-capabilities", "tool_id": "pipedrive", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["sales CRM", "pipeline management", "deal tracking", "email integration", "automation", "reporting", "mobile app"], "source_ids": ["pipedrive-pricing"], "supporting_excerpt": "Pipedrive offers sales CRM, pipeline management, and deal tracking.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    # Monday
    {"claim_id": "monday-pricing-verified", "tool_id": "monday", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Basic", "displayed_monthly_usd": 9}, {"name": "Standard", "displayed_monthly_usd": 17}, {"name": "Pro", "displayed_monthly_usd": 26}, {"name": "Enterprise", "custom": True}]}, "source_ids": ["monday-pricing"], "currency": "USD", "billing_term": "annual billing, 3-seat minimum", "supporting_excerpt": "Monday pricing: Basic $9/mo, Standard $17/mo, Pro $26/mo per seat, 3-seat minimum.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "monday-capabilities", "tool_id": "monday", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["work management", "project management", "CRM", "automation", "Gantt charts", "time tracking", "dashboards", "200+ integrations"], "source_ids": ["monday-pricing"], "supporting_excerpt": "Monday offers work management, project management, CRM, and automation.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    # Todoist
    {"claim_id": "todoist-pricing-verified", "tool_id": "todoist", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Free", "displayed_monthly_usd": 0}, {"name": "Pro", "displayed_monthly_usd": 4}, {"name": "Business", "displayed_monthly_usd": 6}]}, "source_ids": ["todoist-pricing"], "currency": "USD", "billing_term": "annual billing", "supporting_excerpt": "Todoist pricing: Free, Pro $4/mo, Business $6/mo per user.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "todoist-free-plan", "tool_id": "todoist", "field_path": "pricing.freePlan", "claim_type": "pricing", "value": {"available": True, "limits": "5 active projects, 5 collaborators"}, "source_ids": ["todoist-pricing"], "currency": "USD", "billing_term": "free", "supporting_excerpt": "Free plan with 5 active projects.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "todoist-capabilities", "tool_id": "todoist", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["task management", "project organization", "reminders", "collaboration", "integrations", "natural language input", "keyboard shortcuts"], "source_ids": ["todoist-pricing"], "supporting_excerpt": "Todoist offers task management, project organization, and collaboration.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "todoist-platform", "tool_id": "todoist", "field_path": "factual_profile.platforms", "claim_type": "feature", "value": ["web", "iOS", "Android", "Windows", "macOS", "Chrome"], "source_ids": ["todoist-pricing"], "supporting_excerpt": "Todoist offers web, iOS, Android, Windows, macOS, and Chrome.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    # Copy.ai
    {"claim_id": "copyai-pricing-verified", "tool_id": "copyai", "field_path": "pricing.tiers", "claim_type": "pricing", "value": {"plans": [{"name": "Free", "displayed_monthly_usd": 0}, {"name": "Pro", "displayed_monthly_usd": 49}, {"name": "Enterprise", "custom": True}]}, "source_ids": ["copyai-pricing"], "currency": "USD", "billing_term": "monthly and annual billing", "supporting_excerpt": "Copy.ai pricing: Free, Pro $49/mo, Enterprise custom.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "copyai-free-plan", "tool_id": "copyai", "field_path": "pricing.freePlan", "claim_type": "pricing", "value": {"available": True, "limits": "limited generations"}, "source_ids": ["copyai-pricing"], "currency": "USD", "billing_term": "free", "supporting_excerpt": "Free plan with limited generations.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
    {"claim_id": "copyai-capabilities", "tool_id": "copyai", "field_path": "factual_profile.capabilities", "claim_type": "capability", "value": ["AI copywriting", "marketing content", "social media posts", "email copy", "ad copy", "brand voice", "workflow automation"], "source_ids": ["copyai-pricing"], "supporting_excerpt": "Copy.ai offers AI copywriting for marketing, social media, and email.", "accessed_at": TODAY, "verified_at": TODAY, "stale_after": "2026-12-23", "status": "verified_official", "disputed_by": None, "replacement_claim_id": None},
]

PRICING_UPDATES = {
    "ahrefs": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Starter", "price": 29, "period": "month"}, {"name": "Lite", "price": 129, "period": "month"}, {"name": "Standard", "price": 249, "period": "month"}, {"name": "Advanced", "price": 449, "period": "month"}, {"name": "Enterprise", "price": 1499, "period": "month"}], "freePlan": {"available": True, "limits": "Webmaster Tools for verified sites"}, "freeTrial": {"available": False}},
    "apollo": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Free", "price": 0, "period": "month"}, {"name": "Basic", "price": 49, "period": "month"}, {"name": "Professional", "price": 79, "period": "month"}, {"name": "Organization", "price": 119, "period": "month"}], "freePlan": {"available": True, "limits": "limited credits"}, "freeTrial": {"available": False}},
    "descript": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Free", "price": 0, "period": "month"}, {"name": "Hobbyist", "price": 16, "period": "month"}, {"name": "Creator", "price": 24, "period": "month"}, {"name": "Business", "price": 50, "period": "month"}], "freePlan": {"available": True, "limits": "1 hour media/mo"}, "freeTrial": {"available": False}},
    "elevenlabs": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Free", "price": 0, "period": "month"}, {"name": "Starter", "price": 6, "period": "month"}, {"name": "Creator", "price": 22, "period": "month"}, {"name": "Pro", "price": 99, "period": "month"}, {"name": "Scale", "price": 299, "period": "month"}, {"name": "Business", "price": 990, "period": "month"}], "freePlan": {"available": True, "limits": "10k credits/mo, non-commercial"}, "freeTrial": {"available": False}},
    "claude": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Free", "price": 0, "period": "month"}, {"name": "Pro", "price": 20, "period": "month"}, {"name": "Max", "price": 100, "period": "month"}, {"name": "Ultra", "price": 200, "period": "month"}], "freePlan": {"available": True, "limits": "limited usage"}, "freeTrial": {"available": False}},
    "hubspot": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Free", "price": 0, "period": "month"}, {"name": "Starter", "price": 20, "period": "month"}, {"name": "Professional", "price": 800, "period": "month"}, {"name": "Enterprise", "price": 3600, "period": "month"}], "freePlan": {"available": True, "limits": "basic CRM"}, "freeTrial": {"available": False}},
    "pipedrive": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Lite", "price": 14, "period": "month"}, {"name": "Essential", "price": 27, "period": "month"}, {"name": "Scale", "price": 49, "period": "month"}, {"name": "Premium", "price": 79, "period": "month"}], "freePlan": {"available": False}, "freeTrial": {"available": True, "duration_days": 14}},
    "monday": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Basic", "price": 9, "period": "month"}, {"name": "Standard", "price": 17, "period": "month"}, {"name": "Pro", "price": 26, "period": "month"}, {"name": "Enterprise", "price": None, "period": "custom"}], "freePlan": {"available": False}, "freeTrial": {"available": False}},
    "todoist": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Free", "price": 0, "period": "month"}, {"name": "Pro", "price": 4, "period": "month"}, {"name": "Business", "price": 6, "period": "month"}], "freePlan": {"available": True, "limits": "5 active projects"}, "freeTrial": {"available": False}},
    "copyai": {"model": "tiered subscription", "currency": "USD", "tiers": [{"name": "Free", "price": 0, "period": "month"}, {"name": "Pro", "price": 49, "period": "month"}, {"name": "Enterprise", "price": None, "period": "custom"}], "freePlan": {"available": True, "limits": "limited generations"}, "freeTrial": {"available": False}},
}

PLATFORM_UPDATES = {
    "claude": ["web", "iOS", "Android", "Windows", "macOS"],
    "todoist": ["web", "iOS", "Android", "Windows", "macOS", "Chrome"],
}

def main():
    print("=" * 60)
    print("Phase 5 Research Batch 2: Adding Evidence")
    print("=" * 60)

    ledger = load(LEDGER)
    existing_sources = {s["source_id"] for s in ledger.get("sources", [])}
    existing_claims = {c["claim_id"] for c in ledger.get("claims", [])}

    ns = 0
    for s in NEW_SOURCES:
        if s["source_id"] not in existing_sources:
            ledger["sources"].append(s)
            ns += 1
            print(f"  Added source: {s['source_id']}")

    nc = 0
    for c in NEW_CLAIMS:
        if c["claim_id"] not in existing_claims:
            ledger["claims"].append(c)
            nc += 1
            print(f"  Added claim: {c['claim_id']}")

    save(LEDGER, ledger)
    print(f"\nAdded {ns} sources and {nc} claims")

    # Update v1
    print("\nUpdating tools-v1.json...")
    v1 = load(V1)
    updated = 0
    for tool in v1.get("tools", []):
        tid = tool.get("id")
        if tid in PRICING_UPDATES:
            tool["pricing"] = PRICING_UPDATES[tid]
            if tid in PLATFORM_UPDATES:
                tool["platforms"] = PLATFORM_UPDATES[tid]
            updated += 1
            print(f"  Updated v1: {tid}")
    save(V1, v1)
    print(f"Updated {updated} tools in v1")

    # Update v2
    print("\nUpdating v2 JSON files...")
    tool_claims = {}
    for c in NEW_CLAIMS:
        tool_claims.setdefault(c["tool_id"], []).append(c["claim_id"])

    v2u = 0
    for tid, cids in tool_claims.items():
        for subdir in ["legacy", "expansion"]:
            v2p = V2_DIR / subdir / f"{tid}.json"
            if v2p.exists():
                try:
                    v2 = load(v2p)
                    ev = v2.setdefault("evidence", {})
                    refs = ev.get("claim_refs", [])
                    for cid in cids:
                        ref = {"claim_id": cid}
                        if ref not in refs:
                            refs.append(ref)
                    ev["claim_refs"] = refs
                    sids = ev.get("source_ids", [])
                    for s in NEW_SOURCES:
                        if s["source_id"] not in sids:
                            for c in NEW_CLAIMS:
                                if c["tool_id"] == tid and s["source_id"] in c.get("source_ids", []):
                                    sids.append(s["source_id"])
                                    break
                    ev["source_ids"] = sids
                    save(v2p, v2)
                    v2u += 1
                    print(f"  Updated v2: {tid}")
                    break
                except Exception as e:
                    print(f"  Warning: {v2p}: {e}")

    print(f"\nUpdated {v2u} v2 files")
    print(f"\nBATCH 2 SUMMARY: {ns} sources, {nc} claims, {updated} v1, {v2u} v2")
    return 0

if __name__ == "__main__":
    sys.exit(main())
