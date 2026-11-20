#!/usr/bin/env python3
"""Add scenarios and bottom-line sections to best-of pages missing them.

These pages have score=8, missing only no_scenarios and no_bottom_line.
Adding these two sections will push them to Grade A (score >= 9, sections >= 7).
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_JSON = ROOT / "data" / "tools.json"

with open(TOOLS_JSON) as f:
    catalog = {t["id"]: t for t in json.load(f).get("tools", [])}

# For each best-of page, define the scenarios and bottom line content
# based on the tools in the shortlist and their catalog data

SCENARIOS = {
    "best-ai-tools-for-freelancers": {
        "scenarios": [
            {
                "situation": "A freelancer needs one workspace for everything",
                "pick": "Notion",
                "reason": "Notes, tasks, client pages and a simple tracker in one place means fewer tabs and less context switching.",
            },
            {
                "situation": "Client writing is the main revenue source",
                "pick": "Grammarly",
                "reason": "Real-time grammar and tone checking across email, documents and browser keeps client communication clear without extra steps.",
            },
            {
                "situation": "Freelance marketing or copywriting work",
                "pick": "Jasper",
                "reason": "Marketing templates and brand voice features speed up draft copy for ads, landing pages and email sequences.",
            },
            {
                "situation": "Offering SEO or content strategy services",
                "pick": "Semrush",
                "reason": "Keyword research, competitor analysis and site auditing cover the core SEO jobs clients ask for.",
            },
            {
                "situation": "Selling digital products or courses",
                "pick": "Systeme.io",
                "reason": "Email, funnels and course hosting in one account removes the need for separate marketing and hosting tools.",
            },
        ],
        "bottom_line": (
            "If you are just starting out, begin with Notion for organisation and Grammarly for writing quality. "
            "Add Jasper when marketing copy becomes a recurring job. Bring in Semrush only when SEO is part of the service you sell. "
            "Systeme.io makes sense when you are ready to sell digital products or courses directly."
        ),
    },
    "best-ai-tools-for-students": {
        "scenarios": [
            {
                "situation": "A student needs to organise notes, assignments and deadlines",
                "pick": "Notion",
                "reason": "One workspace for class notes, to-do lists and project tracking eliminates the need for separate apps.",
            },
            {
                "situation": "Writing essays and assignments in English",
                "pick": "Grammarly",
                "reason": "Inline grammar and tone checking catches mistakes before submission and helps non-native writers produce clearer work.",
            },
            {
                "situation": "Researching topics with source citations",
                "pick": "Perplexity",
                "reason": "Source-grounded answers with visible links make it easier to verify claims and find references for assignments.",
            },
        ],
        "bottom_line": (
            "Start with Notion for organisation and Grammarly for writing quality — these two cover the most common student needs. "
            "Add Perplexity when research assignments require traceable sources. "
            "Check your institution's policy on AI-assisted writing before relying on any tool for graded work."
        ),
    },
    "best-ai-tools-for-youtubers": {
        "scenarios": [
            {
                "situation": "A YouTuber needs to edit videos quickly",
                "pick": "Descript",
                "reason": "Edit video by editing the transcript, remove filler words and overlay screen recording without traditional timeline editing.",
            },
            {
                "situation": "Creating voiceovers without recording",
                "pick": "ElevenLabs",
                "reason": "Natural-sounding AI voices in multiple languages for narration, intros and B-roll when recording your own voice is not practical.",
            },
            {
                "situation": "Writing video descriptions and titles",
                "pick": "Jasper",
                "reason": "Marketing templates for ad copy and product descriptions adapt well to YouTube descriptions, titles and pinned comments.",
            },
            {
                "situation": "Generating thumbnails and channel art",
                "pick": "Canva",
                "reason": "Template library and drag-and-drop editor make it fast to produce consistent thumbnails and channel branding.",
            },
        ],
        "bottom_line": (
            "Descript is the strongest starting point if editing is the biggest time sink. "
            "ElevenLabs adds voiceover capability when you need narration without recording. "
            "Jasper and Canva are useful additions for channel marketing and visual consistency. "
            "Check ElevenLabs' commercial usage terms if your channel is monetised."
        ),
    },
    "best-ai-video-tools": {
        "scenarios": [
            {
                "situation": "Editing video podcasts or interviews",
                "pick": "Descript",
                "reason": "Transcript-based editing, filler word removal and screen recording overlay make post-production faster for talk-format content.",
            },
            {
                "situation": "Creating AI-generated video content",
                "pick": "Synthesia",
                "reason": "AI avatars and multilingual video generation are useful for training, onboarding or explainer content without filming.",
            },
            {
                "situation": "Short-form social video and quick edits",
                "pick": "Kapwing",
                "reason": "Browser-based editing with collaborative features and social media templates is practical for quick turnaround content.",
            },
            {
                "situation": "Advanced visual effects and creative video",
                "pick": "Runway",
                "reason": "AI-powered visual effects, style transfer and motion tools are designed for creative video production rather than simple editing.",
            },
        ],
        "bottom_line": (
            "Descript is the practical choice for editing spoken-content video. "
            "Synthesia fits when you need avatar-based video without filming. "
            "Kapwing is the fastest route for short-form social content. "
            "Runway is for creative visual effects that go beyond standard editing."
        ),
    },
    "best-ai-voice-tools": {
        "scenarios": [
            {
                "situation": "Natural voiceovers for videos and courses",
                "pick": "ElevenLabs",
                "reason": "Consistently natural-sounding voices across languages make it the strongest option for narration and voiceover work.",
            },
            {
                "situation": "Editing audio from video recordings",
                "pick": "Descript",
                "reason": "Transcript-based audio editing, noise removal and filler word deletion streamline post-production for podcasts and interviews.",
            },
        ],
        "bottom_line": (
            "ElevenLabs is the stronger choice when the job is generating voice from text. "
            "Descript is stronger when the job is editing recorded audio. "
            "If you need both capabilities, they complement each other rather than compete."
        ),
    },
    "best-ai-writing-tools": {
        "scenarios": [
            {
                "situation": "Marketing copy and commercial content",
                "pick": "Jasper",
                "reason": "Templates for ads, landing pages and email sequences with brand voice features keep output consistent across writers.",
            },
            {
                "situation": "Grammar and tone checking across all writing",
                "pick": "Grammarly",
                "reason": "Real-time inline suggestions in browsers, email and documents catch mistakes as you write rather than after.",
            },
            {
                "situation": "Long-form writing and style analysis",
                "pick": "ProWritingAid",
                "reason": "Detailed style reports on sentence variety, pacing and readability go beyond grammar checking for authors and editors.",
            },
        ],
        "bottom_line": (
            "Jasper is the strongest tool for marketing copy production. "
            "Grammarly is the most convenient for everyday writing quality across applications. "
            "ProWritingAid is the deeper tool for long-form authors who want style analysis, not just grammar fixes. "
            "For comprehensive writing feedback, combine Grammarly for real-time checking with ProWritingAid for detailed style reports."
        ),
    },
    "best-website-and-hosting-tools": {
        "scenarios": [
            {
                "situation": "Starting a website with bundled hosting",
                "pick": "Hostinger",
                "reason": "Hosting, domain and site builder in one account at a beginner-friendly price removes the need to manage separate providers.",
            },
            {
                "situation": "Design-led marketing websites and landing pages",
                "pick": "Framer",
                "reason": "Visual design with fast publishing and hosting lets designers launch responsive sites without code.",
            },
            {
                "situation": "Selling digital products or online courses",
                "pick": "Systeme.io",
                "reason": "Email, funnels, courses and a free website builder in one account consolidates the sales stack.",
            },
        ],
        "bottom_line": (
            "Hostinger is the practical starting point for a hosted website at low cost. "
            "Framer is stronger when design control and visual quality are the priority. "
            "Systeme.io makes sense when the site is part of a sales funnel or course business. "
            "Check Hostinger's renewal pricing, which is often higher than the introductory rate."
        ),
    },
}


def upgrade_best_page(filepath: Path) -> bool:
    """Add scenarios and bottom-line sections to a best-of page."""
    stem = filepath.stem
    if stem not in SCENARIOS:
        return False

    info = SCENARIOS[stem]
    content = filepath.read_text()

    # Check if already has scenarios or bottom-line
    if 'id="scenarios"' in content and 'id="bottom-line"' in content:
        return False

    # Build the scenarios section HTML
    scenarios_html = '<section class="p-sec" id="scenarios"><h2>Which pick fits your situation</h2>'
    for scenario in info["scenarios"]:
        scenarios_html += (
            f'<p><strong>{scenario["situation"]}:</strong> '
            f'{scenario["pick"]} — {scenario["reason"]}</p>'
        )
    scenarios_html += '</section>'

    # Build the bottom-line section HTML
    bottom_html = f'<section class="p-sec" id="bottom-line"><h2>The bottom line</h2><p>{info["bottom_line"]}</p></section>'

    # Insert before the FAQ section (id="questions")
    if 'id="questions"' in content:
        # Insert scenarios and bottom-line before FAQ
        content = content.replace(
            '<section',
            scenarios_html + bottom_html + '<section',
            1,  # Only replace the first <section after the picks
        )
        # Actually, let's find the FAQ section and insert before it
        # Reset and do it properly
        filepath.write_text(content)  # Reset
        content = filepath.read_text()

        # Find the FAQ section
        faq_match = re.search(r'(<section[^>]*id="questions"[^>]*>)', content)
        if faq_match:
            content = content[:faq_match.start()] + scenarios_html + bottom_html + '\n' + content[faq_match.start():]
            filepath.write_text(content)
            return True

    # If no FAQ section, insert before the related guides section
    related_match = re.search(r'(<section[^>]*id="related"[^>]*>)', content)
    if related_match:
        content = content[:related_match.start()] + scenarios_html + bottom_html + '\n' + content[related_match.start():]
        filepath.write_text(content)
        return True

    return False


def main():
    pages = [
        "best/best-ai-tools-for-freelancers.html",
        "best/best-ai-tools-for-students.html",
        "best/best-ai-tools-for-youtubers.html",
        "best/best-ai-video-tools.html",
        "best/best-ai-voice-tools.html",
        "best/best-ai-writing-tools.html",
        "best/best-website-and-hosting-tools.html",
    ]

    upgraded = 0
    for page in pages:
        filepath = ROOT / page
        if filepath.exists():
            if upgrade_best_page(filepath):
                print(f"✓ Upgraded: {page}")
                upgraded += 1
            else:
                print(f"  No changes needed: {page}")
        else:
            print(f"✗ Not found: {page}")

    print(f"\nTotal upgraded: {upgraded}/{len(pages)}")


if __name__ == "__main__":
    main()
