#!/usr/bin/env python3
"""
Upgrade the 9 Grade-B best-of pages by adding:
1. scenarios section (situation -> pick -> reasoning)
2. bottom-line section (decision guidance)
3. sources section (official product links with editorial disclaimer)

Uses only data from data/tools.json and existing comparison pages.
No fabricated evidence, pricing, or testing claims.
"""

import json
import os
import re

# Load tools catalog
with open('data/tools.json') as f:
    catalog = {t['id']: t for t in json.load(f).get('tools', [])}

# Map best-of pages to their tools (in rank order)
best_of_map = {
    'best-design-tools': ['canva', 'figma', 'adobeexpress', 'removebg'],
    'best-email-marketing-tools': ['beehiiv', 'kit', 'mailchimp', 'brevo'],
    'best-image-generation-tools': ['midjourney', 'leonardo'],
    'best-marketing-tools': ['jasper', 'copyai'],
    'best-productivity-tools': ['notion', 'otter', 'fireflies', 'clickup', 'asana', 'monday', 'todoist'],
    'best-research-tools': ['perplexity', 'notebooklm'],
    'best-sales-tools': ['systeme', 'hubspot'],
    'best-website-builder-tools': ['framer', 'webflow', 'squarespace'],
    'best-writing-tools': ['grammarly', 'quillbot', 'prowritingaid', 'hemingway', 'writesonic'],
}

# Scenario templates for each category - situation -> pick -> reasoning
# Built from tools.json "best" field and comparison page context
scenarios_data = {
    'best-design-tools': [
        ('You need social graphics fast, without design training', 'Canva', 'The template library and drag-and-drop editor let anyone produce posts, presentations and simple brand assets in minutes.'),
        ('Your job is interface design or prototyping', 'Figma', 'Real-time collaboration, interactive prototypes and reusable design systems make it the standard for product design teams.'),
        ('You need quick social content with Adobe integration', 'Adobe Express', 'It bridges simple social graphics with Adobe font and stock access, useful if your brand already uses Adobe tools.'),
        ('You only need to remove image backgrounds', 'remove.bg', 'It does one job automatically — no editor, no templates, just upload and download a clean cutout.'),
    ],
    'best-email-marketing-tools': [
        ('You publish a newsletter and want to monetize it', 'beehiiv', 'Built-in paid subscriptions, referral growth tools and a publishing editor are designed for newsletter-first creators.'),
        ('You are a blogger or podcaster selling digital products', 'Kit', 'Creator-focused automations, digital product funnels and WordPress integration fit content creators who sell directly to their audience.'),
        ('You run email campaigns for a business', 'Mailchimp', 'Audience segmentation, basic automation and a large template library cover standard business email marketing needs.'),
        ('You need email plus SMS and transactional messaging', 'Brevo', 'It combines marketing email, SMS campaigns and transactional messaging in one account, useful for customer communication beyond newsletters.'),
    ],
    'best-image-generation-tools': [
        ('You want stylized, high-quality AI art', 'Midjourney', 'Known for strong aesthetic output and creative visual concepts, especially for concept art and stylized imagery.'),
        ('You need AI images for ongoing creative production', 'Leonardo AI', 'Asset generation, model training and creative production tools suit workflows that need repeated image generation with control.'),
    ],
    'best-marketing-tools': [
        ('You write ad copy, landing pages or email sequences', 'Jasper', 'Marketing templates and brand voice features speed up draft copy for ads, product pages and email campaigns.'),
        ('You need a broader content workflow for sales and marketing', 'Copy.ai', 'Sales and marketing content workflows cover more formats, from social posts to product descriptions.'),
    ],
    'best-productivity-tools': [
        ('You want one workspace for notes, tasks and client pages', 'Notion', 'Notes, tasks, databases and client pages in one place reduce context switching for solo workers and small teams.'),
        ('You need meeting transcription and searchable notes', 'Otter.ai', 'Automatic transcription and searchable notes mean you do not have to take notes during every meeting.'),
        ('You record meetings and need structured transcripts', 'Fireflies.ai', 'Recording, transcribing and reviewing meetings with integration into your existing tools keeps meeting knowledge accessible.'),
        ('You manage team projects with tasks and documents', 'ClickUp', 'Tasks, documents and project management in one platform suit teams that want to avoid switching between tools.'),
        ('You plan projects and coordinate team work', 'Asana', 'Project timelines, task dependencies and team coordination features fit structured project management.'),
        ('You need custom work boards for operations', 'monday.com', 'Customizable boards and automations adapt to project tracking, operations and team workflows.'),
        ('You only need personal task management', 'Todoist', 'Lightweight, fast task capture and organization without the overhead of a full project management tool.'),
    ],
    'best-research-tools': [
        ('You need web research with visible sources', 'Perplexity', 'Search answers with cited sources, so you can verify claims without opening multiple tabs.'),
        ('You study your own documents and need to ask questions across them', 'NotebookLM', 'Upload your own sources and ask questions across them — useful for studying, briefing and document analysis.'),
    ],
    'best-sales-tools': [
        ('You want to sell a course, product or email list simply', 'Systeme.io', 'Sales pages, email lists and online course hosting in one account remove the need for separate marketing tools.'),
        ('You need a full CRM with marketing and sales workflows', 'HubSpot', 'CRM, marketing automation and sales pipelines in one platform suit businesses that need structured customer management.'),
    ],
    'best-website-builder-tools': [
        ('You want a modern landing page or design-led marketing site', 'Framer', 'Visual responsive design, animations and fast publishing suit designers who want control without code.'),
        ('You need a visual website with CMS and design control', 'Webflow', 'Visual design with CMS collections and interactions, suitable for agencies and designers who need content management.'),
        ('You want a polished portfolio or small business site', 'Squarespace', 'Templates and simplicity make it fast to launch a professional-looking site without design expertise.'),
    ],
    'best-writing-tools': [
        ('You write in English and want clear, mistake-free output', 'Grammarly', 'Real-time grammar, spelling and tone checking across email, documents and browser keeps writing clear.'),
        ('You need to paraphrase, rewrite or summarize text', 'QuillBot', 'Paraphrasing modes, summarization and grammar checking help you rework existing text without starting from scratch.'),
        ('You are a long-form author who wants detailed writing reports', 'ProWritingAid', 'Style reports, readability analysis and consistency checks suit authors who want thorough feedback on longer drafts.'),
        ('You want to make your sentences clearer and punchier', 'Hemingway Editor', 'Highlights complex sentences, adverbs and passive voice so you can simplify your writing.'),
        ('You draft marketing articles, landing pages or campaign copy', 'Writesonic', 'AI-assisted drafting for marketing content, landing pages and SEO articles speeds up first drafts.'),
    ],
}

