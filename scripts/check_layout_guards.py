#!/usr/bin/env python3
"""Static layout risk detection for ToolNest HTML pages.

Checks for common layout issues that cause horizontal scroll, overflow,
or mobile viewport problems. These are static checks, not a replacement
for rendered browser QA.

Checks:
  - Fixed widths exceeding mobile viewport (375px)
  - Excessive min-width values
  - Missing wrap behavior on long strings
  - Overflow-x risks
  - Missing responsive rules
  - Excessively large headings
  - Missing focus styles
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_EXTENSIONS = {".html"}


def find_html_files(directory):
    """Find all HTML files in the project."""
    html_files = []
    for ext in HTML_EXTENSIONS:
        html_files.extend(directory.rglob(f"*{ext}"))
    return sorted(html_files)


def check_fixed_widths(css_content, file_path):
    """Check for fixed widths exceeding mobile viewport."""
    issues = []
    # Match width: XXXpx declarations
    for match in re.finditer(r'width\s*:\s*(\d+)px', css_content):
        width = int(match.group(1))
        if width > 375:
            issues.append(f"Fixed width {width}px exceeds mobile viewport (375px)")
    return issues


def check_min_width(css_content, file_path):
    """Check for excessive min-width values."""
    issues = []
    for match in re.finditer(r'min-width\s*:\s*(\d+)px', css_content):
        width = int(match.group(1))
        if width > 320:
            issues.append(f"min-width {width}px may cause mobile overflow")
    return issues


def check_overflow(css_content, file_path):
    """Check for overflow-x risks."""
    issues = []
    if re.search(r'overflow-x\s*:\s*(hidden|scroll)', css_content):
        issues.append("overflow-x hidden/scroll detected — verify content fits")
    return issues


def check_missing_wrap(css_content, file_path):
    """Check for missing wrap behavior on potentially long strings."""
    issues = []
    # Check for white-space: nowrap without overflow handling
    if re.search(r'white-space\s*:\s*nowrap', css_content):
        if not re.search(r'overflow', css_content):
            issues.append("white-space: nowrap without overflow handling")
    return issues


def check_large_headings(css_content, file_path):
    """Check for excessively large headings."""
    issues = []
    for match in re.finditer(r'font-size\s*:\s*(\d+)px', css_content):
        size = int(match.group(1))
        if size > 48:
            issues.append(f"Large font-size {size}px — may overflow on mobile")
    return issues


def check_missing_focus(css_content, file_path):
    """Check for missing focus styles on interactive elements."""
    issues = []
    # Check if there are interactive elements but no focus styles
    has_interactive = bool(re.search(r'(button|\.btn|\.de-chip|a\s*\[)', css_content))
    has_focus = bool(re.search(r':focus|:focus-visible', css_content))
    if has_interactive and not has_focus:
        issues.append("Interactive elements found but no :focus styles")
    return issues


def check_long_strings(html_content, file_path):
    """Check for unbroken long strings that may cause overflow."""
    issues = []
    # Look for very long words (>100 chars) that aren't in code blocks
    for match in re.finditer(r'(?<![\w-])[A-Za-z0-9]{100,}', html_content):
        word = match.group(0)[:50] + "..."
        issues.append(f"Long unbroken string found: {word}")
    return issues


def check_responsive_rules(css_content, file_path):
    """Check for missing responsive rules."""
    issues = []
    has_media = bool(re.search(r'@media', css_content))
    if not has_media and len(css_content) > 500:
        issues.append("No @media queries found in substantial CSS")
    return issues


def analyze_file(file_path):
    """Analyze a single HTML file for layout risks."""
    issues = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Could not read file: {e}"]

    # Extract inline styles
    for match in re.finditer(r'<style[^>]*>(.*?)</style>', content, re.DOTALL):
        css = match.group(1)
        issues.extend(check_fixed_widths(css, file_path))
        issues.extend(check_min_width(css, file_path))
        issues.extend(check_overflow(css, file_path))
        issues.extend(check_missing_wrap(css, file_path))
        issues.extend(check_large_headings(css, file_path))
        issues.extend(check_missing_focus(css, file_path))
        issues.extend(check_responsive_rules(css, file_path))

    # Check HTML content for long strings
    issues.extend(check_long_strings(content, file_path))

    return issues


def main():
    print("Static Layout Risk Detection")
    print("=" * 60)
    print("(Static checks only — not a replacement for rendered QA)")
    print()

    # Focus on key page families
    target_dirs = [
        ROOT / "tools",
        ROOT / "category",
        ROOT / "compare",
        ROOT / "best",
    ]

    all_issues = {}
    total_files = 0

    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        html_files = find_html_files(target_dir)
        for html_file in html_files:
            total_files += 1
            issues = analyze_file(html_file)
            if issues:
                rel_path = html_file.relative_to(ROOT)
                all_issues[str(rel_path)] = issues

    # Report
    if all_issues:
        print(f"Found {len(all_issues)} files with {sum(len(v) for v in all_issues.values())} potential issues:\n")
        for file_path, issues in sorted(all_issues.items()):
            print(f"  {file_path}:")
            for issue in issues[:5]:  # Limit to 5 per file
                print(f"    - {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more")
    else:
        print("No layout risks detected in static analysis.")

    print(f"\nFiles checked: {total_files}")
    print("Note: These are static checks. Rendered browser QA is recommended.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
