# Phase F Evidence Gap Report

**Date:** 2026-11-23
**Scope:** All 153 tools in `data/tools/`
**Purpose:** Document which fields require first-party verification before Phase F bulk verification begins.

---

## 1. Field Coverage Summary

| Field | Coverage | Tools with data | Tools missing |
|---|---|---|---|
| `editorial_tier` | 100% | 153/153 | 0 |
| `best_for` | 83.7% | 128/153 | 25 |
| `use_cases` | 83.7% | 128/153 | 25 |
| `audiences` | 54.9% | 84/153 | 69 |
| `not_recommended_for` | 48.4% | 74/153 | 79 |
| `platforms` | 39.9% | 61/153 | 92 |
| `pricing` (any) | 14.4% | 22/153 | 131 |
| `pricing.plans` | 14.4% | 22/153 | 131 |
| `pricing.sourceTier: official` | 11.1% | 17/153 | 136 |
| `freePlan` | 11.8% | 18/153 | 135 |
| `trial` | 10.5% | 16/153 | 137 |
| `claims` | 14.4% | 22/153 | 131 |
| `evidence_directory` | 9.2% | 14/153 | 139 |
| `integrations` | 0.7% | 1/153 | 152 |
| `freshness.last_checked` | 0% | 0/153 | 153 |

---

## 2. Evidence Categories

### VERIFIED_OFFICIAL (17 tools)
Tools with `sourceTier: "official"` in at least one pricing plan — pricing verified from official vendor sources.

- asana, bolt, canva, clickup, cursor, github-copilot, grammarly, heygen, hostinger, hubspot, ideogram, lovable, mailchimp, monday, notion, webflow, zapier

**Verified fields:** Monthly price, annual price, billing term, free tier existence
**Source:** Official pricing pages, documented in `data/evidence/` directories

### EDITORIAL_ASSESSMENT (13 tools)
Tools with evidence directories but no `sourceTier: "official"` — editorial research from official sources, but pricing not yet formally verified.

- activecampaign, adcreative, adobeexpress, adwisely, ahrefs, aircall, amplitude, apollo, beautifulai, mozpro, screamingfrog, semrush, surferseo

**Verified fields:** Product features, category placement, basic claims
**Missing:** Formal pricing verification with sourceTier

### RESEARCH_REQUIRED (123 tools)
Tools with no evidence directory and no official pricing verification — all commercial facts need first-party verification.

Full list: beehiiv, bill, brand24, breadbutter, brevo, browseai, callrail, campaignmonitor, capsule, castmagic, chatgpt, circle, claude, clevertap, close, closely, cloudtalk, confetti, connecteam, consensus, copyai, deel, descript, dext, dripify, elevenlabs, expertex, figma, fireflies, flexiquiz, flocksy, framer, freshbooks, freshdesk, gamma, gemini, getresponse, glide, gorgias, helpscout, hemingway, hibob, hightouch, ifttt, instantly, instapage, intercom, invideo, jasper, kapwing, keap, kit, krispcall, learnworlds, lemlist, leonardo, logome, lusha, make, manychat, meetgeek, midjourney, mixpanel, moosend, murf, n8n, netlify, notebooklm, nutshell, omnisend, omniseo, otter, pandadoc, perplexity, pipedrive, pixelunion, prowritingaid, quickbooks, quillbot, quo, removebg, replyio, rgestudio, runway, salesforce-smb, shoeboxed, simpletexting, smartlead, smartli, softr, softsync, spiky, sproutsocial, squarespace, stamped, storydoc, storylane, streak, surveymonkey, survicate, synthesia, systeme, teachable, teamwork, teikametrics, textline, thetop, tidio, timedoctor, todoist, trainual, transpond, ueni, unbounce, upfluence, upwork, windsorai, wingify, wrike, writesonic, xero, xtiles, zendesk

**All fields need verification:** Pricing, free plans, trials, plan limits, features

### DO_NOT_PUBLISH (0 tools)
No tools currently have `publishing.prepublish_status: "draft"`.

---

## 3. Fields Requiring First-Party Verification by Priority

### Critical (blocks Decision Engine accuracy)
1. **`pricing.plans[].priceMonthly`** — 131 tools missing. Decision Engine scoring depends on accurate pricing.
2. **`pricing.freePlan`** — 135 tools missing. Free plan filter is disabled until coverage improves.
3. **`pricing.trial`** — 137 tools missing. Trial availability is a key buyer decision factor.

### High (affects comparison quality)
4. **`discovery.platforms`** — 92 tools missing. Platform filter disabled until coverage improves.
5. **`editorial.not_recommended_for`** — 79 tools missing. Critical for honest comparisons.
6. **`discovery.audiences`** — 69 tools missing. Used by Overlap Checker.

### Medium (affects discoverability)
7. **`discovery.integrations`** — 152 tools missing. Only 1 tool has integration data.
8. **`freshness.last_checked`** — 153 tools missing. No freshness tracking at all.

### Low (nice to have)
9. **`claims`** — 131 tools missing. Structured claims improve trust signals.

---

## 4. Decision Engine, Stack Analyzer, Overlap Checker — Data Provenance

### Decision Engine
- **Scoring rules:** ToolNest editorial logic (use_case_match, category_match, best_for_match, platform_match)
- **Input data:** `discovery.useCaseTags`, `cat`, `editorial.best_for`, `discovery.platforms` from tool records
- **Output:** Scored recommendations — **NOT officially approved vendor data**
- **Wording:** "Score-based recommendations from your requirements" ✅ Correct

### Stack Analyzer
- **Data source:** Tool records directly, no separate config
- **Input data:** Pricing from `pricing.plans` where available
- **Output:** Cost estimates — **ToolNest editorial calculation**
- **Wording:** "Estimate costs and find overlap" ✅ Correct

### Overlap Checker
- **Data source:** Tool records
- **Input data:** `discovery.use_cases`, `discovery.audiences`, `editorial.best_for`
- **Output:** Overlap analysis — **ToolNest editorial assessment**
- **Wording:** "See if two tools share functionality before you buy both" ✅ Correct

---

## 5. Recommended Verification Priority

### Batch 1: Top 20 by category (immediate)
Focus on the highest-traffic categories first:
- Productivity (25 tools): notion, asana, clickup, todoist, monday, wrike, teamwork, etc.
- Sales (23 tools): pipedrive, hubspot, close, keap, salesforce-smb, etc.
- Marketing (21 tools): semrush, jasper, copyai, sproutsocial, etc.

### Batch 2: Tools with existing evidence directories
The 13 EDITORIAL_ASSESSMENT tools already have evidence directories — upgrade them to VERIFIED_OFFICIAL by adding `sourceTier: "official"` to pricing plans.

### Batch 3: Remaining 123 tools
Systematic verification of all RESEARCH_REQUIRED tools, starting with those in high-traffic categories.

---

## 6. Key Findings

1. **11.1% pricing verification** — Only 17 of 153 tools have officially verified pricing. This is the single largest gap.
2. **0% freshness tracking** — No tools have `freshness.last_checked`. This field needs to be populated for all tools.
3. **0.7% integration data** — Only 1 tool has integration lists. Not critical for MVP but important for comparison quality.
4. **Decision Engine filters disabled** — Platform and free plan filters are disabled due to low coverage. Fixing pricing and platform data will enable these.
5. **All interactive features correctly labeled** — Decision Engine, Stack Analyzer, and Overlap Checker are properly identified as ToolNest editorial/decision logic, not "officially approved" vendor data.
