"""Phase 3G Content Integrity Audit Tests

Tests for:
- No double HTML documents (regression guard for the 6 corrupted pages)
- No date contradictions
- Metadata quality (no broken grammar, no truncation, no empty values)
- Public catalog count = 147
- Utility/pipeline pages excluded from catalog
- decision-engine and stack-analyzer not in sitemap
"""

import glob
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT, "tools")
DATA_DIR = os.path.join(ROOT, "data", "tools")
UTILITY_PAGES = {
    "index.html",
    "automation-budget-estimator.html",
    "overlap-checker.html",
    "workflow-explorer.html",
    "decision-engine.html",
    "stack-analyzer.html",
    "seo-cost-calculator.html",
    "price-and-limit-changes.html", "state-of-seo-pricing-2026.html",
}
SITEMAP = os.path.join(ROOT, "sitemap.xml")


# =============================================================================
# Double-HTML Detection (regression guard for 6 corrupted pages)
# =============================================================================

class TestDoubleHTMLDetection:
    """Ensure no HTML file has duplicate HTML document structure."""

    @pytest.mark.parametrize(
        "html_file",
        [
            "beautifulai.html",
            "close.html",
            "consensus.html",
            "freshdesk.html",
            "manychat.html",
            "netlify.html",
        ],
    )
    def test_no_double_html_on_repaired_pages(self, html_file):
        """The 6 previously corrupted pages must have exactly one </html> tag."""
        path = os.path.join(TOOLS_DIR, html_file)
        with open(path, "r") as f:
            content = f.read()
        assert content.count("</html>") == 1, (
            f"{html_file} has {content.count('</html>')} </html> tags "
            f"(double-HTML corruption not fully fixed)"
        )

    def test_no_html_file_has_double_closing_html_tag(self):
        """Every HTML file in tools/ must have exactly one </html> tag."""
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()
            count = content.count("</html>")
            assert count == 1, (
                f"{os.path.basename(html_file)} has {count} </html> tags"
            )

    def test_no_html_file_has_double_doctype(self):
        """Every HTML file in tools/ must have at most one <!doctype html>."""
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()
            count = content.lower().count("<!doctype html>")
            assert count <= 1, (
                f"{os.path.basename(html_file)} has {count} <!doctype html> declarations"
            )

    def test_no_html_file_has_double_html_opening_tag(self):
        """Every HTML file in tools/ must have exactly one <html opening tag."""
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()
            count = len(re.findall(r"<html\b", content, re.IGNORECASE))
            assert count == 1, (
                f"{os.path.basename(html_file)} has {count} <html opening tags"
            )


# =============================================================================
# Date Consistency
# =============================================================================

class TestDateConsistency:
    """Ensure no page has contradictory dates for the same semantic meaning."""

    def test_no_date_contradictions_in_repaired_pages(self):
        """The 6 repaired pages must have consistent dates."""
        repaired = [
            "beautifulai.html",
            "close.html",
            "consensus.html",
            "freshdesk.html",
            "manychat.html",
            "netlify.html",
        ]
        for html_file in repaired:
            path = os.path.join(TOOLS_DIR, html_file)
            with open(path, "r") as f:
                content = f.read()

            # Find all EDITORIAL_REVIEWED date labels
            editorial_dates = re.findall(
                r"Editorial review\s*(\d{4}-\d{2}-\d{2})", content
            )
            assert len(set(editorial_dates)) <= 1, (
                f"{html_file} has contradictory editorial review dates: {editorial_dates}"
            )

    def test_no_page_has_two_different_editorial_review_dates(self):
        """No page in tools/ should have two different editorial review dates."""
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()

            editorial_dates = re.findall(
                r"Editorial review\s*(\d{4}-\d{2}-\d{2})", content, re.IGNORECASE
            )
            unique_dates = set(editorial_dates)
            assert len(unique_dates) <= 1, (
                f"{os.path.basename(html_file)} has contradictory editorial "
                f"review dates: {editorial_dates}"
            )


