#!/usr/bin/env python3
"""Page Quality Gate — deterministic quality classification for ToolNest pages.

Evaluates all tool reviews, comparisons, alternatives, best-of, and category pages
using structured data signals rather than content length alone.

Quality grades:
  A — Strong decision-ready content
  B — Publishable but needing depth
  C — Insufficient/unverified content requiring upgrade

Run: python3 scripts/page_quality_gate.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from content_metrics import measure, unique_marked_sections

ROOT = Path(__file__).resolve().parents[1]
TOOLS_V2_DIR = ROOT / "data" / "tools-v2"
TOOLS_JSON = ROOT / "data" / "tools.json"


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


def load_catalog() -> dict[str, dict]:
    """Load tools.json catalog as id->tool map."""
    data = json.loads(TOOLS_JSON.read_text())
    return {t["id"]: t for t in data.get("tools", [])}


@dataclass
class QualitySignals:
    """Decision-relevant signals for a page."""
    words: int = 0
    sections: int = 0
    unique_marked_sections: int = 0
    has_best_for: bool = False
    has_skip_if: bool = False
    has_alternatives: bool = False
    has_comparisons: bool = False
    has_comparisons_html: bool = False  # comparison pages exist on disk
    has_comparisons_v2: bool = False    # structured relationships in tools-v2
    has_evidence_sources: bool = False
    has_evidence_sources_v2: bool = False   # formal evidence in tools-v2
    has_evidence_catalog: bool = False       # catalog/HTML coverage
    has_limitations: bool = False
    has_pricing_info: bool = False
    has_faq: bool = False
    has_verdict: bool = False
    has_scenario_recommendation: bool = False
    editorial_tier: str = "?"
    pub_quality_status: str = "?"
    review_status: str = "?"
    # For comparisons
    has_choose_a: bool = False
    has_choose_b: bool = False
    has_switching_reasons: bool = False
    # For alternatives
    has_why_replace: bool = False
    has_trade_offs: bool = False
    # For best-of
    has_ranked_selection: bool = False
    has_selection_reasons: bool = False
    has_scenario_section: bool = False
    has_sources_section: bool = False
    has_bottom_line: bool = False
    # For categories
    has_sub_use_cases: bool = False
    has_navigation_routes: bool = False
    # Boilerplate detection
    boilerplate_count: int = 0


BOILERPLATE_PATTERNS = [
    "is included in toolnest for people looking for",
    "check the official site for current details",
    "sits in the .* category and is evaluated against",
    "the strengths below come from the published product information",
    "toolnest has not claimed hands-on testing for this product",
    "the decision comes down to whether the workflow matches",
]


def count_boilerplate(content_text: str) -> int:
    """Count boilerplate patterns in page content."""
    import re
    count = 0
    for pattern in BOILERPLATE_PATTERNS:
        if re.search(pattern, content_text, re.IGNORECASE):
            count += 1
    return count


def check_research_based_disclaimer(slug: str) -> bool:
    """Check if a tool review has a research-based disclaimer in its sources section.

    A research-based disclaimer means the review explicitly states it is based on
    published product information rather than genuine evidence (hands-on testing,
    verified pricing, evidence ledger sources).

    Returns True if the review has such a disclaimer, False otherwise.
    """
    import re
    html_path = ROOT / "tools" / f"{slug}.html"
    if not html_path.exists():
        return False
    content = html_path.read_text()
    # Look for the sources section
    sources_match = re.search(r'id="sources"(.*?)(?=</section>|<section)', content, re.DOTALL)
    if sources_match:
        text = re.sub(r'<[^>]+>', '', sources_match.group(1)).lower()
        if "research-based" in text or "based on published product information" in text:
            return True
    return False


def evaluate_tool_review(slug: str, metrics, unique) -> QualitySignals:
    """Evaluate a tool review page's quality signals."""
    sig = QualitySignals()
    rel = f"tools/{slug}.html"
    m = metrics.get(rel)
    if m:
        sig.words = m.words
        sig.sections = len(m.sections)
        sig.unique_marked_sections = len(unique.get(rel, set()))
        # Check section text for decision signals
        section_texts = " ".join(s.fingerprint for s in m.sections)
        if "best for" in section_texts or "who should use" in section_texts:
            sig.has_best_for = True
        if "skip" in section_texts or "not for" in section_texts or "not recommended" in section_texts:
            sig.has_skip_if = True
        if "limitation" in section_texts or "cost trap" in section_texts:
            sig.has_limitations = True
        if "pricing" in section_texts or "price" in section_texts or "plan" in section_texts:
            sig.has_pricing_info = True
        if "faq" in section_texts or "questions" in section_texts:
            sig.has_faq = True
        if "verdict" in section_texts or "decision" in section_texts:
            sig.has_verdict = True
        if "alternatives" in section_texts or "comparison" in section_texts:
            sig.has_alternatives = True
        if "scenario" in section_texts or "choose" in section_texts:
            sig.has_scenario_recommendation = True
        # Boilerplate detection
        sig.boilerplate_count = count_boilerplate(section_texts)

    # Check for comparison pages on disk (independent of tools-v2)
    compare_dir = ROOT / "compare"
    if compare_dir.exists():
        for f in compare_dir.iterdir():
            if f.suffix == ".html" and slug in f.stem:
                sig.has_comparisons_html = True
                sig.has_comparisons = True  # comparisons exist regardless of v2
                break

    # Check for alternatives page on disk (independent of tools-v2)
    alt_path = ROOT / "alternatives" / f"{slug}-alternatives.html"
    if alt_path.exists():
        sig.has_evidence_catalog = True

    v2 = load_v2(slug)
    if v2:
        editorial = v2.get("editorial", {})
        sig.editorial_tier = editorial.get("editorial_tier", "?")
        sig.review_status = editorial.get("review_status", "?")
        if editorial.get("best_for"):
            sig.has_best_for = True
        if editorial.get("not_recommended_for"):
            sig.has_skip_if = True
        relationships = v2.get("relationships", {})
        if relationships.get("alternatives"):
            sig.has_alternatives = True
        if relationships.get("meaningful_comparisons"):
            sig.has_comparisons_v2 = True
            sig.has_comparisons = True
        evidence = v2.get("evidence", {})
        if evidence.get("source_ids"):
            sig.has_evidence_sources_v2 = True
            sig.has_evidence_sources = True
        factual = v2.get("factual_profile", {})
        if factual.get("limitations"):
            sig.has_limitations = True
        pub = v2.get("publishing", {})
        sig.pub_quality_status = pub.get("content_quality_status", "?")

    return sig


