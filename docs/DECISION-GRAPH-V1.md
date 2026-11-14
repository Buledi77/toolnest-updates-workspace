# ToolNest Decision Graph v1

## Purpose

Decision Graph v1 is the structured foundation for scaling ToolNest beyond manually maintained static records. It separates:

- **identity and discovery:** what a tool is and how users find it;
- **factual profile:** claims that require evidence;
- **editorial judgment:** fit, limitations, and page quality;
- **relationships:** alternatives, comparisons, and workflow edges;
- **monetization:** affiliate metadata kept outside editorial ranking;
- **publishing:** visibility and indexation decisions;
- **freshness:** verification dates and review scheduling.

The v2 records are additive. `data/tools.json` remains the current production dataset and is not replaced by this phase.

## Files

- `data/schemas/toolnest-tool.schema.json` — one Decision Graph tool record.
- `data/schemas/evidence-ledger.schema.json` — source and claim contract.
- `data/schemas/tool-change-ledger.schema.json` — append-only change-event contract.
- `data/evidence/evidence-ledger.json` — current evidence for the three benchmark records.
- `data/changes/tool-change-ledger.json` — intentionally empty until a change is actually observed and verified.
- `data/tools-v2/*.json` — benchmark records for Hostinger, Semrush, and Moz Pro.
- `data/tools-v2/legacy/*.json` — non-indexable Tier C shadow records generated from the current 47 non-benchmark legacy records.
- `data/migrations/legacy-to-v2-map.json` — reproducible mapping for all 50 legacy records.
- `scripts/migrate_legacy_tools.py` — read-only-source migration generator.
- `scripts/validate_decision_graph.py` — record, relationship, publishing, and schema-metadata checks.
- `scripts/validate_evidence_ledger.py` — source, claim, date, currency, and reference checks.
- `scripts/check_freshness.py` — stale evidence and overdue review checks.
- `scripts/check_affiliate_separation.py` — official URL and editorial/affiliate separation checks.
- `data/taxonomy/taxonomy-v1.json` — canonical category, job, platform, and audience vocabulary.
- `data/recommendations/task-catalog.json` — explicit task-to-tool recommendation mappings.
- `data/indexes/tool-search-index.json` — deterministic shadow search index generated from v2 records.
- `data/monetization/affiliate-registry.json` — centralized affiliate metadata independent from editorial fields.
- `data/publishing/page-intents.json` — explicit published URL/page-intent registry.
- `scripts/validate_taxonomy.py` — controlled vocabulary and task-catalog checks.
- `scripts/build_search_index.py` — normalized search-index generator.
- `scripts/recommend_tasks.py` — task-first recommendation adapter.
- `scripts/check_legacy_parity.py` — legacy identity/migration parity check.
- `scripts/check_publishability.py` — tier/indexability/publishing checks.
- `scripts/check_site_quality.py` — read-only local link, asset, canonical, sitemap, and encoding checks.
- `scripts/build_affiliate_registry.py` — centralized affiliate registry generator.
- `scripts/check_affiliate_registry.py` — affiliate separation and completeness checks.
- `scripts/check_publishing_registry.py` — page-intent, canonical, and sitemap alignment checks.

## Record contract

### Identity

`identity.id` is the stable internal key. `identity.slug` is the stable URL-oriented identifier. `official_url` is always the non-affiliate vendor destination. A status such as `discontinued` or `acquired` is data, not a deletion instruction.

### Discovery

Discovery fields contain controlled categories, user jobs, audiences, platforms, integrations, and tags. They are not evidence of product quality or popularity.

### Factual profile

Facts are represented by claim references. The human-readable summary and purpose are intentionally short; detailed claims belong in the evidence ledger. Pricing, plan limits, free access, trials, regional availability, capabilities, and limitations must be evidence-backed or omitted/marked for review.

### Editorial

Editorial fields are a judgment layer:

- **Tier A:** premium, evidence-backed decision page;
- **Tier B:** verified factual profile;
- **Tier C:** directory-only record.

`best_for`, `not_recommended_for`, and `editorial_summary` are not vendor facts. They are ToolNest judgments and need an editorial owner and review date. They must not contain affiliate language or imply hands-on testing that did not occur.

### Relationships

Relationships use stable tool IDs for alternatives and workflow edges. Comparison identifiers refer to existing or future page identities and are not treated as tool records. A relationship must be meaningful; bulk linking every tool to every other tool is prohibited.

### Evidence

