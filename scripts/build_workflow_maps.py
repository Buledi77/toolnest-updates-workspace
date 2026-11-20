#!/usr/bin/env python3
"""
Workflow Maps — Phase 5

Using existing goals/categories/relationships only, create reusable
structured workflow maps.

Each map contains:
- goal
- stages
- decision questions
- candidate tools
- relevant comparisons
- alternatives
- evidence confidence
- unresolved gaps

Do not create new indexable pages.

Output: docs/internal/WORKFLOW-MAPS.json
"""

import json
import os
from pathlib import Path


def load_json(path):
    with open(path) as f:
        return json.load(f)


def build_workflow_maps():
    catalog = load_json("data/tools.json")
    tools = {t["id"]: t for t in catalog.get("tools", [])}

    # Load taxonomy
    taxonomy = load_json("data/taxonomy/taxonomy-v1.json")

    # Load task catalog
    task_catalog = load_json("data/recommendations/task-catalog.json")

    # Load stack builder
    stack_builder = load_json("data/stack/stack-builder-v1.json")

    # Build category-to-tools mapping
    category_tools = {}
    for tool_id, tool in tools.items():
        cat = tool.get("cat", "unknown")
        if cat not in category_tools:
            category_tools[cat] = []
        category_tools[cat].append(tool_id)

    # Build comparison map
    compare_dir = Path("compare")
    comparison_map = {}
    if compare_dir.exists():
        for f in compare_dir.iterdir():
            if f.suffix == ".html" and f.name != "index.html":
                # Extract tool IDs from filename (e.g., asana-vs-notion.html)
                name = f.stem
                parts = name.split("-vs-")
                if len(parts) == 2:
                    t1, t2 = parts
                    if t1 not in comparison_map:
                        comparison_map[t1] = []
                    comparison_map[t1].append({
                        "vs": t2,
                        "path": f"/compare/{f.name}"
                    })

    # Build alternatives map
    alt_dir = Path("alternatives")
    alternatives_map = {}
    if alt_dir.exists():
        for f in alt_dir.iterdir():
            if f.suffix == ".html" and f.name != "index.html":
                base_tool = f.stem.replace("-alternatives", "")
                alternatives_map[base_tool] = f"/alternatives/{f.name}"

    # Build best-of map
    best_dir = Path("best")
    best_of_map = {}
    if best_dir.exists():
        for f in best_dir.iterdir():
            if f.suffix == ".html" and f.name != "index.html":
                best_of_map[f.stem] = f"/best/{f.name}"

    workflows = {
        "schema_version": "workflow-maps-v1",
        "generated_at": "2026-11-20",
        "description": "Reusable structured workflow maps from existing goals, categories, and relationships. No new indexable pages created.",
        "total_workflows": 0,
        "workflows": []
    }

    # Build workflows from task catalog
    for task in task_catalog.get("tasks", []):
        task_id = task.get("id")
        task_label = task.get("label", "")

        # Find relevant categories using expanded keyword mapping
        task_label_lower = task_label.lower()
        relevant_categories = []

        # Keyword mapping from task concepts to category labels
        task_to_categories = {
            "write": ["Writing"],
            "english": ["Writing"],
            "grammar": ["Writing"],
            "copy": ["Writing", "Marketing"],
            "ad": ["Marketing"],
            "organise": ["Productivity"],
            "work": ["Productivity"],
            "task": ["Productivity"],
            "note": ["Productivity"],
            "voice": ["Voice & Video"],
            "video": ["Voice & Video"],
            "podcast": ["Voice & Video"],
            "edit": ["Voice & Video", "Productivity"],
            "editing": ["Voice & Video", "Productivity"],
            "search": ["SEO"],
            "traffic": ["SEO"],
            "seo": ["SEO"],
            "sell": ["Sales", "Marketing"],
            "online": ["Marketing"],
            "course": ["Marketing", "Productivity", "Email Marketing"],
            "website": ["Website Builder", "Hosting"],
            "hosting": ["Hosting"],
            "design": ["Design"],
            "image": ["Image Generation"],
            "email": ["Email Marketing"],
            "automation": ["Automation"],
            "ai": ["AI Assistants"],
            "research": ["Research"],
        }

        matched_cats = set()
        for keyword, cats in task_to_categories.items():
            if keyword in task_label_lower:
                for c in cats:
                    matched_cats.add(c)

        for cat in taxonomy.get("categories", []):
            if cat.get("label", "") in matched_cats:
                relevant_categories.append(cat)

        # Find candidate tools
        candidate_tools = []
        for cat in relevant_categories:
            slug = cat.get("slug", "")
            # Map slug to tools.json category name
            cat_name = cat.get("label", "")
            if cat_name in category_tools:
                for tool_id in category_tools[cat_name]:
                    if tool_id not in candidate_tools:
                        candidate_tools.append(tool_id)

        # Find relevant comparisons
        relevant_comparisons = []
        for tool_id in candidate_tools:
            if tool_id in comparison_map:
                for comp in comparison_map[tool_id]:
                    if comp["vs"] in candidate_tools:
                        relevant_comparisons.append(comp["path"])
        relevant_comparisons = list(set(relevant_comparisons))

        # Find relevant alternatives
        relevant_alternatives = []
        for tool_id in candidate_tools:
            if tool_id in alternatives_map:
                relevant_alternatives.append(alternatives_map[tool_id])

        # Decision questions based on workflow type
        # Order matters: check more specific keywords first to avoid duplicates
        decision_questions = []
        task_lower = task_label.lower()

        # "Edit video or podcasts" — must match before generic "video"
        if "edit" in task_lower and ("video" in task_lower or "podcast" in task_lower):
            decision_questions.extend([
                "Do you need transcript-based editing or timeline editing?",
                "Do you need to remove filler words automatically?",
                "Do you need multi-track audio and video support?"
            ])
        # "Add a voice to videos" — voice generation specifically
        elif "voice" in task_lower:
            decision_questions.extend([
                "Do you need voice cloning or stock voices?",
                "Is this for YouTube, podcasts, or other media?",
                "Do you need editing capabilities?"
            ])
        # "Write ad copy" — must match before generic "write"
        elif "ad" in task_lower and "copy" in task_lower:
            decision_questions.extend([
                "Do you need platform-specific ad formats?",
                "Do you need A/B variant generation?",
                "Is this for social media ads or search ads?"
            ])
        # "Write better English" — general writing
        elif "write" in task_lower:
            decision_questions.extend([
                "Do you need grammar correction or full content generation?",
                "Is this for professional or personal use?",
                "Do you need a free option?"
            ])
        elif "organise" in task_lower or "work" in task_lower:
            decision_questions.extend([
                "Do you need team collaboration or solo use?",
                "Do you prefer notes-first or tasks-first?",
                "Do you need integrations with other tools?"
            ])
        elif "search" in task_lower or "traffic" in task_lower:
            decision_questions.extend([
                "Do you need keyword research, rank tracking, or both?",
                "Are you a beginner or experienced with SEO?",
                "Do you need agency-level features?"
            ])
        # "Launch an online course" — must match before generic "online"
        elif "course" in task_lower:
            decision_questions.extend([
                "Do you need course hosting or just content creation?",
                "Do you need payment processing?",
                "Do you need student management?"
            ])
        # "Sell something online" — e-commerce
        elif "sell" in task_lower or ("online" in task_lower and "website" not in task_lower):
            decision_questions.extend([
                "Do you need a website builder or e-commerce platform?",
                "Do you need hosting included?",
                "What is your expected traffic volume?"
            ])
        elif "website" in task_lower or "hosting" in task_lower:
            decision_questions.extend([
                "Do you need managed hosting or self-hosted?",
                "Do you need a website builder or just a domain?",
                "What is your expected monthly traffic?"
            ])
        else:
            decision_questions.append("What is your primary use case?")

        # Stages
        stages = [
            {"step": 1, "name": "Identify requirements", "description": "Clarify your primary goal and constraints"},
            {"step": 2, "name": "Compare candidates", "description": f"Review {len(candidate_tools)} candidate tools"},
            {"step": 3, "name": "Check alternatives", "description": f"Explore {len(relevant_alternatives)} alternatives pages"},
            {"step": 4, "name": "Make decision", "description": "Choose based on verified evidence"}
        ]

        # Evidence confidence
        evidence_confidence = "low"
        if len(candidate_tools) >= 3 and len(relevant_comparisons) >= 2:
            evidence_confidence = "medium"
        if len(candidate_tools) >= 5 and len(relevant_comparisons) >= 4:
            evidence_confidence = "high"

        # Unresolved gaps
        gaps = []
        if len(candidate_tools) < 2:
            gaps.append("insufficient_candidate_tools")
        if len(relevant_comparisons) < 1:
            gaps.append("no_comparison_pages")
        if len(relevant_alternatives) < 1:
            gaps.append("no_alternatives_pages")

        workflow = {
            "goal_id": task_id,
            "goal_label": task_label,
            "stages": stages,
            "decision_questions": decision_questions,
            "candidate_tools": candidate_tools,
            "candidate_tool_count": len(candidate_tools),
            "relevant_comparisons": relevant_comparisons,
            "comparison_count": len(relevant_comparisons),
            "relevant_alternatives": relevant_alternatives,
            "alternatives_count": len(relevant_alternatives),
            "evidence_confidence": evidence_confidence,
            "unresolved_gaps": gaps
        }

        workflows["workflows"].append(workflow)

    workflows["total_workflows"] = len(workflows["workflows"])

    # Summary
    confidence_counts = {}
    gap_counts = {}
    for w in workflows["workflows"]:
        confidence_counts[w["evidence_confidence"]] = confidence_counts.get(w["evidence_confidence"], 0) + 1
        for gap in w["unresolved_gaps"]:
            gap_counts[gap] = gap_counts.get(gap, 0) + 1

    workflows["summary"] = {
        "confidence_distribution": confidence_counts,
        "gap_distribution": gap_counts,
        "total_candidate_tools": sum(w["candidate_tool_count"] for w in workflows["workflows"]),
        "total_comparisons": sum(w["comparison_count"] for w in workflows["workflows"]),
        "total_alternatives": sum(w["alternatives_count"] for w in workflows["workflows"])
    }

    return workflows


def main():
    print("=== Building Workflow Maps ===\n")
    data = build_workflow_maps()

    output_path = "docs/internal/WORKFLOW-MAPS.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Output: {output_path}")
    print(f"Total workflows: {data['total_workflows']}")
    print()

    summary = data["summary"]
    print("=== Evidence Confidence ===")
    for level, count in sorted(summary["confidence_distribution"].items()):
        print(f"  {level}: {count}")
    print()

    print("=== Unresolved Gaps ===")
    for gap, count in sorted(summary["gap_distribution"].items()):
        print(f"  {gap}: {count}")
    print()

    for w in data["workflows"]:
        print(f"  {w['goal_id']}: {w['candidate_tool_count']} tools, {w['comparison_count']} comparisons, {w['alternatives_count']} alternatives")

    print(f"\n=== Written to {output_path} ===")


if __name__ == "__main__":
    main()
