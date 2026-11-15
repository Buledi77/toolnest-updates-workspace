#!/usr/bin/env python3
"""Build the static ToolNest corpus from committed HTML and site configuration."""

from __future__ import annotations

import html
import json
import re
import subprocess
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from content_metrics import measure, section_name, unique_marked_sections

ROOT = Path(__file__).resolve().parents[1]
SITE_CONFIG = ROOT / "data" / "site.json"
INDEX_ALLOWLIST = ROOT / "data" / "index-allowlist.json"
PUBLIC_HOST = "https://www.toolnestai.tech"
SEO_SUFFIXES = {".html", ".xml", ".txt", ".json", ".css", ".js"}
SKIP_PAGES = {"googlef7f3d54afb5d5344.html"}


def write_utf8(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def strip_boms() -> None:
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in SEO_SUFFIXES and ".git" not in path.parts:
            data = path.read_bytes()
            if data.startswith(b"\xef\xbb\xbf"):
                path.write_bytes(data[3:])


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.h1_count = 0
        self.h1_text = ""
        self.in_title = False
        self.in_h1 = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.in_h1 = True
            self.h1_count += 1
        elif tag == "meta" and attrs.get("name", "").lower() == "description":
            self.description = attrs.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "h1":
            self.in_h1 = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_h1:
            self.h1_text += data


def parse_page(content: str) -> PageParser:
    parser = PageParser()
    parser.feed(content)
    return parser


def attr_pattern(name: str, value: str | None = None) -> str:
    if value is None:
        return rf"\s+{name}\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)"
    return rf"\s+{name}\s*=\s*(?:\"{re.escape(value)}\"|'{re.escape(value)}'|{re.escape(value)})"


def remove_tag(content: str, tag: str, predicate) -> str:
    pattern = re.compile(rf"<{tag}\b[^>]*>", re.IGNORECASE)

    def replace(match):
        return "" if predicate(match.group(0)) else match.group(0)

    return pattern.sub(replace, content)


def add_or_replace_head_meta(content: str, name: str, value: str) -> str:
    content = remove_tag(
        content,
        "meta",
        lambda tag: re.search(attr_pattern("name", name), tag, re.IGNORECASE) is not None,
    )
    return content.replace("</head>", f'<meta name="{name}" content="{html.escape(value, quote=True)}">\n</head>', 1)


def add_or_replace_property(content: str, prop: str, value: str) -> str:
    content = remove_tag(
        content,
        "meta",
        lambda tag: re.search(attr_pattern("property", prop), tag, re.IGNORECASE) is not None,
    )
    return content.replace("</head>", f'<meta property="{prop}" content="{html.escape(value, quote=True)}">\n</head>', 1)


def ensure_title(content: str, title: str) -> str:
    content = re.sub(r"<title\b[^>]*>.*?</title\s*>", "", content, flags=re.IGNORECASE | re.DOTALL)
    return content.replace("<head>", f"<head><title>{html.escape(title)}</title>", 1)


def ensure_canonical(content: str, url: str) -> str:
    content = remove_tag(
        content,
        "link",
        lambda tag: re.search(attr_pattern("rel", "canonical"), tag, re.IGNORECASE) is not None,
    )
    return content.replace("</head>", f'<link rel="canonical" href="{url}">\n</head>', 1)


def ensure_lang(content: str) -> str:
    def replace(match):
        attrs = re.sub(
            r"\s+lang\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
            "",
            match.group(1),
            flags=re.IGNORECASE,
        )
        return f'<html lang="en"{attrs}>'

    return re.sub(r"<html\b([^>]*)>", replace, content, count=1, flags=re.IGNORECASE)


def ensure_h1(content: str, fallback: str) -> str:
    parser = parse_page(content)
    if parser.h1_count:
        return content
    return content.replace("<main", f"<main><h1>{html.escape(fallback)}</h1>", 1)


def normalize_links(content: str) -> str:
    pattern = re.compile(r"<a\b([^>]*?)>", re.IGNORECASE | re.DOTALL)

    def replace(match):
        attrs = match.group(1)
        href_match = re.search(r"\bhref\s*=\s*([\"'])(.*?)\1", attrs, re.IGNORECASE | re.DOTALL)
        if not href_match:
            return match.group(0)
        href = href_match.group(2).strip()
        parsed = urlparse(href)
        external = parsed.scheme in {"http", "https"} and parsed.netloc.lower() not in {
            "toolnestai.tech",
            "www.toolnestai.tech",
        }
        rel_match = re.search(r"\brel\s*=\s*([\"'])(.*?)\1", attrs, re.IGNORECASE | re.DOTALL)
        tokens = rel_match.group(2).split() if rel_match else []
        if external:
            tokens = [token for token in tokens if token not in {"nofollow", "sponsored", "noopener"}]
            tokens = ["sponsored", "nofollow", "noopener"] + tokens
            if rel_match:
                attrs = attrs[: rel_match.start(2)] + " ".join(tokens) + attrs[rel_match.end(2) :]
            else:
                attrs += ' rel="sponsored nofollow noopener"'
            if not re.search(r"\btarget\s*=", attrs, re.IGNORECASE):
                attrs += ' target="_blank"'
        else:
            tokens = [token for token in tokens if token not in {"nofollow", "sponsored"}]
            if rel_match:
                if tokens:
                    attrs = attrs[: rel_match.start(2)] + " ".join(tokens) + attrs[rel_match.end(2) :]
                else:
                    attrs = attrs[: rel_match.start()] + attrs[rel_match.end() :]
        return f"<a{attrs}>"

    return pattern.sub(replace, content)


def make_title(parser: PageParser, path: Path, used: set[str]) -> str:
    base = " ".join((parser.title or parser.h1_text or path.stem).split())
    title = base if 50 <= len(base) <= 60 else f"{base} | ToolNest"
    suffixes = (" Guide", " Review", " Overview", " Explained")
    suffix_index = 0
    while len(title) < 50:
        title += suffixes[min(suffix_index, len(suffixes) - 1)]
        suffix_index += 1
    if len(title) > 60:
        title = title[:60].rstrip(" |:-")
    if title in used:
        title = f"{title[:55].rstrip()} {len(used) + 1}"
    return title[:60].rstrip()


def make_description(parser: PageParser, path: Path, used: set[str]) -> str:
    existing = " ".join(parser.description.split())
    if 140 <= len(existing) <= 160 and existing not in used:
        return existing
    subject = " ".join((parser.h1_text or parser.title or path.stem).split())
    description = (
        f"{subject} from ToolNest: compare fit, trade-offs, alternatives, and current "
        "details before choosing the right option for your workflow."
    )
    if len(description) < 140:
        description += " Verify current details on the official site."
    description = description[:160].rstrip(" ,;:-")
    if description in used:
        description = f"{description[:145].rstrip()} See the page for details."
    return description[:160].rstrip()


def add_analytics_and_verification(content: str, config: dict, url: str, title: str, description: str) -> str:
    content = add_or_replace_property(content, "og:title", title)
    content = add_or_replace_property(content, "og:description", description)
    content = add_or_replace_property(content, "og:url", url)
    content = add_or_replace_property(content, "og:image", f"{PUBLIC_HOST}/assets/og-default.png")
    content = add_or_replace_head_meta(content, "twitter:card", "summary_large_image")
    content = add_or_replace_head_meta(content, "twitter:title", title)
    content = add_or_replace_head_meta(content, "twitter:description", description)
    content = add_or_replace_head_meta(content, "twitter:image", f"{PUBLIC_HOST}/assets/og-default.png")
    for key, name in (("GSC_VERIFY", "google-site-verification"), ("BING_VERIFY", "msvalidate.01")):
        content = remove_tag(
            content,
            "meta",
            lambda tag, name=name: re.search(attr_pattern("name", name), tag, re.IGNORECASE) is not None,
        )
        if config.get(key):
            content = content.replace(
                "</head>",
                f'<meta name="{name}" content="{html.escape(config[key], quote=True)}">\n</head>',
                1,
            )
    ga_id = config.get("GA4_ID", "").strip()
    content = re.sub(
        r'<script async src="https://www\.googletagmanager\.com/gtag/js\?id=[^"]+"></script>\s*<script>window\.dataLayer=.*?</script>',
        "",
        content,
        flags=re.DOTALL,
    )
    if ga_id:
        snippet = (
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={html.escape(ga_id, quote=True)}"></script>'
            f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}'
            f'gtag("js",new Date());gtag("config","{html.escape(ga_id, quote=True)}");</script>'
        )
        content = content.replace("</head>", snippet + "\n</head>", 1)
    return content


