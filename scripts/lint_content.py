#!/usr/bin/env python3
"""Content linter for ToolNest HTML pages.

Checks for common content issues and fails on critical errors.

Usage:
    python3 scripts/lint_content.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Critical patterns that should never appear in output HTML
# These target data rendering errors, not normal English words
CRITICAL_PATTERNS = [
    (r"/bin/bash", "Dollar sign corruption: /bin/bash found (should be $0)"),
    (r"\bTODO\b", "Unresolved TODO found"),
    (r"\{\{[^}]+\}\}", "Unprocessed template variable found"),
    # Shell variable leakage — positional parameters $1-$9 in prose (not in code blocks)
    (r"(?<!\w)\$[1-9](?!\d)", "Shell variable leakage: positional parameter found in prose"),
    # Incomplete shell expressions
    (r"\$\{[^}]*$", "Incomplete shell expression: unclosed ${...}"),
]

# Patterns to check only in specific contexts (data attributes, JSON-LD, etc.)
CONTEXT_PATTERNS = [
    (r'content="undefined"', "Undefined value in meta content"),
    (r'content="null"', "Null value in meta content"),
    (r'"undefined"', "Undefined in JSON/structured data"),
    (r'"null"(?!\s*[,}])', "Null in JSON/structured data (not followed by comma/brace)"),
]

# Warning patterns
WARNING_PATTERNS = [
    (r"\bai-powered\b", "Lowercase 'ai-powered' should be 'AI-powered'"),
    (r"\bai\s+search\b(?!.*AI Search)", "Lowercase 'ai search' should be 'AI Search'"),
]

# Boilerplate patterns
BOILERPLATE_PATTERNS = [
    r"(?i)strong choice for its target audience",
    r"(?i)competes with several",
    r"(?i)may not cover all requirements",
    r"(?i)based on our research",
]


def strip_code_blocks(html_content: str) -> str:
    """Remove <code>, <pre>, <script>, <style> blocks to avoid false positives in code examples."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<pre[^>]*>.*?</pre>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<code[^>]*>.*?</code>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text

def lint_file(path: Path) -> list[dict]:
    """Lint a single HTML file and return list of issues."""
    issues = []
    content = path.read_text(encoding="utf-8", errors="replace")
    rel = path.relative_to(ROOT).as_posix()

    # Strip script and style content for text-only checks
    text_content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
    text_content = re.sub(r"<style[^>]*>.*?</style>", "", text_content, flags=re.DOTALL | re.IGNORECASE)

    # For shell leakage patterns, also strip code blocks to avoid false positives
    prose_content = strip_code_blocks(content)

    # Critical patterns (check full HTML, not just text)
    for pattern, message in CRITICAL_PATTERNS:
        # Shell leakage patterns check prose only (no code blocks)
        if "Shell variable" in message or "Incomplete shell" in message:
            check_content = prose_content
        else:
            check_content = content
        for match in re.finditer(pattern, check_content):
            line_num = check_content[:match.start()].count("\n") + 1
            issues.append({
                "file": rel,
                "line": line_num,
                "severity": "ERROR",
                "message": message,
                "context": match.group(0),
            })

    # Context-specific patterns (check full HTML)
    for pattern, message in CONTEXT_PATTERNS:
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count("\n") + 1
            issues.append({
                "file": rel,
                "line": line_num,
                "severity": "ERROR",
                "message": message,
                "context": match.group(0),
            })

    # Warning patterns
    for pattern, message in WARNING_PATTERNS:
        for match in re.finditer(pattern, text_content):
            line_num = text_content[:match.start()].count("\n") + 1
            issues.append({
                "file": rel,
                "line": line_num,
                "severity": "WARNING",
                "message": message,
                "context": match.group(0),
            })

    # Boilerplate patterns — ERROR per C3
    for pattern in BOILERPLATE_PATTERNS:
        for match in re.finditer(pattern, text_content):
            line_num = text_content[:match.start()].count("\n") + 1
            issues.append({
                "file": rel,
                "line": line_num,
                "severity": "ERROR",
                "message": f"Boilerplate phrase: {match.group(0)[:50]}",
                "context": match.group(0),
            })

    # Check for repeated identical bullets — ERROR per C3
    bullet_pattern = re.compile(r"<li>(.*?)</li>")
    bullets = bullet_pattern.findall(text_content)
    if len(bullets) > 3:
        from collections import Counter
        bullet_counts = Counter(b.strip() for b in bullets if b.strip())
        for bullet, count in bullet_counts.items():
            if count > 1:
                issues.append({
                    "file": rel,
                    "line": 0,
                    "severity": "ERROR",
                    "message": f"Repeated bullet ({count}x): {bullet[:60]}",
                    "context": bullet,
                })

    return issues


def main() -> None:
    all_issues = []
    html_files = list(ROOT.rglob("*.html"))
    html_files = [
        p for p in html_files
        if ".git" not in p.parts
        and p.relative_to(ROOT).as_posix() not in {"404.html", "googlef7f3d54afb5d5344.html"}
    ]

    for path in sorted(html_files):
        issues = lint_file(path)
        all_issues.extend(issues)

    # Print results
    errors = [i for i in all_issues if i["severity"] == "ERROR"]
    warnings = [i for i in all_issues if i["severity"] == "WARNING"]

    print(f"Linted {len(html_files)} HTML files")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print()

    if errors:
        print("=== ERRORS ===")
        for issue in errors[:20]:
            print(f"  {issue['file']}:{issue['line']} - {issue['message']}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")
        print()

    if warnings:
        print("=== WARNINGS ===")
        for issue in warnings[:20]:
            print(f"  {issue['file']}:{issue['line']} - {issue['message']}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")
        print()

    # Exit with error code if critical issues found
    if errors:
        print("FAIL: Critical errors found")
        sys.exit(1)
    else:
        print("PASS: No critical errors")
        sys.exit(0)


if __name__ == "__main__":
    main()
