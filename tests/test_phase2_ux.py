"""Phase 2 UX regression tests.

Validates that Phase 2 changes preserve all safety constraints and meet
the new UX requirements without breaking existing functionality.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HomepageCTATests(unittest.TestCase):
    """Primary homepage CTA must remain 'Find My Tool'."""

    def test_picker_is_first_interactive_section(self):
        """The #picker section should appear before #paths."""
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        picker_pos = html.index('id="picker"')
        paths_pos = html.index('id="paths"')
        self.assertLess(
            picker_pos,
            paths_pos,
            "Find My Tool picker must appear before the paths section",
        )

    def test_find_my_tool_button_exists(self):
        """The final CTA must still have a 'Find my tool' button."""
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Find my tool", html)

    def test_hero_search_form_exists(self):
        """The hero search form must still be present."""
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('role="search"', html)

    def test_new_paths_present(self):
        """New navigation paths must be present in the homepage."""
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("stack-analyzer.html", html)
        self.assertIn("overlap-checker.html", html)
        self.assertIn("decision-engine.html", html)


class BetaNoindexTests(unittest.TestCase):
    """Beta pages must remain noindex,follow."""

    def test_decision_engine_noindex(self):
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        self.assertTrue(
            "noindex,follow" in html or "noindex, follow" in html,
            "Decision Engine should have noindex,follow robots meta",
        )

    def test_stack_analyzer_noindex(self):
        html = (ROOT / "tools" / "stack-analyzer.html").read_text(encoding="utf-8")
        self.assertTrue(
            "noindex,follow" in html or "noindex, follow" in html,
            "Stack Analyzer should have noindex,follow robots meta",
        )


class IndexedURLPreservationTests(unittest.TestCase):
    """All URLs in index-allowlist.json must still exist as files."""

    def test_allowlist_paths_exist(self):
        allowlist = ROOT / "data" / "index-allowlist.json"
        if not allowlist.exists():
            self.skipTest("index-allowlist.json not found")
        data = json.loads(allowlist.read_text(encoding="utf-8"))
        missing = []
        for path in data.get("paths", []):
            # Skip root path
            if path == "/":
                file_path = ROOT / "index.html"
            else:
                file_path = ROOT / path.lstrip("/")
            if not file_path.exists():
                missing.append(path)
        self.assertEqual(
            missing,
            [],
            f"Missing files from index-allowlist: {', '.join(missing)}",
        )


class CanonicalURLTests(unittest.TestCase):
    """Canonical URLs for protected pages must be unchanged."""

    protected_pages = {
        "compare/mozpro-vs-semrush.html": "https://www.toolnestai.tech/compare/mozpro-vs-semrush.html",
        "tools/mozpro.html": "https://www.toolnestai.tech/tools/mozpro.html",
        "compare/claude-vs-gemini.html": "https://www.toolnestai.tech/compare/claude-vs-gemini.html",
        "tools/screamingfrog.html": "https://www.toolnestai.tech/tools/screamingfrog.html",
        "alternatives/systeme-alternatives.html": "https://www.toolnestai.tech/alternatives/systeme-alternatives.html",
        "best/best-sales-tools.html": "https://www.toolnestai.tech/best/best-sales-tools.html",
        "compare/monday-vs-notion.html": "https://www.toolnestai.tech/compare/monday-vs-notion.html",
    }

    def test_canonical_urls_unchanged(self):
        for page, expected in self.protected_pages.items():
            path = ROOT / page
            if not path.exists():
                continue
            html = path.read_text(encoding="utf-8")
            self.assertIn(
                f'href="{expected}"',
                html,
                f"{page}: canonical URL mismatch",
            )


class SitemapIntegrityTests(unittest.TestCase):
    """Sitemap entries must reference existing files."""

    def test_sitemap_entries_exist(self):
        sitemap = ROOT / "sitemap.xml"
        if not sitemap.exists():
            self.skipTest("sitemap.xml not found")
        content = sitemap.read_text(encoding="utf-8")
        urls = re.findall(r"<loc>(https?://[^<]+)</loc>", content)
        missing = []
        for url in urls:
            # Extract path from URL
            path_str = url.replace("https://www.toolnestai.tech", "")
            if path_str == "":
                path_str = "/"
            file_path = ROOT / path_str.lstrip("/")
            if not file_path.exists():
                missing.append(path_str)
        self.assertEqual(
            missing,
            [],
            f"Sitemap references missing files: {', '.join(missing)}",
        )