def add_jsonld(content: str, payload: dict, schema_type: str) -> str:
    pattern = re.compile(
        r'<script type="application/ld\+json">.*?</script>',
        re.IGNORECASE | re.DOTALL,
    )
    content = pattern.sub(
        lambda match: ""
        if f'"@type":"{schema_type}"' in match.group(0).replace(" ", "")
        else match.group(0),
        content,
    )
    script = (
        '<script type="application/ld+json">'
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )
    return content.replace("</head>", script + "\n</head>", 1)


def person_schema(config: dict) -> dict:
    person = {
        "@type": "Person",
        "name": config.get("AUTHOR_NAME", "Abdul Muswir"),
        "url": f"{PUBLIC_HOST}/authors/abdul-muswir.html",
    }
    same_as = [value for value in config.get("AUTHOR_SAME_AS", []) if value]
    if same_as:
        person["sameAs"] = same_as
    return person


def add_structured_data(
    content: str, config: dict, relative: str, title: str, description: str, url: str
) -> str:
    if relative == "index.html":
        organization = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "ToolNest",
            "url": PUBLIC_HOST + "/",
            "logo": f"{PUBLIC_HOST}/assets/og-default.png",
        }
        same_as = [value for value in config.get("ORGANIZATION_SAME_AS", []) if value]
        if same_as:
            organization["sameAs"] = same_as
        content = add_jsonld(content, organization, "Organization")
    elif relative == "authors/abdul-muswir.html":
        person = {"@context": "https://schema.org", **person_schema(config)}
        content = add_jsonld(content, person, "Person")
    elif relative not in {"404.html", "privacy.html", "terms.html", *SKIP_PAGES}:
        article = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": url,
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "author": person_schema(config),
            "publisher": {
                "@type": "Organization",
                "name": "ToolNest",
                "url": PUBLIC_HOST + "/",
                "logo": {"@type": "ImageObject", "url": f"{PUBLIC_HOST}/assets/og-default.png"},
            },
            "image": f"{PUBLIC_HOST}/assets/og-default.png",
        }
        content = add_jsonld(content, article, "Article")
    return content


