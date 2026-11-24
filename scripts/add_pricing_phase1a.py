#!/usr/bin/env python3
"""
Add verified pricing data to the remaining 28 high-priority tools for Phase 1a.
Pricing researched from official vendor pages on 2026-11-23.
"""
import json
import os

PRICING_DATA = {
    "figma": {
        "free_plan_status": "Free Starter plan with 3 Figma files and 3 FigJam boards",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $16/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.figma.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 20,
            "freePlan": True,
            "freeLimits": "3 Figma files, 3 FigJam boards, unlimited viewers",
            "trial": "No free trial; free Starter plan serves as ongoing trial",
            "plans": [
                {"name": "Starter", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"files": 3, "figjam": 3}, "notes": "Free forever. Unlimited viewers."},
                {"name": "Professional", "priceMonthly": 16, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"files": "unlimited", "versionHistory": "30 days"}, "notes": "Per editor per month, billed annually. $20/month billed monthly."},
                {"name": "Organization", "priceMonthly": 55, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"files": "unlimited", "versionHistory": "unlimited", "features": ["SSO", "branching", "private plugins"]}, "notes": "Per editor per month, billed annually. $55/month."},
                {"name": "Enterprise", "priceMonthly": 90, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"files": "unlimited", "features": ["advanced security", "dedicated CSM"]}, "notes": "Per editor per month, billed annually."}
            ],
            "billingCaveat": "Dev seats ($12-$35) and Collab seats ($3-$5) cost less than Full seats. Prices per seat per month. Regional pricing may vary.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "elevenlabs": {
        "free_plan_status": "Free plan with 10,000 credits (about 10 minutes of speech)",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $6/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://elevenlabs.io/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 17,
            "freePlan": True,
            "freeLimits": "10,000 credits per month, no commercial use, 3 Studio projects",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"credits": 10000}, "notes": "No commercial use."},
                {"name": "Starter", "priceMonthly": 6, "priceAnnualMonthlyEquivalent": 5, "sourceTier": "official-snippet", "limits": {"credits": 30000}, "notes": "Commercial license, Instant Voice Cloning."},
                {"name": "Creator", "priceMonthly": 22, "priceAnnualMonthlyEquivalent": 18, "sourceTier": "official-snippet", "limits": {"credits": 121000}, "notes": "Professional Voice Cloning. $11 first month offer may apply."},
                {"name": "Pro", "priceMonthly": 99, "priceAnnualMonthlyEquivalent": 82, "sourceTier": "official-snippet", "limits": {"credits": 600000}, "notes": "44.1kHz PCM output via API."},
                {"name": "Scale", "priceMonthly": 299, "priceAnnualMonthlyEquivalent": 249, "sourceTier": "official-snippet", "limits": {"credits": 1800000, "seats": 3}, "notes": "Team collaboration."},
                {"name": "Business", "priceMonthly": 990, "priceAnnualMonthlyEquivalent": 825, "sourceTier": "official-snippet", "limits": {"credits": 6000000, "seats": 10}, "notes": "Low-latency TTS from 5c/minute."}
            ],
            "billingCaveat": "Annual billing is 10 months, not 12 (effectively 2 months free). Credits shared across products. Voice agents billed separately in call minutes.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "kapwing": {
        "free_plan_status": "Free plan with watermark, 720p export, 10 AI credits",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $16/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.kapwing.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 33,
            "freePlan": True,
            "freeLimits": "10 AI credits, 720p export with watermark, videos up to 4 minutes, 5 GB storage",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"credits": 10, "resolution": "720p", "watermark": True}, "notes": "Watermark on every export."},
                {"name": "Pro", "priceMonthly": 24, "priceAnnualMonthlyEquivalent": 16, "sourceTier": "official-snippet", "limits": {"credits": 1000, "resolution": "4K", "storage": "200 GB"}, "notes": "Per member. No watermark."},
                {"name": "Business", "priceMonthly": 64, "priceAnnualMonthlyEquivalent": 50, "sourceTier": "official-snippet", "limits": {"credits": 4000, "resolution": "4K", "storage": "800 GB", "features": ["voice clones", "lip sync"]}, "notes": "Per member."}
            ],
            "billingCaveat": "Monthly credits reset on the first of the month without rolling over. Enterprise is custom priced.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "kit": {
        "free_plan_status": "Free plan for up to 10,000 contacts with unlimited emails",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $39/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://kit.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 17,
            "freePlan": True,
            "freeLimits": "Up to 10,000 contacts, unlimited broadcasts, landing pages",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"contacts": 10000}, "notes": "Unlimited broadcasts. No automations or integrations."},
                {"name": "Creator", "priceMonthly": 39, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"contacts": 1000}, "notes": "Scales with contacts. $89 at 5,000 contacts. $139 at 10,000 contacts."},
                {"name": "Pro", "priceMonthly": 79, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"contacts": 1000, "features": ["Subscriber Signals", "engagement scoring"]}, "notes": "Scales with contacts. $189 at 10,000 contacts."}
            ],
            "billingCaveat": "Pricing scales with subscriber count. Annual billing saves 17%. 0% take rate on paid subscriptions; only Stripe processing fees apply.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "beehiiv": {
        "free_plan_status": "Free plan for up to 2,500 subscribers with unlimited sends",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $49/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.beehiiv.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 17,
            "freePlan": True,
            "freeLimits": "Up to 2,500 subscribers, unlimited sends, 1 team seat, 1 publication",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"subscribers": 2500}, "notes": "No paid subscriptions or ad network."},
                {"name": "Lite", "priceMonthly": 59, "priceAnnualMonthlyEquivalent": 49, "sourceTier": "official-snippet", "limits": {"subscribers": 100000, "seats": 2}, "notes": "Paid subscriptions with 0% take rate. Scales with subscribers."},
                {"name": "Pro", "priceMonthly": 109, "priceAnnualMonthlyEquivalent": 95, "sourceTier": "official-snippet", "limits": {"subscribers": 250000, "seats": 10}, "notes": "Branding removal, dynamic content. Scales with subscribers."}
            ],
            "billingCaveat": "Pricing scales with subscriber count. 0% take rate on paid subscriptions; only Stripe processing fees. Enterprise is custom.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "brevo": {
        "free_plan_status": "Free plan with 300 emails per day, up to 100,000 contacts",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $9/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.brevo.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 10,
            "freePlan": True,
            "freeLimits": "300 emails per day, up to 100,000 contacts, Brevo branding",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"emails": "300/day", "contacts": 100000}, "notes": "Brevo branding on emails."},
                {"name": "Starter", "priceMonthly": 9, "priceAnnualMonthlyEquivalent": 8, "sourceTier": "official-snippet", "limits": {"emails": 5000, "contacts": 500}, "notes": "No daily limit. Scales with email volume."},
                {"name": "Standard", "priceMonthly": 18, "priceAnnualMonthlyEquivalent": 16, "sourceTier": "official-snippet", "limits": {"emails": 5000, "features": ["automation", "A/B testing"]}, "notes": "Scales with email volume. $65 at 20,000 emails."},
                {"name": "Professional", "priceMonthly": 499, "priceAnnualMonthlyEquivalent": 449, "sourceTier": "official-snippet", "limits": {"emails": 150000, "features": ["WhatsApp", "phone support"]}, "notes": "High-volume senders."}
            ],
            "billingCaveat": "Pricing based on email send volume, not contacts. SMS and WhatsApp billed separately. Nonprofit discount available.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "descript": {
        "free_plan_status": "Free plan with 60 media minutes per month, watermarked exports",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $16/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.descript.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 33,
            "freePlan": True,
            "freeLimits": "60 media minutes per month, 100 one-time AI credits, 720p watermarked export, 5 GB storage",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"mediaMinutes": 60, "aiCredits": 100, "storage": "5 GB"}, "notes": "Watermarked 720p export."},
                {"name": "Hobbyist", "priceMonthly": 24, "priceAnnualMonthlyEquivalent": 16, "sourceTier": "official-snippet", "limits": {"mediaHours": 10, "aiCredits": 400, "storage": "100 GB"}, "notes": "Per editor. 1080p no watermark."},
                {"name": "Creator", "priceMonthly": 35, "priceAnnualMonthlyEquivalent": 24, "sourceTier": "official-snippet", "limits": {"mediaHours": 30, "aiCredits": 800, "storage": "1 TB", "seats": 3}, "notes": "Per editor. 4K export."},
                {"name": "Business", "priceMonthly": 65, "priceAnnualMonthlyEquivalent": 50, "sourceTier": "official-snippet", "limits": {"mediaHours": 40, "aiCredits": 1500, "storage": "2 TB", "seats": 5}, "notes": "Per editor. Brand Studio, translation proofreading."}
            ],
            "billingCaveat": "Media minutes and AI credits reset monthly without rolling over. Enterprise is custom priced.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "intercom": {
        "free_plan_status": "No free plan; 14-day free trial available",
        "trial_status": "14-day free trial, no credit card required",
        "pricing_status": "Paid — subscriptions from $29/seat/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.intercom.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 25,
            "freePlan": False,
            "trial": "14-day free trial, no credit card required",
            "plans": [
                {"name": "Essential", "priceMonthly": 39, "priceAnnualMonthlyEquivalent": 29, "sourceTier": "official-snippet", "limits": {"features": ["Fin AI Agent", "messenger", "shared inbox"]}, "notes": "Per seat per month. No Lite seats included."},
                {"name": "Advanced", "priceMonthly": 99, "priceAnnualMonthlyEquivalent": 85, "sourceTier": "official-snippet", "limits": {"features": ["workflows", "round-robin", "private help center"], "liteSeats": 20}, "notes": "Per seat per month. 20 free Lite seats."},
                {"name": "Expert", "priceMonthly": 139, "priceAnnualMonthlyEquivalent": 132, "sourceTier": "official-snippet", "limits": {"features": ["SSO", "HIPAA", "SLAs"], "liteSeats": 50}, "notes": "Per seat per month. 50 free Lite seats."}
            ],
            "billingCaveat": "Fin AI Agent costs $0.99 per outcome on every plan, billed separately. Early Stage startup program available at $33/month for Advanced with 2 seats.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "helpscout": {
        "free_plan_status": "Free plan for up to 5 users, 100 contacts per month",
        "trial_status": "15-day free trial on paid plans, no credit card required",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $25/user/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.helpscout.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 16,
            "freePlan": True,
            "freeLimits": "Up to 5 users, 1 inbox, 1 Docs site, 100 contacts per month",
            "trial": "15-day free trial on paid plans, no credit card required",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"users": 5, "contacts": 100}, "notes": "1 inbox, 1 Docs site."},
                {"name": "Standard", "priceMonthly": 30, "priceAnnualMonthlyEquivalent": 25, "sourceTier": "official-snippet", "limits": {"users": 25, "contacts": "unlimited"}, "notes": "Per user per month. 2 inboxes, 2 Docs sites."},
                {"name": "Plus", "priceMonthly": 54, "priceAnnualMonthlyEquivalent": 45, "sourceTier": "official-snippet", "limits": {"users": 50, "contacts": "unlimited", "lightUsers": 5}, "notes": "Per user per month. 5 inboxes, 3 Docs sites."},
                {"name": "Pro", "priceMonthly": 90, "priceAnnualMonthlyEquivalent": 75, "sourceTier": "official-snippet", "limits": {"users": "unlimited", "minUsers": 10, "contacts": "unlimited", "lightUsers": 15}, "notes": "Per user per month. SSO, HIPAA, dedicated onboarding."}
            ],
            "billingCaveat": "AI Answers (Envoy) costs $0.75 per resolution on every paid plan, billed separately. Nonprofit discount of 10% available.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "make": {
        "free_plan_status": "Free plan with 1,000 credits per month, 2 active scenarios",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $9/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.make.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 15,
            "freePlan": True,
            "freeLimits": "1,000 credits per month, 2 active scenarios, 15-minute minimum interval",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"credits": 1000, "scenarios": 2}, "notes": "15-minute minimum interval, 5-minute max run time."},
                {"name": "Core", "priceMonthly": 10, "priceAnnualMonthlyEquivalent": 9, "sourceTier": "official-snippet", "limits": {"credits": 10000, "scenarios": "unlimited"}, "notes": "1-minute scheduling, 40-minute max run time."},
                {"name": "Pro", "priceMonthly": 19, "priceAnnualMonthlyEquivalent": 16, "sourceTier": "official-snippet", "limits": {"credits": 10000, "scenarios": "unlimited", "features": ["priority execution"]}, "notes": "Custom variables, full-text log search."},
                {"name": "Teams", "priceMonthly": 34, "priceAnnualMonthlyEquivalent": 29, "sourceTier": "official-snippet", "limits": {"credits": 10000, "scenarios": "unlimited", "features": ["teams", "team roles"]}, "notes": "Shareable scenario templates."}
            ],
            "billingCaveat": "Credits are the same across Core, Pro, and Teams at entry tier — you pay for capability, not volume. Enterprise is custom priced.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "n8n": {
        "free_plan_status": "Free Community Edition, self-hosted with unlimited executions",
        "trial_status": "No free trial for cloud; Community Edition is free self-hosted",
        "pricing_status": "Freemium — free self-hosted tier plus cloud subscriptions from $20/month",
        "pricing_regions": ["EU", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://n8n.io/pricing"],
            "currency": "EUR",
            "billingBasis": "monthly",
            "annualDiscount": 17,
            "freePlan": True,
            "freeLimits": "Community Edition: self-hosted, unlimited executions, you pay for your own server",
            "trial": "No free trial for cloud; Community Edition is free self-hosted",
            "plans": [
                {"name": "Community Edition", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"executions": "unlimited", "hosting": "self-hosted"}, "notes": "Source-available. You run and maintain it."},
                {"name": "Starter", "priceMonthly": 24, "priceAnnualMonthlyEquivalent": 20, "sourceTier": "official-snippet", "limits": {"executions": 2500, "concurrency": 5}, "notes": "n8n Cloud. 1 shared project."},
                {"name": "Pro", "priceMonthly": 60, "priceAnnualMonthlyEquivalent": 50, "sourceTier": "official-snippet", "limits": {"executions": 10000, "concurrency": 20}, "notes": "n8n Cloud. 3 shared projects, admin roles."},
                {"name": "Business", "priceMonthly": 800, "priceAnnualMonthlyEquivalent": 667, "sourceTier": "official-snippet", "limits": {"executions": 40000, "concurrency": 30}, "notes": "Self-hosted. SSO, LDAP, environments."}
            ],
            "billingCaveat": "Prices in EUR. One execution = one workflow run regardless of steps. Overage billed at API rates. Enterprise is custom.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "framer": {
        "free_plan_status": "Free plan with Framer subdomain, 1 GB bandwidth",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $10/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.framer.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 33,
            "freePlan": True,
            "freeLimits": "Framer subdomain, 1 GB bandwidth, 500 one-time AI credits",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"bandwidth": "1 GB", "aiCredits": 500}, "notes": "Non-commercial use. Framer subdomain only."},
                {"name": "Basic", "priceMonthly": 15, "priceAnnualMonthlyEquivalent": 10, "sourceTier": "official-snippet", "limits": {"pages": 30, "cmsCollections": 2, "bandwidth": "50 GB", "aiCredits": 1000}, "notes": "Custom domain, first year free on yearly."},
                {"name": "Pro", "priceMonthly": 45, "priceAnnualMonthlyEquivalent": 30, "sourceTier": "official-snippet", "limits": {"pages": 150, "cmsCollections": 10, "bandwidth": "100 GB", "aiCredits": 3000}, "notes": "Staging, redirects, branching. Per site."}
            ],
            "billingCaveat": "Additional editors cost $20/month each. A/B testing (Convert) is a separate add-on. Enterprise is custom.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "invideo": {
        "free_plan_status": "Free plan available with limited credits and watermark",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $10/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://invideo.io/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 50,
            "freePlan": True,
            "freeLimits": "Limited credits, watermarked exports",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Starter", "priceMonthly": 20, "priceAnnualMonthlyEquivalent": 10, "sourceTier": "official-snippet", "limits": {"credits": 400}, "notes": "Per seat. Seedance 2.0 Fast and Mini only."},
                {"name": "Plus", "priceMonthly": 60, "priceAnnualMonthlyEquivalent": 30, "sourceTier": "official-snippet", "limits": {"credits": 2000}, "notes": "Per seat. All frontier agents, Seedance 2.5 at 1080p."},
                {"name": "Max", "priceMonthly": 150, "priceAnnualMonthlyEquivalent": 75, "sourceTier": "official-snippet", "limits": {"credits": "5000-15000"}, "notes": "Per seat. All models and features."}
            ],
            "billingCaveat": "Unused credits do not roll over. Video models billed per second, so long or 4K clips burn credits fast. Team plans also available from $65/seat/month.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "jasper": {
        "free_plan_status": "No free plan; 7-day free trial available",
        "trial_status": "7-day free trial of Pro plan",
        "pricing_status": "Paid — subscriptions from $59/seat/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.jasper.ai/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 15,
            "freePlan": False,
            "trial": "7-day free trial of Pro plan",
            "plans": [
                {"name": "Pro", "priceMonthly": 69, "priceAnnualMonthlyEquivalent": 59, "sourceTier": "official-snippet", "limits": {"seats": 1, "brandVoices": 2, "knowledgeAssets": 5}, "notes": "Per seat. Unlimited word output. 1 seat included."},
                {"name": "Business", "priceMonthly": None, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"seats": "custom", "brandVoices": "unlimited"}, "notes": "Custom quote. 12-month commitment. API access, custom agents."}
            ],
            "billingCaveat": "Pro includes exactly 1 seat. Additional seats require custom Business pricing. GEO agents draw credits on top of seat pricing.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "fireflies": {
        "free_plan_status": "Free plan with unlimited transcription, 400 minutes storage per team",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $10/user/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://fireflies.ai/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 44,
            "freePlan": True,
            "freeLimits": "Unlimited transcription, 400 minutes storage per team, 20 AI credits",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"storage": "400 min per team", "aiCredits": 20}, "notes": "Unlimited transcription. 2-hour max recording."},
                {"name": "Pro", "priceMonthly": 18, "priceAnnualMonthlyEquivalent": 10, "sourceTier": "official-snippet", "limits": {"storage": "8000 min per seat", "aiCredits": 20}, "notes": "Per seat. Video recording, downloads."},
                {"name": "Business", "priceMonthly": 29, "priceAnnualMonthlyEquivalent": 19, "sourceTier": "official-snippet", "limits": {"storage": "unlimited", "aiCredits": 30}, "notes": "Per seat. Team analytics, conversation intelligence."},
                {"name": "Enterprise", "priceMonthly": 39, "priceAnnualMonthlyEquivalent": 39, "sourceTier": "official-snippet", "limits": {"storage": "unlimited", "aiCredits": 50}, "notes": "Per seat. Annual billing only. SSO, HIPAA, audit logs."}
            ],
            "billingCaveat": "Annual billing saves 44% on Pro and Business. Enterprise is annual only. Extra AI credits available from $5/month for 50.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "instantly": {
        "free_plan_status": "No free plan; 14-day free trial available",
        "trial_status": "14-day free trial",
        "pricing_status": "Paid — subscriptions from $47/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://instantly.ai/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 20,
            "freePlan": False,
            "trial": "14-day free trial",
            "plans": [
                {"name": "Growth", "priceMonthly": 47, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"contacts": 1000, "emails": 5000, "mailboxes": "unlimited"}, "notes": "Warm-up included."},
                {"name": "Hypergrowth", "priceMonthly": 97, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"contacts": 25000, "emails": 100000, "mailboxes": "unlimited"}, "notes": "AI Unibox, advanced analytics."},
                {"name": "Light Speed", "priceMonthly": 358, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"contacts": 100000, "emails": 500000, "mailboxes": "unlimited"}, "notes": "SISR, dedicated success manager, API access."}
            ],
            "billingCaveat": "Unlimited mailboxes on every tier. Lead database credits cost extra. Yearly billing saves 20%. Contact cap does not reset monthly.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "surveymonkey": {
        "free_plan_status": "Free Basic plan with 10 questions per survey, limited responses",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $25/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.surveymonkey.com/pricing/"],
            "currency": "USD",
            "billingBasis": "annual",
            "freePlan": True,
            "freeLimits": "10 questions per survey, limited viewable responses, no data export",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Basic", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"questions": 10}, "notes": "Limited responses per survey. No data export."},
                {"name": "Standard Monthly", "priceMonthly": 149, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"responses": 1000}, "notes": "Monthly billing only. 1,000 responses/month."},
                {"name": "Advantage Annual", "priceMonthly": 39, "priceAnnualMonthlyEquivalent": 39, "sourceTier": "official-snippet", "limits": {"responses": 15000}, "notes": "Annual billing only. $468/year. 15,000 responses/year."},
                {"name": "Premier Annual", "priceMonthly": 139, "priceAnnualMonthlyEquivalent": 139, "sourceTier": "official-snippet", "limits": {"responses": 40000}, "notes": "Annual billing only. $1,668/year. Crosstabs, advanced logic."},
                {"name": "Team Advantage", "priceMonthly": 30, "priceAnnualMonthlyEquivalent": 30, "sourceTier": "official-snippet", "limits": {"responses": 50000, "minUsers": 3}, "notes": "Per user per month, annual billing. 50,000 responses/year."}
            ],
            "billingCaveat": "Overage is $0.15 per extra response. Audience panel responses cost extra. Team plans require 3+ users. Most individual plans are annual only.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "aircall": {
        "free_plan_status": "No free plan; 7-day free trial available",
        "trial_status": "7-day free trial",
        "pricing_status": "Paid — subscriptions from $30/license/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://aircall.io/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 25,
            "freePlan": False,
            "trial": "7-day free trial",
            "plans": [
                {"name": "Essentials", "priceMonthly": 40, "priceAnnualMonthlyEquivalent": 30, "sourceTier": "official-snippet", "limits": {"minLicenses": 3, "features": ["IVR", "call recording", "SMS"]}, "notes": "Per license per month. 1 number included."},
                {"name": "Professional", "priceMonthly": 70, "priceAnnualMonthlyEquivalent": 50, "sourceTier": "official-snippet", "limits": {"minLicenses": 3, "features": ["Power Dialer", "voicemail drop", "Salesforce"]}, "notes": "Per license per month."}
            ],
            "billingCaveat": "3-license minimum on both plans. Extra numbers $6/month each. AI Assist Pro $49/seat/month. AI Voice Agent $0.29/minute. Enterprise is custom, 25+ licenses.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "copyai": {
        "free_plan_status": "No free plan (previously available, now sunset)",
        "trial_status": "No free trial",
        "pricing_status": "Paid — subscriptions from $24/month for 5 seats",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.copy.ai/prices"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 17,
            "freePlan": False,
            "trial": "No free trial",
            "plans": [
                {"name": "Chat", "priceMonthly": 29, "priceAnnualMonthlyEquivalent": 24, "sourceTier": "official-snippet", "limits": {"seats": 5}, "notes": "Unlimited words in Chat. 5 seats included."},
                {"name": "Growth", "priceMonthly": 1000, "priceAnnualMonthlyEquivalent": 1000, "sourceTier": "official-snippet", "limits": {"seats": 75, "workflowCredits": 20000}, "notes": "Annual billing only. Workflow automation."},
                {"name": "Expansion", "priceMonthly": 2000, "priceAnnualMonthlyEquivalent": 2000, "sourceTier": "official-snippet", "limits": {"seats": 150, "workflowCredits": 45000}, "notes": "Annual billing only."},
                {"name": "Scale", "priceMonthly": 3000, "priceAnnualMonthlyEquivalent": 3000, "sourceTier": "official-snippet", "limits": {"seats": 200, "workflowCredits": 75000}, "notes": "Annual billing only."}
            ],
            "billingCaveat": "Chat plan covers 5 seats for $24/month annually. Growth and above are annual-only. Enterprise is custom.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "hemingway": {
        "free_plan_status": "Free web editor with core readability features",
        "trial_status": "14-day free trial of Editor Plus, no credit card required",
        "pricing_status": "Freemium — free web editor plus paid subscriptions from $8.33/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://hemingwayapp.com/hemingway-editor-plus"],
            "currency": "USD",
            "billingBasis": "annual",
            "freePlan": True,
            "freeLimits": "Free web editor with readability analysis, color-coded highlights, grade level assessment",
            "trial": "14-day free trial of Editor Plus, no credit card required",
            "plans": [
                {"name": "Free Web", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {}, "notes": "Core editing features only. No AI."},
                {"name": "Classic Desktop", "priceMonthly": None, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {}, "notes": "$19.99 one-time purchase. Mac and Windows. No AI features."},
                {"name": "Individual 5K", "priceMonthly": 100, "priceAnnualMonthlyEquivalent": 100, "sourceTier": "official-snippet", "limits": {"aiSentences": 5000}, "notes": "$100 billed annually. 5,000 AI sentences per month."},
                {"name": "Individual 10K", "priceMonthly": 150, "priceAnnualMonthlyEquivalent": 150, "sourceTier": "official-snippet", "limits": {"aiSentences": 10000}, "notes": "$150 billed annually. 10,000 AI sentences per month."},
                {"name": "Team 10K", "priceMonthly": 150, "priceAnnualMonthlyEquivalent": 150, "sourceTier": "official-snippet", "limits": {"aiSentences": 10000, "seats": 50}, "notes": "$150 per seat billed annually. Up to 50 seats."}
            ],
            "billingCaveat": "Editor Plus is annual billing only. Classic desktop is a one-time $19.99 purchase. Enterprise is custom.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "adobeexpress": {
        "free_plan_status": "Free plan with basic design features and templates",
        "trial_status": "7-day free trial of Premium",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $9.99/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.adobe.com/express/pricing.html"],
            "currency": "USD",
            "billingBasis": "monthly",
            "freePlan": True,
            "freeLimits": "Basic templates, limited premium features, Adobe branding",
            "trial": "7-day free trial of Premium",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {}, "notes": "Basic templates and features."},
                {"name": "Premium", "priceMonthly": 9.99, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {}, "notes": "Premium templates, brand kit, background removal, bulk resize."},
                {"name": "Teams", "priceMonthly": 7.99, "priceAnnualMonthlyEquivalent": 4.99, "sourceTier": "official-snippet", "limits": {"minLicenses": 2}, "notes": "Per license per month. $4.99 first year, then $7.99. Admin console."}
            ],
            "billingCaveat": "Teams requires annual commitment with 2-license minimum. First-year discount of $4.99/license, then $7.99. Enterprise is custom.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "cloudtalk": {
        "free_plan_status": "No free plan; 14-day free trial available",
        "trial_status": "14-day free trial on Expert features",
        "pricing_status": "Paid — subscriptions from $25/user/month",
        "pricing_regions": ["EU", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.cloudtalk.io/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 30,
            "freePlan": False,
            "trial": "14-day free trial on Expert features",
            "plans": [
                {"name": "Starter", "priceMonthly": 34, "priceAnnualMonthlyEquivalent": 25, "sourceTier": "official-snippet", "limits": {"features": ["click to call", "call flow builder", "queues"]}, "notes": "Per user per month. 1 free number."},
                {"name": "Essential", "priceMonthly": 39, "priceAnnualMonthlyEquivalent": 29, "sourceTier": "official-snippet", "limits": {"features": ["IVR", "skills-based routing", "CRM integrations"]}, "notes": "Per user per month."},
                {"name": "Expert", "priceMonthly": 69, "priceAnnualMonthlyEquivalent": 49, "sourceTier": "official-snippet", "limits": {"minLicenses": 3, "features": ["AI Sales Dialer", "live monitoring", "Salesforce"]}, "notes": "Per user per month. Power mode included."}
            ],
            "billingCaveat": "AI Sales Dialer Power mode is $15/user add-on on Starter/Essential. Parallel dialer $39/user. AI conversation intelligence $9/user. Prices shown in EUR on vendor page.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "castmagic": {
        "free_plan_status": "No free plan; free trial available",
        "trial_status": "Free trial available",
        "pricing_status": "Paid — subscriptions from $19/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://castmagic.io/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 33,
            "freePlan": False,
            "trial": "Free trial available",
            "plans": [
                {"name": "Hobby", "priceMonthly": 29, "priceAnnualMonthlyEquivalent": 19, "sourceTier": "official-snippet", "limits": {"transcribedHours": 30, "spaces": 3, "storage": "50 GB"}, "notes": "Solo creators. Library total."},
                {"name": "Starter", "priceMonthly": 69, "priceAnnualMonthlyEquivalent": 48, "sourceTier": "official-snippet", "limits": {"transcribedHours": 100, "spaces": 10, "storage": "250 GB"}, "notes": "API access included. Onboarding call."},
                {"name": "Team", "priceMonthly": 199, "priceAnnualMonthlyEquivalent": 139, "sourceTier": "official-snippet", "limits": {"transcribedHours": 400, "spaces": 25, "storage": "1 TB", "seats": 5}, "notes": "Priority support. Unlimited team size."}
            ],
            "billingCaveat": "Annual billing saves 33%. Business and Scale plans start from $699/month. Additional seats $159/year each on Team.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "omnisend": {
        "free_plan_status": "Free plan with 250 contacts and 500 emails per month",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $16/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.omnisend.com/pricing/"],
            "currency": "USD",
            "billingBasis": "monthly",
            "freePlan": True,
            "freeLimits": "250 contacts, 500 emails per month, 500 web push messages",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"contacts": 250, "emails": 500}, "notes": "Omnisend branding on emails."},
                {"name": "Standard", "priceMonthly": 16, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"contacts": 500, "emails": "12x contacts"}, "notes": "Scales with contacts. $132 at 10,000 contacts."},
                {"name": "Pro", "priceMonthly": 59, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"contacts": 2500, "emails": "unlimited"}, "notes": "Scales with contacts. SMS credits sold separately."}
            ],
            "billingCaveat": "Pricing scales with contact count. SMS credits from $0.007/SMS at volume. No annual billing option for Standard/Pro.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "glide": {
        "free_plan_status": "Free plan with unlimited drafts, 2 team members",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $19/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.glideapps.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 24,
            "freePlan": True,
            "freeLimits": "Unlimited drafts, 2 team members, cannot publish",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"members": 2}, "notes": "Unlimited drafts. Cannot publish."},
                {"name": "Explorer", "priceMonthly": 25, "priceAnnualMonthlyEquivalent": 19, "sourceTier": "official-snippet", "limits": {"apps": 1, "users": 100}, "notes": "1 published app. 100 personal users."},
                {"name": "Maker", "priceMonthly": 60, "priceAnnualMonthlyEquivalent": 49, "sourceTier": "official-snippet", "limits": {"apps": 3, "users": "unlimited"}, "notes": "Custom domains, Google Sheets. Personal users only."},
                {"name": "Business", "priceMonthly": 249, "priceAnnualMonthlyEquivalent": 199, "sourceTier": "official-snippet", "limits": {"apps": "unlimited", "users": 30}, "notes": "Unlimited apps. Work email sign-ins."}
            ],
            "billingCaveat": "Update overages cost $0.02 each. Enterprise is custom. Maker is personal-email users only; Business needed for work emails.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "ifttt": {
        "free_plan_status": "Free plan with 1,000 credits per month",
        "trial_status": "No free trial; free plan serves as ongoing trial",
        "pricing_status": "Freemium — free tier plus paid subscriptions from $2/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://ifttt.com/plans"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 30,
            "freePlan": True,
            "freeLimits": "1,000 credits per month, standard speed",
            "trial": "No free trial; free plan serves as ongoing trial",
            "plans": [
                {"name": "Free", "priceMonthly": 0, "priceAnnualMonthlyEquivalent": None, "sourceTier": "official-snippet", "limits": {"credits": 1000}, "notes": "Standard speed. Unlimited applets."},
                {"name": "Starter", "priceMonthly": 3, "priceAnnualMonthlyEquivalent": 2, "sourceTier": "official-snippet", "limits": {"credits": 5000}, "notes": "Faster execution speed."},
                {"name": "Pro", "priceMonthly": 8, "priceAnnualMonthlyEquivalent": 5, "sourceTier": "official-snippet", "limits": {"credits": 20000}, "notes": "Even faster execution."},
                {"name": "Pro+", "priceMonthly": 20, "priceAnnualMonthlyEquivalent": 14, "sourceTier": "official-snippet", "limits": {"credits": 100000}, "notes": "AI services, filter code, multiple accounts."}
            ],
            "billingCaveat": "Annual billing saves 30%. Credits reset monthly. Speed increases with each tier.",
            "conflicts": [],
            "changeLog": []
        }
    },
    "krispcall": {
        "free_plan_status": "No free plan",
        "trial_status": "No free trial",
        "pricing_status": "Paid — subscriptions from $12/user/month",
        "pricing_regions": ["US", "Global"],
        "pricing": {
            "checkedOn": "2026-11-23",
            "sourceUrls": ["https://www.krispcall.com/pricing"],
            "currency": "USD",
            "billingBasis": "monthly",
            "annualDiscount": 20,
            "freePlan": False,
            "trial": "No free trial",
            "plans": [
                {"name": "Starter", "priceMonthly": 15, "priceAnnualMonthlyEquivalent": 12, "sourceTier": "official-snippet", "limits": {"users": 5, "numbers": 1}, "notes": "Per user per month. 1 free number. Unlimited calling to 100+ countries."},
                {"name": "Advance", "priceMonthly": 40, "priceAnnualMonthlyEquivalent": 32, "sourceTier": "official-snippet", "limits": {"users": "unlimited", "features": ["Power Dialer", "bulk SMS", "call recording"]}, "notes": "Per user per month."},
                {"name": "Max", "priceMonthly": 60, "priceAnnualMonthlyEquivalent": 48, "sourceTier": "official-snippet", "limits": {"users": "unlimited", "features": ["unlimited calling", "1000 SMS segments"]}, "notes": "Per user per month. Shared usage pools."}
            ],
            "billingCaveat": "Prices cover platform and one number. Call minutes and SMS billed separately by the minute. Enterprise is custom.",
            "conflicts": [],
            "changeLog": []
        }
    },
}

def update_tool(slug, data):
    path = f"data/tools/{slug}.json"
    if not os.path.exists(path):
        print(f"  SKIP: {path} not found")
        return False
    
    with open(path) as f:
        tool = json.load(f)
    
    # Update factual_profile fields
    fp = tool.setdefault("factual_profile", {})
    for key in ["free_plan_status", "trial_status", "pricing_status", "pricing_regions"]:
        if key in data:
            fp[key] = data[key]
    
    # Add pricing section
    if "pricing" in data:
        tool["pricing"] = data["pricing"]
    
    # Update freshness
    fresh = tool.setdefault("freshness", {})
    fresh["updated_at"] = "2026-11-23T20:00:00Z"
    fresh["last_verified_at"] = "2026-11-23T20:00:00Z"
    
    with open(path, "w") as f:
        json.dump(tool, f, indent=2)
        f.write("\n")
    
    print(f"  OK: {slug}")
    return True

if __name__ == "__main__":
    print(f"Updating {len(PRICING_DATA)} tools with pricing data...")
    count = 0
    for slug, data in PRICING_DATA.items():
        if update_tool(slug, data):
            count += 1
    print(f"\nDone: {count}/{len(PRICING_DATA)} tools updated.")
