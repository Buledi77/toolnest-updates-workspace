#!/usr/bin/env python3
"""Validate controlled taxonomy and task-catalog references."""

from decision_graph_common import ROOT, load_json, print_result

TAXONOMY_PATH = ROOT / "data" / "taxonomy" / "taxonomy-v1.json"
TASK_PATH = ROOT / "data" / "recommendations" / "task-catalog.json"


def validate_taxonomy():
    taxonomy = load_json(TAXONOMY_PATH)
    tasks = load_json(TASK_PATH)
    errors = []
    categories = taxonomy.get("categories", [])
    category_slugs = [item.get("slug") for item in categories]
    if len(category_slugs) != len(set(category_slugs)):
        errors.append("taxonomy contains duplicate category slugs")
    if any(not item.get("label") or not item.get("slug") for item in categories):
        errors.append("taxonomy category is missing a slug or label")
    task_ids = [task.get("id") for task in tasks.get("tasks", [])]
    if len(task_ids) != len(set(task_ids)):
        errors.append("task catalog contains duplicate task IDs")
    job_ids = {job.get("id") for job in taxonomy.get("jobs", [])}
    for task in tasks.get("tasks", []):
        if task.get("id") not in job_ids:
            errors.append(f"task {task.get('id')} is not in the canonical job taxonomy")
        if not task.get("guide", "").startswith("/"):
            errors.append(f"task {task.get('id')} has an invalid guide path")
        if not task.get("tool_ids"):
            errors.append(f"task {task.get('id')} has no tool IDs")
    return errors


if __name__ == "__main__":
    raise SystemExit(print_result("Taxonomy validation", validate_taxonomy()))