# =============================================================================
# Metadata Quality
# =============================================================================

class TestMetadataQuality:
    """Ensure metadata titles and descriptions are well-formed."""

    def test_no_broken_title_grammar(self):
        """No title should contain obvious broken phrases."""
        broken_phrases = [
            "who it Review",
            "current SEO Review",
            "Call Review",
        ]
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()

            title_match = re.search(r"<title>([^<]+)</title>", content)
            if not title_match:
                continue

            title = title_match.group(1)
            for phrase in broken_phrases:
                # Word boundaries avoid false positives such as "Call Review"
                # inside the legitimate product name "KrispCall Review".
                assert not re.search(
                    r"\b" + re.escape(phrase) + r"\b", title, re.IGNORECASE
                ), (
                    f"{os.path.basename(html_file)} title contains broken phrase "
                    f"'{phrase}': {title}"
                )

    def test_no_redundant_title_words(self):
        """No title should repeat the same significant word unnecessarily."""
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()

            title_match = re.search(r"<title>([^<]+)</title>", content)
            if not title_match:
                continue

            title = title_match.group(1)
            # Check for "Pricing Review: Features & Pricing" pattern
            # (Pricing appears twice in a short title)
            words = re.findall(r"\b\w+\b", title.lower())
            word_counts = {}
            for w in words:
                if len(w) > 3:  # Ignore short words
                    word_counts[w] = word_counts.get(w, 0) + 1

            for word, count in word_counts.items():
                if count > 1 and word not in ("the", "and", "for", "with"):
                    # Allow "Review" to appear once, but not redundant product names
                    if word == "pricing" and count > 1:
                        assert False, (
                            f"{os.path.basename(html_file)} title has redundant "
                            f"'{word}': {title}"
                        )

    def test_meta_description_length(self):
        """All meta descriptions should be between 100-170 characters."""
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()

            desc_match = re.search(
                r'<meta name="description" content="([^"]*)">', content
            )
            if not desc_match:
                continue

            desc = desc_match.group(1)
            assert 100 <= len(desc) <= 170, (
                f"{os.path.basename(html_file)} meta description is {len(desc)} chars "
                f"(expected 100-170): {desc[:80]}..."
            )

    def test_no_empty_metadata(self):
        """No indexable page should have empty title, description, og:title, or og:description."""
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()

            title_match = re.search(r"<title>([^<]+)</title>", content)
            assert title_match, f"{os.path.basename(html_file)} has no <title> tag"
            assert title_match.group(1).strip(), (
                f"{os.path.basename(html_file)} has empty <title>"
            )

            desc_match = re.search(
                r'<meta name="description" content="([^"]*)">', content
            )
            if desc_match:
                assert desc_match.group(1).strip(), (
                    f"{os.path.basename(html_file)} has empty meta description"
                )

            og_title_match = re.search(
                r'<meta property="og:title" content="([^"]*)">', content
            )
            if og_title_match:
                assert og_title_match.group(1).strip(), (
                    f"{os.path.basename(html_file)} has empty og:title"
                )

            og_desc_match = re.search(
                r'<meta property="og:description" content="([^"]*)">', content
            )
            if og_desc_match:
                assert og_desc_match.group(1).strip(), (
                    f"{os.path.basename(html_file)} has empty og:description"
                )


# =============================================================================
# Catalog Integrity
# =============================================================================

