#!/usr/bin/env python3
"""Audit date consistency across all tool pages.

Extracts every user-visible date and structured-data date from each tool page,
creates a date map, and flags only real semantic contradictions.

Date types distinguished:
  FACTS_CHECKED     — When commercial/product facts were verified
  PRICING_CHECKED   — When pricing information was verified
  EDITORIAL_REVIEWED — When the page was last editorially reviewed
  SOURCE_VERIFIED   — When source data was verified
  DATE_MODIFIED     — Last modification date

Outputs:
  reports/phase3/date-consistency-audit.json
  reports/phase3/date-consistency-audit.md
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports" / "phase3"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def strip_script_style(html: str) -> str:
    """Remove <script> and <style> blocks."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text


def extract_dates_from_text(text: str) -> list[tuple[str, str]]:
    """Extract dates from text and return (date_string, context) pairs."""
    dates = []
    
    # ISO dates: 2026-11-22
    for m in re.finditer(r'(\d{4}-\d{2}-\d{2})', text):
        dates.append((m.group(1), m.group(0)))
    
    # Written dates: November 22, 2026 or 22 November 2026
    for m in re.finditer(r'([A-Z][a-z]+ \d{1,2},? \d{4})', text):
        dates.append((m.group(1), m.group(1)))
    for m in re.finditer(r'(\d{1,2} [A-Z][a-z]+ \d{4})', text):
        dates.append((m.group(1), m.group(1)))
    
    # Month Year: November 2026
    for m in re.finditer(r'([A-Z][a-z]+ \d{4})(?!\d)', text):
        dates.append((m.group(1), m.group(1)))
    
    return dates


def classify_date_location(html: str, date_str: str) -> list[dict]:
    """Classify where a date appears and what it represents."""
    text = strip_script_style(html)
    classifications = []
    
    # Find all occurrences of this date in the HTML
    for m in re.finditer(re.escape(date_str), text):
        pos = m.start()
        # Get surrounding context (200 chars before and after)
        start = max(0, pos - 200)
        end = min(len(text), pos + len(date_str) + 200)
        context = text[start:end]
        
        # Determine the date type based on context
        date_type = None
        location = None
        
        # Check for trust strip
        if 'tn-trust-strip' in context or 'tn-research-line' in context:
            if 'Editorial review' in context or 'editorial review' in context.lower():
                date_type = "EDITORIAL_REVIEWED"
                location = "Trust strip"
        
        # Check for facts checked
        if 'facts checked' in context.lower() or 'facts were checked' in context.lower():
            date_type = "FACTS_CHECKED"
            if 'pricing' in context.lower():
                date_type = "PRICING_CHECKED"
                location = "Sources section (pricing)"
            else:
                location = "Sources section"
        
        # Check for pricing checked
        if 'pricing' in context.lower() and ('checked' in context.lower() or 'verified' in context.lower()):
            date_type = "PRICING_CHECKED"
            location = "Pricing section"
        
        # Check for source verified
        if 'source verified' in context.lower() or 'evidence' in context.lower():
            date_type = "SOURCE_VERIFIED"
            location = "Evidence status"
        
        # Check for last reviewed
        if 'last reviewed' in context.lower() or 'last_reviewed' in context.lower():
            date_type = "EDITORIAL_REVIEWED"
            location = "Meta information"
        
        # Check for commercial facts
        if 'commercial facts' in context.lower():
            date_type = "FACTS_CHECKED"
            location = "Sidebar / CTA"
        
        # Check for info card
        if 'info' in context.lower() and 'checked' in context.lower():
            date_type = "FACTS_CHECKED"
            location = "Info card"
        
        # Check for pricing table
        if 'pricing' in context.lower() and 'as of' in context.lower():
            date_type = "PRICING_CHECKED"
            location = "Pricing table note"
        
        # Check for sources section
        if 'sources' in context.lower() and 'checked' in context.lower():
            date_type = "FACTS_CHECKED"
            location = "Sources section"
        
        # Check for sidebar
        if 'p-side-cta' in context or 'p-aside' in context:
            if 'checked' in context.lower():
                date_type = "FACTS_CHECKED"
                location = "Sidebar"
        
        # Check for dateModified in structured data
        if 'dateModified' in context or 'date_published' in context:
            date_type = "DATE_MODIFIED"
            location = "Structured data"
        
        # Check for editorial review in sub text
        if 'Editorial review' in context:
            date_type = "EDITORIAL_REVIEWED"
            location = "Hero sub text"
        
        # Check for Commercial facts checked
        if 'Commercial facts checked' in context:
            date_type = "FACTS_CHECKED"
            location = "Hero sub text"
        
        if date_type is None:
            # Try to determine from broader context
            if 'review' in context.lower():
                date_type = "EDITORIAL_REVIEWED"
                location = "Review context"
            elif 'check' in context.lower():
                date_type = "FACTS_CHECKED"
                location = "Check context"
            else:
                date_type = "UNKNOWN"
                location = "Unknown context"
        
        if location is None:
            location = "Unknown"
        
        classifications.append({
            "date": date_str,
            "date_type": date_type,
            "location": location,
            "context_snippet": context[:100],
        })
    
    return classifications


