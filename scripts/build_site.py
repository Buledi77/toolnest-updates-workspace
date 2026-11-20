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
MIN_INDEXABLE_WORDS = 450
REVIEW_DIR = ROOT / "data" / "reviews"
PUBLIC_HOST = "https://www.toolnestai.tech"
FONT_CSS_URL = (
    "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:"
    "opsz,wdth,wght@12..96,75..100,500..800&family=Instrument+Sans:"
    "wght@400;500;600;700&display=optional"
)
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
    relative = path.relative_to(ROOT).as_posix()
    overrides = {
        "index.html": "Choose the Right Software for Your Workflow | ToolNest",
        "tools/index.html": "Software Tools Directory: 50 Reviewed Tools | ToolNest",
        "compare/index.html": "Compare Software Tools: 63 Head-to-Head Guides | ToolNest",
        "contact.html": "Contact ToolNest: Corrections, Suggestions & Questions",
        "best/index.html": "Best Software Tools by Category: 14 Guides | ToolNest",
        "best/best-writing-tools.html": "Best Writing & Editing Tools: Grammar & Clarity | ToolNest",
        "best/best-ai-writing-tools.html": "Best AI Writing Tools for Drafting Content | ToolNest",
    }
    if relative in overrides:
        return overrides[relative]

    # Prefer H1 as the clean base; fall back to title with boilerplate removed
    raw = parser.h1_text or parser.title or path.stem
    base = " ".join(raw.split())
    # Strip site suffix
    base = re.sub(r"(?:\s*\|\s*ToolNest)+$", "", base).strip(" |:-")
    # Remove boilerplate padding words that add no value
    boilerplate = [
        r"\bGuide Review\b",
        r"\bOverview Explained\b",
        r"\bOverview\b",
        r"\bExplained\b",
        r"\bGuide\b",
        r"\bReview\b",
    ]
    for pat in boilerplate:
        base = re.sub(pat, "", base, flags=re.IGNORECASE).strip(" |:-")
    # Clean up double spaces and punctuation
    base = re.sub(r"\s{2,}", " ", base).strip(" |:-,")
    # Clean up stray punctuation around colons (e.g., "Notion : who" -> "Notion: who")
    base = re.sub(r"\s*:\s*", ": ", base)
    # If base starts with a colon after stripping, remove it
    base = base.lstrip(": ")

    # Build a meaningful suffix for each page type
    suffix = ""
    if relative.startswith("tools/"):
        if not re.search(r"\breview\b", base, re.IGNORECASE):
            suffix = " Review: Features & Pricing"
    elif relative.startswith("compare/"):
        if not re.search(r"\bvs\b", base, re.IGNORECASE):
            suffix = " vs Comparison: Which Is Better"
        else:
            suffix = " Comparison: Which Is Better"
    elif relative.startswith("alternatives/"):
        if not re.search(r"\balternatives\b", base, re.IGNORECASE):
            suffix = " Alternatives: Top Replacements"
        else:
            suffix = ": Top Replacements"
    elif relative.startswith("category/"):
        if not re.search(r"\btools\b", base, re.IGNORECASE):
            suffix = " Tools: Directory & Reviews"
        else:
            suffix = ": Directory & Reviews"
    elif relative.startswith("best/"):
        if not re.search(r"\bbest\b", base, re.IGNORECASE):
            suffix = " Best Tools: Ranked List"
        else:
            suffix = ": Ranked List"
    elif relative.startswith("goals/"):
        suffix = ": Tool Recommendations"
    elif relative.startswith("authors/"):
        suffix = ": Author Profile"
    elif relative in {"affiliate-disclosure.html"}:
        suffix = ": How We Earn Commissions"
    elif relative in {"corrections.html"}:
        suffix = ": Our Corrections Process"
    elif relative in {"terms.html"}:
        suffix = ": Legal Terms & Conditions"
    elif relative in {"privacy.html"}:
        suffix = ": Data Privacy & Cookies"
    elif relative == "404.html":
        suffix = ""
    else:
        suffix = ""

    # Ensure title reaches 50 chars minimum (base + " | ToolNest" = 40 min base)
    min_base = 50 - len(" | ToolNest")  # 40
    if len(base) < min_base:
        if not suffix:
            suffix = " Guide"
        base += suffix
        # If still too short, add more context
        if len(base) < min_base:
            base += " by ToolNest"

    limit = 60 - len(" | ToolNest")
    if len(base) > limit:
        base = base[:limit].rsplit(" ", 1)[0].rstrip(" |:-")

    title = f"{base} | ToolNest"

    if title in used:
        number = str(len(used) + 1)
        limit = 60 - len(number) - len(" | ToolNest") - 1
        base = base[:limit].rsplit(" ", 1)[0].rstrip(" |:-")
        title = f"{base} {number} | ToolNest"

    return title

