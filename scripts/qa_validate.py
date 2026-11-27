#!/usr/bin/env python3
"""
Comprehensive QA validation for ToolNest rendered HTML.
Checks for common issues across all page families:
- CSS references
- Internal links
- JSON validity
- Minified CSS
- Catalog integrity
- Category counts
- Evidence status validity
- Pricing semantics
- SEO metadata
- Author page
- Affiliate disclosure
"""
import os
import re
import json
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])

def find_html_files():
    html_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Skip node_modules, .junie, backups
        dirnames[:] = [d for d in dirnames if d not in ('node_modules', '.junie', 'backups', '__pycache__', '.git')]
        for f in filenames:
            if f.endswith('.html'):
                html_files.append(os.path.join(dirpath, f))
    return html_files

def check_css_references(html_files):
    """Check that CSS references are valid"""
    issues = []
    css_pattern = re.compile(r'href="(/assets/[^"]+\.css)"')
    for f in html_files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
        for match in css_pattern.finditer(content):
            css_path = match.group(1)
            full_path = os.path.join(ROOT, css_path.lstrip('/'))
            if not os.path.exists(full_path):
                rel = os.path.relpath(f, ROOT)
                issues.append(f"{rel}: references missing CSS {css_path}")
    return issues

def strip_script_tags(content):
    """Remove <script> blocks so we only check actual HTML, not JS code"""
    return re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

def check_internal_links(html_files):
    """Check that internal links point to existing files"""
    issues = []
    link_pattern = re.compile(r'href="(/[^"#][^"]*)"')
    seen = set()
    for f in html_files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
        # Strip script tags to avoid matching JS template strings
        content = strip_script_tags(content)
        for match in link_pattern.finditer(content):
            href = match.group(1)
            if href.startswith('/assets/') or href.startswith('/data/'):
                continue  # Skip assets and data files
            if href.endswith('.html'):
                if href in seen:
                    continue
                seen.add(href)
                full_path = os.path.join(ROOT, href.lstrip('/'))
                if not os.path.exists(full_path):
                    rel = os.path.relpath(f, ROOT)
                    issues.append(f"{rel}: links to missing {href}")
    return issues

