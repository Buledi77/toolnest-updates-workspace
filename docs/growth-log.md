# Growth log

Owner-supplied brief: 0 clicks, ~1.09K impressions, average position 41.7 (8 days of Search Console data,
read 2026-11-28). The working hypothesis is ranking depth, not click-through rate.

## Search update annotations

- **2026-11-10 to 2026-11-24 — November 2026 core update.** Treat this window as a volatility period when
  comparing Search Console snapshots; do not attribute changes inside it to our edits.
- **December 2026 core update — preannounced.** Not yet observed in our data. Record the rollout dates here
  when Google confirms them; do not guess.

## Phase A before/after (2026-11-28)

| Metric | Before | After |
|---|---|---|
| Indexable pages | 265 | 264 |
| Sitemap URLs | 265 | 264 |
| Pages with <5 inbound links | 82 | 0 |
| Zero-inbound pages | 1 | 0 |
| Sitemap URLs unreachable from homepage | 2 | 0 |
| Titles over 60 chars | 11 | 0 |
| Descriptions over 155 chars | 49 | 0 |
| Pages sharing duplicate H2s | 427 | 0 |
| `/tools/index.html` words | 171 | 765 |

Merged in PR #7, commit `c92e3cb`. Production verified: sitemap 264 URLs, new footer navigation present.

## Phase B before/after (2026-11-28)

| Metric | Before | After |
|---|---|---|
| Indexable pages / sitemap URLs | 264 / 264 | 169 / 169 |
| Pages below quality gate | 128 of 264 | 4 of 169 (all on the enrich-next list) |
| `noindex` pages | 92 | 187 |
| Thin pages (<300 words, indexable) | 93 | 20 |

95 pages were noindexed and removed from the sitemap, none deleted; see `docs/indexation-log.md` for the
reversible list. 4 protected utility/category pages were restored after regression tests flagged them.
30 pages were placed on the enrich-next list with >=8 inbound links each.
Merged in PR #8, commit `a81c441`.

## Phase C (2026-11-28)

30 enrich-next pages received answer-first, ledger-sourced sections; 4 pages remain marginally above the
15% sentence-overlap threshold and are flagged in `data/quality/page-scores.csv`. Moz's official page does
not publish a trial length or a free-account Keyword Explorer allowance; both are shown as **not verified**
on `tools/mozpro.html` and `compare/mozpro-vs-semrush.html` with the official URL cited.
Merged in PR #9 (`6cd6a9f`) and CI repair PR #10 (`dae1a14`).

## Phase D (2026-11-28)

Downloadable CSV/JSON, an SVG chart, a "cite this" box, a ledger-only pricing data page, an embeddable
calculator with visible attribution, a press page and a 40-target owner-only outreach list.
`docs/outreach-list.md` has NOT been actioned; the owner does all outreach. No link buying, PBNs,
reciprocal swaps or comment spam.

## Weekly measurement

Run `python scripts/weekly_growth_report.py`. It writes `data/quality/weekly-growth-report.json` and reads
any GSC CSV exports the owner places in `data/gsc/`. It never invents search data.

## Owner actions still required

1. Supply `data/gsc/404.csv` so the 4 GSC 404s can be mapped to 301s with clear replacements.
2. Confirm the single Vercel project that should serve www + apex (three projects are connected).
3. Provide official ≥128px brand kits for the 10 legacy 48px logos.
4. Perform outreach from `docs/outreach-list.md`; no emails have been sent by the agent.