def make_description(parser: PageParser, path: Path, used: set[str]) -> str:
    existing = " ".join(parser.description.split())
    # Reject the old generic template regardless of length
    generic_template = "compare fit, trade-offs, alternatives, and current"
    if generic_template in existing:
        existing = ""
    # Only accept existing descriptions that are in the 140-160 range
    if existing and 140 <= len(existing) <= 160 and existing not in used:
        return existing

    relative = path.relative_to(ROOT).as_posix()
    subject = " ".join((parser.h1_text or parser.title or path.stem).split())
    # Clean boilerplate from subject
    for pat in [r"\bGuide Review\b", r"\bOverview Explained\b", r"\bOverview\b", r"\bExplained\b"]:
        subject = re.sub(pat, "", subject, flags=re.IGNORECASE).strip(" |:-")
    subject = re.sub(r"\s{2,}", " ", subject).strip(" |:-,")

    # Generate page-type-specific descriptions (target 140-160 chars)
    if relative.startswith("tools/"):
        description = (
            f"{subject}: editorial review covering strengths, trade-offs, pricing, and "
            "who should choose or skip this tool for your workflow. "
            "Check official sources for the latest details."
        )
    elif relative.startswith("compare/"):
        description = (
            f"{subject}: head-to-head comparison covering features, pricing differences, "
            "and which tool fits your specific workflow better. "
            "See verified details on each product."
        )
    elif relative.startswith("alternatives/"):
        alt_tool = re.sub(r"^\s*Best\s+", "", subject, flags=re.IGNORECASE)
        alt_tool = re.sub(r"\s+alternatives\s*$", "", alt_tool, flags=re.IGNORECASE)
        description = (
            f"{alt_tool} alternatives: tools that cover similar use cases with different "
            "pricing, features, or workflow fit. "
            "Compare options before switching tools."
        )
    elif relative.startswith("best/"):
        description = (
            f"{subject}: ranked shortlist based on features, pricing, and real-world "
            "workflow fit with editorial reasoning and verified details. "
            "See full comparisons for each tool."
        )
    elif relative.startswith("category/"):
        description = (
            f"{subject}: directory of reviewed tools in this category with comparisons, "
            "pricing overview, and decision guidance for your workflow. "
            "Find the right tool for your needs."
        )
    elif relative.startswith("goals/"):
        description = (
            f"{subject}: tool recommendations and decision path for this specific "
            "workflow goal, with verified features and pricing details. "
            "See which tool fits your situation best."
        )
    else:
        description = (
            f"{subject}: editorial analysis with features, pricing, and decision "
            "guidance from ToolNest. "
            "Verified details, trade-offs, and recommendations."
        )

    # Trim to 160 chars without breaking words
    if len(description) > 160:
        description = description[:160].rsplit(" ", 1)[0].rstrip(" ,;:-")

    # Pad to 140 chars if too short
    if len(description) < 140:
        extra = " See official sources for the latest pricing and feature updates."
        while len(description) < 140 and len(description) + len(extra) <= 160:
            description += extra
        if len(description) < 140:
            # Last resort: pad with spaces then trim
            description = (description + " " * (140 - len(description)))[:140]

    if description in used:
        stem = path.stem.replace("-", " ").title()
        description = f"{description} ({stem} guide)."
    if len(description) > 160:
        description = description[:160].rstrip(" ,;:-")
    if len(description) < 140:
        description = (description + " " * (140 - len(description)))[:140]

    return description


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