def evaluate_compare_page(slug: str, metrics, unique) -> QualitySignals:
    """Evaluate a comparison page's quality signals."""
    sig = QualitySignals()
    rel = f"compare/{slug}.html"
    m = metrics.get(rel)
    if m:
        sig.words = m.words
        sig.sections = len(m.sections)
        sig.unique_marked_sections = len(unique.get(rel, set()))
        section_texts = " ".join(s.fingerprint for s in m.sections)
        if "choose" in section_texts or "should pick" in section_texts:
            sig.has_choose_a = True
            sig.has_choose_b = True
        if "switch" in section_texts or "trade-off" in section_texts:
            sig.has_switching_reasons = True
        if "verdict" in section_texts or "decision" in section_texts:
            sig.has_verdict = True
    return sig


def evaluate_alternatives_page(slug: str, metrics, unique) -> QualitySignals:
    """Evaluate an alternatives page's quality signals."""
    sig = QualitySignals()
    rel = f"alternatives/{slug}.html"
    m = metrics.get(rel)
    if m:
        sig.words = m.words
        sig.sections = len(m.sections)
        sig.unique_marked_sections = len(unique.get(rel, set()))
        section_texts = " ".join(s.fingerprint for s in m.sections)
        if "why" in section_texts and ("replace" in section_texts or "switch" in section_texts):
            sig.has_why_replace = True
        if "trade-off" in section_texts or "trade off" in section_texts:
            sig.has_trade_offs = True
    return sig


