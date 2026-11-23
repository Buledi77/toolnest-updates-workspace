#!/usr/bin/env python3
"""
Trust Language Auditor for ToolNest.

Scans all public HTML pages for trust-related keywords and classifies
each occurrence to ensure factual implications are supportable.

Keywords scanned:
verified, official, reviewed, researched, source-verified, tested,
recommended, best, expert, independent, unbiased, accurate
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

# Trust keywords and their required support level
TRUST_KEYWORDS = {
    "verified": {
        "risk": "HIGH",
        "requirement": "Must be backed by evidence-ledger entry with verified_official status",
        "acceptable_contexts": ["evidence section", "claim provenance", "fact check date"]
    },
    "official": {
        "risk": "HIGH",
        "requirement": "Must reference actual official source, not implied authority",
        "acceptable_contexts": ["source URL", "official pricing", "official documentation"]
    },
    "reviewed": {
        "risk": "MEDIUM",
        "requirement": "Must indicate what was reviewed and by whom",
        "acceptable_contexts": ["editorial review", "peer review", "fact check"]
    },
    "researched": {
        "risk": "MEDIUM",
        "requirement": "Must indicate research methodology",
        "acceptable_contexts": ["research methodology", "source research"]
    },
    "tested": {
        "risk": "HIGH",
        "requirement": "Must describe actual testing performed",
        "acceptable_contexts": ["testing methodology", "hands-on testing"]
    },
    "recommended": {
        "risk": "LOW",
        "requirement": "Editorial recommendation is acceptable with disclosure",
        "acceptable_contexts": ["editorial recommendation", "best for"]
    },
    "best": {
        "risk": "LOW",
        "requirement": "Must be qualified (best for X, not absolute best)",
        "acceptable_contexts": ["best for", "best tool for"]
    },
    "expert": {
        "risk": "HIGH",
        "requirement": "Must reference real expert with verifiable credentials",
        "acceptable_contexts": []
    },
    "independent": {
        "risk": "MEDIUM",
        "requirement": "Must be true — no affiliate influence on scoring",
        "acceptable_contexts": ["affiliate disclosure", "editorial independence"]
    },
    "unbiased": {
        "risk": "HIGH",
        "requirement": "Must be demonstrable through methodology",
        "acceptable_contexts": ["methodology section"]
    },
    "accurate": {
        "risk": "MEDIUM",
        "requirement": "Must be qualified (accurate as of date)",
        "acceptable_contexts": ["fact check date", "data accuracy"]
    },
    "source-verified": {
        "risk": "HIGH",
        "requirement": "Must link to specific source",
        "acceptable_contexts": ["evidence section"]
    },
}


def find_html_files() -> List[Path]:
    """Find all public HTML files."""
    html_files = []
    skip_dirs = {'node_modules', '.junie', 'backups', '__pycache__', '.git'}
    
    for html in ROOT.rglob("*.html"):
        parts = html.parts
        if any(skip in parts for skip in skip_dirs):
            continue
        html_files.append(html)
    
    return html_files


def scan_trust_language(content: str, filepath: Path) -> List[Dict[str, Any]]:
    """Scan HTML content for trust keywords."""
    findings: List[Dict[str, Any]] = []
    
    # Strip script and style tags
    clean = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    
    # Strip HTML tags for text analysis
    text = re.sub(r'<[^>]+>', ' ', clean)
    text = re.sub(r'\s+', ' ', text).strip()
    
    for keyword, config in TRUST_KEYWORDS.items():
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
        matches = list(pattern.finditer(text))
        
        for match in matches:
            # Get surrounding context
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            findings.append({
                "file": str(filepath.relative_to(ROOT)),
                "keyword": keyword,
                "risk": config["risk"],
                "context": context,
                "requirement": config["requirement"],
                "acceptable_contexts": config["acceptable_contexts"]
            })
    
    return findings


def classify_finding(finding: Dict[str, Any]) -> str:
    """Classify a finding as SUPPORTED, NEEDS_REVIEW, or POTENTIALLY_MISLEADING."""
    keyword = finding["keyword"].lower()
    context = finding["context"].lower()
    file = finding["file"].lower()
    
    # Check if in acceptable context
    for acc_ctx in finding.get("acceptable_contexts", []):
        if acc_ctx.lower() in context:
            return "SUPPORTED"
    
    # Check file type for context
    if "about" in file or "methodology" in file or "policy" in file:
        return "SUPPORTED"
    
    # High-risk keywords in unsupported contexts
    if finding["risk"] == "HIGH" and keyword in ("verified", "official", "tested", "expert"):
        if "evidence" not in context and "source" not in context:
            return "POTENTIALLY_MISLEADING"
    
    return "NEEDS_REVIEW"


def main():
    print("=" * 60)
    print("ToolNest Trust Language Auditor")
    print("=" * 60)
    
    html_files = find_html_files()
    print(f"\nScanning {len(html_files)} HTML files...")
    
    all_findings: List[Dict[str, Any]] = []
    
    for html_file in html_files:
        try:
            content = html_file.read_text(encoding="utf-8", errors="ignore")
            findings = scan_trust_language(content, html_file)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  Warning: Could not read {html_file}: {e}")
    
    # Classify findings
    classification_counts = Counter()
    high_risk_findings = []
    
    for finding in all_findings:
        classification = classify_finding(finding)
        finding["classification"] = classification
        classification_counts[classification] += 1
        
        if finding["risk"] == "HIGH" and classification in ("POTENTIALLY_MISLEADING", "NEEDS_REVIEW"):
            high_risk_findings.append(finding)
    
    # Keyword counts
    keyword_counts = Counter()
    for finding in all_findings:
        keyword_counts[finding["keyword"]] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("TRUST LANGUAGE AUDIT RESULTS")
    print("=" * 60)
    
    print(f"\nTotal occurrences found: {len(all_findings)}")
    print(f"\nClassification Summary:")
    for cls, count in classification_counts.most_common():
        print(f"  {cls}: {count}")
    
    print(f"\nKeyword Frequency:")
    for kw, count in keyword_counts.most_common():
        print(f"  '{kw}': {count}")
    
    if high_risk_findings:
        print(f"\nHIGH-RISK Findings Requiring Review: {len(high_risk_findings)}")
        for finding in high_risk_findings[:20]:
            print(f"\n  File: {finding['file']}")
            print(f"  Keyword: '{finding['keyword']}' ({finding['risk']})")
            print(f"  Context: \"{finding['context']}\"")
            print(f"  Classification: {finding['classification']}")
            print(f"  Requirement: {finding['requirement']}")
        if len(high_risk_findings) > 20:
            print(f"\n  ... and {len(high_risk_findings) - 20} more")
    
    # Save report
    report = {
        "total_findings": len(all_findings),
        "classifications": dict(classification_counts),
        "keyword_frequency": dict(keyword_counts),
        "high_risk_count": len(high_risk_findings),
        "high_risk_findings": high_risk_findings[:50]
    }
    
    report_path = ROOT / "reports" / "trust-language-audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to {report_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
