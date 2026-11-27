"""Contract between the runtime catalog (data/tools-v1.json) and everything that renders it.

data/tools-v1.json is fetched in the browser by the homepage, the tool directory, the stack analyzer, the
overlap checker and the decision engine. One malformed record (a leaked test fixture) used to add an extra
tool, an "undefined" filter chip, a broken card and a wrong visible count, while the existing catalog checks
stayed green because they validate the per-tool v2 records instead of this file.

These checks only read files: no network, no browser, nothing is written.
"""

import functools
import json
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "tools-v1.json"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_FIELDS = ("id", "name", "cat", "site", "best", "logo", "category")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def load_catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=None)
def _names_in(directory):
    return frozenset(entry.name for entry in directory.iterdir())


def exists_exact_case(relative):
    """True only if every path component matches exactly (Windows and macOS would accept any case, Vercel does not)."""
    current = ROOT
    for part in Path(relative).parts:
        if not current.is_dir() or part not in _names_in(current):
            return False
        current = current / part
    return current.is_file()


def read_page(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class CatalogRenderingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()
        cls.tools = cls.catalog["tools"]
        cls.by_id = {tool.get("id"): tool for tool in cls.tools}

    def assertNoProblems(self, problems, headline):
        self.assertEqual([], problems, headline + ":\n  " + "\n  ".join(problems))

    # -- the shape of the catalog itself ----------------------------------------------------------------

    def test_envelope_count_matches_the_records(self):
        self.assertEqual(
            self.catalog["count"],
            len(self.tools),
            "data/tools-v1.json says count=%s but holds %s records" % (self.catalog["count"], len(self.tools)),
        )

    def test_ids_are_unique_url_safe_slugs(self):
        problems = []
        seen = set()
        for tool in self.tools:
            tool_id = tool.get("id")
            if not isinstance(tool_id, str) or not SLUG_RE.match(tool_id):
                problems.append("invalid id %r" % (tool_id,))
            elif tool_id in seen:
                problems.append("duplicate id %s" % tool_id)
            seen.add(tool_id)
        self.assertNoProblems(problems, "catalog ids")

    def test_no_test_fixtures_in_the_production_catalog(self):
        leaked = [
            tool.get("id")
            for tool in self.tools
            if re.search(r"fixture", "%s %s" % (tool.get("id"), tool.get("name")), re.IGNORECASE)
        ]
        self.assertEqual(
            [],
            leaked,
            "test fixture(s) %s leaked into data/tools-v1.json (see tests/test_canonical_propagation.py)" % leaked,
        )

    def test_every_record_has_the_fields_the_pages_render(self):
        problems = []
        for tool in self.tools:
            for field in REQUIRED_FIELDS:
                if not tool.get(field):
                    problems.append("%s: missing %s" % (tool.get("id"), field))
            category = tool.get("category") or {}
            if category and not (category.get("label") and category.get("slug")):
                problems.append("%s: category needs a label and a slug" % tool.get("id"))
            elif category and tool.get("cat") != category.get("label"):
                problems.append("%s: cat %r != category.label %r" % (tool.get("id"), tool.get("cat"), category.get("label")))
        self.assertNoProblems(problems, "records the directory and homepage cannot render")

    def test_category_slugs_are_consistent_and_have_a_page(self):
        slugs_by_label = {}
        for tool in self.tools:
            category = tool.get("category") or {}
            slugs_by_label.setdefault(category.get("label"), set()).add(category.get("slug"))
        problems = []
        for label, slugs in sorted(slugs_by_label.items(), key=lambda item: str(item[0])):
            if len(slugs) > 1:
                problems.append("category %r uses several slugs: %s" % (label, sorted(map(str, slugs))))
            for slug in slugs:
                if not exists_exact_case("category/%s.html" % slug):
                    problems.append("category %r: no page category/%s.html" % (label, slug))
        self.assertNoProblems(problems, "category data")

    # -- everything a record points at must exist ---------------------------------------------------------

    def test_every_tool_has_a_review_page(self):
        missing = [t["id"] for t in self.tools if t.get("id") and not exists_exact_case("tools/%s.html" % t["id"])]
        self.assertEqual([], missing, "records without tools/<id>.html (cards would link to a 404): %s" % missing)

    def test_logo_files_exist_and_are_valid_images(self):
        problems = []
        for tool in self.tools:
            logo = tool.get("logo")
            if not logo:
                continue  # reported by the required-fields check
            if not logo.startswith("/assets/logos/"):
                problems.append("%s: logo %s is not under /assets/logos/" % (tool["id"], logo))
                continue
            relative = logo.lstrip("/")
            if not exists_exact_case(relative):
                problems.append("%s: %s not found (exact case)" % (tool["id"], relative))
                continue
            data = (ROOT / relative).read_bytes()
            if relative.endswith(".png"):
                if not data.startswith(PNG_SIGNATURE):
                    problems.append("%s: %s is not a valid PNG" % (tool["id"], relative))
                    continue
                width, height = struct.unpack(">II", data[16:24])
                if min(width, height) < 32:
                    problems.append("%s: %s is only %sx%s" % (tool["id"], relative, width, height))
                if abs(width - height) > max(1, 0.02 * max(width, height)):
                    problems.append("%s: %s is not square (%sx%s), it would render distorted" % (tool["id"], relative, width, height))
            elif relative.endswith(".svg"):
                if b"<svg" not in data[:2000]:
                    problems.append("%s: %s is not an SVG" % (tool["id"], relative))
            else:
                problems.append("%s: unsupported logo type %s" % (tool["id"], relative))
        self.assertNoProblems(problems, "logo references")

    # -- the homepage hard-codes ids that must resolve in the catalog ------------------------------------

    def _homepage_ids(self):
        html = read_page("index.html")
        featured = re.search(r"var FEATURED = (\[[^\]]*\]);", html)
        goals = re.search(r"var GOALS = \[(.*?)\n\s*\];", html, re.DOTALL)
        self.assertIsNotNone(featured, "var FEATURED not found in index.html; update this test if it moved")
        self.assertIsNotNone(goals, "var GOALS not found in index.html; update this test if it moved")
        goal_tools = re.findall(r'tool:\s*"([^"]+)"', goals.group(1))
        also = [i for group in re.findall(r"also_consider:\s*\[([^\]]*)\]", goals.group(1)) for i in re.findall(r'"([^"]+)"', group)]
        guides = re.findall(r'guide:\s*"([^"]+)"', goals.group(1))
        self.assertTrue(goal_tools, "no goals parsed from index.html")
        return json.loads(featured.group(1)), goal_tools, also, guides

    def test_homepage_featured_and_goal_ids_exist_in_the_catalog(self):
        featured, goal_tools, also, guides = self._homepage_ids()
        problems = []
        for label, ids in (("featured", featured), ("goal tool", goal_tools), ("also_consider", also)):
            for tool_id in ids:
                if tool_id not in self.by_id:
                    problems.append("%s %s is not in the catalog (the picker/featured card would never render)" % (label, tool_id))
        for guide in guides:
            if not exists_exact_case(guide.lstrip("/")):
                problems.append("goal guide %s does not exist" % guide)
        self.assertNoProblems(problems, "homepage ids")

    # -- numbers that are written into static HTML must agree with the catalog ----------------------------

    def test_static_directory_counts_match_the_catalog(self):
        total = len(self.tools)
        html = read_page("tools/index.html")
        problems = []
        title = re.search(r"<title>[^<]*?(\d+) Researched Tools", html)
        if not title or int(title.group(1)) != total:
            problems.append("<title> says %s, catalog has %s" % (title.group(1) if title else "nothing", total))
        itemlist = re.search(r'id="tn-tools-itemlist">.*?"numberOfItems":(\d+)', html, re.DOTALL)
        if not itemlist or int(itemlist.group(1)) != total:
            problems.append("ItemList numberOfItems is %s, catalog has %s" % (itemlist.group(1) if itemlist else "missing", total))
        heading = re.search(r"<h2>All (\d+) tool profiles</h2>", html)
        if not heading or int(heading.group(1)) != total:
            problems.append("'All N tool profiles' says %s, catalog has %s" % (heading.group(1) if heading else "missing", total))
        self.assertNoProblems(problems, "static counts on tools/index.html")

    def test_category_pages_do_not_misstate_how_many_tools_exist(self):
        label_by_slug = {}
        for tool in self.tools:
            category = tool.get("category") or {}
            label_by_slug[category.get("slug")] = category.get("label")
        problems = []
        for page in sorted((ROOT / "category").glob("*.html")):
            slug = page.stem
            if slug == "index" or slug not in label_by_slug:
                continue
            in_catalog = sum(1 for t in self.tools if t.get("cat") == label_by_slug[slug])
            html = page.read_text(encoding="utf-8")
            section = html.split('id="tools"', 1)[-1].split("</section>", 1)[0]
            listed = len(re.findall(r'<article class="card" id="t-', section))
            claim_all = re.search(r"Browse all (\d+) ", section)
            claim_part = re.search(r"Browse (\d+) of the (\d+) ", section)
            if claim_all and (int(claim_all.group(1)) != in_catalog or listed != in_catalog):
                problems.append(
                    "%s says 'all %s' but the catalog has %s and the page lists %s" % (page.name, claim_all.group(1), in_catalog, listed)
                )
            if claim_part and (int(claim_part.group(2)) != in_catalog or int(claim_part.group(1)) != listed):
                problems.append(
                    "%s says %s of %s but the catalog has %s and the page lists %s"
                    % (page.name, claim_part.group(1), claim_part.group(2), in_catalog, listed)
                )
        self.assertNoProblems(problems, "category page counts")


if __name__ == "__main__":
    unittest.main()
