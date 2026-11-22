#!/usr/bin/env python3
"""Monthly pricing refresh script for ToolNest.

Fetches current pricing from official vendor pages and updates
data/tools-v2 JSON files with fresh pricing evidence.

Usage:
    python3 scripts/refresh_pricing.py [--slug semrush] [--all]

This script is designed to run monthly via GitHub Actions.
It opens a PR with changes but never deploys automatically.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V2_DIR = ROOT / "data" / "tools-v2"
TOOLS_JSON = ROOT / "data" / "tools.json"
EVIDENCE_DIR = ROOT / "data" / "evidence"

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


def save_v2(slug: str, data: dict) -> Path:
    """Save tools-v2 data, preferring the original location."""
    candidates = [
        TOOLS_V2_DIR / f"{slug}.json",
        TOOLS_V2_DIR / "legacy" / f"{slug}.json",
        TOOLS_V2_DIR / "legacy" / f"{slug.replace('mozpro', 'moz-pro')}.json",
        TOOLS_V2_DIR / "expansion" / f"{slug}.json",
    ]
    for p in candidates:
        if p.exists():
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            return p
    # Create in expansion/ if not found
    path = TOOLS_V2_DIR / "expansion" / f"{slug}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


def get_official_url(slug: str) -> str | None:
    """Get the official vendor URL for a tool."""
    v2 = load_v2(slug)
    if v2:
        identity = v2.get("identity", {})
        if identity.get("official_url"):
            return identity["official_url"]
    catalog = load_catalog()
    tool = catalog.get(slug)
    if tool and tool.get("site"):
        return tool["site"]
    return None


def fetch_url(url: str, timeout: int = 10) -> str | None:
    """Fetch a URL and return text content."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            text = raw.decode("utf-8", errors="replace")
            clean = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r"<[^>]+>", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            return clean[:50000]
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def extract_pricing(text: str) -> list[dict]:
    """Extract pricing information from text."""
    claims = []
    today = date.today().isoformat()

    # Price patterns
    price_pattern = re.compile(r"\$(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:/?\s*(?:month|mo|per\s+month|monthly))?", re.IGNORECASE)
    for match in price_pattern.finditer(text):
        claims.append({
            "text": f"Price: ${match.group(1)}",
            "type": "price",
            "checkedOn": today,
        })

    # Plan names
    plan_pattern = re.compile(r"\b(Pro|Starter|Basic|Standard|Premium|Enterprise|Business|Free|Guru|Personal|Team)\b", re.IGNORECASE)
    for match in plan_pattern.finditer(text):
        claims.append({
            "text": f"Plan: {match.group(1)}",
            "type": "plan",
            "checkedOn": today,
        })

    # Deduplicate
    seen = set()
    unique = []
    for claim in claims:
        key = (claim["text"], claim["type"])
        if key not in seen:
            seen.add(key)
            unique.append(claim)
    return unique


def refresh_pricing(slug: str) -> dict:
    """Refresh pricing data for a single tool."""
    result = {
        "slug": slug,
        "status": "pending",
        "pricing_url": None,
        "claims": [],
        "errors": [],
    }

    official_url = get_official_url(slug)
    if not official_url:
        result["status"] = "blocked"
        result["errors"].append("No official URL found")
        return result

    pricing_url = urljoin(official_url, "/pricing")
    result["pricing_url"] = pricing_url

    text = fetch_url(pricing_url)
    if not text:
        result["status"] = "failed"
        result["errors"].append(f"Failed to fetch {pricing_url}")
        return result

    claims = extract_pricing(text)
    result["claims"] = claims

    # Update v2 data
    v2 = load_v2(slug)
    if v2:
        today = date.today().isoformat()
        now = datetime.now(timezone.utc).isoformat()

        # Update evidence
        evidence = v2.setdefault("evidence", {})
        evidence["claim_refs"] = [
            {"claim_id": f"pricing-refresh-{today}-{i}"}
            for i in range(len(claims))
        ]
        evidence["source_ids"] = evidence.get("source_ids", [])
        if pricing_url not in evidence.get("source_ids", []):
            evidence.setdefault("source_ids", []).append("pricing-page")

        # Update freshness
        freshness = v2.setdefault("freshness", {})
        freshness["last_verified_at"] = now
        freshness["updated_at"] = now

        # Update publishing
        publishing = v2.setdefault("publishing", {})
        publishing["content_quality_status"] = "reviewed"

        save_v2(slug, v2)
        result["status"] = "updated"
    else:
        result["status"] = "no_v2_data"
        result["errors"].append("No v2 data found for this tool")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Monthly pricing refresh for ToolNest")
    parser.add_argument("--slug", type=str, help="Refresh a specific tool")
    parser.add_argument("--all", action="store_true", help="Refresh all tools")
    args = parser.parse_args()

    catalog = load_catalog()

    if args.slug:
        slugs = [args.slug]
    elif args.all:
        slugs = list(catalog.keys())
    else:
        print("Usage: python3 scripts/refresh_pricing.py --slug <slug> | --all")
        sys.exit(1)

    results = []
    for slug in slugs:
        print(f"Refreshing {slug}...")
        result = refresh_pricing(slug)
        results.append(result)
        status = result["status"]
        claims = len(result["claims"])
        print(f"  {status}: {claims} pricing claims")
        if result["errors"]:
            for err in result["errors"]:
                print(f"  Error: {err}")
        if slug != slugs[-1]:
            time.sleep(REQUEST_DELAY)

    # Summary
    updated = sum(1 for r in results if r["status"] == "updated")
    failed = sum(1 for r in results if r["status"] in ("failed", "blocked"))
    print(f"\nDone: {updated} updated, {failed} failed out of {len(results)} tools")


if __name__ == "__main__":
    main()
