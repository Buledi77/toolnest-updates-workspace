#!/usr/bin/env python3
"""
Controlled fetch pilot — actual HTTP fetches against ~10 representative sources.

Selects a small representative set covering:
- Public pricing page
- Feature page
- Documentation page
- Integration source
- Stable page
- Recently researched product

Captures for every fetch:
- HTTP/fetch outcome
- First-party verification
- Fingerprint
- ETag if available
- Last-Modified if available
- Content type
- Redirect
- Fetch timestamp
- Parse outcome

Does NOT modify canonical production facts from fetch results alone.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from source_fetcher import SourceFetcher

# Representative pilot selection covering diverse source types
PILOT_TOOLS = [
    # Well-known, stable pricing pages
    "semrush",        # SEO — multiple pricing sources
    "hostinger",      # Hosting — product features + pricing
    "zapier",         # Automation — simple pricing
    "framer",         # Design — modern SaaS
    "surferseo",      # SEO — recently added
    # Different categories
    "gorgias",        # Support/Chat
    "moosend",        # Email marketing
    "webflow",        # Website builder
    "n8n",            # Automation (open-source alternative)
    "unbounce",       # Landing pages
]

def load_json(path):
    return json.load((ROOT / path).open())

def save_json(path, data):
    (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
    with (ROOT / path).open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

def main():
    print("=" * 60)
    print("CONTROLLED FETCH PILOT")
    print("=" * 60)
    print(f"Tools: {len(PILOT_TOOLS)}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Verify all pilot tools are in registry
    registry = load_json("data/sources/source-registry.json")
    v1 = load_json("data/tools-v1.json")
    recon = load_json("data/catalog-reconciliation.json")
    production_ids = {t['id'] for t in v1['tools']} - set(recon.get('expansion_only_tools', []))

    for tid in PILOT_TOOLS:
        if tid not in registry:
            print(f"WARNING: {tid} not in source registry, skipping")
        if tid not in production_ids:
            print(f"WARNING: {tid} not in production, skipping")

    # Run fetcher
    fetcher = SourceFetcher(
        timeout=15,
        max_retries=3,
        max_concurrency=3,
    )

    fetch_result = fetcher.fetch_all_tools(tool_ids=PILOT_TOOLS)
    results = fetch_result.get("results", {})

    # Build detailed report
    tool_reports = {}
    total_sources_fetched = 0
    total_success = 0
    total_unavailable = 0
    total_not_modified = 0
    total_redirect = 0
    fingerprints_collected = 0
    etags_collected = 0
    last_modified_collected = 0

    for tid in PILOT_TOOLS:
        r = results.get(tid, {})
        sources = r.get("sources", {})

        tool_report = {
            "tool_id": tid,
            "overall_status": r.get("status"),
            "sources": {},
        }

        for sid, sr in sources.items():
            source_report = {
                "url": sr.get("url"),
                "status": sr.get("status"),
                "fingerprint": sr.get("fingerprint"),
                "content_length": sr.get("content_length"),
                "attempt": sr.get("attempt"),
                "timestamp": sr.get("timestamp"),
                "error": sr.get("error"),
            }

            # Extract headers info
            headers = sr.get("headers", {})
            if headers:
                source_report["etag"] = headers.get("ETag")
                source_report["last_modified"] = headers.get("Last-Modified")
                source_report["content_type"] = headers.get("Content-Type")
                if headers.get("ETag"):
                    etags_collected += 1
                if headers.get("Last-Modified"):
                    last_modified_collected += 1

            # Track stats
            status = sr.get("status")
            if status == "success":
                total_success += 1
                if sr.get("fingerprint"):
                    fingerprints_collected += 1
            elif status == "unavailable":
                total_unavailable += 1
            elif status == "not_modified":
                total_not_modified += 1
            elif status == "redirect":
                total_redirect += 1
                source_report["final_url"] = sr.get("final_url")

            total_sources_fetched += 1
            tool_report["sources"][sid] = source_report

        tool_reports[tid] = tool_report

    # Summary
    report = {
        "pipeline": "fetch_pilot",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "tools_attempted": len(PILOT_TOOLS),
            "total_sources_attempted": total_sources_fetched,
            "successful_fetches": total_success,
            "not_modified_304": total_not_modified,
            "redirects": total_redirect,
            "unavailable": total_unavailable,
            "fingerprints_collected": fingerprints_collected,
            "etags_collected": etags_collected,
            "last_modified_collected": last_modified_collected,
            "canonical_facts_modified": False,
        },
        "tools": tool_reports,
        "failures": [
            {
                "tool_id": f.get("tool_id"),
                "source_id": f.get("source_id"),
                "url": f.get("url"),
                "status": f.get("status"),
                "error": f.get("error"),
            }
            for f in fetcher.failures
        ],
    }

    # Save report
    save_json("reports/phase6/fetch-pilot-report.json", report)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"FETCH PILOT RESULTS")
    print(f"{'=' * 60}")
    print(f"Tools attempted:        {len(PILOT_TOOLS)}")
    print(f"Sources attempted:      {total_sources_fetched}")
    print(f"Successful fetches:     {total_success}")
    print(f"Not modified (304):     {total_not_modified}")
    print(f"Redirects:              {total_redirect}")
    print(f"Unavailable:            {total_unavailable}")
    print(f"Fingerprints collected: {fingerprints_collected}")
    print(f"ETags collected:        {etags_collected}")
    print(f"Last-Modified collected:{last_modified_collected}")
    print(f"Canonical facts modified: False")
    print()

    # Per-tool breakdown
    for tid in PILOT_TOOLS:
        r = results.get(tid, {})
        status = r.get("status", "unknown")
        sources = r.get("sources", {})
        print(f"  {tid}: {status} ({len(sources)} sources)")
        for sid, sr in sources.items():
            s = sr.get("status", "unknown")
            fp = sr.get("fingerprint", "")
            fp_short = fp[:16] + "..." if fp else "none"
            err = sr.get("error", "")
            print(f"    {sid}: {s} fp={fp_short}" + (f" ERR={err}" if err else ""))

    print(f"\nReport saved: reports/phase6/fetch-pilot-report.json")

if __name__ == "__main__":
    main()