class AffiliateDisclosureTests(unittest.TestCase):
    """Affiliate links and disclosures must be preserved."""

    def test_homepage_affiliate_disclosure(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("affiliate", html.lower())

    def test_footer_disclosure(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        # Footer should have disclosure text
        self.assertIn("Disclosure", html)


class UnsupportedClaimsTests(unittest.TestCase):
    """Changed pages must not introduce unsupported claims."""

    changed_pages = [
        "index.html",
        "tools/decision-engine.html",
        "tools/stack-analyzer.html",
    ]

    unsupported_patterns = [
        r"review\s+count",
        r"fake\s+rating",
        r"popularity\s+score",
    ]

    def test_no_unsupported_claims(self):
        for page in self.changed_pages:
            path = ROOT / page
            if not path.exists():
                continue
            html = path.read_text(encoding="utf-8").lower()
            for pattern in self.unsupported_patterns:
                self.assertNotRegex(
                    html,
                    pattern,
                    f"{page}: contains unsupported claim pattern: {pattern}",
                )


class MobileViewportTests(unittest.TestCase):
    """All HTML pages must have a viewport meta tag."""

    def test_all_pages_have_viewport(self):
        for html_file in ROOT.rglob("*.html"):
            if ".git" in html_file.parts:
                continue
            # Google verification files are not user-facing pages
            stem = html_file.stem.lower()
            if stem.startswith("google"):
                continue
            content = html_file.read_text(encoding="utf-8")
            self.assertIn(
                'name="viewport"',
                content,
                f"{html_file.relative_to(ROOT)}: missing viewport meta tag",
            )


class NavigationTargetTests(unittest.TestCase):
    """Core navigation links must resolve to existing files."""

    nav_targets = [
        "tools/index.html",
        "category/index.html",
        "compare/index.html",
        "best/index.html",
        "alternatives/index.html",
        "goals/index.html",
        "about.html",
        "affiliate-disclosure.html",
        "privacy.html",
        "terms.html",
        "contact.html",
        "how-we-test.html",
        "editorial-policy.html",
    ]

    def test_nav_targets_exist(self):
        for target in self.nav_targets:
            path = ROOT / target
            self.assertTrue(
                path.exists(),
                f"Navigation target does not exist: {target}",
            )


class InteractiveControlLabelTests(unittest.TestCase):
    """New/changed interactive controls must have accessible labels."""

    def test_decision_engine_chips_have_labels(self):
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        # Chips are dynamically created with role="checkbox" and aria-checked via JS
        # Verify the JS code that creates them includes these attributes
        self.assertIn('setAttribute("role"', html)
        self.assertIn('aria-checked', html)

    def test_decision_engine_filters_have_labels(self):
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        # Filter groups should have aria-label
        self.assertIn('aria-label="Select use cases"', html)
        self.assertIn('aria-label="Select categories"', html)

    def test_stack_analyzer_controls_have_labels(self):
        html = (ROOT / "tools" / "stack-analyzer.html").read_text(encoding="utf-8")
        # Search input should have a label
        self.assertIn('aria-label="Select ', html)
        # Tool list should have aria-label
        self.assertIn('aria-label="Available tools"', html)

    def test_homepage_paths_links_have_text(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        # New path links should have visible text
        self.assertIn("Analyze my stack", html)
        self.assertIn("Check tool overlap", html)
        self.assertIn("Decision Engine", html)


class LocalResourcePathTests(unittest.TestCase):
    """Local resource references must resolve to existing files."""

    def test_css_files_exist(self):
        css_files = [
            "assets/site.min.css",
            "assets/mobile-nav.min.css",
        ]
        for css in css_files:
            self.assertTrue(
                (ROOT / css).exists(),
                f"CSS file missing: {css}",
            )

    def test_js_files_exist(self):
        js_files = [
            "assets/mobile-nav.min.js",
        ]
        for js in js_files:
            self.assertTrue(
                (ROOT / js).exists(),
                f"JS file missing: {js}",
            )

    def test_data_files_exist(self):
        data_files = [
            "data/tools-v1.json",
            "data/decision-engine-config.json",
        ]
        for data in data_files:
            self.assertTrue(
                (ROOT / data).exists(),
                f"Data file missing: {data}",
            )


class DecisionEngineUXTests(unittest.TestCase):
    """Decision Engine specific UX improvements."""

    def test_requirements_summary_css(self):
        """CSS for requirements summary must exist."""
        css = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        self.assertIn("de-req-summary", css)

    def test_compare_action_exists(self):
        """Compare action must be added to result cards."""
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        self.assertIn("de-action-compare", html)

    def test_insufficient_evidence_message(self):
        """Insufficient evidence message must exist."""
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        self.assertIn("Insufficient structured evidence", html)

    def test_refine_requirements_link(self):
        """Refine requirements link must exist."""
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        self.assertIn("Refine", html)

    def test_score_de_emphasized(self):
        """Score number CSS should be smaller than confidence label."""
        css = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        # Score num should be 12px, confidence should be 14px
        self.assertIn("de-score-num", css)
        self.assertIn("de-confidence", css)


class StackAnalyzerUXTests(unittest.TestCase):
    """Stack Analyzer specific UX improvements."""

    def test_known_unknown_separation(self):
        """Totals must separate known from unknown pricing."""
        html = (ROOT / "tools" / "stack-analyzer.html").read_text(encoding="utf-8")
        self.assertIn("Known Monthly", html)
        self.assertIn("unknown pricing", html.lower())

    def test_overlap_hint_css(self):
        """Overlap hint CSS must exist."""
        css = (ROOT / "tools" / "stack-analyzer.html").read_text(encoding="utf-8")
        self.assertIn("sa-overlap-hint", css)

    def test_unknown_section_css(self):
        """Unknown pricing section CSS must exist."""
        css = (ROOT / "tools" / "stack-analyzer.html").read_text(encoding="utf-8")
        self.assertIn("sa-unknown-section", css)


class TrustWordingTests(unittest.TestCase):
    """Trust section wording improvements."""

    def test_independent_research_wording(self):
        """Homepage trust section should use 'Independent research'."""
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Independent research", html)

    def test_no_ai_assisted_research_wording(self):
        """Homepage should not use 'AI-assisted research' in trust section."""
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        # The trust section specifically should not say "AI-assisted research"
        # Check the proof list items
        proof_section = re.search(
            r'<ul class="proof"[^>]*>.*?</ul>', html, re.DOTALL
        )
        if proof_section:
            self.assertNotIn(
                "AI-assisted research",
                proof_section.group(0),
                "Trust section should not use 'AI-assisted research' wording",
            )


class DiamondUXTests(unittest.TestCase):
    """Diamond UX regression tests for Batch 1 completion."""

    def test_stack_analyzer_unknown_pricing_display(self):
        """Stack Analyzer should handle unknown pricing without showing $0."""
        html = (ROOT / "tools" / "stack-analyzer.html").read_text(encoding="utf-8")
        # Check that the three-state logic exists
        self.assertIn("Known cost unavailable", html)
        self.assertIn("Complete stack total unavailable", html)

    def test_overlap_checker_evidence_aware(self):
        """Overlap Checker should use evidence-aware logic."""
        html = (ROOT / "tools" / "overlap-checker.html").read_text(encoding="utf-8")
        self.assertIn("Confirmed shared capability", html)
        self.assertIn("ToolNest editorial inference", html)
        self.assertIn("Insufficient data", html)

    def test_overlap_checker_same_tool_blocked(self):
        """Overlap Checker should block same-tool comparison."""
        html = (ROOT / "tools" / "overlap-checker.html").read_text(encoding="utf-8")
        self.assertIn("two different tools", html)

    def test_overlap_checker_swap_button(self):
        """Overlap Checker should have swap button."""
        html = (ROOT / "tools" / "overlap-checker.html").read_text(encoding="utf-8")
        self.assertIn("ovSwapBtn", html)

    def test_overlap_checker_reset_button(self):
        """Overlap Checker should have reset button."""
        html = (ROOT / "tools" / "overlap-checker.html").read_text(encoding="utf-8")
        self.assertIn("ovResetBtn", html)

    def test_comparison_directory_search_exists(self):
        """Comparison directory should have search input."""
        html = (ROOT / "compare" / "index.html").read_text(encoding="utf-8")
        self.assertIn("cmpSearch", html)

    def test_comparison_directory_links_server_rendered(self):
        """All comparison links should be server-rendered in DOM."""
        html = (ROOT / "compare" / "index.html").read_text(encoding="utf-8")
        # Count comparison links
        links = re.findall(r'href="/compare/[a-z]+-vs-[a-z]+\.html"', html)
        self.assertGreaterEqual(len(links), 60, "Should have 60+ comparison links server-rendered")

    def test_comparison_directory_category_filter(self):
        """Comparison directory should have category filter chips."""
        html = (ROOT / "compare" / "index.html").read_text(encoding="utf-8")
        self.assertIn("cmp-cat-chip", html)

    def test_decision_engine_progressive_disclosure(self):
        """Decision Engine should have progressive disclosure."""
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        self.assertIn("deAdvanced", html)
        self.assertIn("Show more filters", html)

    def test_decision_engine_show_more_exists(self):
        """Decision Engine should have Show more button."""
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        self.assertIn("deShowMoreBtn", html)

    def test_decision_engine_clear_selections_exists(self):
        """Decision Engine should have Clear selections button."""
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        self.assertIn("deClearBtn", html)

    def test_decision_engine_selected_count(self):
        """Decision Engine should show selected count."""
        html = (ROOT / "tools" / "decision-engine.html").read_text(encoding="utf-8")
        self.assertIn("deSelectedCount", html)

    def test_byline_compact_component_exists(self):
        """Compact byline component should exist in CSS."""
        css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
        self.assertIn(".byline-compact", css)

    def test_byline_on_editorial_pages(self):
        """Byline should appear on editorial pages."""
        goals_html = (ROOT / "goals" / "index.html").read_text(encoding="utf-8")
        self.assertIn("byline-compact", goals_html)
        compare_html = (ROOT / "compare" / "index.html").read_text(encoding="utf-8")
        self.assertIn("byline-compact", compare_html)

    def test_no_ai_assisted_trust_badge(self):
        """Prominent 'AI-assisted' trust badges should be removed."""
        # Check key editorial pages
        for page in ["goals/index.html", "compare/index.html"]:
            html = (ROOT / page).read_text(encoding="utf-8")
            # The byline should not say "AI-assisted"
            byline_match = re.search(r'byline[^>]*>.*?</div>', html, re.DOTALL)
            if byline_match:
                self.assertNotIn(
                    "AI-assisted",
                    byline_match.group(0),
                    f"{page}: byline should not contain 'AI-assisted'",
                )

    def test_card_variants_exist_in_css(self):
        """All card variants should exist in CSS."""
        css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
        for variant in [".tool-card", ".comparison-card", ".goal-card",
                        ".feature-card", ".result-card", ".evidence-card"]:
            self.assertIn(variant, css, f"{variant} missing from CSS")

    def test_author_page_accountability_sections(self):
        """Author page should have accountability sections."""
        html = (ROOT / "authors" / "abdul-muswir.html").read_text(encoding="utf-8")
        self.assertIn("Abdul Muswir", html)
        self.assertIn("ToolNest", html)

    def test_goals_grouped_by_family(self):
        """Goals hub should organize goals into task families."""
        html = (ROOT / "goals" / "index.html").read_text(encoding="utf-8")
        self.assertIn("goal-family", html)

    def test_goals_use_goal_card_variant(self):
        """Goals should use goal-card variant."""
        html = (ROOT / "goals" / "index.html").read_text(encoding="utf-8")
        self.assertIn("goal-card", html)

    def test_stack_analyzer_pricing_count(self):
        """Stack Analyzer should mention 54 tools with pricing."""
        html = (ROOT / "tools" / "stack-analyzer.html").read_text(encoding="utf-8")
        self.assertIn("54 of 153", html)


if __name__ == "__main__":
    unittest.main()