def add_footer_trust_links(content: str) -> str:
    pattern = re.compile(
        r'(<nav\b[^>]*aria-label="About this site"[^>]*>)(.*?)(</nav>)',
        re.IGNORECASE | re.DOTALL,
    )

    def replace(match):
        body = match.group(2)
        links = (
            '<a href="/authors/abdul-muswir.html">Author: Abdul Muswir</a>'
            '<a href="/how-we-test.html">How we test</a>'
            '<a href="/editorial-policy.html">Editorial policy</a>'
        )
        for href in (
            "/authors/abdul-muswir.html",
            "/how-we-test.html",
            "/editorial-policy.html",
        ):
            if href in body:
                links = links.replace(
                    re.search(rf'<a href="{re.escape(href)}">.*?</a>', links).group(0),
                    "",
                )
        return match.group(1) + body + links + match.group(3)

    return pattern.sub(replace, content, count=1)


def add_editorial_strip(content: str, path: Path, config: dict) -> str:
    relative_parts = path.relative_to(ROOT).parts
    if relative_parts[0] not in {"tools", "compare", "alternatives"} or path.stem == "index":
        return content
    content = re.sub(
        r'<div class="wrap tn-trust-strip">.*?</div>',
        "",
        content,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
    status = (
        "Hands-on tested"
        if re.search(r"(?<!not )hands-on tested", content, re.IGNORECASE)
        else "Researched"
    )
    updated = git_date(path)
    name = html.escape(config.get("AUTHOR_NAME", "Abdul Muswir"))
    strip = (
        '<div class="wrap tn-trust-strip">'
        f'<p class="byline">By <a href="/authors/abdul-muswir.html">{name}</a> '
        f'&middot; Updated {updated} &middot; '
        f'<a href="/how-we-test.html">{status}</a></p>'
        '<p class="affiliate-note">Some links may be affiliate links; they never change the verdict. '
        '<a href="/affiliate-disclosure.html">Affiliate disclosure</a>.</p>'
        "</div>"
    )
    marker = content.find("</section>", content.find('<section class="hero phero"'))
    if marker == -1:
        return content
    return content[: marker + len("</section>")] + strip + content[marker + len("</section>") :]


def set_robots(content: str, indexable: bool) -> str:
    value = "index,follow,max-image-preview:large" if indexable else "noindex, follow"
    return add_or_replace_head_meta(content, "robots", value)


def load_allowlist() -> set[str]:
    data = json.loads(INDEX_ALLOWLIST.read_text(encoding="utf-8"))
    return {str(path) for path in data.get("paths", [])}


def page_route(relative: str) -> str:
    return "/" if relative == "index.html" else f"/{relative}"


def filter_homepage_featured(content: str, indexable: dict[str, bool]) -> str:
    match = re.search(r"var FEATURED = \[([^\]]*)\];", content)
    if not match:
        return content
    ids = re.findall(r'"([^"]+)"', match.group(1))
    kept = [
        tool_id
        for tool_id in ids
        if indexable.get(f"tools/{tool_id}.html", False)
    ]
    replacement = "var FEATURED = " + json.dumps(kept, separators=(", ", ": ")) + ";"
    return content[: match.start()] + replacement + content[match.end() :]


def git_date(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--format=%cs", "--", str(path.relative_to(ROOT))],
            cwd=ROOT,
            text=True,
        ).strip() or date.today().isoformat()
    except (subprocess.CalledProcessError, ValueError):
        return date.today().isoformat()


def redirect_sources() -> set[str]:
    sources = set()
    vercel = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    for redirect in vercel.get("redirects", []):
        sources.add(redirect["source"].split("?", 1)[0])
    return sources


def build_sitemap(pages: list[tuple[Path, str]], indexable: dict[str, bool]) -> None:
    redirects = redirect_sources()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, content in sorted(pages):
        relative = path.relative_to(ROOT).as_posix()
        if relative in {"404.html", *SKIP_PAGES} or not indexable.get(relative, False):
            continue
        route = page_route(relative)
        if route in redirects:
            continue
        canonical = f"{PUBLIC_HOST}{route}"
        lines.extend(["  <url>", f"    <loc>{canonical}</loc>", f"    <lastmod>{git_date(path)}</lastmod>", "  </url>"])
    lines.append("</urlset>")
    write_utf8(ROOT / "sitemap.xml", "\n".join(lines) + "\n")


def compare_report(indexable: dict[str, bool], sitemap_routes: set[str]) -> list[str]:
    compare_dir = ROOT / "compare"
    files = {path.stem for path in compare_dir.glob("*.html") if path.stem != "index"}
    pairs = []
    for slug in sorted(files):
        if "-vs-" not in slug:
            continue
        left, right = slug.split("-vs-", 1)
        reverse = f"{right}-vs-{left}"
        if reverse not in files or slug > reverse:
            continue
        routes = {f"/compare/{slug}.html", f"/compare/{reverse}.html"}
        canonical = sorted(route for route in routes if route in sitemap_routes)
        pairs.append(
            f"- `{slug}` / `{reverse}`: canonical in sitemap: "
            f"{', '.join(canonical) if len(canonical) == 1 else 'INVALID'}"
        )
    if not pairs:
        return ["- No reverse comparison page pairs are present; existing Vercel redirects were retained and verified."]
    return pairs


def build_index_report(
    metrics: dict[str, object],
    unique: dict[str, set[str]],
    indexable: dict[str, bool],
    allowlist: set[str],
    sitemap_routes: set[str],
) -> None:
    sections = sorted({section_name(Path(path)) for path in metrics})
    lines = [
        "# Indexability report",
        "",
        "Generated by `python3 scripts/build_site.py`.",
        "",
        "A page is indexable when its main content has at least 600 words and it has",
        "at least one marked section whose full text is unique across pages. Paths in",
        "`data/index-allowlist.json` are explicit overrides.",
        f"Current allowlist overrides: {', '.join(sorted(allowlist)) or 'none'}.",
        "",
        "## Counts by section",
        "",
        "| Section | Indexable | Noindex | Total |",
        "| --- | ---: | ---: | ---: |",
    ]
    for section in sections:
        paths = [path for path in metrics if section_name(Path(path)) == section]
        indexed = sum(indexable[path] for path in paths)
        lines.append(f"| `{section}` | {indexed} | {len(paths) - indexed} | {len(paths)} |")
    lines.extend(["", "## Noindex pages", ""])
    for section in sections:
        lines.append(f"### `{section}`")
        paths = sorted(
            path for path in metrics
            if section_name(Path(path)) == section and not indexable[path]
        )
        if not paths:
            lines.append("- None")
        else:
            lines.extend(
                f"- `/{path}` ({metrics[path].words} words; "
                f"{'below 600 words' if metrics[path].words < 600 else 'no unique marked section'})"
                for path in paths
            )
        lines.append("")
    lines.extend(["## Comparison canonicalization", ""])
    lines.extend(compare_report(indexable, sitemap_routes))
    lines.extend(
        [
            "",
            "The sitemap contains only indexable pages and excludes redirect sources.",
            f"Current sitemap URL count: {len(sitemap_routes)}.",
        ]
    )
    write_utf8(ROOT / "docs" / "internal" / "INDEX-REPORT.md", "\n".join(lines) + "\n")


def build_ads(config: dict) -> None:
    ads = ROOT / "ads.txt"
    pub_id = config.get("ADSENSE_PUB_ID", "").strip()
    if pub_id:
        write_utf8(ads, f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n")


def main() -> None:
    strip_boms()
    config = json.loads(SITE_CONFIG.read_text(encoding="utf-8"))
    allowlist = load_allowlist()
    metrics = {}
    for path in sorted(ROOT.rglob("*.html")):
        relative = path.relative_to(ROOT).as_posix()
        if ".git" not in path.parts and relative not in {"404.html", *SKIP_PAGES}:
            content = path.read_text(encoding="utf-8")
            metrics[relative] = measure(content)
    unique = unique_marked_sections(metrics)
    indexable = {
        relative: page_route(relative) in allowlist
        or (item.words >= 600 and bool(unique[relative]))
        for relative, item in metrics.items()
    }
    pages = []
    used_titles: set[str] = set()
    used_descriptions: set[str] = set()
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts or path.relative_to(ROOT).as_posix() in SKIP_PAGES:
            continue
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        parser = parse_page(content)
        title = make_title(parser, path, used_titles)
        description = make_description(parser, path, used_descriptions)
        used_titles.add(title)
        used_descriptions.add(description)
        route = "/" if relative == "index.html" else f"/{relative}"
        url = f"{PUBLIC_HOST}{route}"
        content = ensure_lang(content)
        content = ensure_title(content, title)
        content = add_or_replace_head_meta(content, "description", description)
        content = ensure_canonical(content, url)
        content = ensure_h1(content, parser.h1_text or title)
        content = add_analytics_and_verification(content, config, url, title, description)
        content = normalize_links(content)
        email = html.escape(config.get("CONTACT_EMAIL", "").strip(), quote=True)
        content = content.replace("{{CONTACT_EMAIL}}", email)
        content = add_editorial_strip(content, path, config)
        content = add_footer_trust_links(content)
        content = add_structured_data(content, config, relative, title, description, url)
        if relative in indexable:
            content = set_robots(content, indexable[relative])
        if relative == "index.html":
            content = filter_homepage_featured(content, indexable)
        content = re.sub(r"\n{4,}", "\n\n\n", content)
        write_utf8(path, content)
        pages.append((path, content))
    build_sitemap(pages, indexable)
    sitemap_content = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_routes = set(re.findall(r"<loc>" + re.escape(PUBLIC_HOST) + r"([^<]+)</loc>", sitemap_content))
    build_index_report(metrics, unique, indexable, allowlist, sitemap_routes)
    build_ads(config)
    strip_boms()


if __name__ == "__main__":
    main()