Each claim has:

- a unique `claim_id`;
- owning `tool_id`;
- field path;
- claim type;
- value;
- one or more source IDs;
- access and verification dates;
- region, currency, and billing context when relevant;
- an excerpt or evidence note;
- `stale_after`;
- a status: `verified`, `needs_review`, `stale`, or `disputed`.

The source record identifies the URL, source type, publisher, official status, and source history. Multiple claims may use one source, and one claim may use multiple sources.

Pricing claims must include currency and billing context. A promotional monthly equivalent must not be stored as an ordinary month-to-month price.

### Monetization

`official_non_affiliate_url` is the canonical vendor destination. `affiliate_url` is optional and is never the source of a factual claim. Affiliate status, network, geography, restrictions, disclosure, and link-check date are operational fields only.

An affiliate record cannot:

- alter an editorial tier;
- create a `best_for` judgment;
- remove a limitation;
- change search ranking;
- replace the official URL.

### Publishing and freshness

`indexability` and `sitemap_eligible` are explicit. Tier C records do not automatically receive standalone indexable pages. An indexable record must have a canonical URL; a sitemap-eligible record must be indexable.

Freshness is a publication control. A stale record can remain in the database for investigation, but it must not silently continue to present expired facts as verified.

## Evidence workflow

1. Start with the official product, pricing, documentation, help, or legal source.
2. Create a source record with access date, publisher, official status, region, currency, and billing term.
3. Extract one claim per meaningful factual assertion.
4. Add the source IDs and a concise excerpt or evidence note.
5. Set `verified_at` and a recheck deadline appropriate to volatility.
6. Link the claim to the tool record.
7. Run all validators.
8. Have an editor review interpretation, limitations, and tier.
9. Keep unresolved or disputed claims visible as such; do not guess.

## Freshness workflow

Pricing, plans, limits, availability, and status should normally have shorter review windows than stable identity fields. A checker may detect a source change, but detection does not equal verification.

When a source changes:

1. create a change-ledger event only after the change is observed;
2. mark affected claims `needs_review` or `stale`;
3. preserve the prior claim and source history;
4. add replacement evidence after verification;
5. update the record's `stale_fields` and `next_review_at`;
6. update editorial pages only through the normal content review process.

Do not invent historical changes. The initial change ledger is empty for that reason.

## Affiliate separation

Affiliate data is maintained centrally and checked independently from editorial data. The official URL is retained even when an affiliate program is approved. A disclosure is required where a commercial link is shown. Regions and restrictions are explicit so a link is not shown to an ineligible user.

## Future publishing workflow

Future page generation should consume validated records and a page-intent registry. It must not publish every record automatically.

Before a page is eligible:

- the record passes schema and evidence checks;
- its tier permits a page;
- the intended query is not already served by another URL;
- the page has a canonical and internal-link path;
- factual modules display source dates and appropriate caveats;
- structured data matches visible content;
- browser and link QA pass.

Tier C can power search results, recommendations, and internal workflows without creating an indexable review page.

## Adding a tool

See [ADDING-A-TOOL.md](ADDING-A-TOOL.md) for the short operational checklist. A new record should be created in a branch, never directly in the production dataset.

The current 50-record shadow migration is deliberately non-publishing: the three benchmark records remain the reviewed top-level records, while the other 47 records are Tier C, `noindex`, and absent from the sitemap until evidence and editorial review exist.

## Promotion: C → B → A

### Tier C to Tier B

Require confirmed identity and official URL, core factual evidence, a useful task/category classification, status/link checks, limitations, and an editor sign-off. The record can remain non-indexable until a distinct page intent exists.

### Tier B to Tier A

Require demonstrated user/search demand, enough evidence for a maintained decision page, original ToolNest value beyond vendor copy, explicit limitations, a review owner, update triggers, and a conflict-of-interest check.

Affiliate approval is never a promotion criterion.

## Handling stale records

Do not silently remove a stale record. Mark the affected claims and record fields, stop presenting them as current, check the official source, and either replace the evidence, archive the tool, or retain it as an explicitly uncertain directory record. Public indexation and sitemap eligibility should be reconsidered through the publishing gate.

## Validation commands

```bash
python3 scripts/validate_decision_graph.py
python3 scripts/validate_evidence_ledger.py
python3 scripts/check_freshness.py --as-of 2026-11-14
python3 scripts/check_affiliate_separation.py
python3 -m unittest discover -s tests -p 'test_*.py'
```
