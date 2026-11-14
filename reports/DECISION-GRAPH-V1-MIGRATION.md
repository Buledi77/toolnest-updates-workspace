# Decision Graph v1 Migration Report

**Date:** 14 November 2026  
**Scope:** Read-only assessment and safe migration plan. `data/tools.json` was not modified.

## Current dataset

`data/tools.json` is a 50-record extract of the homepage tools array. Its current legacy fields are:

| Legacy field | Current meaning | v2 destination |
|---|---|---|
| `id` | Primary record key and current card identity | `identity.id` and migration slug map |
| `name` | Display name | `identity.name` |
| `cat` | Display category label | `discovery.categories` after controlled taxonomy mapping |
| `h` | Card hue value | Presentation-only compatibility field; not part of the v2 factual model |
| `site` | Official website URL | `identity.official_url` and `monetization.official_non_affiliate_url` |
| `badge` | Legacy card badge | Presentation field in a future card adapter |
| `featured` | Legacy featured boolean | Editorial/presentation policy, not factual evidence |
| `best` | One-line positioning statement | Draft editorial summary; requires review before promotion |
| `pros` | Short card advantages | Editorial `best_for`/capability notes only after evidence review |
| `logo` | Site-relative logo path | `identity.logo` |
| `affiliateUrl` | Legacy affiliate URL or empty string | `monetization.affiliate_url` only after approval and revalidation |

The legacy file does not contain evidence IDs, source history, pricing context, regional availability, freshness, editorial tier, page quality, relationships, or change history. Those gaps are the reason for a shadow migration rather than an in-place replacement.

## v2 mapping

The v2 record separates the legacy card data into:

- stable identity and official URL;
- discovery taxonomy and use cases;
- evidence-backed factual claims;
- editorial fit and limitations;
- relationships;
- monetization metadata;
- publishing eligibility;
- freshness.

Legacy fields must not be copied into factual claims automatically. For example, `best` and `pros` are useful drafts but are not proof of capabilities or quality.

## Unmapped or requiring review

- `h`: keep only in a compatibility adapter if the current card renderer needs it.
- `badge`: requires a defined badge policy and should not become a trust or quality claim.
- `featured`: requires an editorial/product rule and an audit trail.
- `best` and `pros`: require evidence and editorial review before appearing in Tier A/B factual modules.
- `affiliateUrl`: requires program approval, region, restrictions, disclosure, expiry, and link checks.
- categories: require one-to-one controlled taxonomy mapping; do not infer new category slugs.
- pricing, limits, trials, integrations, availability, status, alternatives, comparisons, and freshness: missing from the legacy dataset and must be researched.

## Migration risks

1. Treating homepage card copy as verified facts.
2. Changing an existing ID or slug and breaking internal URLs.
3. Copying affiliate URLs into official destinations.
4. Generating indexable pages before quality and intent checks.
5. Losing current card presentation fields during a dual-read period.
6. Introducing inconsistent category labels or duplicate taxonomy.
7. Assuming one region's price applies globally.
8. Replacing static output before parity tests cover links, metadata, structured data, accessibility, and responsive behavior.
9. Creating evidence records without a source excerpt, billing context, or stale deadline.
10. Treating automated change detection as editorial verification.

## First safe migration batch

The first batch is intentionally the three existing Phase 2A benchmark subjects:

1. Hostinger — current premium review and official pricing/AI Builder evidence.
2. Semrush — current premium review and current SEO/AI Visibility plan evidence.
3. Moz Pro — comparison benchmark evidence; standalone review remains `in_review` and is not published by this phase.

These records exercise hosting, website-builder, SEO, AI-search, promotional pricing, annual billing, plan limits, regional caveats, editorial tiers, and a non-indexable in-review record.

## Recommended incremental path for the current 50 tools

1. Keep `data/tools.json` as the production read source.
2. Import the 50 legacy records into a temporary mapping report without publishing from it.
3. Assign stable v2 IDs and preserve a legacy-ID-to-v2-ID map.
4. Research and verify five records at a time, beginning with high-demand commercial tools.
5. Run both datasets in shadow mode and compare directory cards, official URLs, logos, categories, badges, and featured behavior.
6. Add evidence and editorial review before promoting a record to Tier B or A.
7. Render one non-public preview page from a v2 record and compare HTML, metadata, structured data, links, and mobile behavior against the existing page.
8. Switch one bounded consumer at a time, with rollback to the current static output.
9. Keep Tier C records available to internal search and recommendations without automatically creating indexable pages.
10. Only after parity and freshness metrics are stable, make v2 the generated source for selected page families.

## Exact recommendation

The read-only shadow importer is now present as `scripts/migrate_legacy_tools.py`. It generated 47 Tier C, `noindex`, non-sitemap records under `data/tools-v2/legacy/`, preserved the three benchmark records at the top level, and wrote the 50-record mapping manifest to `data/migrations/legacy-to-v2-map.json`.

Do not replace `data/tools.json` yet. The next migration decision should be based on directory parity, evidence coverage, and freshness metrics—not on record count.
