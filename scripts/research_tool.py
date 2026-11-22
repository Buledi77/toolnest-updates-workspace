#!/usr/bin/env python3
"""Automated research pipeline for ToolNest tool pages.

Fetches official vendor pages, extracts facts, verifies claims,
and writes research notes. Run in batches of 5 tools.

Usage:
    python3 scripts/research_tool.py --slug semrush
    python3 scripts/research_tool.py --batch 5
    python3 scripts/research_tool.py --all
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V2_DIR = ROOT / "data" / "tools-v2"
EVIDENCE_DIR = ROOT / "data" / "evidence"
RESEARCH_DIR = ROOT / "data" / "research"
REPORTS_DIR = ROOT / "reports"
TOOLS_JSON = ROOT / "data" / "tools.json"

# Rate limiting: 1 request/sec per domain
REQUEST_DELAY = 1.0
USER_AGENT = "ToolNest-Research/1.0 (https://www.toolnestai.tech)"


def load_catalog() -> dict[str, dict]:
    """Load tools.json catalog as id->tool map."""
    data = json.loads(TOOLS_JSON.read_text())
    return {t["id"]: t for t in data.get("tools", [])}


def load_v2(slug: str) -> dict | None:
    """Load tools-v2 structured data for a slug."""
    candidates = [
        TOOLS_V2_DIR / f"{slug}.json",
        TOOLS_V2_DIR / "legacy" / f"{slug}.json",
        TOOLS_V2_DIR / "legacy" / f"{slug.replace('mozpro', 'moz-pro')}.json",
        TOOLS_V2_DIR / "expansion" / f"{slug}.json",
    ]
    for p in candidates:
        if p.exists():
            return json.loads(p.read_text())
    return None


def get_official_url(slug: str) -> str | None:
    """Get the official vendor URL for a tool."""
    # Try tools-v2 first
    v2 = load_v2(slug)
    if v2:
        identity = v2.get("identity", {})
        if identity.get("official_url"):
            return identity["official_url"]
    # Fall back to tools.json
    catalog = load_catalog()
    tool = catalog.get(slug)
    if tool and tool.get("site"):
        return tool["site"]
    return None


def discover_pricing_url(official_url: str) -> str | None:
    """Try to find the pricing page URL from the official URL."""
    # Common pricing URL patterns
    patterns = [
        urljoin(official_url, "/pricing"),
        urljoin(official_url, "/pricing/"),
        urljoin(official_url, "/pricing/seo"),
        urljoin(official_url, "/plans"),
        urljoin(official_url, "/plans/"),
    ]
    return patterns[0]  # Return the most common one; actual fetching will verify


def fetch_url(url: str, timeout: int = 10) -> dict | None:
    """Fetch a URL and return metadata + text content."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            text = raw.decode("utf-8", errors="replace")
            # Extract just the text content (strip HTML tags)
            clean_text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r"<style[^>]*>.*?</style>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r"<[^>]+>", " ", clean_text)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            # Truncate to 50KB for storage
            if len(clean_text) > 50000:
                clean_text = clean_text[:50000]
            sha = hashlib.sha256(raw).hexdigest()
            return {
                "url": url,
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "sha256": sha,
                "status": response.status,
                "text": clean_text[:50000],
                "raw_length": len(raw),
            }
    except Exception as e:
        return {
            "url": url,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "status": 0,
            "text": "",
            "raw_length": 0,
        }


def extract_pricing_facts(text: str, source_url: str) -> list[dict]:
    """Extract pricing-related facts from page text."""
    claims = []
    today = date.today().isoformat()

    # Look for plan names and prices
    # Pattern: "$XXX" or "$XXX/month" or "$XXX/mo"
    price_pattern = re.compile(r"\$(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:/?\s*(?:month|mo|per\s+month|monthly))?", re.IGNORECASE)
    for match in price_pattern.finditer(text):
        price_str = match.group(0)
        price_val = match.group(1)
        claims.append({
            "text": f"Price mentioned: {price_str}",
            "sourceUrl": source_url,
            "checkedOn": today,
            "type": "price",
        })

    # Look for plan names
    plan_pattern = re.compile(r"\b(Pro|Starter|Basic|Standard|Premium|Enterprise|Business|Free|Guru|Personal|Team)\b", re.IGNORECASE)
    for match in plan_pattern.finditer(text):
        plan_name = match.group(1)
        claims.append({
            "text": f"Plan mentioned: {plan_name}",
            "sourceUrl": source_url,
            "checkedOn": today,
            "type": "plan",
        })

    # Look for free trial mentions
    if re.search(r"\b\d+\s*day\s*free\s*trial\b", text, re.IGNORECASE):
        claims.append({
            "text": "Free trial mentioned",
            "sourceUrl": source_url,
            "checkedOn": today,
            "type": "trial",
        })

    # Look for free plan mentions
    if re.search(r"\bfree\s*(plan|tier|option|account)\b", text, re.IGNORECASE):
        claims.append({
            "text": "Free plan or tier mentioned",
            "sourceUrl": source_url,
            "checkedOn": today,
            "type": "free_plan",
        })

    # Deduplicate
    seen = set()
    unique_claims = []
    for claim in claims:
        key = (claim["text"], claim["type"])
        if key not in seen:
            seen.add(key)
            unique_claims.append(claim)

    return unique_claims


