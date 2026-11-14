# Search and Recommendation V1

This phase adds a shadow consumer for Decision Graph records. It does not replace
the current `data/tools-v1.json` consumer or change any public page.

## Normalized search index

`scripts/build_search_index.py` converts validated records in `data/tools-v2/` into
`data/indexes/tool-search-index.json`. Each document has a stable ID and slug,
normalized discovery tokens, editorial tier, indexability, freshness, and the
official URL. The output is deterministic and sorted by ID so it can be diffed
in review.

The index is suitable for a future client or server search adapter. Tier C
records are searchable internally, but their `indexability` and sitemap flags
remain authoritative and must not be used to create public review pages.

## Task-first recommendations

`data/recommendations/task-catalog.json` is the canonical mapping from a user
job to an explicit guide and known tool IDs. `scripts/recommend_tasks.py` scores
query tokens against task signals and returns only records that exist in the
Decision Graph. It does not infer a rating, popularity, testing claim, or
affiliate preference.

`scripts/directory_adapter.py` provides the pure search, category filter,
sorting, pagination, and public-page eligibility operations needed by a future
directory consumer. It is currently a shadow adapter; the legacy HTML
directory remains the production consumer until output parity and browser QA
are completed.

The current homepage goal picker is intentionally not wired to this adapter
until parity and browser QA prove that the migration preserves the existing
experience.

## Validation

```bash
python3 scripts/validate_taxonomy.py
python3 scripts/build_search_index.py
python3 scripts/check_legacy_parity.py
python3 scripts/check_publishability.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

The next integration gate is a read-only parity comparison between the legacy
directory output and this normalized index. Only after that comparison passes
should a public consumer be switched.
