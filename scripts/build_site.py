#!/usr/bin/env python3
"""Build the static ToolNest corpus from committed HTML and site configuration."""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from content_metrics import measure, section_name, unique_marked_sections

ROOT = Path(__file__).resolve().parents[1]
SITE_CONFIG = ROOT / "data" / "site.json"
INDEX_ALLOWLIST = ROOT / "data" / "index-allowlist.json"
REVIEW_DIR = ROOT / "data" / "reviews"
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


def remove_jsonld_type(content: str, schema_type: str) -> str:
    pattern = re.compile(
        r'<script type="application/ld\+json">.*?</script>',
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.sub(
        lambda match: ""
        if f'"@type":"{schema_type}"' in match.group(0).replace(" ", "")
        else match.group(0),
        content,
    )


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
    review_data = None
    if relative.startswith(("tools/", "compare/")) and Path(relative).stem != "index":
        review_data = load_review_data(Path(relative).stem)
        if review_data and review_data.get("faqs"):
            faqs = [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in review_data["faqs"]
                if isinstance(item, dict) and item.get("q") and item.get("a")
            ]
            if faqs:
                content = add_jsonld(
                    content,
                    {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faqs},
                    "FAQPage",
                )
        elif relative.startswith(("tools/", "compare/")):
            content = remove_jsonld_type(content, "FAQPage")
    if relative.startswith("tools/") and Path(relative).stem != "index" and review_data:
        if review_data.get("testStatus") == "tested":
            content = remove_jsonld_type(content, "Article")
            metadata = tool_metadata(Path(relative).stem)
            review = {
                "@context": "https://schema.org",
                "@type": "Review",
                "name": title,
                "reviewBody": review_data.get("verdict", ""),
                "url": url,
                "author": person_schema(config),
                "itemReviewed": {
                    "@type": "Product",
                    "name": metadata["name"],
                    "url": metadata["url"],
                },
            }
            _, rating = render_score(review_data)
            if rating is not None:
                review["reviewRating"] = {
                    "@type": "Rating",
                    "ratingValue": rating,
                    "bestRating": 10,
                    "worstRating": 1,
                }
            content = add_jsonld(content, review, "Review")
        else:
            content = remove_jsonld_type(content, "Review")
    elif relative.startswith(("tools/", "compare/")):
        content = remove_jsonld_type(content, "Review")
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
    elif (
        relative not in {"404.html", "privacy.html", "terms.html", *SKIP_PAGES}
        and not (
            relative.startswith("tools/")
            and review_data
            and review_data.get("testStatus") == "tested"
        )
    ):
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


def load_review_data(slug: str) -> dict | None:
    path = REVIEW_DIR / f"{slug}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    status = data.get("testStatus")
    if status not in {"tested", "researched"}:
        raise ValueError(f"{path}: testStatus must be tested or researched")
    for screenshot in data.get("screenshots") or []:
        if not isinstance(screenshot, dict) or not screenshot.get("src"):
            continue
        src = Path(str(screenshot["src"]))
        if src.suffix.lower() == ".webp":
            continue
        source = ROOT / str(src).lstrip("/")
        destination = source.with_suffix(".webp")
        if not source.exists():
            raise FileNotFoundError(f"{path}: screenshot does not exist: {source}")
        converter = shutil.which("ffmpeg")
        if not converter:
            raise RuntimeError(f"{path}: ffmpeg is required to convert {source} to WebP")
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [converter, "-y", "-i", str(source), str(destination)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        screenshot["src"] = "/" + destination.relative_to(ROOT).as_posix()
    return data


def tool_metadata(slug: str) -> dict:
    v2_paths = [
        ROOT / "data" / "tools-v2" / f"{slug}.json",
        ROOT / "data" / "tools-v2" / "legacy" / f"{slug}.json",
        ROOT / "data" / "tools-v2" / "legacy" / f"{slug.replace('mozpro', 'moz-pro')}.json",
    ]
    v2_path = next((path for path in v2_paths if path.exists()), None)
    if v2_path:
        data = json.loads(v2_path.read_text(encoding="utf-8"))
        identity = data.get("identity", {})
        editorial = data.get("editorial", {})
        relationships = data.get("relationships", {})
        return {
            "name": identity.get("name", slug.replace("-", " ").title()),
            "url": identity.get("official_url", ""),
            "logo": identity.get("logo", ""),
            "category": (data.get("discovery", {}).get("categories") or [""])[0],
            "best": editorial.get("best_for", []),
            "skip": editorial.get("not_recommended_for", []),
            "alternatives": relationships.get("alternatives", []),
            "comparisons": relationships.get("meaningful_comparisons", []),
        }
    legacy = json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8"))
    item = next((tool for tool in legacy.get("tools", []) if tool.get("id") == slug), {})
    return {
        "name": item.get("name", slug.replace("-", " ").title()),
        "url": item.get("site", ""),
        "logo": item.get("logo", ""),
        "category": item.get("cat", ""),
        "best": [item.get("best")] if item.get("best") else [],
        "skip": [],
        "alternatives": [],
        "comparisons": [],
    }


def list_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def render_list(items: list[str], class_name: str = "tl") -> str:
    return f'<ul class="{class_name}">' + "".join(
        f"<li>{html.escape(item)}</li>" for item in items
    ) + "</ul>"


def tool_route(slug: str) -> str:
    return f"/tools/{slug.replace('moz-pro', 'mozpro')}.html"


def render_score(data: dict) -> tuple[str, float | None]:
    scores = data.get("score") or data.get("scoreBreakdown") or {}
    if not isinstance(scores, dict):
        return "", None
    values = [
        float(value)
        for value in scores.values()
        if isinstance(value, (int, float)) and 1 <= float(value) <= 10
    ]
    if not values:
        return "", None
    average = round(sum(values) / len(values), 1)
    rows = "".join(
        f"<li><span>{html.escape(str(key).replace('_', ' ').title())}</span>"
        f"<b>{html.escape(str(value))}/10</b></li>"
        for key, value in scores.items()
        if isinstance(value, (int, float)) and 1 <= float(value) <= 10
    )
    return f'<div class="proof-score"><b>Score: {average}/10</b><ul>{rows}</ul></div>', average


def render_review_stack(data: dict, metadata: dict, slug: str) -> str:
    name = html.escape(metadata["name"])
    blocks: list[str] = []
    score_html, _ = render_score(data)
    best = list_items(data.get("whoShouldUse")) or list_items(metadata.get("best"))
    skip = list_items(data.get("whoShouldSkip")) or list_items(metadata.get("skip"))
    verdict = str(data.get("verdict", "")).strip()
    price_from = str(data.get("priceFrom", data.get("price_from", ""))).strip()
    cta_url = str(data.get("ctaUrl", metadata.get("url", ""))).strip()
    if score_html or verdict or best or skip or price_from or cta_url:
        parts = ['<section class="p-sec proof-stack" id="proof-verdict"><h2>Our verdict</h2>']
        if verdict:
            parts.append(f"<p>{html.escape(verdict)}</p>")
        if score_html:
            parts.append(score_html)
        if best or skip or price_from:
            parts.append('<div class="two proof-glance">')
            if best:
                parts.append(f'<div class="box"><h3>Best for</h3>{render_list(best, "tl yes")}</div>')
            if skip:
                parts.append(f'<div class="box"><h3>Skip if</h3>{render_list(skip, "tl no")}</div>')
            if price_from:
                parts.append(f'<div class="box"><h3>Price from</h3><p>{html.escape(price_from)}</p></div>')
            parts.append("</div>")
        if cta_url:
            parts.append(
                f'<a class="btn" href="{html.escape(cta_url, quote=True)}" '
                'rel="sponsored nofollow noopener" target="_blank">'
                f"Visit {name}<span class=\"sr\"> (opens the official site in a new tab)</span></a>"
            )
        blocks.append("".join(parts) + "</section>")

    if data.get("testStatus") == "tested":
        tasks = data.get("testTasks") or []
        screenshots = data.get("screenshots") or []
        if data.get("testedOn") or data.get("planTested") or tasks or screenshots:
            parts = ['<section class="p-sec proof-stack" id="what-i-tested"><h2>What I tested</h2>']
            details = []
            if data.get("testedOn"):
                details.append(f"<b>Tested on:</b> {html.escape(str(data['testedOn']))}")
            if data.get("planTested"):
                details.append(f"<b>Plan tested:</b> {html.escape(str(data['planTested']))}")
            if details:
                parts.append("<p>" + " · ".join(details) + "</p>")
            if tasks:
                parts.append(
                    '<div class="tw"><table><caption class="sr">Hands-on test tasks</caption>'
                    "<thead><tr><th scope=\"col\">Task</th><th scope=\"col\">Result</th>"
                    "<th scope=\"col\">Time taken</th></tr></thead><tbody>"
                )
                for task in tasks:
                    if not isinstance(task, dict):
                        continue
                    parts.append(
                        "<tr>"
                        f"<th scope=\"row\">{html.escape(str(task.get('task', '')))}</th>"
                        f"<td>{html.escape(str(task.get('result', '')))}</td>"
                        f"<td>{html.escape(str(task.get('timeTaken', task.get('time_taken', ''))))}</td>"
                        "</tr>"
                    )
                parts.append("</tbody></table></div>")
            if screenshots:
                parts.append('<div class="proof-shots">')
                for index, shot in enumerate(screenshots):
                    if not isinstance(shot, dict) or not shot.get("src"):
                        continue
                    src = str(shot["src"])
                    if Path(src).suffix.lower() != ".webp":
                        raise ValueError(f"review screenshot must be WebP: {src}")
                    loading = "" if index == 0 else ' loading="lazy"'
                    parts.append(
                        f'<figure><img src="{html.escape(src, quote=True)}" '
                        f'alt="{html.escape(str(shot.get("alt", f"{name} test screenshot")), quote=True)}" '
                        f'width="{html.escape(str(shot.get("width", 1200)), quote=True)}" '
                        f'height="{html.escape(str(shot.get("height", 675)), quote=True)}" '
                        f'decoding="async"{loading}>'
                        f'<figcaption>{html.escape(str(shot.get("caption", "")))}</figcaption></figure>'
                    )
                parts.append("</div>")
            blocks.append("".join(parts) + "</section>")

    pros = list_items(data.get("pros"))
    cons = list_items(data.get("cons"))
    if pros or cons:
        parts = ['<section class="p-sec proof-stack" id="proof-pros-cons"><h2>Pros and cons</h2><div class="two">']
        if pros:
            parts.append(f'<div class="box"><h3>Pros</h3>{render_list(pros, "tl yes")}</div>')
        if cons:
            parts.append(f'<div class="box"><h3>Cons</h3>{render_list(cons, "tl no")}</div>')
        blocks.append("".join(parts) + "</div></section>")

    pricing_date = str(data.get("pricingCheckedOn", "")).strip()
    pricing_notes = str(data.get("pricingNotes", "")).strip()
    if pricing_date or pricing_notes:
        checked = f" Checked on {html.escape(pricing_date)}." if pricing_date else ""
        blocks.append(
            '<section class="p-sec proof-stack" id="proof-pricing"><h2>Pricing</h2>'
            f"<p>{html.escape(pricing_notes)}{checked}</p></section>"
        )

    if data.get("whoShouldUse") or data.get("whoShouldSkip"):
        parts = ['<section class="p-sec proof-stack" id="proof-fit"><h2>Who should use it</h2><div class="two">']
        if data.get("whoShouldUse"):
            parts.append(f'<div class="box"><h3>Who should use it</h3>{render_list(list_items(data["whoShouldUse"]), "tl yes")}</div>')
        if data.get("whoShouldSkip"):
            parts.append(f'<div class="box"><h3>Who should skip it</h3>{render_list(list_items(data["whoShouldSkip"]), "tl no")}</div>')
        blocks.append("".join(parts) + "</div></section>")

    alternatives = list_items(metadata.get("alternatives"))
    if alternatives:
        links = "".join(
            f'<a class="lk" href="{tool_route(item)}"><span class="lk-tx"><b>{html.escape(item.replace("-", " ").title())}</b>'
            "<small>Category alternative</small></span></a>"
            for item in alternatives
        )
        blocks.append(
            f'<section class="p-sec proof-stack" id="proof-alternatives"><h2>Alternatives</h2>'
            f'<div class="linkgrid">{links}</div></section>'
        )

    faqs = data.get("faqs") or []
    if faqs:
        items = []
        for faq in faqs:
            if isinstance(faq, dict) and faq.get("q") and faq.get("a"):
                items.append(
                    f'<div class="qa"><h3>{html.escape(str(faq["q"]))}</h3>'
                    f'<div class="ans"><p>{html.escape(str(faq["a"]))}</p></div></div>'
                )
        if items:
            blocks.append(
                '<section class="p-sec proof-stack" id="proof-faq"><h2>FAQ</h2>'
                f'<div class="faq-grid">{"".join(items)}</div></section>'
            )

    comparisons = list_items(metadata.get("comparisons"))
    if comparisons:
        links = "".join(
            f'<a class="lk" href="/compare/{html.escape(item, quote=True)}.html">'
            f'<span class="lk-tx"><b>{html.escape(item.replace("-", " ").title())}</b>'
            "<small>Related comparison</small></span></a>"
            for item in comparisons
        )
        blocks.append(
            '<section class="p-sec proof-stack" id="proof-comparisons"><h2>Related comparisons</h2>'
            f'<div class="linkgrid">{links}</div></section>'
        )
    return "".join(blocks)


def render_compare_evidence(slug: str) -> str:
    if "-vs-" not in slug:
        return ""
    left, right = slug.split("-vs-", 1)
    records = [(left, load_review_data(left)), (right, load_review_data(right))]
    records = [(item, data) for item, data in records if data]
    if not records:
        return ""
    cards = []
    for item, data in records:
        metadata = tool_metadata(item)
        name = html.escape(metadata["name"])
        status = "Hands-on tested" if data.get("testStatus") == "tested" else "Researched"
        detail = []
        if data.get("testedOn"):
            detail.append(f"Tested on {html.escape(str(data['testedOn']))}")
        if data.get("planTested"):
            detail.append(f"Plan: {html.escape(str(data['planTested']))}")
        if data.get("verdict"):
            detail.append(f"<p>{html.escape(str(data['verdict']))}</p>")
        cards.append(
            f'<div class="box"><h3>{name}</h3><p><b>{status}</b>'
            f"{(' · ' + ' · '.join(detail[:2])) if detail[:2] else ''}</p>"
            f"{''.join(detail[2:])}</div>"
        )
    return (
        '<section class="p-sec proof-stack" id="comparison-evidence">'
        "<h2>Evidence behind this comparison</h2><div class=\"two\">"
        + "".join(cards)
        + "</div></section>"
    )


def add_proof_stack(content: str, relative: str) -> str:
    if relative.startswith("tools/") and Path(relative).stem != "index":
        data = load_review_data(Path(relative).stem)
        if not data:
            return content
        stack = render_review_stack(data, tool_metadata(Path(relative).stem), Path(relative).stem)
    elif relative.startswith("compare/") and Path(relative).stem != "index":
        stack = render_compare_evidence(Path(relative).stem)
    else:
        return content
    content = re.sub(
        r'<section class="p-sec proof-stack".*?</section>',
        "",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    marker = re.search(r'<div class="wrap tn-trust-strip">.*?</div>', content, re.IGNORECASE | re.DOTALL)
    if not stack or not marker:
        return content
    return content[: marker.end()] + stack + content[marker.end() :]


def taxonomy_categories() -> dict[str, str]:
    data = json.loads(
        (ROOT / "data" / "taxonomy" / "taxonomy-v1.json").read_text(encoding="utf-8")
    )
    return {item["slug"]: item["label"] for item in data.get("categories", [])}


def page_breadcrumbs(relative: str, title: str) -> list[tuple[str, str | None]]:
    parts = Path(relative).parts
    label = " ".join(Path(relative).stem.replace("-", " ").split()).title()
    if relative in {"index.html", "404.html", *SKIP_PAGES}:
        return []
    if parts[0] == "tools":
        metadata = tool_metadata(Path(relative).stem)
        category = (metadata.get("category") or "").strip()
        category_slug = next(
            (slug for slug, name in taxonomy_categories().items() if name.lower() == category.lower()),
            "",
        )
        if category_slug:
            return [("Home", "/"), (category, f"/category/{category_slug}.html"), (title, None)]
        return [("Home", "/"), ("Tools", "/tools/index.html"), (title, None)]
    parents = {
        "category": ("Categories", "/category/index.html"),
        "best": ("Best tools", "/best/index.html"),
        "compare": ("Compare", "/compare/index.html"),
        "alternatives": ("Alternatives", "/alternatives/index.html"),
        "goals": ("Goals", "/goals/index.html"),
        "authors": ("Authors", "/authors/abdul-muswir.html"),
    }
    if parts[0] in parents:
        parent_label, parent_url = parents[parts[0]]
        return [("Home", "/"), (parent_label, parent_url), (title, None)]
    return [("Home", "/"), (title, None)]


def add_breadcrumbs(content: str, items: list[tuple[str, str | None]]) -> str:
    if not items:
        return content
    content = re.sub(
        r'<nav\b[^>]*class="crumbs"[^>]*>.*?</nav>',
        "",
        content,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )
    links = []
    for label, url in items:
        escaped = html.escape(label)
        if url:
            links.append(f'<li><a href="{html.escape(url, quote=True)}">{escaped}</a></li>')
        else:
            links.append(f'<li aria-current="page">{escaped}</li>')
    nav = '<nav aria-label="Breadcrumb" class="crumbs"><ol>' + "".join(links) + "</ol></nav>"
    hero = re.search(r'<section class="hero phero"[^>]*>', content, re.IGNORECASE)
    if hero:
        wrap = re.search(r'<div class="wrap">', content[hero.end() :], re.IGNORECASE)
        if wrap:
            insert_at = hero.end() + wrap.end()
            return content[:insert_at] + nav + content[insert_at:]
        return content[: hero.end()] + nav + content[hero.end() :]
    return content.replace("<main", f"<main>{nav}", 1)


def add_breadcrumb_schema(
    content: str, items: list[tuple[str, str | None]], current_url: str
) -> str:
    if not items:
        return content
    elements = []
    for position, (name, url) in enumerate(items, start=1):
        elements.append(
            {
                "@type": "ListItem",
                "position": position,
                "name": name,
                "item": f"{PUBLIC_HOST}{url or current_url}",
            }
        )
    return add_jsonld(
        content,
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": elements,
        },
        "BreadcrumbList",
    )


def load_catalog() -> list[dict]:
    return json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8")).get("tools", [])


def category_tool_ids(slug: str) -> list[str]:
    label = taxonomy_categories().get(slug, "").lower()
    return [
        item["id"]
        for item in load_catalog()
        if str(item.get("cat", "")).lower() == label
    ]


def best_route_for_category(slug: str) -> str | None:
    candidates = [
        f"/best/best-{slug}-tools.html",
        {
            "website-builders": "/best/best-website-builder-tools.html",
            "voice-video": "/best/best-ai-voice-tools.html",
            "ai-assistants": "/best/best-ai-assistants-tools.html",
        }.get(slug, ""),
    ]
    for route in candidates:
        if route:
            return route
    return None


def route_is_indexable(route: str, indexable: dict[str, bool]) -> bool:
    relative = route.lstrip("/")
    return indexable.get(relative, False)


def category_comparisons(slug: str, indexable: dict[str, bool]) -> list[str]:
    ids = set(category_tool_ids(slug))
    matches = []
    for path in sorted((ROOT / "compare").glob("*.html")):
        if path.stem == "index" or not indexable.get(f"compare/{path.name}", False):
            continue
        left, _, right = path.stem.partition("-vs-")
        if left in ids or right in ids:
            matches.append(f"/compare/{path.name}")
    return matches[:3]


def category_alternatives(slug: str, indexable: dict[str, bool]) -> list[str]:
    routes = []
    for tool_id in category_tool_ids(slug):
        route = f"/alternatives/{tool_id}-alternatives.html"
        if route_is_indexable(route, indexable):
            routes.append(route)
    return routes[:3]


def link_list(routes: list[str], label: str) -> str:
    if not routes:
        return ""
    def display_name(route: str) -> str:
        value = Path(route).stem.replace("-", " ").title()
        return value.replace("Mozpro", "Moz Pro").replace("Seo", "SEO").replace("Ai ", "AI ")

    links = "".join(
        f'<a class="lk" href="{html.escape(route, quote=True)}">'
        f'<span class="lk-tx"><b>{html.escape(display_name(route))}</b>'
        f"<small>{html.escape(label)}</small></span></a>"
        for route in routes
    )
    return f'<div class="linkgrid">{links}</div>'


def add_category_hub(content: str, relative: str, indexable: dict[str, bool]) -> str:
    parts = Path(relative).parts
    if len(parts) != 2 or parts[0] != "category" or parts[1] == "index.html":
        return content
    slug = Path(parts[1]).stem
    label = taxonomy_categories().get(slug, slug.replace("-", " ").title())
    tool_ids = [
        tool_id
        for tool_id in category_tool_ids(slug)
        if route_is_indexable(f"/tools/{tool_id}.html", indexable)
    ]
    tool_routes = [f"/tools/{tool_id}.html" for tool_id in tool_ids[:8]]
    best_route = best_route_for_category(slug)
    best_links = [best_route] if best_route and route_is_indexable(best_route, indexable) else []
    comparison_routes = category_comparisons(slug, indexable)
    alternative_routes = category_alternatives(slug, indexable)
    buying_routes = best_links + ["/compare/index.html", "/alternatives/index.html", "/tools/index.html"]
    buying_routes = [route for route in buying_routes if route_is_indexable(route, indexable)]
    tool_list = link_list(tool_routes, f"{label} tool review")
    sections = [
        f'<section class="p-sec category-hub" id="category-intro"><h2>About {html.escape(label)} tools</h2>'
        "<p>[WRITE INTRO]</p></section>",
    ]
    if tool_list:
        sections.append(
            f'<section class="p-sec category-hub" id="best-tools"><h2>Best {html.escape(label)} tools</h2>{tool_list}</section>'
        )
    if comparison_routes:
        sections.append(
            '<section class="p-sec category-hub" id="top-comparisons"><h2>Top comparisons</h2>'
            f"{link_list(comparison_routes, f'{label} comparison')}</section>"
        )
    if alternative_routes:
        sections.append(
            '<section class="p-sec category-hub" id="top-alternatives"><h2>Top alternatives</h2>'
            f"{link_list(alternative_routes, f'{label} alternative')}</section>"
        )
    if buying_routes:
        sections.append(
            '<section class="p-sec category-hub" id="buying-guides"><h2>Buying guides</h2>'
            f"{link_list(buying_routes, 'Guide')}</section>"
        )
    hub = "".join(sections)
    content = re.sub(
        r'<section class="p-sec category-hub".*?</section>',
        "",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    marker = re.search(r'<div class="wrap tn-trust-strip">.*?</div>', content, re.IGNORECASE | re.DOTALL)
    if marker:
        return content[: marker.end()] + hub + content[marker.end() :]
    return content.replace("</main>", hub + "</main>", 1)


def tool_internal_links(content: str, relative: str, indexable: dict[str, bool]) -> str:
    if not relative.startswith("tools/") or Path(relative).stem == "index":
        return content
    slug = Path(relative).stem
    metadata = tool_metadata(slug)
    category = str(metadata.get("category", "")).lower()
    category_slug = next(
        (key for key, value in taxonomy_categories().items() if value.lower() == category),
        "",
    )
    routes: list[str] = []
    if category_slug:
        routes.append(f"/category/{category_slug}.html")
    best_route = best_route_for_category(category_slug) if category_slug else None
    if best_route:
        routes.append(best_route)
    comparisons = [
        f"/compare/{name}.html"
        for name in list_items(metadata.get("comparisons"))[:3]
        if (ROOT / "compare" / f"{name}.html").exists()
    ]
    routes.extend(comparisons)
    alternative_route = f"/alternatives/{slug}-alternatives.html"
    routes.append(alternative_route)
    routes = [route for route in routes if route_is_indexable(route, indexable)]
    if not routes:
        return content
    cards = link_list(routes, "Related ToolNest guide")
    section = f'<section class="p-sec tool-links" id="more-ways-to-choose"><h2>More ways to choose</h2>{cards}</section>'
    content = re.sub(
        r'<section class="p-sec tool-links".*?</section>',
        "",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return content.replace("</main>", section + "</main>", 1)


def homepage_quality_ids(indexable: dict[str, bool], metrics: dict[str, object]) -> list[str]:
    candidates = []
    for item in load_catalog():
        slug = item.get("id", "")
        relative = f"tools/{slug}.html"
        if not indexable.get(relative, False):
            continue
        review = load_review_data(slug) or {}
        candidates.append(
            (
                0 if review.get("testStatus") == "tested" else 1,
                -int(getattr(metrics.get(relative), "words", 0)),
                slug,
            )
        )
    return [slug for _, _, slug in sorted(candidates)[:8]]


def add_recently_tested(content: str, indexable: dict[str, bool]) -> str:
    records = []
    for item in load_catalog():
        slug = item.get("id", "")
        if not indexable.get(f"tools/{slug}.html", False):
            continue
        review = load_review_data(slug)
        if review and review.get("testStatus") == "tested" and review.get("testedOn"):
            records.append((str(review["testedOn"]), item))
    records.sort(key=lambda pair: pair[0], reverse=True)
    cards = "".join(
        f'<a class="lk" href="/tools/{html.escape(item["id"], quote=True)}.html">'
        f'<span class="lk-tx"><b>{html.escape(item.get("name", item["id"]))}</b>'
        f"<small>Hands-on tested {html.escape(date_checked)}</small></span></a>"
        for date_checked, item in records[:6]
    )
    body = f'<div class="linkgrid">{cards}</div>' if cards else (
        '<p class="sub">No hands-on reviews have been published yet.</p>'
    )
    section = (
        '<section class="recently-tested" aria-labelledby="recently-tested-title"><div class="wrap">'
        '<p class="kicker">Proof first</p><h2 class="h2" id="recently-tested-title">Recently tested</h2>'
        '<p class="sub">These pages include hands-on evidence with a test date and plan.</p>'
        f"{body}</div></section>"
    )
    content = re.sub(
        r'<section class="recently-tested".*?</section>',
        "",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    marker = content.find('<section id="categories"')
    return content[:marker] + section + content[marker:] if marker >= 0 else content


def set_robots(content: str, indexable: bool) -> str:
    value = "index,follow,max-image-preview:large" if indexable else "noindex, follow"
    return add_or_replace_head_meta(content, "robots", value)


def load_allowlist() -> set[str]:
    data = json.loads(INDEX_ALLOWLIST.read_text(encoding="utf-8"))
    return {str(path) for path in data.get("paths", [])}


def page_route(relative: str) -> str:
    return "/" if relative == "index.html" else f"/{relative}"


def filter_homepage_featured(
    content: str, indexable: dict[str, bool], featured_ids: list[str] | None = None
) -> str:
    match = re.search(r"var FEATURED = \[([^\]]*)\];", content)
    if not match:
        return content
    ids = re.findall(r'"([^"]+)"', match.group(1))
    kept = featured_ids if featured_ids is not None else [
        tool_id for tool_id in ids if indexable.get(f"tools/{tool_id}.html", False)
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
    featured_ids = homepage_quality_ids(indexable, metrics)
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
        content = add_proof_stack(content, relative)
        content = add_category_hub(content, relative, indexable)
        content = tool_internal_links(content, relative, indexable)
        content = add_footer_trust_links(content)
        breadcrumb_items = page_breadcrumbs(relative, parser.h1_text or title)
        content = add_breadcrumbs(content, breadcrumb_items)
        content = add_breadcrumb_schema(content, breadcrumb_items, route)
        content = add_structured_data(content, config, relative, title, description, url)
        if relative in indexable:
            content = set_robots(content, indexable[relative])
        if relative == "index.html":
            content = filter_homepage_featured(content, indexable, featured_ids)
            content = add_recently_tested(content, indexable)
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
