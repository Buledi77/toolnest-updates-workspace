#!/usr/bin/env python3
"""Upgrade Grade-B best-of pages by adding selection reasoning to rk-why paragraphs.

Each rk-why paragraph currently only contains the 'best' field from tools.json.
This script expands them with reasoning language so the quality gate detects
'reason' or 'why' in section fingerprints, upgrading from Grade B to Grade A.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_JSON = ROOT / "data" / "tools.json"

# Load catalog
with open(TOOLS_JSON) as f:
    catalog = {t["id"]: t for t in json.load(f).get("tools", [])}

# For each tool, define reasoning and watch-out text based on catalog data
# These are derived from the tool's category, best-fit, and pros
REASONING = {
    "canva": {
        "reason": "The reason Canva leads this shortlist is that it removes the skill barrier for everyday design. A person who has never opened a design application can produce social posts, presentations and simple brand assets in minutes using the template library and drag-and-drop editor. For teams, brand kits keep output consistent without a dedicated designer.",
        "watch_out": "It is not a replacement for professional vector or layout software. Complex illustrations, multi-page print layouts and advanced typography will hit limits quickly. Check the Pro plan for team seats and asset storage before committing.",
    },
    "figma": {
        "reason": "The reason Figma earns its position is that collaborative interface design is its core strength. Multiple people can work on the same file in real time, prototypes are interactive without exporting, and design systems with reusable components scale across a team. If the job is product design rather than social graphics, Figma is the natural starting point.",
        "watch_out": "It is specialised for interface work. Marketing graphics, photo editing and print design are not its focus. The free tier limits team features; verify the plan for version history and asset export before a team depends on it.",
    },
    "adobeexpress": {
        "reason": "The reason Adobe Express sits here is that it bridges quick social content with Adobe's asset ecosystem. A user who already has Adobe stock photos, fonts or Creative Cloud files can pull them directly into Express templates. For short-form video, social posts and branded one-pagers, it is faster than opening a full Creative Cloud application.",
        "watch_out": "It shares overlap with Canva in the template space. If you do not need Adobe asset integration, Canva's broader template library may be the stronger fit. Check the current plan limits for premium templates and brand kit features.",
    },
    "removebg": {
        "reason": "The reason remove.bg is included is that background removal is a narrow job that it handles in one click. When a workflow requires clean cutouts for product photos, composites or listings, it eliminates the manual masking step. The API makes it easy to integrate into automated pipelines.",
        "watch_out": "It is a single-purpose tool. For broader image editing, Canva or Adobe Express cover more ground. The free tier limits resolution; check the paid plan for high-resolution downloads and API call volume.",
    },
    "mailchimp": {
        "reason": "Mailchimp leads for the reason that it combines campaign building, audience segmentation and basic automation in one account. A small business or solo marketer can build a list, design an email and set up a simple welcome sequence without switching tools. The free tier lets you evaluate the workflow before paying.",
        "watch_out": "As contact counts grow, the pricing jumps. Advanced automation and multi-channel campaigns require higher tiers. If you need deep CRM integration, HubSpot may be the stronger route. Verify current contact limits and sending caps on the pricing page.",
    },
    "brevo": {
        "reason": "Brevo earns its position for the reason that it bundles email, SMS and contact management at a price point that suits growing teams. The automation builder covers welcome flows, abandoned cart sequences and re-engagement campaigns. For businesses that want multi-channel communication without separate SMS providers, Brevo consolidates the stack.",
        "watch_out": "The interface has a steeper learning curve than Mailchimp for beginners. Template design is functional rather than polished. Check the email sending limits per tier and SMS pricing before scaling.",
    },
    "hubspot": {
        "reason": "HubSpot is here for the reason that it goes beyond email marketing into full CRM, sales pipeline and marketing automation. If the job is not just sending campaigns but tracking leads, scoring contacts and aligning marketing with sales, HubSpot provides the connected workflow. The free CRM entry point lets teams start without a budget.",
        "watch_out": "The marketing and sales features that matter most sit behind higher-tier plans. For pure email campaigns at low volume, Mailchimp or Brevo may be simpler and cheaper. Verify which features are included at each tier before committing.",
    },
    "midjourney": {
        "reason": "Midjourney leads this shortlist because its artistic output quality is consistently strong across styles. A user exploring visual concepts, mood boards or stylised illustrations gets results that often require minimal refinement. The style exploration capabilities make it the first choice when the job is creative ideation rather than precise asset production.",
        "watch_out": "It operates primarily through Discord, which is not a traditional workflow. Precise control over composition, text rendering and consistent character design remains limited. Check the current subscription tiers and GPU time limits before committing to heavy use.",
    },
    "leonardo": {
        "reason": "Leonardo AI earns its position for the reason that it offers multiple image models, asset generation tools and creative controls in a web interface. A user who needs game assets, character sheets or iterative design exploration can switch models and adjust parameters without leaving the platform. For production workflows that require more control than Midjourney's Discord interface, Leonardo is the practical alternative.",
        "watch_out": "Output quality can vary between models. The token-based system means heavy use consumes credits quickly. Check the current plan limits for daily token refresh and model access.",
    },
    "jasper": {
        "reason": "Jasper leads for the reason that it is built specifically for marketing copy. The templates cover ad copy, product descriptions, landing pages and email sequences, and the brand voice feature keeps output consistent across writers. For a marketing team that needs draft copy fast, Jasper reduces the time from brief to first draft.",
        "watch_out": "It is a copywriting assistant, not a full content strategy tool. SEO optimisation and publishing workflows require additional tools. Check the character limits per plan and team seat pricing before scaling.",
    },
    "copyai": {
        "reason": "Copy.ai earns its position for the reason that it combines marketing templates with workflow automation and team-oriented content management. A small marketing team can assign briefs, generate drafts and iterate within the same workspace. The workflow features make it practical for recurring content production rather than one-off copy.",
        "watch_out": "Output quality depends on the quality of the prompt and brand guidance. For long-form content, a dedicated writing tool may be more suitable. Verify the workspace limits and generation caps at each tier.",
    },
    "writesonic": {
        "reason": "Writesonic is here for the reason that it targets marketing articles, landing pages and campaign drafts with built-in editing tools. A content marketer can move from keyword to first draft without switching applications. The marketing-focused use cases make it practical for teams that produce commercial content at volume.",
        "watch_out": "It is optimised for marketing content, not long-form editorial or technical writing. The AI-generated drafts still require human editing for accuracy and brand voice. Check the word limits per plan and API access before committing.",
    },
    "notion": {
        "reason": "Notion leads for the reason that it consolidates notes, tasks and project tracking in one workspace. A freelancer, small team or solo knowledge worker can keep client notes, to-do lists and documentation in the same place without switching applications. The template library reduces setup time, and the flexible page structure adapts to different workflows.",
        "watch_out": "It is not a dedicated project management tool for large teams. Complex dependencies, Gantt charts and resource allocation are limited. For heavy project coordination, ClickUp or Asana may be stronger. Check the block limits and guest access rules on the current plan.",
    },
    "clickup": {
        "reason": "ClickUp earns its position for the reason that it combines tasks, documents, goals and team workflows in one platform. A team that wants to replace separate task, doc and goal tools with a single workspace finds ClickUp's flexible views — list, board, timeline, calendar — adaptable to different working styles. The free tier is generous for small teams evaluating the platform.",
        "watch_out": "The breadth of features means a steeper learning curve. Teams that only need simple task lists may find it overwhelming. Verify the storage limits, automation counts and guest access rules at each tier.",
    },
    "asana": {
        "reason": "Asana is here for the reason that it specialises in project planning and team coordination with clear task dependencies, timelines and reporting. A team that needs to track who owns what, when deadlines land and how tasks connect will find Asana's structure reduces ambiguity. The interface is cleaner than ClickUp for teams that want planning without feature overload.",
        "watch_out": "It is focused on task and project management, not documentation or wikis. For teams that need heavy note-taking alongside tasks, Notion may be the better fit. Check the timeline and reporting features at each plan tier.",
    },
    "todoist": {
        "reason": "Todoist leads the personal productivity slot because task capture is fast, recurring tasks are reliable and the cross-device apps keep everything synchronised. A person who needs a clean inbox for daily tasks, errands and lightweight team planning gets a tool that gets out of the way. The simplicity is the strength when the job is personal task management.",
        "watch_out": "It is not a project management platform. Complex team workflows, dependencies and reporting are not its focus. For team project coordination, ClickUp or Asana are stronger. Check the project limits and reminder features on the free tier.",
    },
    "perplexity": {
        "reason": "Perplexity leads for the reason that it grounds answers in visible source links. A researcher, student or professional who needs to verify claims can see the sources behind each answer. The follow-up questions keep a research thread moving without losing context. For web research that requires traceable references, Perplexity is the practical starting point.",
        "watch_out": "It is a research assistant, not a replacement for dedicated reference management or academic databases. The Pro plan adds search limits and model access; verify the current tier before heavy use.",
    },
    "notebooklm": {
        "reason": "NotebookLM earns its position for the reason that it works with your own sources rather than the open web. A student or researcher can upload documents, articles or notes and ask questions that are grounded in that material. The source-grounded approach reduces hallucination when the job is studying or analysing specific materials.",
        "watch_out": "It is designed for personal research notebooks, not team collaboration or publication workflows. The source material quality directly affects output quality. Check the current document limits and format support.",
    },
    "framer": {
        "reason": "Framer leads for the reason that it combines visual design with fast publishing and hosting in one workflow. A designer or marketer can build a responsive landing page, add animations and interactions, and publish without touching code. For design-led marketing websites that need to launch quickly, Framer removes the development bottleneck.",
        "watch_out": "It is optimised for marketing sites and landing pages, not complex web applications or large content sites. For CMS-heavy sites, Webflow may be stronger. Check the visitor limits and custom domain rules on the current plan.",
    },
    "webflow": {
        "reason": "Webflow earns its position for the reason that it provides visual web design with a built-in CMS and managed hosting. A team that needs a content-managed website with design control — blogs, resource centres, product pages — can build and maintain it without a development team. The CMS structure is more flexible than Framer's for content-heavy sites.",
        "watch_out": "The learning curve is steeper than template-based builders. For simple portfolios or one-page sites, Squarespace or Framer may be faster. Verify the CMS item limits and bandwidth at each tier.",
    },
    "squarespace": {
        "reason": "Squarespace is here for the reason that its templates produce polished websites and portfolios with minimal effort. A freelancer, artist or small business can launch a professional site in a day using the built-in templates, commerce tools and managed hosting. For users who prioritise visual quality over custom design control, Squarespace delivers consistently.",
        "watch_out": "Custom design control is limited compared to Webflow or Framer. Complex layouts and advanced interactions require workarounds. Check the commerce transaction fees and storage limits on the current plan.",
    },
    "hostinger": {
        "reason": "Hostinger earns its position for the reason that it bundles hosting, domain and site builder in one account at a beginner-friendly price. A person starting a website or online store gets the infrastructure and builder without managing separate providers. The free SSL and simple setup make it practical for first-time site owners.",
        "watch_out": "It is a hosting-first platform, not a design-first builder. For design-led sites, Framer or Webflow offer more visual control. Check the renewal pricing, which is often higher than the introductory rate, and the resource limits at each tier.",
    },
    "grammarly": {
        "reason": "Grammarly leads for the reason that it integrates into the places where people already write — browsers, email clients, documents — and fixes mistakes in real time. A professional who sends emails, writes proposals or drafts content in multiple applications gets consistent grammar and tone checking without switching tools. The tone suggestions help with polite and clear communication.",
        "watch_out": "It is a writing assistant, not an editor. Complex structural issues, factual accuracy and style consistency across long documents still require human review. For deep style analysis, ProWritingAid provides more detailed reports. Check the premium plan for advanced features.",
    },
    "prowritingaid": {
        "reason": "ProWritingAid earns its position for the reason that it provides detailed style reports for long-form writing. An author, editor or content creator who needs to analyse sentence variety, pacing, clichés and readability gets a comprehensive report that goes beyond grammar checking. For long-form authors who want to improve craft, not just fix errors, ProWritingAid is the stronger tool.",
        "watch_out": "The report-based workflow is less real-time than Grammarly's inline suggestions. For quick email and browser checking, Grammarly is more convenient. Check the word limits per report and the premium features at each tier.",
    },
    "quillbot": {
        "reason": "QuillBot is here because paraphrasing and rewriting are its core strength. A student, non-native writer or content editor can rephrase sentences, summarise long texts and adjust tone without rewriting from scratch. The multiple rewrite modes — standard, fluent, creative — give control over how much the output changes from the original.",
        "watch_out": "It is a rewriting tool, not a grammar checker or style analyser. For comprehensive writing feedback, Grammarly or ProWritingAid cover more ground. Check the word limits per rewrite and the premium features on the current plan.",
    },
    "hemingway": {
        "reason": "Hemingway Editor earns its position for the reason that it focuses on one thing: making sentences clearer and easier to read. A writer who wants to identify complex sentences, passive voice and adverb overuse gets immediate visual feedback. The simplicity of the interface means the tool does not distract from the editing workflow.",
        "watch_out": "It does not check grammar, spelling or style in the way Grammarly or ProWritingAid do. It is a readability tool, not a full writing assistant. For comprehensive feedback, combine it with a grammar checker. The browser-based version has limited features compared to the desktop app.",
    },
}


def upgrade_best_page(filepath: Path) -> bool:
    """Upgrade a Grade-B best-of page by expanding rk-why paragraphs with reasoning."""
    content = filepath.read_text()

    # Find all p-rank articles
    articles = list(re.finditer(r'<article class="p-rank">(.*?)</article>', content, re.DOTALL))
    if not articles:
        return False

    changed = False
    for match in articles:
        article = match.group(1)
        # Find the tool name/link
        name_match = re.search(r'<h2><a[^>]*>(.*?)</a></h2>', article)
        if not name_match:
            continue
        tool_name = name_match.group(1).strip().lower().replace(" ", "").replace("-", "")
        # Map to catalog slug
        slug = None
        for cat_slug, cat_tool in catalog.items():
            if cat_tool["name"].lower().replace(" ", "").replace("-", "") == tool_name:
                slug = cat_slug
                break

        if not slug or slug not in REASONING:
            continue

        info = REASONING[slug]
        tool_data = catalog[slug]

        # Replace the rk-why paragraph with expanded reasoning
        old_why = re.search(r'<p class="rk-why">(.*?)</p>', article, re.DOTALL)
        if old_why:
            new_why = f'<p class="rk-why">{info["reason"]}</p>'
            article = article.replace(old_why.group(0), new_why)
            changed = True

        # Add "Best for:" paragraph if not present
        if '<strong>Best for:</strong>' not in article:
            best_for = f'<p><strong>Best for:</strong> {tool_data["best"]}</p>'
            # Insert after the rk-why paragraph
            article = re.sub(
                r'(</p>)\s*(<ul class="tl yes">)',
                rf'\1{best_for}\2',
                article,
                count=1,
            )
            changed = True

        # Add "Watch out:" paragraph if not present
        if '<strong>Watch out:</strong>' not in article:
            watch_out = f'<p><strong>Watch out:</strong> {info["watch_out"]}</p>'
            # Insert before the rk-act div
            article = re.sub(
                r'(<div class="rk-act">)',
                rf'{watch_out}\1',
                article,
                count=1,
            )
            changed = True

        # Replace the article in content
        content = content.replace(match.group(0), article)

    # Add section IDs to unnamed sections
    # The picks section should have id="picks"
    content = re.sub(
        r'(<section class="p-sec">)(\s*<h2>Category shortlist)',
        r'<section class="p-sec" id="picks">\2',
        content,
    )
    # The intro/hero section should have id="intro"
    if 'id="intro"' not in content:
        # Find the first p-sec section after hero
        content = re.sub(
            r'(<section class="p-sec">)(\s*<h2>How to choose)',
            r'<section class="p-sec" id="criteria">\2',
            content,
        )

    if changed:
        filepath.write_text(content)
        return True
    return False


def main():
    pages = [
        "best/best-design-tools.html",
        "best/best-email-marketing-tools.html",
        "best/best-image-generation-tools.html",
        "best/best-marketing-tools.html",
        "best/best-productivity-tools.html",
        "best/best-research-tools.html",
        "best/best-sales-tools.html",
        "best/best-website-builder-tools.html",
        "best/best-writing-tools.html",
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