def evaluate_best_page(slug: str, metrics, unique) -> QualitySignals:
    """Evaluate a best-of page's quality signals."""
    sig = QualitySignals()
    rel = f"best/{slug}.html"
    m = metrics.get(rel)
    if m:
        sig.words = m.words
        sig.sections = len(m.sections)
        sig.unique_marked_sections = len(unique.get(rel, set()))
        section_texts = " ".join(s.fingerprint for s in m.sections)
        section_ids = [s.identifier for s in m.sections]
        if "rank" in section_texts or "best" in section_texts:
            sig.has_ranked_selection = True
        if "reason" in section_texts or "why" in section_texts:
            sig.has_selection_reasons = True
        # Additional decision content signals
        if "scenario" in section_texts or "which pick" in section_texts or "fits your" in section_texts:
            sig.has_scenario_section = True
        if "sources" in section_ids or "how this page" in section_texts or "checked" in section_texts:
            sig.has_sources_section = True
        if "bottom" in section_texts or "conclusion" in section_texts or "final" in section_texts:
            sig.has_bottom_line = True
    return sig


def evaluate_category_page(slug: str, metrics, unique) -> QualitySignals:
    """Evaluate a category page's quality signals."""
    sig = QualitySignals()
    rel = f"category/{slug}.html"
    m = metrics.get(rel)
    if m:
        sig.words = m.words
        sig.sections = len(m.sections)
        sig.unique_marked_sections = len(unique.get(rel, set()))
        section_texts = " ".join(s.fingerprint for s in m.sections)
        section_ids = [s.identifier for s in m.sections]
        # Sub-use-case navigation
        if "use case" in section_texts or "sub-use" in section_texts or "use-case" in section_texts:
            sig.has_sub_use_cases = True
        # Navigation routes (guides, comparisons, alternatives links)
        if "guides" in section_ids or "comparisons" in section_ids or "alternatives" in section_ids:
            sig.has_navigation_routes = True
    return sig


def grade_tool_review(sig: QualitySignals, slug: str = "") -> tuple[str, int, list[str]]:
    """Grade a tool review page. Returns (grade, score, missing_elements).

    Grade A requires:
    - High score (≥8)
    - Low boilerplate (<3 patterns)
    - Genuine evidence OR substantive content depth:
      - evidence_sources from tools-v2, OR
      - words ≥ 800 (substantive analysis), OR
      - NOT a research-based review (no disclaimer about lacking evidence)

    A research-based review with thin content (< 800 words) and no genuine
    evidence cannot reach Grade A, even if structural signals are complete.
    This prevents tools-v2 relationships from inflating grades.
    """
    score = 0
    missing = []

    # Word count — Grade A requires substantive length
    if sig.words >= 1000:
        score += 3
    elif sig.words >= 800:
        score += 2
    elif sig.words >= 450:
        score += 1
    else:
        missing.append("low_word_count")

    # Unique marked sections — original decision value
    if sig.unique_marked_sections >= 5:
        score += 3
    elif sig.unique_marked_sections >= 3:
        score += 2
    elif sig.unique_marked_sections >= 1:
        score += 1
    else:
        missing.append("no_unique_sections")

    # Decision signals
    if sig.has_best_for:
        score += 1
    else:
        missing.append("no_best_for")

    if sig.has_skip_if:
        score += 1
    else:
        missing.append("no_skip_if")

    if sig.has_limitations:
        score += 1
    else:
        missing.append("no_limitations")

    if sig.has_alternatives:
        score += 1
    else:
        missing.append("no_alternatives")

    if sig.has_comparisons:
        score += 1
    else:
        missing.append("no_comparisons")

    if sig.has_evidence_sources:
        score += 1
    else:
        missing.append("no_evidence_sources")

    if sig.has_verdict:
        score += 1
    else:
        missing.append("no_verdict")

    if sig.has_pricing_info:
        score += 1
    else:
        missing.append("no_pricing_info")

    if sig.has_faq:
        score += 1
    else:
        missing.append("no_faq")

    # Boilerplate penalty — deduct points for generic filler
    if sig.boilerplate_count >= 4:
        score -= 3
        missing.append("high_boilerplate")
    elif sig.boilerplate_count >= 2:
        score -= 1
        missing.append("some_boilerplate")

    # Research-based penalty — a review that explicitly disclaims evidence
    # cannot reach Grade A without substantive content depth
    is_research_based = check_research_based_disclaimer(slug)
    if is_research_based:
        missing.append("research_based")

    # Grade assignment — Grade A requires high score, low boilerplate,
    # AND genuine evidence or substantive depth
    has_genuine_evidence = sig.has_evidence_sources
    has_substantive_depth = sig.words >= 800
    has_justification = has_genuine_evidence or has_substantive_depth or not is_research_based

    if score >= 8 and sig.boilerplate_count < 3 and has_justification:
        grade = "A"
    elif score >= 5:
        grade = "B"
    else:
        grade = "C"

    return grade, score, missing