# Bottom-line templates for each category
bottom_line_data = {
    'best-design-tools': 'If you need speed and simplicity, start with Canva. Move to Figma when the job is interface design or team collaboration. Adobe Express fits if your brand already uses Adobe tools. Use remove.bg only when background removal is the sole task.',
    'best-email-marketing-tools': 'If you publish a newsletter, start with beehiiv. Kit is the better fit if you sell digital products to an audience. Mailchimp covers standard business email campaigns. Brevo makes sense when you need SMS and transactional messaging alongside email.',
    'best-image-generation-tools': 'Midjourney produces the strongest stylized output for creative concepts. Leonardo AI suits workflows that need repeated generation with more control over models and assets. Choose based on whether quality or workflow control matters more.',
    'best-marketing-tools': 'Jasper is stronger for marketing copy with brand voice control. Copy.ai covers a broader range of sales and marketing formats. Pick Jasper if copy quality is the priority; pick Copy.ai if format variety matters more.',
    'best-productivity-tools': 'For solo work, start with Notion for organization and Todoist for tasks. Add Otter or Fireflies when meeting notes become a bottleneck. For team projects, ClickUp, Asana or monday.com depend on whether you prefer documents-first, timeline-first or board-first workflows.',
    'best-research-tools': 'Perplexity is the starting point for web research with cited sources. NotebookLM is for when your material is already in documents and you need to ask questions across them. They serve different research jobs.',
    'best-sales-tools': 'Systeme.io covers the basics — sales pages, email and courses — at a lower cost. HubSpot is for when you need a full CRM with marketing automation and sales pipelines. Start simple with Systeme.io; scale to HubSpot when customer management becomes complex.',
    'best-website-builder-tools': 'Framer suits designers who want visual control and fast publishing. Webflow adds CMS and deeper design control for agencies. Squarespace is the fastest route to a polished site with templates. Pick based on how much design control you need versus how fast you need to launch.',
    'best-writing-tools': 'For everyday writing clarity, Grammarly is the baseline. Add QuillBot when you need to rework existing text. ProWritingAid suits long-form authors who want detailed style reports. Hemingway Editor helps you simplify sentences. Writesonic speeds up marketing draft creation.',
}