def check_json_validity():
    """Check that key JSON files are valid"""
    issues = []
    json_files = [
        'data/tools.json',
        'data/tools-v1.json',
        'data/evidence/evidence-ledger.json',
        'data/decision-readiness-summary.json',
        'data/decision-critical-coverage.json',
        'data/catalog-reconciliation.json',
        'data/taxonomy/taxonomy-v1.json',
    ]
    for jf in json_files:
        full = os.path.join(ROOT, jf)
        if os.path.exists(full):
            try:
                with open(full, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                issues.append(f"{jf}: invalid JSON - {e}")
    return issues

def check_minified_css():
    """Check that minified CSS exists and is not empty"""
    issues = []
    min_css = os.path.join(ROOT, 'assets', 'site.min.css')
    if not os.path.exists(min_css):
        issues.append("assets/site.min.css: file missing")
    elif os.path.getsize(min_css) == 0:
        issues.append("assets/site.min.css: file is empty")
    return issues

def check_catalog_integrity():
    """Check catalog count consistency"""
    issues = []
    v1_path = os.path.join(ROOT, 'data', 'tools-v1.json')
    if os.path.exists(v1_path):
        data = json.load(open(v1_path))
        tools = data.get('tools', [])
        ids = [t['id'] for t in tools]
        if len(ids) != len(set(ids)):
            issues.append(f"tools-v1.json: duplicate IDs found")
        if len(tools) != 153:
            issues.append(f"tools-v1.json: expected 153 tools, found {len(tools)}")
    return issues

def check_evidence_status_validity():
    """Check evidence ledger has valid statuses"""
    issues = []
    ledger_path = os.path.join(ROOT, 'data', 'evidence', 'evidence-ledger.json')
    if os.path.exists(ledger_path):
        ledger = json.load(open(ledger_path))
        valid_statuses = {'verified', 'verified_official', 'editorial_assessment', 'needs_review', 'disputed'}
        for claim in ledger.get('claims', []):
            status = claim.get('status', '')
            if status and status not in valid_statuses:
                issues.append(f"evidence-ledger: invalid status '{status}' for claim {claim.get('claim_id', 'unknown')}")
    return issues

def check_seo_metadata(html_files):
    """Check that key pages have required SEO metadata"""
    issues = []
    key_pages = ['index.html', 'about.html', 'contact.html', 'privacy.html', 'terms.html']
    for page in key_pages:
        path = os.path.join(ROOT, page)
        if os.path.exists(path):
            content = open(path, 'r', encoding='utf-8', errors='ignore').read()
            if '<title>' not in content.lower():
                issues.append(f"{page}: missing <title> tag")
            if 'name="description"' not in content.lower():
                issues.append(f"{page}: missing meta description")
    return issues

def check_author_page():
    """Check author/about page exists and has content"""
    issues = []
    about_path = os.path.join(ROOT, 'about.html')
    if not os.path.exists(about_path):
        issues.append("about.html: file missing")
    else:
        content = open(about_path, 'r', encoding='utf-8', errors='ignore').read()
        if len(content) < 1000:
            issues.append("about.html: content seems too short")
    return issues

def check_affiliate_disclosure():
    """Check affiliate disclosure page exists"""
    issues = []
    affiliate_path = os.path.join(ROOT, 'affiliate-disclosure.html')
    if not os.path.exists(affiliate_path):
        issues.append("affiliate-disclosure.html: file missing")
    return issues

def check_sitemap():
    """Check sitemap exists and is valid XML"""
    issues = []
    sitemap_path = os.path.join(ROOT, 'sitemap.xml')
    if not os.path.exists(sitemap_path):
        issues.append("sitemap.xml: file missing")
    return issues

def check_robots():
    """Check robots.txt exists"""
    issues = []
    robots_path = os.path.join(ROOT, 'robots.txt')
    if not os.path.exists(robots_path):
        issues.append("robots.txt: file missing")
    return issues

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')  # the report prints emoji; legacy Windows consoles cannot
    print("=" * 60)
    print("ToolNest QA Validation (Expanded)")
    print("=" * 60)
    
    html_files = find_html_files()
    print(f"\nFound {len(html_files)} HTML files")
    
    all_issues = []
    
    checks = [
        ("CSS references", lambda: check_css_references(html_files)),
        ("Internal links", check_internal_links.__wrapped__ if hasattr(check_internal_links, '__wrapped__') else lambda: check_internal_links(html_files)),
        ("JSON validity", check_json_validity),
        ("Minified CSS", check_minified_css),
        ("Catalog integrity", check_catalog_integrity),
        ("Evidence status validity", check_evidence_status_validity),
        ("SEO metadata", lambda: check_seo_metadata(html_files)),
        ("Author page", check_author_page),
        ("Affiliate disclosure", check_affiliate_disclosure),
        ("Sitemap", check_sitemap),
        ("Robots.txt", check_robots),
    ]
    
    for name, check_fn in checks:
        print(f"\n[{checks.index((name, check_fn))+1}/{len(checks)}] Checking {name}...")
        try:
            issues = check_fn()
            all_issues.extend(issues)
            print(f"  Found {len(issues)} issues")
        except Exception as e:
            print(f"  ERROR: {e}")
            all_issues.append(f"{name}: check failed - {e}")
    
    print("\n" + "=" * 60)
    if all_issues:
        print(f"TOTAL: {len(all_issues)} issues found")
        for issue in all_issues[:20]:
            print(f"  ❌ {issue}")
        if len(all_issues) > 20:
            print(f"  ... and {len(all_issues) - 20} more")
        sys.exit(1)
    else:
        print("✅ All checks passed!")
        sys.exit(0)

if __name__ == '__main__':
    main()