def normalize_date(date_str: str) -> str:
    """Normalize a date string to ISO format for comparison."""
    # Already ISO
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return date_str
    
    # November 22, 2026
    m = re.match(r'([A-Z][a-z]+) (\d{1,2}),? (\d{4})', date_str)
    if m:
        month_str, day, year = m.groups()
        months = {'January': '01', 'February': '02', 'March': '03', 'April': '04',
                  'May': '05', 'June': '06', 'July': '07', 'August': '08',
                  'September': '09', 'October': '10', 'November': '11', 'December': '12'}
        month = months.get(month_str, '00')
        return f"{year}-{month}-{day.zfill(2)}"
    
    # 22 November 2026
    m = re.match(r'(\d{1,2}) ([A-Z][a-z]+) (\d{4})', date_str)
    if m:
        day, month_str, year = m.groups()
        months = {'January': '01', 'February': '02', 'March': '03', 'April': '04',
                  'May': '05', 'June': '06', 'July': '07', 'August': '08',
                  'September': '09', 'October': '10', 'November': '11', 'December': '12'}
        month = months.get(month_str, '00')
        return f"{year}-{month}-{day.zfill(2)}"
    
    # November 2026 (month-year only)
    m = re.match(r'([A-Z][a-z]+) (\d{4})', date_str)
    if m:
        month_str, year = m.groups()
        months = {'January': '01', 'February': '02', 'March': '03', 'April': '04',
                  'May': '05', 'June': '06', 'July': '07', 'August': '08',
                  'September': '09', 'October': '10', 'November': '11', 'December': '12'}
        month = months.get(month_str, '00')
        return f"{year}-{month}"
    
    return date_str


def check_json_date_fields(json_path: Path) -> dict:
    """Check date fields in the tool's JSON data file."""
    if not json_path.exists():
        return {}
    
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return {}
    
    date_fields = {}
    
    # Check top-level date fields
    for field in ['lastReviewed', 'checkedOn']:
        if field in data and data[field]:
            date_fields[field] = str(data[field])
    
    # Check freshness sub-object
    freshness = data.get('freshness', {})
    if isinstance(freshness, dict):
        for field in ['created_at', 'updated_at', 'last_verified_at', 'next_review_at']:
            if field in freshness and freshness[field]:
                date_fields[f"freshness.{field}"] = str(freshness[field])
    
    # Check editorial sub-object
    editorial = data.get('editorial', {})
    if isinstance(editorial, dict):
        if 'editorial_last_reviewed' in editorial and editorial['editorial_last_reviewed']:
            date_fields["editorial.editorial_last_reviewed"] = str(editorial['editorial_last_reviewed'])
    
    # Check evidence array/object
    evidence = data.get('evidence', {})
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                for field in ['checkedOn', 'lastReviewed', 'verified_at']:
                    if field in item and item[field]:
                        key = f"evidence.{field}"
                        date_fields[key] = str(item[field])
    elif isinstance(evidence, dict):
        for field in ['checkedOn', 'lastReviewed', 'verified_at']:
            if field in evidence and evidence[field]:
                key = f"evidence.{field}"
                date_fields[key] = str(evidence[field])
    
    return date_fields


