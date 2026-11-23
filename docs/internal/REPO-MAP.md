# ToolNest repository map

Generated on 2026-11-14 for the `seo-v2` branch.

## a) Page build and data flow

The public pages are committed static HTML files. `scripts/build_site.py` now
normalizes and rebuilds the HTML corpus in `tools/`, `compare/`, `alternatives/`,
`best/`, `category/`, and `goals/` from the committed HTML plus
`data/site.json` and `data/index-allowlist.json`. It also applies the
main-content indexability gate and writes the sitemap and indexability report.
The repository has no `package.json` and no root README with
an npm build command. The exact whole-site build command is:

```bash
python3 scripts/build_site.py
```

The current production catalog is `data/tools.json`; the repository documentation
explicitly says that it remains the production dataset. `data/tools-v1.json` is a
structured copy with additional fields, while `data/tools-v2/` is an additive
Decision Graph/shadow dataset and is not wired to replace the public HTML.

The scripts build or validate page and data artifacts:

- `scripts/build_site.py` writes normalized UTF-8 HTML, `sitemap.xml`, and
  optional `ads.txt`; it also injects configured analytics and verification
  tags, normalizes outbound link attributes, and applies the indexability gate.
- `scripts/content_metrics.py` extracts main-content word counts and unique
  marked-section fingerprints while excluding shared navigation and related
  content.
- `scripts/count_main_content.py` prints the per-page content metrics.
- `data/index-allowlist.json` contains explicit manual indexability overrides.
- `docs/internal/INDEX-REPORT.md` records indexable/noindex counts and URLs.

- `scripts/build_search_index.py` reads `data/tools-v2/` and writes
  `data/indexes/tool-search-index.json`.
- `scripts/build_affiliate_registry.py` reads `data/tools-v2/` and writes
  `data/monetization/affiliate-registry.json`.
- `scripts/migrate_legacy_tools.py` reads `data/tools.json` and writes
  `data/tools-v2/legacy/*.json` plus
  `data/migrations/legacy-to-v2-map.json`.
- `scripts/build_stack.py` reads the v2 records and
  `data/stack/stack-builder-v1.json` and prints recommendations.
- `scripts/recommend_tasks.py` uses
  `data/recommendations/task-catalog.json` and v2 records as a shadow adapter.

The closest reproducible repository-wide validation command is the command
sequence in `.github/workflows/decision-graph-validation.yml`, ending with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

That workflow does not rebuild the public HTML. It runs the validators, rebuilds
the search index and affiliate registry, and checks site quality. The static
site build and SEO QA are local commands because the repository has no npm
package manifest.

## b) Vercel and Netlify deployment rules

`vercel.json` exists and defines 376 permanent redirects. It has no `headers`
section. The redirects cover duplicate comparison ordering, `/categories/*` to
`/category/*`, extensionless routes to explicit `.html` routes, and other
canonical route variants.

`_headers` and `_redirects` are Netlify-format files and Vercel ignores them.
Their rules are not duplicated in `vercel.json`: `_headers` contains security
and asset-cache headers, while `_redirects` contains the host migration,
canonicalization, duplicate comparisons, category consolidation, and route
redirect rules. Vercel therefore currently has the redirect rules from
`vercel.json`, but not the `_headers` rules or the additional `_redirects`
rules unless they are configured elsewhere in the Vercel project.

## c) Public deployment surface

Vercel serves every file in the output directory unless excluded. The
repository does not define a Vercel output directory or an exclusion manifest
for these paths. Files/directories that are currently tracked and would
therefore be publicly reachable include:

- `_headers` and `_redirects` (as ordinary files; Vercel does not interpret
  their Netlify directives).
- `data/*.json` and nested JSON data, including schemas, evidence, monetization,
  publishing, recommendation, migration, taxonomy, analytics, stack, and v2
  records.
- `docs/`, including the project design and operating documents.
- `reports/`, including the migration and market blueprint reports.
- `tests/`, including the Python test suite.
- `scripts/`, including validators, adapters, generators, and ingestion tools.
- Root text files `TOOLNEST-COPILOT-FULL-AUDIT.txt`, `llms.txt`,
  `llms-full.txt`, and `robots.txt`.
