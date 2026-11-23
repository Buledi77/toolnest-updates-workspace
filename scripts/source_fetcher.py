#!/usr/bin/env python3
"""Safe source fetcher — respectful HTTP fetching with retry, backoff, and throttling.

Provides controlled concurrent fetching of official sources with:
- Configurable timeouts (default 15s)
- Retry with exponential backoff (3 retries: 1s, 2s, 4s)
- Per-domain throttling (max 2 req/s per domain)
- Controlled concurrency (max 3 concurrent fetches)
- ETag/Last-Modified conditional requests
- Content fingerprinting (SHA-256 of normalized HTML)
- Failure logging to data/changes/fetch-failures.json
- Never bypasses CAPTCHA/login/paywall — marks as SOURCE_UNAVAILABLE

Usage:
    python3 scripts/source_fetcher.py --tool semrush    # Fetch sources for one tool
    python3 scripts/source_fetcher.py --all              # Fetch all production tools
    python3 scripts/source_fetcher.py --dry-run          # Show what would be fetched
"""

from __future__ import annotations

import hashlib
import json
import re
import socket
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY_PATH = ROOT / "data" / "sources" / "source-registry.json"
FETCH_FAILURES_PATH = ROOT / "data" / "changes" / "fetch-failures.json"
TOOLS_V1_PATH = ROOT / "data" / "tools-v1.json"
CATALOG_RECON_PATH = ROOT / "data" / "catalog-reconciliation.json"

# Default configuration
DEFAULT_TIMEOUT = 15  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 1  # seconds
DEFAULT_MAX_CONCURRENCY = 3
DEFAULT_RATE_LIMIT = 2  # requests per second per domain
USER_AGENT = "ToolNest-Research/1.0 (https://www.toolnestai.tech)"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def content_fingerprint(html_bytes: bytes) -> str:
    """Compute SHA-256 fingerprint of normalized HTML content.
    
    Normalizes whitespace and removes script/style tags for stable comparison.
    """
    try:
        text = html_bytes.decode("utf-8", errors="replace")
        # Remove scripts and styles
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Take first 100KB to avoid hashing massive pages
        text = text[:100000]
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    except Exception:
        return hashlib.sha256(html_bytes).hexdigest()


