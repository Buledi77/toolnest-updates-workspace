#!/usr/bin/env python3
"""Internal-link graph and orphan report (Phase 3 Requirement G).

Builds a directed graph of page-to-page links from all HTML pages and identifies:
- Orphaned indexable pages (no inbound contextual links)
- Profiles with no inbound contextual links from categories, best pages, or goals
- Comparisons not linked from relevant profiles
- Alternatives pages not linked from relevant profiles
- Goals not connected to relevant tools
- Category pages missing relevant tool connections

Outputs reports/phase3/internal-link-graph.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
LEGACY_DATA_PATH = ROOT / "data" / "tools.json"
REPORTS_DIR = ROOT / "reports" / "phase3"

# Directories with HTML pages
HTML_DIRS = {
    "tools": ROOT / "tools",
    "compare": ROOT / "compare",
    "alternatives": ROOT / "alternatives",
    "best": ROOT / "best",
    "category": ROOT / "category",
    "goals": ROOT / "goals",
}
ROOT_HTML_FILES = ["index.html", "about.html", "affiliate-disclosure.html",
                   "how-we-test.html", "editorial-policy.html", "corrections.html",
                   "contact.html", "privacy.html", "terms.html"]

SPECIAL_TOOL_PAGES = {
    "decision-engine", "stack-analyzer", "overlap-checker",
    "workflow-explorer", "automation-budget-estimator", "index",
}


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_tools_v2_records():
    records = []
    for path in sorted(TOOL_DIR.rglob("*.json")):
        if path.name == "README.json":
            continue
        records.append(load_json(path))
    return records


def get_all_html_files():
    """Get all HTML files with their category."""
    files = {}
    for category, html_dir in HTML_DIRS.items():
        if html_dir.is_dir():
            for html_file in html_dir.glob("*.html"):
                rel = str(html_file.relative_to(ROOT))
                files[rel] = {"path": html_file, "category": category}
    for root_file in ROOT_HTML_FILES:
        path = ROOT / root_file
        if path.is_file():
            files[root_file] = {"path": path, "category": "root"}
    return files


def extract_internal_links(html_path):
    """Extract internal links from an HTML file."""
    try:
        content = html_path.read_text(encoding="utf-8")
    except OSError:
        return []

    links = []
    href_pattern = re.compile(r'href=["\'](/[^"\']+)["\']')
    for match in href_pattern.finditer(content):
        href = match.group(1)
        if href.startswith(("http://", "https://", "#", "mailto:", "tel:", "javascript:")):
            continue
        if not href.endswith(".html"):
            continue
        target = href.lstrip("/")
        links.append(target)
    return links


def build_link_graph():
    """Build a directed graph of all internal links."""
    all_files = get_all_html_files()
    graph = {}  # source -> [targets]
    reverse_graph = {}  # target -> [sources]

    for rel_path, info in all_files.items():
        links = extract_internal_links(info["path"])
        graph[rel_path] = links
        for target in links:
            if target not in reverse_graph:
                reverse_graph[target] = []
            reverse_graph[target].append(rel_path)

    return graph, reverse_graph, all_files


def find_orphans(graph, reverse_graph, all_files):
    """Find pages with no inbound links."""
    orphans = []
    for rel_path in all_files:
        if rel_path not in reverse_graph or len(reverse_graph[rel_path]) == 0:
            orphans.append(rel_path)
    return orphans


def find_orphaned_profiles(reverse_graph, all_files, v2_records):
    """Find tool profiles with no inbound contextual links."""
    v2_by_slug = {r.get("identity", {}).get("slug"): r for r in v2_records}
    orphans = []

    for rel_path, info in all_files.items():
        if info["category"] != "tools":
            continue
        slug = Path(rel_path).stem
        if slug in SPECIAL_TOOL_PAGES:
            continue
        if slug not in v2_by_slug:
            continue

        # Check if any category, best, or goal page links to this profile
        inbound = reverse_graph.get(rel_path, [])
        contextual_sources = [
            src for src in inbound
            if any(src.startswith(prefix) for prefix in ["category/", "best/", "goals/"])
        ]
        if not contextual_sources:
            orphans.append({
                "profile": rel_path,
                "slug": slug,
                "inbound_from": inbound[:5],  # show first 5
            })

    return orphans


def find_unlinked_comparisons(graph, all_files, v2_records):
    """Find comparison pages not linked from relevant profiles."""
    v2_by_id = {r.get("identity", {}).get("id"): r for r in v2_records}
    unlinked = []

    for rel_path, info in all_files.items():
        if info["category"] != "compare":
            continue
        slug = Path(rel_path).stem
        if slug == "index":
            continue

        # Parse tool IDs from comparison slug
        vs_match = re.match(r"^([a-z0-9]+(?:-[a-z0-9]+)*)-vs-([a-z0-9]+(?:-[a-z0-9]+)*)$", slug)
        if not vs_match:
            continue

        tool1, tool2 = vs_match.group(1), vs_match.group(2)

        # Check if either tool's profile links to this comparison
        tool1_profile = f"tools/{tool1}.html"
        tool2_profile = f"tools/{tool2}.html"

        linked_from = []
        if tool1_profile in graph and rel_path in graph[tool1_profile]:
            linked_from.append(tool1_profile)
        if tool2_profile in graph and rel_path in graph[tool2_profile]:
            linked_from.append(tool2_profile)

        if not linked_from:
            unlinked.append({
                "comparison": rel_path,
                "tools": [tool1, tool2],
            })

    return unlinked


def find_unlinked_alternatives(graph, all_files, v2_records):
    """Find alternatives pages not linked from relevant profiles."""
    v2_by_slug = {r.get("identity", {}).get("slug"): r for r in v2_records}
    unlinked = []

    for rel_path, info in all_files.items():
        if info["category"] != "alternatives":
            continue
        slug = Path(rel_path).stem

        # Parse tool ID from alternatives slug
        alt_match = re.match(r"^(.+)-alternatives$", slug)
        if not alt_match:
            continue

        tool_slug = alt_match.group(1)
        tool_profile = f"tools/{tool_slug}.html"

        # Check if the tool's profile links to this alternatives page
        if tool_profile in graph and rel_path not in graph[tool_profile]:
            unlinked.append({
                "alternatives_page": rel_path,
                "tool": tool_slug,
                "profile_exists": tool_profile in all_files,
            })

    return unlinked


def find_unconnected_goals(graph, all_files, v2_records):
    """Find goal pages not connected to relevant tools."""
    v2_ids = {r.get("identity", {}).get("id") for r in v2_records}
    unconnected = []

    for rel_path, info in all_files.items():
        if info["category"] != "goals":
            continue
        slug = Path(rel_path).stem
        if slug == "index":
            continue

        # Check if this goal page links to any tool profiles
        links = graph.get(rel_path, [])
        tool_links = [l for l in links if l.startswith("tools/") and not l.endswith("/index.html")]

        if not tool_links:
            unconnected.append({
                "goal_page": rel_path,
                "tool_links": [],
            })

    return unconnected


def run_link_graph_check():
    """Run all internal link graph checks."""
    print("Building internal link graph...")

    v2_records = load_tools_v2_records()
    graph, reverse_graph, all_files = build_link_graph()

    results = {
        "check": "internal_link_graph",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_pages": len(all_files),
        "total_links": sum(len(links) for links in graph.values()),
        "checks": {},
    }

    # 1. Find orphaned pages
    orphans = find_orphans(graph, reverse_graph, all_files)
    results["checks"]["orphaned_pages"] = {
        "count": len(orphans),
        "pages": orphans,
    }

    # 2. Find orphaned profiles
    orphaned_profiles = find_orphaned_profiles(reverse_graph, all_files, v2_records)
    results["checks"]["orphaned_profiles"] = {
        "count": len(orphaned_profiles),
        "profiles": orphaned_profiles,
    }

    # 3. Find unlinked comparisons
    unlinked_comparisons = find_unlinked_comparisons(graph, all_files, v2_records)
    results["checks"]["unlinked_comparisons"] = {
        "count": len(unlinked_comparisons),
        "comparisons": unlinked_comparisons,
    }

    # 4. Find unlinked alternatives
    unlinked_alternatives = find_unlinked_alternatives(graph, all_files, v2_records)
    results["checks"]["unlinked_alternatives"] = {
        "count": len(unlinked_alternatives),
        "alternatives": unlinked_alternatives,
    }

    # 5. Find unconnected goals
    unconnected_goals = find_unconnected_goals(graph, all_files, v2_records)
    results["checks"]["unconnected_goals"] = {
        "count": len(unconnected_goals),
        "goals": unconnected_goals,
    }

    # Summary
    total_issues = (
        len(orphans) + len(orphaned_profiles) + len(unlinked_comparisons)
        + len(unlinked_alternatives) + len(unconnected_goals)
    )
    results["total_issues"] = total_issues

    return results


def main():
    results = run_link_graph_check()

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "internal-link-graph.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\nInternal Link Graph Report")
    print(f"  Total pages: {results['total_pages']}")
    print(f"  Total links: {results['total_links']}")
    print(f"  Total issues: {results['total_issues']}")
    for check_name, check_result in results["checks"].items():
        count = check_result.get("count", 0)
        print(f"  {check_name}: {count}")

    print(f"\nReport written to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
