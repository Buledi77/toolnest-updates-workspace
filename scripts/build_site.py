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

ROOT = Path(__file__).resolve().parents[1]
SITE_CONFIG = ROOT / "data" / "site.json"
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


def build_sitemap(pages: list[tuple[Path, str]]) -> None:
    redirects = redirect_sources()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, content in sorted(pages):
        relative = path.relative_to(ROOT).as_posix()
        if relative in {"404.html", *SKIP_PAGES}:
            continue
        parser = parse_page(content)
        robots = re.search(
            r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']*)',
            content,
            re.IGNORECASE,
        )
        if robots and "noindex" in robots.group(1).lower():
            continue
        route = "/" if relative == "index.html" else "/" + relative
        if route in redirects:
            continue
        canonical = f"{PUBLIC_HOST}{route}"
        lines.extend(["  <url>", f"    <loc>{canonical}</loc>", f"    <lastmod>{git_date(path)}</lastmod>", "  </url>"])
    lines.append("</urlset>")
    write_utf8(ROOT / "sitemap.xml", "\n".join(lines) + "\n")


def build_ads(config: dict) -> None:
    ads = ROOT / "ads.txt"
    pub_id = config.get("ADSENSE_PUB_ID", "").strip()
    if pub_id:
        write_utf8(ads, f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n")


def main() -> None:
    strip_boms()
    config = json.loads(SITE_CONFIG.read_text(encoding="utf-8"))
    pages = []
    used_titles: set[str] = set()
    used_descriptions: set[str] = set()
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts or path.relative_to(ROOT).as_posix() in SKIP_PAGES:
            continue
        content = path.read_text(encoding="utf-8")
        parser = parse_page(content)
        title = make_title(parser, path, used_titles)
        description = make_description(parser, path, used_descriptions)
        used_titles.add(title)
        used_descriptions.add(description)
        relative = path.relative_to(ROOT).as_posix()
        route = "/" if relative == "index.html" else f"/{relative}"
        url = f"{PUBLIC_HOST}{route}"
        content = ensure_lang(content)
        content = ensure_title(content, title)
        content = add_or_replace_head_meta(content, "description", description)
        content = ensure_canonical(content, url)
        content = ensure_h1(content, parser.h1_text or title)
        content = add_analytics_and_verification(content, config, url, title, description)
        content = normalize_links(content)
        write_utf8(path, content)
        pages.append((path, content))
    build_sitemap(pages)
    build_ads(config)
    strip_boms()


if __name__ == "__main__":
    main()