def grade_compare_page(sig: QualitySignals) -> tuple[str, int, list[str]]:
    """Grade a comparison page."""
    score = 0
    missing = []

    if sig.words >= 600:
        score += 2
    elif sig.words >= 300:
        score += 1
    else:
        missing.append("low_word_count")

    if sig.unique_marked_sections >= 2:
        score += 2
    elif sig.unique_marked_sections >= 1:
        score += 1
    else:
        missing.append("no_unique_sections")

    if sig.has_choose_a:
        score += 2
    else:
        missing.append("no_choose_logic")

    if sig.has_switching_reasons:
        score += 1
    else:
        missing.append("no_switching_reasons")

    if sig.has_verdict:
        score += 1
    else:
        missing.append("no_verdict")

    if score >= 5:
        grade = "A"
    elif score >= 3:
        grade = "B"
    else:
        grade = "C"

    return grade, score, missing


def grade_alternatives_page(sig: QualitySignals) -> tuple[str, int, list[str]]:
    """Grade an alternatives page."""
    score = 0
    missing = []

    if sig.words >= 400:
        score += 2
    elif sig.words >= 200:
        score += 1
    else:
        missing.append("low_word_count")

    if sig.unique_marked_sections >= 2:
        score += 2
    elif sig.unique_marked_sections >= 1:
        score += 1
    else:
        missing.append("no_unique_sections")

    if sig.has_why_replace:
        score += 2
    else:
        missing.append("no_why_replace")

    if sig.has_trade_offs:
        score += 1
    else:
        missing.append("no_trade_offs")

    if score >= 4:
        grade = "A"
    elif score >= 2:
        grade = "B"
    else:
        grade = "C"

    return grade, score, missing


