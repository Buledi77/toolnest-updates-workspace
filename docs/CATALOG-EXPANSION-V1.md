# Catalog Expansion V1

Catalog expansion is intake-first and non-publishing by default.

## Workflow

1. Add a bounded candidate batch to `data/intake/catalog-expansion-v1.json`.
2. Include an official product URL, a source note, a canonical ID, and discovery
   tags. Do not add pricing, limits, ratings, or editorial conclusions without
   evidence records.
3. Run the dry-run verifier:

   ```bash
   python3 scripts/ingest_catalog_candidates.py
   ```

4. Review the official URL statuses and candidate diff.
5. Apply only the reviewed batch:

   ```bash
   python3 scripts/ingest_catalog_candidates.py --apply --as-of 2026-11-14T21:55:21Z
   ```

6. Run every Decision Graph, freshness, affiliate, publishing, site-quality,
   search-index, and test gate.

## Publishing boundary

New records are generated as Tier C, `noindex`, sitemap-ineligible,
directory-only records. They can support internal search and recommendation
experiments, but they do not create review pages, canonicals, sitemap entries,
or public URLs.

Promotion requires independent evidence, editorial review, limitations, a
distinct page intent, and preview QA. Affiliate approval cannot promote a
record or affect its ranking.

## Verified batches

The first batch adds eight official destinations: Cursor, Lovable, v0, Replit,
Gamma, Glean, Le Chat, and Granola. The second batch adds Windsurf, Bolt,
Firecrawl, Browserbase, AssemblyAI, Together AI, HeyGen, and Ideogram. Their
current records contain identity and discovery data only; product facts remain
unassessed until source-specific evidence is collected.
