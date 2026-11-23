#!/usr/bin/env python3
"""Audit all 147 public catalog tools for cross-layer consistency.

Checks each tool against:
- v1 record exists
- v2 record exists
- Profile HTML exists
- Tool appears in tools directory
- Tool appears in search index
- Tool appears in sitemap
- Canonical URL matches expected pattern
- Robots meta matches expected directive
- Referenced logo file exists on disk
- If affiliate URL present, entry in affiliate registry

Output: reports/phase3/147-tool-consistency-matrix.json
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def load_tools():
    with open(BASE / "data/tools.json") as f:
        return json.load(f)["tools"]

def load_v1():
    with open(BASE / "data/tools-v1.json") as f:
        return {t["id"]: t for t in json.load(f)["tools"]}

def load_v2():
    v2 = {}
    v2_dir = BASE / "data/tools-v2"
    for root, dirs, files in os.walk(v2_dir):
        for fname in files:
            if fname.endswith(".json"):
                fpath = os.path.join(root, fname)
                with open(fpath) as f:
                    record = json.load(f)
                tid = record.get("identity", {}).get("id", "")
                if not tid:
                    # Try filename
                    tid = fname.replace(".json", "")
                v2[tid] = record
    return v2

def load_search_index():
    with open(BASE / "data/indexes/tool-search-index.json") as f:
        data = json.load(f)
    docs = data.get("documents", [])
    return {d["id"]: d for d in docs}

def load_sitemap():
    tree = ET.parse(BASE / "sitemap.xml")
    root = tree.getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []
    for url_elem in root.findall(".//sm:url/sm:loc", ns):
        if url_elem.text:
            urls.append(url_elem.text.strip())
    return urls

def load_directory():
    with open(BASE / "tools/index.html") as f:
        content = f.read()
    links = re.findall(r"href=[\"'](/tools/[^\"']+\.html)[\"']", content)
    # Extract tool slugs from links
    slugs = set()
    for link in links:
        slug = link.replace("/tools/", "").replace(".html", "")
        if slug and slug != "index":
            slugs.add(slug)
    return slugs

def load_affiliate_registry():
    with open(BASE / "data/monetization/affiliate-registry.json") as f:
        data = json.load(f)
    entries = data.get("entries", [])
    return {e["tool_id"]: e for e in entries}

def check_html(tool_id):
    html_path = BASE / "tools" / f"{tool_id}.html"
    if not html_path.exists():
        return None, None, None
    with open(html_path) as f:
        content = f.read()
    # Check canonical
    canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', content)
    canonical = canonical_match.group(1) if canonical_match else None
    # Check robots
    robots_match = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', content)
    robots = robots_match.group(1) if robots_match else None
    return html_path, canonical, robots

def audit():
    tools = load_tools()
    v1 = load_v1()
    v2 = load_v2()
    search_index = load_search_index()
    sitemap_urls = load_sitemap()
    directory_slugs = load_directory()
    affiliate_registry = load_affiliate_registry()

    # Build sitemap tool set
    sitemap_tools = set()
    for url in sitemap_urls:
        match = re.search(r"/tools/([^/]+\.html)$", url)
        if match:
            slug = match.group(1).replace(".html", "")
            sitemap_tools.add(slug)

    results = []
    summary = {
        "total_tools": len(tools),
        "checks": {},
        "contradictions": [],
        "pass_count": 0,
        "fail_count": 0,
    }

    check_names = [
        "v1_exists", "v2_exists", "html_exists", "in_directory",
        "in_search_index", "in_sitemap", "canonical_ok", "robots_ok",
        "logo_exists", "affiliate_registry_ok"
    ]
    for cn in check_names:
        summary["checks"][cn] = {"pass": 0, "fail": 0, "details": []}

    for tool in tools:
        tid = tool["id"]
        tresult = {"tool_id": tid, "name": tool["name"], "checks": {}}

        # 1. V1 exists
        v1_ok = tid in v1
        tresult["checks"]["v1_exists"] = v1_ok
        summary["checks"]["v1_exists"]["pass" if v1_ok else "fail"] += 1
        if not v1_ok:
            summary["checks"]["v1_exists"]["details"].append(tid)

        # 2. V2 exists
        v2_ok = tid in v2
        tresult["checks"]["v2_exists"] = v2_ok
        summary["checks"]["v2_exists"]["pass" if v2_ok else "fail"] += 1
        if not v2_ok:
            summary["checks"]["v2_exists"]["details"].append(tid)

        # 3. HTML exists
        html_path, canonical, robots = check_html(tid)
        html_ok = html_path is not None
        tresult["checks"]["html_exists"] = html_ok
        summary["checks"]["html_exists"]["pass" if html_ok else "fail"] += 1
        if not html_ok:
            summary["checks"]["html_exists"]["details"].append(tid)

        # 4. In directory
        in_dir = tid in directory_slugs
        tresult["checks"]["in_directory"] = in_dir
        summary["checks"]["in_directory"]["pass" if in_dir else "fail"] += 1
        if not in_dir:
            summary["checks"]["in_directory"]["details"].append(tid)

        # 5. In search index
        in_si = tid in search_index
        tresult["checks"]["in_search_index"] = in_si
        summary["checks"]["in_search_index"]["pass" if in_si else "fail"] += 1
        if not in_si:
            summary["checks"]["in_search_index"]["details"].append(tid)

        # 6. In sitemap
        in_sm = tid in sitemap_tools
        tresult["checks"]["in_sitemap"] = in_sm
        summary["checks"]["in_sitemap"]["pass" if in_sm else "fail"] += 1
        if not in_sm:
            summary["checks"]["in_sitemap"]["details"].append(tid)

        # 7. Canonical OK
        expected_canonical = f"https://www.toolnestai.tech/tools/{tid}.html"
        canonical_ok = (canonical == expected_canonical) if canonical else (not html_ok)
        tresult["checks"]["canonical_ok"] = canonical_ok
        tresult["checks"]["canonical_actual"] = canonical
        summary["checks"]["canonical_ok"]["pass" if canonical_ok else "fail"] += 1
        if not canonical_ok and html_ok:
            summary["checks"]["canonical_ok"]["details"].append(f"{tid}: {canonical}")

        # 8. Robots OK (public tools should be index,follow)
        robots_ok = True
        if robots:
            robots_ok = "index" in robots and "noindex" not in robots
        elif html_ok:
            robots_ok = False  # HTML exists but no robots meta
        tresult["checks"]["robots_ok"] = robots_ok
        tresult["checks"]["robots_actual"] = robots
        summary["checks"]["robots_ok"]["pass" if robots_ok else "fail"] += 1
        if not robots_ok:
            summary["checks"]["robots_ok"]["details"].append(f"{tid}: {robots}")

        # 9. Logo exists
        logo_path = tool.get("logo", "")
        logo_ok = True
        if logo_path:
            abs_logo = BASE / logo_path.lstrip("/")
            logo_ok = abs_logo.exists()
        tresult["checks"]["logo_exists"] = logo_ok
        summary["checks"]["logo_exists"]["pass" if logo_ok else "fail"] += 1
        if not logo_ok:
            summary["checks"]["logo_exists"]["details"].append(f"{tid}: {logo_path}")

        # 10. Affiliate registry check
        affiliate_url = tool.get("affiliateUrl", "")
        aff_ok = True
        if affiliate_url:
            aff_ok = tid in affiliate_registry
        tresult["checks"]["affiliate_registry_ok"] = aff_ok
        summary["checks"]["affiliate_registry_ok"]["pass" if aff_ok else "fail"] += 1
        if not aff_ok and affiliate_url:
            summary["checks"]["affiliate_registry_ok"]["details"].append(tid)

        # Check for contradictions
        contradictions = []
        if v2_ok and html_ok:
            v2_record = v2[tid]
            v2_pub = v2_record.get("publishing", {})
            v2_index = v2_pub.get("indexability", "")
            if v2_index == "noindex" and robots and "index" in robots:
                contradictions.append(f"v2 says {v2_index} but HTML says {robots}")
            elif v2_index == "index" and robots and "noindex" in robots:
                contradictions.append(f"v2 says {v2_index} but HTML says {robots}")
        if contradictions:
            tresult["contradictions"] = contradictions
            summary["contradictions"].append({"tool_id": tid, "issues": contradictions})

        # Overall pass/fail
        all_checks = [
            v1_ok, v2_ok, html_ok, in_dir, in_si, in_sm,
            canonical_ok, robots_ok, logo_ok, aff_ok
        ]
        tresult["overall"] = "PASS" if all(all_checks) else "FAIL"
        if tresult["overall"] == "PASS":
            summary["pass_count"] += 1
        else:
            summary["fail_count"] += 1

        results.append(tresult)

    report = {
        "summary": summary,
        "tools": results,
    }

    os.makedirs(BASE / "reports/phase3", exist_ok=True)
    with open(BASE / "reports/phase3/147-tool-consistency-matrix.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"Audit complete: {summary['pass_count']} PASS, {summary['fail_count']} FAIL out of {summary['total_tools']}")
    print(f"Contradictions found: {len(summary['contradictions'])}")
    for cn in check_names:
        p = summary["checks"][cn]["pass"]
        fa = summary["checks"][cn]["fail"]
        if fa > 0:
            print(f"  {cn}: {p} pass, {fa} fail - {summary['checks'][cn]['details'][:5]}")

if __name__ == "__main__":
    audit()