def grade_best_page(sig: QualitySignals) -> tuple[str, int, list[str]]:
    """Grade a best-of page. Grade A requires comprehensive decision content."""
    score = 0
    missing = []

    # Word count — Grade A requires substantive depth
    if sig.words >= 1200:
        score += 3
    elif sig.words >= 600:
        score += 2
    elif sig.words >= 300:
        score += 1
    else:
        missing.append("low_word_count")

    # Section count — Grade A requires multiple decision sections
    if sig.sections >= 9:
        score += 3
    elif sig.sections >= 7:
        score += 2
    elif sig.sections >= 4:
        score += 1
    else:
        missing.append("too_few_sections")

    # Unique marked sections — original decision value
    if sig.unique_marked_sections >= 5:
        score += 2
    elif sig.unique_marked_sections >= 2:
        score += 1
    else:
        missing.append("no_unique_sections")

    if sig.has_ranked_selection:
        score += 1
    else:
        missing.append("no_ranked_selection")

    if sig.has_selection_reasons:
        score += 1
    else:
        missing.append("no_selection_reasons")

    # Scenario recommendations — critical for decision value
    if sig.has_scenario_section:
        score += 2
    else:
        missing.append("no_scenarios")

    # Sources section — trust signal
    if sig.has_sources_section:
        score += 1
    else:
        missing.append("no_sources")

    # Bottom line / conclusion
    if sig.has_bottom_line:
        score += 1
    else:
        missing.append("no_bottom_line")

    # Grade assignment — Grade A requires comprehensive content
    if score >= 9 and sig.sections >= 7:
        grade = "A"
    elif score >= 5:
        grade = "B"
    else:
        grade = "C"

    return grade, score, missing


def priority(grade: str, page_type: str, words: int) -> str:
    """Determine upgrade priority based on grade and page importance."""
    if grade == "A":
        return "none"
    if page_type == "tool_review" and words < 450:
        return "critical"
    if page_type == "tool_review" and grade == "C":
        return "high"
    if page_type == "compare" and grade == "C":
        return "high"
    if page_type == "best" and grade == "C":
        return "medium"
    if grade == "B":
        return "medium"
    return "low"