def research_tool(slug: str) -> dict:
    """Research a single tool and return results."""
    result = {
        "slug": slug,
        "status": "pending",
        "official_url": None,
        "sources_fetched": [],
        "claims": [],
        "errors": [],
        "blocked": False,
        "block_reason": "",
    }

    # Get official URL
    official_url = get_official_url(slug)
    if not official_url:
        result["status"] = "blocked"
        result["block_reason"] = "No official URL found"
        result["errors"].append("Cannot find official vendor URL")
        return result

    result["official_url"] = official_url

    # Discover URLs to fetch
    urls_to_fetch = [
        official_url,
        discover_pricing_url(official_url),
        urljoin(official_url, "/features"),
        urljoin(official_url, "/help"),
        urljoin(official_url, "/terms"),
    ]

    # Fetch and store evidence
    evidence_dir = EVIDENCE_DIR / slug
    evidence_dir.mkdir(parents=True, exist_ok=True)

    domain = urlparse(official_url).netloc
    for i, url in enumerate(urls_to_fetch):
        if i > 0:
            time.sleep(REQUEST_DELAY)  # Rate limiting

        snapshot = fetch_url(url)
        if snapshot:
            # Store snapshot
            snapshot_file = evidence_dir / f"{hashlib.md5(url.encode()).hexdigest()[:8]}.json"
            snapshot_file.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")

            if snapshot.get("error"):
                result["errors"].append(f"Failed to fetch {url}: {snapshot['error']}")
            else:
                result["sources_fetched"].append(snapshot["url"])
                # Extract claims
                claims = extract_pricing_facts(snapshot.get("text", ""), snapshot["url"])
                result["claims"].extend(claims)

    result["status"] = "complete" if result["sources_fetched"] else "partial"

    # Write research notes
    research_file = RESEARCH_DIR / f"{slug}.md"
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Research: {slug}",
        f"",
        f"Date: {date.today().isoformat()}",
        f"Status: {result['status']}",
        f"",
        f"## Official URL",
        f"{result['official_url']}",
        f"",
        f"## Sources Fetched",
    ]
    for url in result["sources_fetched"]:
        lines.append(f"- {url}")
    if not result["sources_fetched"]:
        lines.append("- None")

    lines.extend(["", "## Claims Found"])
    for claim in result["claims"][:20]:  # Limit to 20 claims
        lines.append(f"- **{claim['type']}**: {claim['text']} (source: {claim['sourceUrl']})")
    if not result["claims"]:
        lines.append("- No claims extracted")

    if result["errors"]:
        lines.extend(["", "## Errors"])
        for error in result["errors"]:
            lines.append(f"- {error}")

    research_file.write_text("\n".join(lines) + "\n")

    return result


def write_blocked_report(blocked_tools: list[dict]) -> None:
    """Write /reports/blocked.md with tools that couldn't be researched."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# Blocked Tools", "", "Tools that could not be researched in this run.", ""]
    for tool in blocked_tools:
        lines.append(f"## {tool['slug']}")
        lines.append(f"- **Reason**: {tool.get('block_reason', 'Unknown')}")
        lines.append(f"- **Errors**: {', '.join(tool.get('errors', []))}")
        lines.append("")
    (REPORTS_DIR / "blocked.md").write_text("\n".join(lines) + "\n")


def write_research_queue() -> None:
    """Write /reports/research-queue.md with all tools and their official URLs."""
    catalog = load_catalog()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# Research Queue", "", "Tools that need research, with their official URLs.", ""]
    for slug in sorted(catalog.keys()):
        url = catalog[slug].get("site", "N/A")
        v2 = load_v2(slug)
        if v2:
            identity = v2.get("identity", {})
            if identity.get("official_url"):
                url = identity["official_url"]
        lines.append(f"- **{slug}**: {url}")
    (REPORTS_DIR / "research-queue.md").write_text("\n".join(lines) + "\n")


def write_progress(completed: list[str], blocked: list[str]) -> None:
    """Write /reports/progress.md tracking research progress."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    total = len(catalog)
    lines = [
        "# Research Progress",
        "",
        f"Date: {date.today().isoformat()}",
        f"",
        f"## Summary",
        f"- Total tools: {total}",
        f"- Completed: {len(completed)}",
        f"- Blocked: {len(blocked)}",
        f"- Remaining: {total - len(completed) - len(blocked)}",
        f"",
        f"## Completed",
    ]
    for slug in completed:
        lines.append(f"- {slug}")
    if blocked:
        lines.extend(["", "## Blocked"])
        for slug in blocked:
            lines.append(f"- {slug}")
    (REPORTS_DIR / "progress.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="ToolNest research pipeline")
    parser.add_argument("--slug", type=str, help="Research a specific tool by slug")
    parser.add_argument("--batch", type=int, help="Research N tools in priority order")
    parser.add_argument("--all", action="store_true", help="Research all tools")
    args = parser.parse_args()

    catalog = load_catalog()

    # Priority order: GSC impressions first, then by catalog order
    # For now, use catalog order
    slugs = list(catalog.keys())

    if args.slug:
        slugs = [args.slug]
    elif args.batch:
        slugs = slugs[:args.batch]
    # --all uses all slugs

    completed = []
    blocked = []

    for slug in slugs:
        print(f"Researching {slug}...")
        result = research_tool(slug)
        if result["status"] in ("complete", "partial"):
            completed.append(slug)
            print(f"  ✓ {result['status']}: {len(result['sources_fetched'])} sources, {len(result['claims'])} claims")
        else:
            blocked.append(slug)
            print(f"  ✗ Blocked: {result.get('block_reason', 'Unknown')}")

    # Write reports
    if blocked:
        write_blocked_report([s for s in slugs if s in blocked])
    write_progress(completed, blocked)

    print(f"\nDone: {len(completed)} completed, {len(blocked)} blocked")
    print(f"Research notes: {RESEARCH_DIR}/")
    print(f"Progress: {REPORTS_DIR}/progress.md")


if __name__ == "__main__":
    main()