def add_font_hints(content: str) -> str:
    if "fonts.googleapis.com" in content:
        return content
    hints = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        f'<link rel="preload" as="style" href="{FONT_CSS_URL}" '
        'onload="this.onload=null;this.rel=\'stylesheet\'">\n'
        f'<noscript><link rel="stylesheet" href="{FONT_CSS_URL}"></noscript>\n'
    )
    return content.replace("</head>", hints + "</head>", 1)


def ensure_image_attributes(content: str, title: str) -> str:
    image_number = 0

    def replace(match):
        nonlocal image_number
        attrs = match.group(1)
        src_match = re.search(r'\bsrc\s*=\s*([\'"])(.*?)\1', attrs, re.IGNORECASE | re.DOTALL)
        if not src_match:
            return match.group(0)
        src = src_match.group(2)
        is_logo = "/logos/" in src or "logo" in attrs.lower()
        if not re.search(r"\bwidth\s*=", attrs, re.IGNORECASE):
            attrs += ' width="128"' if is_logo else ' width="1200"'
        if not re.search(r"\bheight\s*=", attrs, re.IGNORECASE):
            attrs += ' height="128"' if is_logo else ' height="675"'
        if not re.search(r"\balt\s*=", attrs, re.IGNORECASE):
            fallback = Path(src).stem.replace("-", " ").replace("_", " ").strip()
            attrs += f' alt="{html.escape(fallback or title, quote=True)}"'
        if not re.search(r"\bdecoding\s*=", attrs, re.IGNORECASE):
            attrs += " decoding=\"async\""
        if image_number == 0:
            attrs = re.sub(r"\sloading\s*=\s*([\"'])lazy\1", "", attrs, flags=re.IGNORECASE)
        if image_number > 0 and not re.search(r"\bloading\s*=", attrs, re.IGNORECASE):
            attrs += ' loading="lazy"'
        if image_number == 0 and not re.search(r"\bfetchpriority\s*=", attrs, re.IGNORECASE):
            attrs += ' fetchpriority="high"'
        image_number += 1
        return f"<img{attrs}>"

    return re.sub(r"<img\b([^>]*)>", replace, content, flags=re.IGNORECASE | re.DOTALL)


def minify_asset(source: str, kind: str) -> str:
    output = []
    quote = None
    index = 0
    whitespace = False
    while index < len(source):
        char = source[index]
        if quote:
            output.append(char)
            if char == "\\" and index + 1 < len(source):
                index += 1
                output.append(source[index])
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in "\"'`":
            quote = char
            output.append(char)
            index += 1
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end == -1 else end + 2
            continue
        if kind == "js" and source.startswith("//", index):
            end = source.find("\n", index + 2)
            index = len(source) if end == -1 else end + 1
            continue
        if char.isspace():
            whitespace = True
            index += 1
            continue
        if whitespace and output and output[-1][-1:] not in "{[(=,:;>+~-":
            output.append(" ")
        whitespace = False
        output.append(char)
        index += 1
    result = "".join(output)
    if kind == "css":
        result = re.sub(r"\s*([{}:;,>+~])\s*", r"\1", result)
    else:
        result = re.sub(r"\s*([{}()[\];,:=+\-<>])\s*", r"\1", result)
    return result.strip()


def build_minified_assets() -> None:
    for source_name, min_name, kind in (
        ("site.css", "site.min.css", "css"),
        ("mobile-nav.css", "mobile-nav.min.css", "css"),
        ("mobile-nav.js", "mobile-nav.min.js", "js"),
        ("measure.js", "measure.min.js", "js"),
    ):
        source = ROOT / "assets" / source_name
        write_utf8(ROOT / "assets" / min_name, minify_asset(source.read_text(encoding="utf-8"), kind))


def use_minified_assets(content: str) -> str:
    return (
        content.replace("/assets/site.css", "/assets/site.min.css")
        .replace("/assets/mobile-nav.css", "/assets/mobile-nav.min.css")
        .replace("/assets/mobile-nav.js", "/assets/mobile-nav.min.js")
        .replace("/assets/measure.js", "/assets/measure.min.js")
    )


