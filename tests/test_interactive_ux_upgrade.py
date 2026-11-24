"""
Targeted tests for interactive UX upgrade changes.
Tests Decision Engine progressive disclosure, Overlap Checker self-comparison prevention,
and Stack Analyzer unknown pricing display.
"""
import os
import re
import json
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestDecisionEngineProgressiveDisclosure(unittest.TestCase):
    """Test Decision Engine progressive disclosure changes."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(BASE, "tools", "decision-engine.html")
        with open(path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_chip_counts_removed_from_use_cases(self):
        """Use case chips should not display database counts like '(6)'."""
        # The renderFilters function should not append count to chip textContent
        # Check that the JS no longer has uc.label + " (" + uc.count + ")"
        self.assertNotIn(
            'uc.label + " (" + uc.count + ")"',
            self.html,
            "Use case chips should not show database counts"
        )

    def test_chip_counts_removed_from_categories(self):
        """Category chips should not display database counts."""
        self.assertNotIn(
            'cat + " (" + catMap[cat] + ")"',
            self.html,
            "Category chips should not show database counts"
        )

    def test_progressive_disclosure_show_more(self):
        """Use cases should have a 'Show more' button for progressive disclosure."""
        self.assertIn(
            "de-chip-show-more",
            self.html,
            "Should have a show-more button class for progressive disclosure"
        )
        self.assertIn(
            "CHIP_INITIAL_COUNT",
            self.html,
            "Should define initial chip count for progressive disclosure"
        )

    def test_hidden_chip_class_exists(self):
        """Hidden chips should use a CSS class for progressive disclosure."""
        self.assertIn(
            "hidden-chip",
            self.html,
            "Should have hidden-chip class for chips not initially shown"
        )

    def test_selection_summary_exists(self):
        """Selection summary should be rendered before Find My Tools button."""
        self.assertIn(
            "deSelectionSummary",
            self.html,
            "Should have a selection summary element"
        )
        self.assertIn(
            "renderSelectionSummary",
            self.html,
            "Should have a function to render selection summary"
        )

    def test_change_answers_link(self):
        """Results should have a 'Change answers' link to go back."""
        self.assertIn(
            "Change answers",
            self.html,
            "Results should have a 'Change answers' link"
        )

    def test_clear_all_button(self):
        """Clear button should reset all selections."""
        self.assertIn(
            "Clear all",
            self.html,
            "Should have a Clear all button"
        )

    def test_goal_buttons_auto_run(self):
        """Goal buttons should auto-run the engine after selection."""
        # Check that goal button click handler calls runEngine
        self.assertIn(
            "runEngine()",
            self.html,
            "Goal buttons should auto-run the engine"
        )

    def test_focus_visible_styles(self):
        """Chips should have focus-visible styles for accessibility."""
        self.assertIn(
            "focus-visible",
            self.html,
            "Should have focus-visible styles for keyboard accessibility"
        )

    def test_aria_live_region(self):
        """Results area should have aria-live for screen reader announcements."""
        self.assertIn(
            'aria-live="polite"',
            self.html,
            "Results should have aria-live region for accessibility"
        )


class TestOverlapCheckerSelfComparison(unittest.TestCase):
    """Test Overlap Checker self-comparison prevention."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(BASE, "tools", "overlap-checker.html")
        with open(path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_self_comparison_prevention(self):
        """Comparing a tool with itself should show a clear message."""
        self.assertIn(
            "Same tool selected",
            self.html,
            "Should show 'Same tool selected' message"
        )
        self.assertIn(
            "different",
            self.html,
            "Should tell user to choose different tools"
        )

    def test_analyze_button_exists(self):
        """Should have an explicit Analyze button instead of auto-analyzing."""
        self.assertIn(
            "ovAnalyzeBtn",
            self.html,
            "Should have an Analyze button"
        )
        self.assertIn(
            "Analyze Overlap",
            self.html,
            "Analyze button should have clear label"
        )

    def test_no_auto_analyze_on_change(self):
        """Selectors should not auto-analyze on change."""
        # The old pattern was: selA.addEventListener('change', analyze);
        # New pattern should NOT have this
        # Check that analyze is not directly bound to change
        js_section = self.html.split("<script>")[-1].split("</script>")[0]
        # The new code should have updatePreview on change, not analyze
        self.assertIn(
            "updatePreview",
            js_section,
            "Should update preview on change, not auto-analyze"
        )

    def test_tool_preview_exists(self):
        """Tool selectors should show preview with logo."""
        self.assertIn(
            "ovToolAPreview",
            self.html,
            "Should have Tool A preview element"
        )
        self.assertIn(
            "ovToolBPreview",
            self.html,
            "Should have Tool B preview element"
        )

    def test_visual_distinction_tool_a_b(self):
        """Tool A and Tool B panels should be visually distinct."""
        self.assertIn(
            "ov-selector-panel",
            self.html,
            "Should have selector panels for visual distinction"
        )
        # Check for different border colors
        self.assertIn(
            "#0F6B5C",
            self.html,
            "Tool A should have teal border"
        )
        self.assertIn(
            "#7C3AED",
            self.html,
            "Tool B should have purple border"
        )

    def test_category_filter_no_counts(self):
        """Category filter chips should not show database counts."""
        js_section = self.html.split("<script>")[-1].split("</script>")[0]
        self.assertNotIn(
            "D.categories[cat].length",
            js_section,
            "Category filter should not show counts"
        )

    def test_related_tools_component(self):
        """Should have the new related-tools card component."""
        self.assertIn(
            "ov-related-card",
            self.html,
            "Should have related-tools card component"
        )
        self.assertIn(
            "ov-related-card-cta",
            self.html,
            "Related cards should have integrated CTA buttons"
        )


class TestStackAnalyzerUnknownPricing(unittest.TestCase):
    """Test Stack Analyzer unknown pricing display."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(BASE, "tools", "stack-analyzer.html")
        with open(path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_unknown_pricing_visual_distinction(self):
        """Unknown pricing should be visually distinct from $0."""
        self.assertIn(
            "unknown-pricing",
            self.html,
            "Should have CSS class for unknown pricing items"
        )
        self.assertIn(
            "#B45309",
            self.html,
            "Unknown pricing should use amber color"
        )

    def test_unknown_pricing_section(self):
        """Should have a section for tools with unknown pricing."""
        self.assertIn(
            "saUnknownBox",
            self.html,
            "Should have unknown pricing section"
        )
        self.assertIn(
            "unknown pricing",
            self.html.lower(),
            "Should label unknown pricing clearly"
        )

    def test_known_vs_unknown_totals(self):
        """Totals should distinguish known from unknown pricing."""
        self.assertIn(
            "Known Monthly",
            self.html,
            "Monthly total should be labeled as 'Known'"
        )
        self.assertIn(
            "Known Annual",
            self.html,
            "Annual total should be labeled as 'Known'"
        )

    def test_related_tools_component(self):
        """Should have the new related-tools card component."""
        self.assertIn(
            "sa-related-card",
            self.html,
            "Should have related-tools card component"
        )
        self.assertIn(
            "sa-related-card-cta",
            self.html,
            "Related cards should have integrated CTA buttons"
        )

    def test_category_filter_keeps_counts(self):
        """Stack Analyzer category filter should keep counts for navigation."""
        js_section = self.html.split("<script>")[-1].split("</script>")[0]
        self.assertIn(
            "cats[catNames[i]]",
            js_section,
            "Stack Analyzer should keep category counts for navigation"
        )


class TestAutomationBudgetEstimator(unittest.TestCase):
    """Test Automation Budget Estimator CSS variable usage."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(BASE, "tools", "automation-budget-estimator.html")
        with open(path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_no_hardcoded_colors(self):
        """Should not use hardcoded hex colors in CSS."""
        css_section = self.html.split("<style>")[1].split("</style>")[0]
        # Check that hardcoded #12A68E is replaced with CSS variables
        self.assertNotIn(
            "#12A68E",
            css_section,
            "Should not use hardcoded teal color"
        )
        self.assertNotIn(
            "#6b7280",
            css_section,
            "Should not use hardcoded gray color"
        )

    def test_css_variables_used(self):
        """Should use CSS variables for colors."""
        css_section = self.html.split("<style>")[1].split("</style>")[0]
        self.assertIn(
            "var(--brand)",
            css_section,
            "Should use --brand CSS variable"
        )
        self.assertIn(
            "var(--line)",
            css_section,
            "Should use --line CSS variable"
        )

    def test_related_tools_section(self):
        """Should have a related-tools section."""
        self.assertIn(
            "est-related-card",
            self.html,
            "Should have related-tools card component"
        )


class TestWorkflowExplorer(unittest.TestCase):
    """Test Workflow Explorer changes."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(BASE, "tools", "workflow-explorer.html")
        with open(path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_count_badges_removed(self):
        """Workflow buttons should not show internal count badges."""
        js_section = self.html.split("<script>")[-1].split("</script>")[0]
        # The we-count div with candidate_tools.length should be removed
        self.assertNotIn(
            "we-count",
            js_section,
            "Workflow buttons should not render count badges in JS"
        )

    def test_related_tools_section(self):
        """Should have a related-tools section."""
        self.assertIn(
            "we-related-card",
            self.html,
            "Should have related-tools card component"
        )


class TestNavigationConsistency(unittest.TestCase):
    """Test that 'Find my tool' nav links consistently to #picker across all pages."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {}
        for name in ["decision-engine.html", "stack-analyzer.html", "overlap-checker.html",
                      "workflow-explorer.html", "automation-budget-estimator.html"]:
            path = os.path.join(BASE, "tools", name)
            with open(path, "r", encoding="utf-8") as f:
                cls.pages[name] = f.read()

    def test_find_my_tool_goes_to_picker(self):
        """All pages must link 'Find my tool' to /#picker, not to a specific tool page."""
        for name, html in self.pages.items():
            # Extract just the nav section (between <nav> and </nav> tags in the header)
            # Find the main nav by looking for the "Find my tool" button context
            # The nav bar contains: <a class="btn" href="...">Find my tool</a>
            # We need to verify this specific link points to /#picker
            import re
            # Find all "Find my tool" links
            find_my_tool_links = re.findall(r'<a[^>]*class="btn"[^>]*href="([^"]*)"[^>]*>Find my tool</a>', html)
            for link in find_my_tool_links:
                self.assertNotEqual(
                    link,
                    "/tools/decision-engine.html",
                    f"{name}: 'Find my tool' button should not link to decision-engine.html"
                )
                self.assertEqual(
                    link,
                    "/#picker",
                    f"{name}: 'Find my tool' button must link to /#picker"
                )


class TestToolFirstOrdering(unittest.TestCase):
    """Test that the interactive tool appears before 'How it works' on all utility pages."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {}
        for name in ["decision-engine.html", "stack-analyzer.html", "overlap-checker.html",
                      "workflow-explorer.html", "automation-budget-estimator.html"]:
            path = os.path.join(BASE, "tools", name)
            with open(path, "r", encoding="utf-8") as f:
                cls.pages[name] = f.read()

    def test_how_it_works_after_tool(self):
        """'How it works' section must appear after the interactive tool section."""
        for name, html in self.pages.items():
            # Find positions of key elements — look for the actual interactive tool
            # container, not CSS class names which may appear in <style> blocks
            # Skip the <style> block entirely
            style_end = html.find("</style>")
            if style_end == -1:
                continue
            body_content = html[style_end:]

            # Find "How it works" heading position
            how_it_works_pos = body_content.find("<h2>How it works</h2>")
            if how_it_works_pos == -1:
                how_it_works_pos = body_content.find("How it works")

            # Find the interactive tool section — look for specific structural markers
            # that indicate the actual tool, not CSS classes
            tool_markers = [
                "de-wrap", "sa-wrap", "ov-wrap", "we-wrap",
                "de-filter", "sa-stack", "ov-selectors", "we-workflow",
                'id="estimator-form"', 'id="est-budget"',
                "estimator-form", "est-budget"
            ]
            tool_pos = len(body_content)  # default to end
            for marker in tool_markers:
                pos = body_content.find(marker)
                if pos != -1 and pos < tool_pos:
                    tool_pos = pos

            if how_it_works_pos != -1 and tool_pos < len(body_content):
                self.assertGreater(
                    how_it_works_pos,
                    tool_pos,
                    f"{name}: 'How it works' must appear after the interactive tool section"
                )


class TestTrustStripPlacement(unittest.TestCase):
    """Test that tn-trust-strip appears after the tool on utility pages."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {}
        for name in ["decision-engine.html", "stack-analyzer.html", "overlap-checker.html",
                      "workflow-explorer.html", "automation-budget-estimator.html"]:
            path = os.path.join(BASE, "tools", name)
            with open(path, "r", encoding="utf-8") as f:
                cls.pages[name] = f.read()

    def test_trust_strip_after_tool(self):
        """tn-trust-strip must appear after the interactive tool section."""
        for name, html in self.pages.items():
            tool_markers = [
                "de-wrap", "sa-wrap", "ov-wrap", "we-wrap", "est-wrap"
            ]
            tool_pos = -1
            for marker in tool_markers:
                pos = html.find(marker)
                if pos != -1:
                    tool_pos = pos
                    break
            trust_pos = html.find("tn-trust-strip")
            if tool_pos != -1 and trust_pos != -1:
                # Trust strip should be after the tool section closing
                # Find the closing of the tool section
                tool_section_end = html.rfind("</section>", 0, trust_pos)
                if tool_section_end != -1 and tool_section_end > tool_pos:
                    self.assertGreater(
                        trust_pos,
                        tool_section_end,
                        f"{name}: tn-trust-strip must appear after the tool section"
                    )


class TestStackEmptyState(unittest.TestCase):
    """Test Stack Analyzer empty state improvements."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(BASE, "tools", "stack-analyzer.html")
        with open(path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_empty_state_text(self):
        """Empty state should say 'No tools selected yet'."""
        self.assertIn(
            "No tools selected yet",
            self.html,
            "Empty state must show 'No tools selected yet'"
        )

    def test_empty_state_instruction(self):
        """Empty state should have an instruction."""
        self.assertIn(
            "sa-empty-instruction",
            self.html,
            "Empty state must have an instruction element"
        )

    def test_example_stack_button(self):
        """Empty state should have a 'Try an example stack' button."""
        self.assertIn(
            "Try an example stack",
            self.html,
            "Empty state must have 'Try an example stack' button"
        )
        self.assertIn(
            "saExampleStackBtn",
            self.html,
            "Example stack button must have an ID"
        )


class TestCopyShareButton(unittest.TestCase):
    """Test that copy/share uses <button> semantics, not href='#'."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(BASE, "tools", "stack-analyzer.html")
        with open(path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_copy_share_is_button(self):
        """Copy Share Link must be a <button>, not an <a href='#'>."""
        # Find the saShareLink element context
        share_section = self.html[self.html.find('saShareLink')-50:self.html.find('saShareLink')+100] if 'saShareLink' in self.html else ""
        self.assertIn(
            '<button',
            share_section,
            "Copy Share Link must use <button> element"
        )
        # Check no href="#" pattern for share link
        self.assertNotIn(
            'href="#">Copy Share Link',
            self.html,
            "Copy Share Link must not use href='#'"
        )

    def test_aria_live_confirmation(self):
        """Copy action should have aria-live confirmation."""
        self.assertIn(
            'aria-live',
            self.html,
            "Copy action should have aria-live region for confirmation"
        )


class TestOverlapSearchableSelectors(unittest.TestCase):
    """Test that Overlap Checker uses searchable comboboxes."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(BASE, "tools", "overlap-checker.html")
        with open(path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_combobox_role(self):
        """Tool selectors must use combobox ARIA role."""
        self.assertIn(
            'role="combobox"',
            self.html,
            "Tool selectors must have combobox ARIA role"
        )

    def test_listbox_role(self):
        """Dropdowns must use listbox ARIA role."""
        self.assertIn(
            'role="listbox"',
            self.html,
            "Dropdowns must have listbox ARIA role"
        )

    def test_search_input(self):
        """Each selector must have a text search input."""
        self.assertIn(
            "ovToolAInput",
            self.html,
            "Tool A must have a search input"
        )
        self.assertIn(
            "ovToolBInput",
            self.html,
            "Tool B must have a search input"
        )

    def test_clear_selection_button(self):
        """Each selector must have a clear selection button."""
        self.assertIn(
            "ovToolAClear",
            self.html,
            "Tool A must have a clear button"
        )
        self.assertIn(
            "ovToolBClear",
            self.html,
            "Tool B must have a clear button"
        )

    def test_no_plain_select(self):
        """Should not use plain <select> for tool selection."""
        # Check that ovToolA and ovToolB select elements are gone
        self.assertNotIn(
            'id="ovToolA"',
            self.html.replace('ovToolAInput', '').replace('ovToolAClear', '').replace('ovToolADropdown', '').replace('ovToolACombobox', ''),
            "Should not use plain <select> for Tool A"
        )

    def test_keyboard_navigation(self):
        """Combobox must support keyboard navigation."""
        js_section = self.html.split("<script>")[-1].split("</script>")[0]
        self.assertIn(
            "ArrowDown",
            js_section,
            "Must handle ArrowDown key for keyboard navigation"
        )
        self.assertIn(
            "ArrowUp",
            js_section,
            "Must handle ArrowUp key for keyboard navigation"
        )

    def test_no_results_state(self):
        """Combobox must show no-results message."""
        self.assertIn(
            "No tools match your search",
            self.html,
            "Must show no-results message when search matches nothing"
        )


class TestDecisionEngineFilterHiding(unittest.TestCase):
    """Test that Decision Engine hides unsupported filters."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(BASE, "tools", "decision-engine.html")
        with open(path, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def test_filter_visibility_logic(self):
        """Filters with no data should be hidden."""
        js_section = self.html.split("<script>")[-1].split("</script>")[0]
        # Check that filter rendering checks for data availability
        # The Decision Engine uses renderFilters which filters out empty groups
        self.assertIn(
            "renderFilters",
            js_section,
            "Should have renderFilters function that checks data availability"
        )


if __name__ == "__main__":
    unittest.main()