def main():
    tools_dir = ROOT / "tools"
    data_dir = ROOT / "data" / "tools"
    html_files = sorted(tools_dir.glob("*.html"))
    
    all_tool_dates = []
    contradictions = []
    date_field_coverage = {
        "editorial_last_reviewed": {"present": 0, "null": 0, "missing": 0},
        "freshness.created_at": {"present": 0, "null": 0, "missing": 0},
        "freshness.updated_at": {"present": 0, "null": 0, "missing": 0},
        "freshness.last_verified_at": {"present": 0, "null": 0, "missing": 0},
        "lastReviewed": {"present": 0, "null": 0, "missing": 0},
    }
    
    for path in html_files:
        rel = path.name
        tool_id = rel.replace(".html", "")
        content = path.read_text(encoding="utf-8", errors="replace")
        text = strip_script_style(content)
        
        # Extract all dates from the HTML
        raw_dates = extract_dates_from_text(text)
        
        # Deduplicate
        unique_dates = list(set(d[0] for d in raw_dates))
        
        # Classify each date
        date_map = []
        for date_str in unique_dates:
            classifications = classify_date_location(content, date_str)
            for cls in classifications:
                cls["normalized_date"] = normalize_date(date_str)
                date_map.append(cls)
        
        # Check JSON data file
        json_path = data_dir / f"{tool_id}.json"
        json_dates = check_json_date_fields(json_path)
        
        # Track date field coverage
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                # editorial_last_reviewed
                ed = data.get('editorial', {})
                if isinstance(ed, dict):
                    val = ed.get('editorial_last_reviewed')
                    if val:
                        date_field_coverage["editorial_last_reviewed"]["present"] += 1
                    elif 'editorial_last_reviewed' in ed:
                        date_field_coverage["editorial_last_reviewed"]["null"] += 1
                    else:
                        date_field_coverage["editorial_last_reviewed"]["missing"] += 1
                else:
                    date_field_coverage["editorial_last_reviewed"]["missing"] += 1
                # freshness fields
                fr = data.get('freshness', {})
                if isinstance(fr, dict):
                    for f in ['created_at', 'updated_at', 'last_verified_at']:
                        key = f"freshness.{f}"
                        if f in fr:
                            if fr[f]:
                                date_field_coverage[key]["present"] += 1
                            else:
                                date_field_coverage[key]["null"] += 1
                        else:
                            date_field_coverage[key]["missing"] += 1
                else:
                    for f in ['created_at', 'updated_at', 'last_verified_at']:
                        date_field_coverage[f"freshness.{f}"]["missing"] += 1
                # lastReviewed
                if 'lastReviewed' in data:
                    if data['lastReviewed']:
                        date_field_coverage["lastReviewed"]["present"] += 1
                    else:
                        date_field_coverage["lastReviewed"]["null"] += 1
                else:
                    date_field_coverage["lastReviewed"]["missing"] += 1
            except (json.JSONDecodeError, IOError):
                for field in date_field_coverage:
                    date_field_coverage[field]["missing"] += 1
        else:
            for field in date_field_coverage:
                date_field_coverage[field]["missing"] += 1
        
        # Check for contradictions
        tool_contradictions = []
        
        # Group dates by type
        dates_by_type = defaultdict(list)
        for entry in date_map:
            dates_by_type[entry["date_type"]].append(entry)
        
        # Check for conflicting dates in duplicate trust strips
        editorial_dates = dates_by_type.get("EDITORIAL_REVIEWED", [])
        if len(editorial_dates) > 1:
            normalized = [normalize_date(e["date"]) for e in editorial_dates]
            unique_normalized = set(normalized)
            # Only flag if there are genuinely different full dates (not just month-year vs full-date)
            full_dates = {d for d in unique_normalized if len(d) == 10}  # YYYY-MM-DD format
            if len(full_dates) > 1:
                tool_contradictions.append({
                    "type": "CONFLICTING_EDITORIAL_DATES",
                    "description": f"Multiple editorial review dates: {', '.join(sorted(full_dates))}",
                    "dates": editorial_dates,
                })
        
        # Check for facts checked vs editorial review contradictions
        facts_dates = dates_by_type.get("FACTS_CHECKED", [])
        if facts_dates and editorial_dates:
            facts_norm = {normalize_date(d["date"]) for d in facts_dates}
            editorial_norm = {normalize_date(d["date"]) for d in editorial_dates}
            # Flag if facts checked date is after editorial review date
            for f_date in facts_norm:
                for e_date in editorial_norm:
                    if f_date > e_date and len(f_date) == 10 and len(e_date) == 10:
                        tool_contradictions.append({
                            "type": "FACTS_AFTER_REVIEW",
                            "description": f"Facts checked ({f_date}) after editorial review ({e_date})",
                            "facts_date": f_date,
                            "editorial_date": e_date,
                        })
        
        tool_entry = {
            "tool_id": tool_id,
            "page": rel,
            "date_map": date_map,
            "json_date_fields": json_dates,
            "contradictions": tool_contradictions,
            "has_contradictions": len(tool_contradictions) > 0,
        }
        all_tool_dates.append(tool_entry)
        contradictions.extend(tool_contradictions)
    
    # Summary statistics
    tools_with_dates = sum(1 for t in all_tool_dates if t["date_map"])
    tools_with_contradictions = sum(1 for t in all_tool_dates if t["has_contradictions"])
    
    # Build JSON report
    report = {
        "summary": {
            "total_tool_pages_audited": len(html_files),
            "tools_with_user_visible_dates": tools_with_dates,
            "tools_with_contradictions": tools_with_contradictions,
            "total_contradictions": len(contradictions),
            "date_field_coverage": date_field_coverage,
        },
        "tools": all_tool_dates,
        "contradictions": contradictions,
    }
    
    json_path = REPORTS_DIR / "date-consistency-audit.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {json_path}")
    
    # Build Markdown report
    md_lines = []
    md_lines.append("# Date Consistency Audit Report\n")
    md_lines.append(f"**Generated:** 2026-11-22\n")
    md_lines.append(f"**Tool pages audited:** {len(html_files)}\n")
    md_lines.append(f"**Tools with user-visible dates:** {tools_with_dates}\n")
    md_lines.append(f"**Tools with contradictions:** {tools_with_contradictions}\n")
    md_lines.append(f"**Total contradictions found:** {len(contradictions)}\n")
    
    md_lines.append("## Date Field Coverage (JSON data files)\n")
    md_lines.append("| Field | Present | Null | Missing |")
    md_lines.append("|---|---|---|---|")
    for field, counts in date_field_coverage.items():
        md_lines.append(f"| `{field}` | {counts['present']} | {counts['null']} | {counts['missing']} |")
    md_lines.append("")
    
    md_lines.append("## Contradictions Found\n")
    if contradictions:
        for i, c in enumerate(contradictions, 1):
            md_lines.append(f"### Contradiction {i}: {c['type']}\n")
            md_lines.append(f"- **Description:** {c['description']}")
            if "dates" in c:
                for d in c["dates"]:
                    md_lines.append(f"  - Date: `{d['date']}` at {d['location']} ({d['date_type']})")
            md_lines.append("")
    else:
        md_lines.append("No semantic contradictions found.\n")
    
    md_lines.append("## Tools with Conflicting Dates\n")
    conflicting_tools = [t for t in all_tool_dates if t["has_contradictions"]]
    if conflicting_tools:
        for t in conflicting_tools:
            md_lines.append(f"### `{t['page']}`\n")
            for c in t["contradictions"]:
                md_lines.append(f"- {c['description']}")
            md_lines.append("")
    else:
        md_lines.append("No tools with conflicting dates.\n")
    
    md_lines.append("## Date Map Examples\n")
    # Show examples of complex date maps
    complex_tools = sorted(all_tool_dates, key=lambda t: -len(t["date_map"]))[:5]
    for t in complex_tools:
        if t["date_map"]:
            md_lines.append(f"### `{t['page']}` ({len(t['date_map'])} date entries)\n")
            for entry in t["date_map"]:
                md_lines.append(f"- `{entry['date']}` → {entry['date_type']} at {entry['location']}")
            md_lines.append("")
    
    md_lines.append("## Verification\n")
    md_lines.append(f"- Total tool pages audited: {len(html_files)}")
    md_lines.append(f"- Tools with user-visible dates: {tools_with_dates}")
    md_lines.append(f"- Tools with contradictions: {tools_with_contradictions}")
    md_lines.append(f"- Date field coverage tracked for: {', '.join(date_field_coverage.keys())}")
    md_lines.append("")
    
    md_content = "\n".join(md_lines)
    md_path = REPORTS_DIR / "date-consistency-audit.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"Written: {md_path}")
    
    # Print summary
    print(f"\n=== Date Consistency Audit Summary ===")
    print(f"Tool pages audited: {len(html_files)}")
    print(f"Tools with user-visible dates: {tools_with_dates}")
    print(f"Tools with contradictions: {tools_with_contradictions}")
    print(f"Total contradictions: {len(contradictions)}")
    print()
    print("Date field coverage:")
    for field, counts in date_field_coverage.items():
        print(f"  {field}: {counts['present']} present, {counts['null']} null, {counts['missing']} missing")
    print()
    if contradictions:
        print("Contradictions:")
        for c in contradictions:
            print(f"  - {c['type']}: {c['description']}")


if __name__ == "__main__":
    main()