def main() -> None:
    catalog = load_catalog()

    # Measure all HTML pages
    metrics = {}
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        if ".git" not in path.parts and rel not in {"404.html", "googlef7f3d54afb5d5344.html"}:
            metrics[rel] = measure(path.read_text())

    unique = unique_marked_sections(metrics)

    results = []

    # Tool reviews
    for slug in sorted(catalog.keys()):
        sig = evaluate_tool_review(slug, metrics, unique)
        grade, score, missing = grade_tool_review(sig, slug)
        pri = priority(grade, "tool_review", sig.words)
        results.append({
            "path": f"/tools/{slug}.html",
            "type": "tool_review",
            "grade": grade,
            "score": score,
            "words": sig.words,
            "sections": sig.sections,
            "unique_marked": sig.unique_marked_sections,
            "editorial_tier": sig.editorial_tier,
            "pub_quality": sig.pub_quality_status,
            "missing": missing,
            "priority": pri,
        })

    # Compare pages
    for path in sorted((ROOT / "compare").glob("*.html")):
        slug = path.stem
        if slug == "index":
            continue
        sig = evaluate_compare_page(slug, metrics, unique)
        grade, score, missing = grade_compare_page(sig)
        pri = priority(grade, "compare", sig.words)
        results.append({
            "path": f"/compare/{slug}.html",
            "type": "compare",
            "grade": grade,
            "score": score,
            "words": sig.words,
            "sections": sig.sections,
            "unique_marked": sig.unique_marked_sections,
            "missing": missing,
            "priority": pri,
        })

    # Alternatives pages
    for path in sorted((ROOT / "alternatives").glob("*.html")):
        slug = path.stem
        if slug == "index":
            continue
        sig = evaluate_alternatives_page(slug, metrics, unique)
        grade, score, missing = grade_alternatives_page(sig)
        pri = priority(grade, "alternatives", sig.words)
        results.append({
            "path": f"/alternatives/{slug}.html",
            "type": "alternatives",
            "grade": grade,
            "score": score,
            "words": sig.words,
            "sections": sig.sections,
            "unique_marked": sig.unique_marked_sections,
            "missing": missing,
            "priority": pri,
        })

    # Best-of pages
    for path in sorted((ROOT / "best").glob("*.html")):
        slug = path.stem
        if slug == "index":
            continue
        sig = evaluate_best_page(slug, metrics, unique)
        grade, score, missing = grade_best_page(sig)
        pri = priority(grade, "best", sig.words)
        results.append({
            "path": f"/best/{slug}.html",
            "type": "best",
            "grade": grade,
            "score": score,
            "words": sig.words,
            "sections": sig.sections,
            "unique_marked": sig.unique_marked_sections,
            "missing": missing,
            "priority": pri,
        })

    # Category pages
    for path in sorted((ROOT / "category").glob("*.html")):
        slug = path.stem
        if slug == "index":
            continue
        sig = evaluate_category_page(slug, metrics, unique)
        # Grade category pages based on content signals
        cat_score = 0
        cat_missing = []
        if sig.words >= 500:
            cat_score += 2
        elif sig.words >= 300:
            cat_score += 1
        else:
            cat_missing.append("low_word_count")
        if sig.has_sub_use_cases:
            cat_score += 2
        else:
            cat_missing.append("no_sub_use_cases")
        if sig.has_navigation_routes:
            cat_score += 1
        else:
            cat_missing.append("no_navigation_routes")
        if sig.unique_marked_sections >= 2:
            cat_score += 1
        if cat_score >= 4:
            grade = "A"
        elif cat_score >= 2:
            grade = "B"
        else:
            grade = "C"
        results.append({
            "path": f"/category/{slug}.html",
            "type": "category",
            "grade": grade,
            "score": cat_score,
            "words": sig.words,
            "sections": sig.sections,
            "unique_marked": sig.unique_marked_sections,
            "missing": cat_missing,
            "priority": "low" if grade == "A" else "medium",
        })

    # Compute upgrade queue (sorted by priority)
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
    upgrade_queue = sorted(
        [r for r in results if r["priority"] != "none"],
        key=lambda r: (priority_order.get(r["priority"], 5), -r["score"]),
    )

    # Write JSON report
    report = {
        "total_pages": len(results),
        "grade_distribution": {},
        "priority_distribution": {},
        "upgrade_queue": upgrade_queue,
        "pages": results,
    }

    # Compute distributions
    for r in results:
        key = f"{r['type']}:{r['grade']}"
        report["grade_distribution"][key] = report["grade_distribution"].get(key, 0) + 1
        report["priority_distribution"][r["priority"]] = report["priority_distribution"].get(r["priority"], 0) + 1

    report_path = ROOT / "docs" / "internal" / "QUALITY-REPORT.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    # Print summary
    print(f"Page Quality Gate Report: {report_path}")
    print(f"Total pages evaluated: {len(results)}")
    print()
    print("Grade distribution:")
    for key, count in sorted(report["grade_distribution"].items()):
        print(f"  {key}: {count}")
    print()
    print("Priority distribution:")
    for pri, count in sorted(report["priority_distribution"].items()):
        print(f"  {pri}: {count}")
    print()

    # Print upgrade queue (already computed above for JSON report)
    print(f"Upgrade queue ({len(upgrade_queue)} pages):")
    for r in upgrade_queue[:20]:
        missing_str = ", ".join(r["missing"][:3]) if r["missing"] else "none"
        print(f"  [{r['priority'].upper()}] {r['path']} (grade={r['grade']}, words={r['words']}, missing={missing_str})")
    if len(upgrade_queue) > 20:
        print(f"  ... and {len(upgrade_queue) - 20} more")

    # Print flagship SEO cluster
    print()
    print("Flagship SEO cluster:")
    seo_tools = ["semrush", "ahrefs", "mozpro", "screamingfrog", "surferseo"]
    for slug in seo_tools:
        r = next((x for x in results if x["path"] == f"/tools/{slug}.html"), None)
        if r:
            print(f"  {slug}: grade={r['grade']} score={r['score']} words={r['words']} tier={r.get('editorial_tier', '?')} missing={r['missing']}")

    print()
    print(f"Full report: {report_path}")


if __name__ == "__main__":
    main()