- `.env.local` exists in the working tree. It is ignored by `.gitignore` and
  is not tracked, but would be exposed if copied into the deployed output
  directory.

The `.vercel/` directory is ignored by `.gitignore`; it is local Vercel
metadata, not a deliberately deployable public directory.

## d) SEO utility files

`sitemap.xml`, `robots.txt`, `llms.txt`, `llms-full.txt`, and `404.html` are
hand-written/committed static files. No repository script generates them.
`scripts/check_site_quality.py` and
`scripts/check_publishing_registry.py` read and validate the sitemap; they do
not write it. `404.html` is a committed static error page.

## e) Affiliate and outbound links

`scripts/build_site.py` is the shared renderer/normalizer for the committed HTML
templates. It identifies external vendor URLs and writes:

```html
rel="nofollow noopener" target="_blank"
```

The links point to the official vendor URL in the rendered pages. Affiliate
metadata is maintained separately in v2 records and the generated
`data/monetization/affiliate-registry.json`; the validation code keeps
`official_non_affiliate_url` separate from any optional `affiliate_url`.

## f) Alternatives selection

The alternatives pages are static source templates; the build normalizes their
shared metadata and links but does not choose their cards. The production catalog fields
`alternatives`, `comparisons`, and `goals` are empty for all 50 records in both
`data/tools.json` and `data/tools-v1.json`, so those pages are not currently
derived from those fields.

The v2 schema supports a `relationships.alternatives` list of stable tool IDs,
and `scripts/decision_graph_common.py` validates those references. The v2
relationship data is additive/shadow data and is not connected to the public
HTML renderer. `data/recommendations/task-catalog.json` is used by the separate
task-first recommendation adapter, not by the static alternatives pages.

## g) Tests and CI

The repository has 22 Python test modules under `tests/`:

- `test_catalog_intake.py`
- `test_catalog_integrity.py`
- `test_decision_graph.py`
- `test_directory_adapter.py`
- `test_search_and_publishability.py`
- `test_site_quality.py`
- `test_stack_builder.py`
- `test_freshness_pipeline.py` — Freshness recheck pipeline tests
- `test_browser_qa.py` — Browser QA automation tests
- (plus 14 other test modules)

There is one workflow, `.github/workflows/decision-graph-validation.yml`. It
runs on pull requests changing the Decision Graph, scripts, tests, or related
data. It uses Python 3.12 and runs all validators, data artifact builders,
site-quality checks, and the full unittest discovery command.

Run the test suite locally with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Run the static SEO checker with:

```bash
scripts/qa-check
```

### h) Freshness and Browser QA pipelines (added 2026-11-23)

**Freshness recheck pipeline** — automated detection and rechecking of stale facts:

```bash
python3 scripts/freshness_recheck_pipeline.py              # Dry run, generate report
python3 scripts/freshness_recheck_pipeline.py --apply      # Apply updates to ledger and v2 records
python3 scripts/freshness_recheck_pipeline.py --as-of 2026-11-23  # Use specific date
```

Outputs: `reports/phase6/freshness-recheck-report.json`

**Browser QA automation** — Playwright-based cross-viewport testing of all HTML pages:

```bash
python3 scripts/browser_qa.py                              # Test all pages
python3 scripts/browser_qa.py --sample 50                  # Test 50 pages
```

Outputs: `reports/phase6/browser-qa-report.json`

### i) Validation pipeline (complete)

All 16 validation gates pass. To mirror the full validation sequence, run:

```bash
python3 scripts/validate_decision_graph.py
python3 scripts/validate_evidence_ledger.py
python3 scripts/check_freshness.py
python3 scripts/check_affiliate_separation.py
python3 scripts/validate_taxonomy.py
python3 scripts/build_affiliate_registry.py
python3 scripts/check_affiliate_registry.py
python3 scripts/check_publishing_registry.py
python3 scripts/ingest_catalog_candidates.py --offline
python3 scripts/validate_analytics_taxonomy.py
python3 scripts/check_catalog_integrity.py
python3 scripts/check_legacy_parity.py
python3 scripts/check_publishability.py
python3 scripts/build_search_index.py
python3 scripts/check_site_quality.py
python3 scripts/validate_real_catalog.py
python3 -m unittest discover -s tests -p 'test_*.py'
```