def get_domain(url: str) -> str:
    """Extract domain from URL for rate limiting."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return url


class DomainRateLimiter:
    """Per-domain rate limiter using token bucket algorithm."""
    
    def __init__(self, max_requests_per_second: float = DEFAULT_RATE_LIMIT):
        self.max_rps = max_requests_per_second
        self.last_request_time: Dict[str, float] = {}
        self.lock = Lock()
    
    def wait(self, domain: str) -> None:
        """Wait until we can make a request to this domain."""
        with self.lock:
            now = time.monotonic()
            last = self.last_request_time.get(domain, 0)
            min_interval = 1.0 / self.max_rps
            elapsed = now - last
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                # Release lock while sleeping
                self.lock.release()
                try:
                    time.sleep(wait_time)
                finally:
                    self.lock.acquire()
            self.last_request_time[domain] = time.monotonic()


class SourceFetcher:
    """Safe source fetcher with retry, backoff, throttling, and fingerprinting."""
    
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        rate_limit: float = DEFAULT_RATE_LIMIT,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.max_concurrency = max_concurrency
        self.rate_limiter = DomainRateLimiter(rate_limit)
        self.etag_cache: Dict[str, str] = {}
        self.last_modified_cache: Dict[str, str] = {}
        self.failures: List[dict] = []
        self.failures_lock = Lock()
    
    def fetch_url(
        self, url: str, source_id: Optional[str] = None
    ) -> dict:
        """Fetch a single URL with retry and backoff.
        
        Returns:
            Dict with status, content, fingerprint, headers, etc.
        """
        domain = get_domain(url)
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            # Rate limiting
            self.rate_limiter.wait(domain)
            
            try:
                # Build request with conditional headers
                headers = {
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                
                # Add conditional request headers if we have cached values
                if url in self.etag_cache:
                    headers["If-None-Match"] = self.etag_cache[url]
                if url in self.last_modified_cache:
                    headers["If-Modified-Since"] = self.last_modified_cache[url]
                
                req = Request(url, headers=headers)
                
                with urlopen(req, timeout=self.timeout) as response:
                    status_code = response.status
                    response_headers = dict(response.headers)
                    raw_bytes = response.read()
                    
                    # Update conditional request cache
                    etag = response_headers.get("ETag")
                    if etag:
                        self.etag_cache[url] = etag
                    last_modified = response_headers.get("Last-Modified")
                    if last_modified:
                        self.last_modified_cache[url] = last_modified
                    
                    # Check for 304 Not Modified
                    if status_code == 304:
                        return {
                            "status": "not_modified",
                            "url": url,
                            "source_id": source_id,
                            "fingerprint": None,
                            "content_length": 0,
                            "attempt": attempt + 1,
                        }
                    
                    # Check for redirect (3xx)
                    if 300 <= status_code < 400:
                        final_url = response.url if hasattr(response, 'url') else url
                        if final_url != url:
                            return {
                                "status": "redirect",
                                "url": url,
                                "final_url": final_url,
                                "source_id": source_id,
                                "fingerprint": None,
                                "attempt": attempt + 1,
                            }
                    
                    # Success — compute fingerprint
                    fingerprint = content_fingerprint(raw_bytes)
                    
                    # Extract text content (first 50KB)
                    try:
                        text = raw_bytes.decode("utf-8", errors="replace")
                        # Remove scripts and styles
                        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
                        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
                        text = re.sub(r"<[^>]+>", " ", text)
                        text = re.sub(r"\s+", " ", text).strip()[:50000]
                    except Exception:
                        text = ""
                    
                    return {
                        "status": "success",
                        "url": url,
                        "source_id": source_id,
                        "fingerprint": fingerprint,
                        "content_length": len(raw_bytes),
                        "text_content": text,
                        "headers": {k: v for k, v in response_headers.items() if isinstance(k, str)},
                        "attempt": attempt + 1,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
            
            except HTTPError as e:
                last_error = str(e)
                # 403, 401, 407 — likely bot protection, don't retry
                if e.code in (401, 403, 407):
                    return {
                        "status": "unavailable",
                        "url": url,
                        "source_id": source_id,
                        "error": f"HTTP {e.code} — access denied (possible bot protection)",
                        "attempt": attempt + 1,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                # 404 — not found, don't retry
                if e.code == 404:
                    return {
                        "status": "unavailable",
                        "url": url,
                        "source_id": source_id,
                        "error": f"HTTP 404 — not found",
                        "attempt": attempt + 1,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                # 429 — rate limited, wait longer
                if e.code == 429:
                    wait_time = self.backoff_base * (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue
                # Other 5xx — retry
                if e.code >= 500:
                    wait_time = self.backoff_base * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                # Other errors — return as unavailable
                return {
                    "status": "unavailable",
                    "url": url,
                    "source_id": source_id,
                    "error": f"HTTP {e.code}",
                    "attempt": attempt + 1,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            
            except (URLError, socket.timeout, OSError) as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    wait_time = self.backoff_base * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                return {
                    "status": "unavailable",
                    "url": url,
                    "source_id": source_id,
                    "error": f"Network error: {last_error}",
                    "attempt": attempt + 1,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            
            except Exception as e:
                last_error = str(e)
                return {
                    "status": "unavailable",
                    "url": url,
                    "source_id": source_id,
                    "error": f"Unexpected error: {last_error}",
                    "attempt": attempt + 1,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        
        # All retries exhausted
        return {
            "status": "unavailable",
            "url": url,
            "source_id": source_id,
            "error": f"All {self.max_retries + 1} attempts failed: {last_error}",
            "attempt": self.max_retries + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def fetch_tool_sources(self, tool_id: str) -> dict:
        """Fetch all registered sources for a tool.
        
        Returns:
            Dict with overall status and per-source results.
        """
        if not SOURCE_REGISTRY_PATH.is_file():
            return {
                "status": "unavailable",
                "error": "Source registry not found",
                "sources": {},
            }
        
        registry = load_json(SOURCE_REGISTRY_PATH)
        tool_entry = registry.get(tool_id)
        if not tool_entry:
            return {
                "status": "unavailable",
                "error": f"No sources registered for {tool_id}",
                "sources": {},
            }
        
        sources = tool_entry.get("sources", [])
        results = {}
        
        for source in sources:
            url = source.get("source_url", "")
            sid = source.get("source_id", "")
            if not url:
                continue
            
            result = self.fetch_url(url, sid)
            results[sid] = result
            
            # Log failures
            if result.get("status") != "success":
                with self.failures_lock:
                    self.failures.append({
                        "tool_id": tool_id,
                        "source_id": sid,
                        "url": url,
                        "status": result.get("status"),
                        "error": result.get("error"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
        
        # Determine overall status
        statuses = [r.get("status") for r in results.values()]
        if all(s == "success" for s in statuses):
            overall = "success"
        elif any(s == "success" for s in statuses):
            overall = "partial"
        else:
            overall = "unavailable"
        
        return {
            "status": overall,
            "tool_id": tool_id,
            "sources": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def fetch_all_tools(
        self, tool_ids: Optional[List[str]] = None, dry_run: bool = False
    ) -> dict:
        """Fetch sources for all specified tools with controlled concurrency.
        
        Args:
            tool_ids: List of tool IDs to fetch (defaults to all in registry)
            dry_run: If True, only show what would be fetched
        
        Returns:
            Report dict with all fetch results.
        """
        if not SOURCE_REGISTRY_PATH.is_file():
            return {"error": "Source registry not found", "results": {}}
        
        registry = load_json(SOURCE_REGISTRY_PATH)
        
        if tool_ids is None:
            tool_ids = list(registry.keys())
        
        # Filter to production tools only
        production_ids = set()
        if TOOLS_V1_PATH.is_file():
            v1 = load_json(TOOLS_V1_PATH)
            tools = v1.get("tools", []) if isinstance(v1, dict) else v1
            production_ids = {t["id"] for t in tools}
        
        # Filter out expansion-only tools
        expansion_ids = set()
        if CATALOG_RECON_PATH.is_file():
            recon = load_json(CATALOG_RECON_PATH)
            expansion_ids = set(recon.get("expansion_only_tools", []))
        
        tool_ids = [tid for tid in tool_ids if tid in production_ids and tid not in expansion_ids]
        
        if dry_run:
            total_sources = 0
            for tid in tool_ids:
                entry = registry.get(tid, {})
                total_sources += len(entry.get("sources", []))
            return {
                "mode": "dry_run",
                "tools_to_fetch": len(tool_ids),
                "total_sources": total_sources,
                "tool_ids": tool_ids,
            }
        
        # Fetch with controlled concurrency
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_concurrency) as executor:
            future_to_tool = {
                executor.submit(self.fetch_tool_sources, tid): tid
                for tid in tool_ids
            }
            for future in as_completed(future_to_tool):
                tid = future_to_tool[future]
                try:
                    results[tid] = future.result()
                except Exception as e:
                    results[tid] = {
                        "status": "unavailable",
                        "error": str(e),
                        "sources": {},
                    }
        
        # Save failures log
        if self.failures:
            save_json(FETCH_FAILURES_PATH, self.failures)
        
        # Summary
        success_count = sum(1 for r in results.values() if r.get("status") == "success")
        partial_count = sum(1 for r in results.values() if r.get("status") == "partial")
        fail_count = sum(1 for r in results.values() if r.get("status") == "unavailable")
        
        return {
            "mode": "fetch",
            "total_tools": len(tool_ids),
            "success": success_count,
            "partial": partial_count,
            "failed": fail_count,
            "failures": len(self.failures),
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Safe source fetcher")
    parser.add_argument("--tool", type=str, default=None, help="Fetch sources for a specific tool")
    parser.add_argument("--all", action="store_true", help="Fetch all production tools")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fetched")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="Max retry attempts")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_MAX_CONCURRENCY, help="Max concurrent fetches")
    args = parser.parse_args()
    
    fetcher = SourceFetcher(
        timeout=args.timeout,
        max_retries=args.max_retries,
        max_concurrency=args.concurrency,
    )
    
    if args.tool:
        result = fetcher.fetch_tool_sources(args.tool)
        print(f"\nFetch result for {args.tool}:")
        print(f"  Status: {result.get('status')}")
        for sid, sr in result.get("sources", {}).items():
            print(f"  {sid}: {sr.get('status')}")
    elif args.all:
        result = fetcher.fetch_all_tools(dry_run=args.dry_run)
        if args.dry_run:
            print(f"\nDry run: {result.get('total_sources')} sources across {result.get('tools_to_fetch')} tools")
        else:
            print(f"\nFetch results:")
            print(f"  Success: {result.get('success')}")
            print(f"  Partial: {result.get('partial')}")
            print(f"  Failed: {result.get('failed')}")
            print(f"  Total failures: {result.get('failures')}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