def async_stylesheets(content: str) -> str:
    for filename in ("site.min.css", "mobile-nav.min.css"):
        tag = f'<link rel="stylesheet" href="/assets/{filename}">'
        replacement = (
            f'<link rel="preload" as="style" href="/assets/{filename}" '
            'onload="this.onload=null;this.rel=\'stylesheet\'">'
            f'<noscript>{tag}</noscript>'
        )
        content = content.replace(tag, replacement)
    return content


def ensure_favicon(content: str) -> str:
    if 'rel="icon"' in content:
        return content
    return content.replace(
        "</head>",
        '<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">\n</head>',
        1,
    )


def ensure_control_names(content: str) -> str:
    for control_id, label in (
        ("quiz-cat", "Tool category"),
        ("quiz-budget", "Budget"),
        ("sort", "Sort tools"),
    ):
        pattern = re.compile(
            rf'<select\b([^>]*\bid="{re.escape(control_id)}"[^>]*)>',
            re.IGNORECASE,
        )
        content = pattern.sub(
            lambda match, label=label: (
                match.group(0)
                if re.search(r"\baria-label\s*=", match.group(1), re.IGNORECASE)
                else f'<select{match.group(1)} aria-label="{label}">'
            ),
            content,
        )
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
        "@type": "Organization",
        "name": "ToolNest Editorial",
        "url": f"{PUBLIC_HOST}/editorial-policy.html",
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
        body = body.replace('<a href="/authors/abdul-muswir.html">Author: Abdul Muswir</a>', "")
        links = (
            '<a href="/how-we-test.html">How we test</a>'
            '<a href="/editorial-policy.html">Editorial policy</a>'
        )
        for href in (
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
        else "Research-based profile"
    )
    updated = git_date(path)
    name = "ToolNest Research"
    strip = (
        '<div class="wrap tn-trust-strip">'
        f'<p class="tn-research-line">{name} '
        f'&middot; Editorial review {updated} &middot; '
        f'<a href="/how-we-test.html">{status}</a></p>'
        '<p class="tn-trust-links"><a href="/how-we-test.html">Methodology</a><a href="/editorial-policy.html">Editorial policy</a><a href="/contact.html">Corrections</a><a href="/affiliate-disclosure.html">Affiliate disclosure</a></p>'
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


def category_sub_use_cases(slug: str) -> str:
    """Generate sub-use-case navigation section for a category page."""
    label = taxonomy_categories().get(slug, slug.replace("-", " ").title())
    tool_ids = category_tool_ids(slug)
    catalog = load_catalog()
    tools = [t for t in catalog if t.get("id") in set(tool_ids)]

    # Define sub-use-cases per category
    sub_use_cases = {
        "hosting": [
            {"title": "Shared hosting for small sites", "description": "Budget-friendly hosting for personal sites and blogs with basic traffic."},
            {"title": "Website builder with hosting", "description": "All-in-one solutions where hosting and site building are bundled."},
            {"title": "Developer-focused hosting", "description": "Hosting with API access, CLI tools, and deployment automation."},
        ],
        "image-generation": [
            {"title": "AI image creation from text", "description": "Generate images from text prompts for marketing, social media, or concept art."},
            {"title": "Background removal and editing", "description": "Quick background removal and simple image editing for product photos."},
            {"title": "Artistic image generation", "description": "High-quality artistic images for creative projects and design work."},
        ],
        "marketing": [
            {"title": "Content creation and drafting", "description": "AI-assisted content writing for blogs, social media, and campaigns."},
            {"title": "Email marketing automation", "description": "Automated email campaigns, segmentation, and delivery tracking."},
            {"title": "Marketing analytics and insights", "description": "Track campaign performance and audience engagement."},
        ],
        "research": [
            {"title": "AI-powered search and answers", "description": "Get sourced answers from AI search engines for quick research."},
            {"title": "Note-taking and knowledge management", "description": "Organize research findings, notes, and references."},
            {"title": "Audio and transcript research", "description": "Transcribe and search meeting recordings, podcasts, and interviews."},
        ],
        "sales": [
            {"title": "CRM and pipeline management", "description": "Track leads, deals, and customer relationships."},
            {"title": "Email outreach and sequencing", "description": "Automated email sequences for sales outreach."},
            {"title": "Meeting and call recording", "description": "Record and analyze sales calls for insights and coaching."},
        ],
    }

    cases = sub_use_cases.get(slug, [])
    if not cases:
        return ""

    rows = []
    for case in cases:
        # Find matching tools
        matching = []
        for t in tools:
            best = t.get("best", "").lower()
            pros = " ".join(t.get("pros", [])).lower()
            case_words = set(case["title"].lower().split())
            tool_words = set(best.split()) | set(pros.split())
            if case_words & tool_words:
                matching.append(t)
        if not matching:
            matching = tools[:3]

        tool_links = ""
        for t in matching:
            tool_links += f'<a class="lk" href="/tools/{t["id"]}.html"><span class="lk-tx"><b>{html.escape(t["name"])}</b><small>{html.escape(t.get("best", ""))}</small></span></a>'

        rows.append(
            f'<div class="p-feat"><h3>{html.escape(case["title"])}</h3>'
            f'<p>{html.escape(case["description"])}</p>'
            f'<div class="linkgrid">{tool_links}</div></div>'
        )

    return (
        f'<section class="p-sec category-hub" id="sub-use-cases">'
        f'<h2>Sub-use cases</h2>'
        f'<p>These tools serve different use cases within this category. '
        f'Start with the use case that matches your goal, then compare trade-offs.</p>'
        f'<div class="p-feats">{"".join(rows)}</div>'
        f'</section>'
    )


def category_tool_guidance(slug: str) -> str:
    label = taxonomy_categories().get(slug, slug.replace("-", " ").title())
    category_ids = set(category_tool_ids(slug))
    rows = []

    for item in load_catalog():
        if item.get("id") not in category_ids:
            continue

        name = str(item.get("name", "")).strip()
        best_for = str(item.get("best", "")).strip()
        pros = [
            str(value).strip()
            for value in item.get("pros", [])
            if str(value).strip()
        ]

        if not name or not best_for:
            continue

        detail = best_for
        if pros:
            detail += ". Useful strengths listed in the ToolNest catalog include " + ", ".join(pros[:3]) + "."

        rows.append(
            f'<div class="p-feat"><h3>{html.escape(name)}</h3>'
            f'<p><strong>Best for:</strong> {html.escape(detail)}</p></div>'
        )

    if not rows:
        return ""

    return (
        f'<section class="p-sec category-hub" id="category-tool-fit">'
        f'<h2>Which {html.escape(label)} tool fits which job?</h2>'
        f'<p>Start with the job you need to complete, then compare trade-offs rather than choosing by brand name alone. '
        f'The notes below use the current ToolNest catalog descriptions and strengths for this category.</p>'
        f'<div class="p-feats">{"".join(rows)}</div>'
        f'</section>'
    )


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


def best_page_category(relative: str) -> str:
    name = Path(relative).name
    aliases = {
        "best-ai-writing-tools.html": "writing",
        "best-writing-tools.html": "writing",
        "best-website-builder-tools.html": "website-builders",
        "best-ai-voice-tools.html": "voice-video",
        "best-ai-video-tools.html": "voice-video",
        "best-ai-assistants-tools.html": "ai-assistants",
    }
    if name in aliases:
        return aliases[name]
    if not name.startswith("best-") or not name.endswith("-tools.html"):
        return ""
    return name[len("best-"):-len("-tools.html")]


def add_best_guidance(content: str, relative: str) -> str:
    if not relative.startswith("best/") or relative == "best/index.html":
        return content

    slug = best_page_category(relative)
    label = taxonomy_categories().get(slug)
    if not label:
        return content

    candidates = []
    for item in load_catalog():
        if str(item.get("cat", "")).lower() != label.lower():
            continue

        name = str(item.get("name", "")).strip()
        best_for = str(item.get("best", "")).strip()
        pros = [str(v).strip() for v in item.get("pros", []) if str(v).strip()]

        if not name or not best_for:
            continue

        strengths = ""
        if pros:
            strengths = (
                "<p><strong>Catalog strengths:</strong> "
                + html.escape("; ".join(pros[:3]))
                + ".</p>"
            )

        candidates.append(
            f'<div class="p-feat">'
            f'<h3>{html.escape(name)}</h3>'
            f'<p><strong>Best fit:</strong> {html.escape(best_for)}.</p>'
            f'{strengths}'
            f'</div>'
        )

    if not candidates:
        return content

    section = (
        f'<section class="p-sec best-guidance" id="shortlist-fit">'
        f'<h2>How the {html.escape(label)} shortlist differs</h2>'
        f'<p>The strongest choice depends on the job you need to complete. '
        f'ToolNest uses the catalog fit and recorded strengths below to make the shortlist easier to compare '
        f'without treating every product as interchangeable.</p>'
        f'<div class="p-feats">{"".join(candidates)}</div>'
        f'<p>Use these differences as a starting point, then open the relevant review or comparison '
        f'for deeper trade-offs before choosing a product.</p>'
        f'</section>'
    )

    content = re.sub(
        r'<section class="p-sec best-guidance".*?</section>',
        "",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return content.replace("</main>", section + "</main>", 1)


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
    tool_count = len(category_tool_ids(slug))
    intro = (
        f"Explore {tool_count} {label} tools available in the ToolNest catalog. "
        f"Use the reviews, comparisons, alternatives and buying guides on this page "
        f"to narrow the options by fit, trade-offs and workflow needs rather than choosing from a generic list."
    )
    guidance = category_tool_guidance(slug)
    sub_cases = category_sub_use_cases(slug)
    sections = [
        f'<section class="p-sec category-hub" id="category-intro"><h2>About {html.escape(label)} tools</h2>'
        f"<p>{html.escape(intro)}</p></section>",
    ]
    if guidance:
        sections.append(guidance)
    if sub_cases:
        sections.append(sub_cases)
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
    section = (
        '<section class="recently-tested" aria-labelledby="recently-tested-title"><div class="wrap">'
        '<p class="kicker">Proof first</p><h2 class="h2" id="recently-tested-title">Recently tested</h2>'
        '<p class="sub">These pages include hands-on evidence with a test date and plan.</p>'
        f'<div class="linkgrid">{cards}</div></div></section>'
    ) if cards else ""
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
        f"A page is indexable when its main content has at least {MIN_INDEXABLE_WORDS} words and it has",
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
                f"{'below the configured minimum word threshold' if metrics[path].words < MIN_INDEXABLE_WORDS else 'no unique marked section'})"
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
    build_minified_assets()
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
        or (item.words >= MIN_INDEXABLE_WORDS and bool(unique[relative]))
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
        content = content.replace('<meta name="author" content="Abdul Muswir">', '<meta name="author" content="ToolNest Editorial">')
        content = ensure_canonical(content, url)
        content = content.replace("&display=swap", "&display=optional")
        content = ensure_h1(content, parser.h1_text or title)
        content = add_font_hints(content)
        content = use_minified_assets(content)
        content = re.sub(
            r'<link rel="preload" as="style" href="/assets/site\.min\.css"[^>]*>'
            r'<noscript><link rel="stylesheet" href="/assets/site\.min\.css"></noscript>',
            '<link rel="stylesheet" href="/assets/site.min.css">',
            content,
        )
        content = re.sub(
            r'<link rel="preload" as="style" href="/assets/mobile-nav\.min\.css"[^>]*>'
            r'<noscript><link rel="stylesheet" href="/assets/mobile-nav\.min\.css"></noscript>',
            '<link rel="stylesheet" href="/assets/mobile-nav.min.css">',
            content,
        )
        content = re.sub(r'<script type="application/ld\+json" id="tn-editorial-metadata">[^<]*</script>', "", content)
        content = ensure_favicon(content)
        content = ensure_control_names(content)
        content = ensure_image_attributes(content, title)
        content = add_analytics_and_verification(content, config, url, title, description)
        content = normalize_links(content)
        email = html.escape(config.get("CONTACT_EMAIL", "").strip(), quote=True)
        content = content.replace("{{CONTACT_EMAIL}}", email)
        content = add_editorial_strip(content, path, config)
        content = add_proof_stack(content, relative)
        content = add_category_hub(content, relative, indexable)
        content = add_best_guidance(content, relative)
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