def build_scenarios_section(best_name):
    """Build the scenarios section HTML."""
    scenarios = scenarios_data.get(best_name, [])
    if not scenarios:
        return ''

    items = []
    for situation, pick_name, reasoning in scenarios:
        items.append(f'<div class="p-feat"><b>{situation}</b><p><strong>{pick_name}</strong> — {reasoning}</p></div>')

    html = '<section class="p-sec" id="scenarios"><h2>Which pick fits your situation</h2><div class="p-feats">'
    html += ''.join(items)
    html += '</div></section>'
    return html


def build_bottom_line_section(best_name):
    """Build the bottom-line section HTML."""
    text = bottom_line_data.get(best_name, '')
    if not text:
        return ''

    return f'<section class="p-sec" id="bottom-line"><h2>The bottom line</h2><p>{text}</p></section>'


def build_sources_section(best_name):
    """Build the sources section HTML with official product links."""
    tools = best_of_map.get(best_name, [])
    if not tools:
        return ''

    items = []
    for tool_id in tools:
        tool = catalog.get(tool_id, {})
        name = tool.get('name', tool_id)
        site = tool.get('site', '')
        if site:
            items.append(f'<li><a class="lnk inl" href="{site}" rel="sponsored nofollow noopener" target="_blank">{name} official site</a></li>')

    if not items:
        return ''

    html = '<section class="p-sec" id="sources"><h2>Sources and how this page was checked</h2>'
    html += '<p>This page is based on published product information from the official sources listed below. It is not a hands-on lab test, and we do not claim to have used every feature. Prices and limits change: confirm them on the vendor site before you buy.</p>'
    html += '<ul class="tl">' + ''.join(items) + '</ul></section>'
    return html


def upgrade_best_page(best_name):
    """Upgrade a single best-of page by adding missing sections."""
    filepath = f'best/{best_name}.html'
    if not os.path.exists(filepath):
        print(f'  SKIP: {filepath} not found')
        return False

    with open(filepath) as f:
        content = f.read()

    # Check if already has scenarios section
    if 'id="scenarios"' in content:
        print(f'  SKIP: {best_name} already has scenarios section')
        return False

    # Build the new sections
    scenarios_html = build_scenarios_section(best_name)
    bottom_line_html = build_bottom_line_section(best_name)
    sources_html = build_sources_section(best_name)

    if not scenarios_html and not bottom_line_html and not sources_html:
        print(f'  SKIP: {best_name} no content to add')
        return False

    # Insert scenarios and bottom-line BEFORE the hero section
    # The hero section starts with <section class="hero
    hero_match = re.search(r'(<section class="hero)', content)
    if hero_match:
        insert_before_hero = scenarios_html + bottom_line_html
        content = content[:hero_match.start()] + insert_before_hero + content[hero_match.start():]
        print(f'  Added scenarios + bottom-line before hero')
    else:
        print(f'  WARNING: {best_name} no hero section found')
        return False

    # Insert sources section AFTER the picks section (before p-method or at end of main)
    # Find the p-method section or the shortlist-fit section
    method_match = re.search(r'(<section class="p-method")', content)
    if method_match:
        content = content[:method_match.start()] + sources_html + content[method_match.start():]
        print(f'  Added sources before p-method')
    else:
        # Try to insert before the shortlist-fit section
        shortlist_match = re.search(r'(<section class="p-sec best-guidance")', content)
        if shortlist_match:
            content = content[:shortlist_match.start()] + sources_html + content[shortlist_match.start():]
            print(f'  Added sources before shortlist-fit')
        else:
            # Insert before </main>
            main_end = content.rfind('</main>')
            if main_end > 0:
                content = content[:main_end] + sources_html + content[main_end:]
                print(f'  Added sources before </main>')
            else:
                print(f'  WARNING: {best_name} cannot find insertion point for sources')
                return False

    with open(filepath, 'w') as f:
        f.write(content)

    print(f'  OK: {best_name} upgraded')
    return True


def main():
    print('=== Upgrading Grade-B Best-of Pages ===\n')
    upgraded = 0
    for best_name in best_of_map:
        print(f'Processing: {best_name}')
        if upgrade_best_page(best_name):
            upgraded += 1
        print()

    print(f'=== Upgraded {upgraded} pages ===')


if __name__ == '__main__':
    main()