class TestCatalogIntegrity:
    """Ensure the public catalog count and structure is correct."""

    def test_public_catalog_count_is_153(self):
        """Exactly 153 JSON files in data/tools/ (147 + 6 Batch A tools)."""
        json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
        assert len(json_files) == 153, (
            f"Expected 153 JSON files in data/tools/, found {len(json_files)}"
        )

    def test_tools_html_count_matches_catalog_plus_utilities(self):
        """HTML files in tools/ = 153 catalog profiles + known utility pages."""
        html_files = glob.glob(os.path.join(TOOLS_DIR, "*.html"))
        expected = UTILITY_PAGES | {
            f"{t['id']}.html" for t in json.load(
                open(os.path.join(DATA_DIR, "..", "tools-v1.json"), encoding="utf-8")
            )["tools"]
        }
        assert len(html_files) == len(expected), (
            f"Expected {len(expected)} HTML files in tools/, found {len(html_files)}"
        )

    def test_utility_pages_excluded_from_catalog(self):
        """Utility pages are not counted as catalog tools."""
        utility_pages = UTILITY_PAGES

        # These should NOT have corresponding JSON in data/tools/
        for page in utility_pages:
            tool_id = page.replace(".html", "")
            json_path = os.path.join(DATA_DIR, f"{tool_id}.json")
            assert not os.path.exists(json_path), (
                f"{page} is a utility page but has a JSON in data/tools/ "
                f"(should be excluded from catalog)"
            )

    def test_decision_engine_not_in_sitemap(self):
        """decision-engine.html must not be in sitemap.xml."""
        with open(SITEMAP, "r") as f:
            sitemap = f.read()
        assert "decision-engine.html" not in sitemap, (
            "decision-engine.html should not be in sitemap.xml"
        )

    def test_stack_analyzer_not_in_sitemap(self):
        """stack-analyzer.html must not be in sitemap.xml."""
        with open(SITEMAP, "r") as f:
            sitemap = f.read()
        assert "stack-analyzer.html" not in sitemap, (
            "stack-analyzer.html should not be in sitemap.xml"
        )

    def test_pipeline_tools_in_sitemap(self):
        """Pipeline tools should be in sitemap."""
        with open(SITEMAP, "r") as f:
            sitemap = f.read()
        for tool in [
            "automation-budget-estimator.html",
            "overlap-checker.html",
            "workflow-explorer.html",
        ]:
            assert tool in sitemap, (
                f"{tool} should be in sitemap.xml"
            )


# =============================================================================
# Shell Leakage (verify existing guards still pass)
# =============================================================================

class TestShellLeakage:
    """Ensure no shell variable leakage in generated HTML."""

    def test_no_bin_bash_in_tools_html(self):
        """No HTML file in tools/ should contain /bin/bash."""
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()
            assert "/bin/bash" not in content, (
                f"{os.path.basename(html_file)} contains /bin/bash "
                f"(shell variable leakage)"
            )

    def test_no_shell_positional_params_in_prose(self):
        """No HTML file should contain $1-$9 shell positional params (not dollar amounts)."""
        for html_file in glob.glob(os.path.join(TOOLS_DIR, "*.html")):
            with open(html_file, "r") as f:
                content = f.read()
            # Look for $1 through $9 as shell positional params
            # Exclude legitimate dollar amounts which are very common in pricing content:
            #   $6, $500, $1,199, $10/user, $29/mo, $5.99, $6–10/user/month, etc.
            # A real shell param would appear in prose like "run $1 to test" or "$0 free option"
            # Dollar amounts are always followed by: digits, commas, dots, slashes,
            # en-dashes (–), spaces followed by words like "per", "month", "mo", "yr",
            # or HTML closing tags.
            for match in re.finditer(r"\$([1-9])", content):
                start = match.start()
                end = match.end()
                after = content[end:end+30]
                before = content[max(0, start-30):start]
                # Skip dollar amounts: followed by currency-like patterns
                if re.match(r"[/\d,.\s–\-]|</|>|$|per|month|mo|yr|/user", after, re.IGNORECASE):
                    continue
                # Skip if in a table cell
                if "<td" in before or "</td>" in after:
                    continue
                # Skip if context suggests pricing
                if any(w in before.lower() for w in ["price", "cost", "save", "saving", "plan", "billing"]):
                    continue
                # This looks like a shell param — flag it
                assert False, (
                    f"{os.path.basename(html_file)} contains possible shell positional "
                    f"param '${match.group(1)}' at position {start}: "
                    f"...{before[-40:]}|${match.group(1)}|{after[:40]}..."
                )
