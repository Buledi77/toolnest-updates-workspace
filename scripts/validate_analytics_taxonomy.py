#!/usr/bin/env python3
"""Validate the internal analytics event contract."""

from decision_graph_common import ROOT, load_json, print_result

EVENTS_PATH = ROOT / "data" / "analytics" / "event-taxonomy-v1.json"


def validate():
    data = load_json(EVENTS_PATH)
    errors = []
    names = [event.get("name") for event in data.get("events", [])]
    if len(names) != len(set(names)):
        errors.append("analytics event names must be unique")
    for event in data.get("events", []):
        if not event.get("name") or not event.get("name").islower():
            errors.append(f"invalid event name {event.get('name')}")
        if not isinstance(event.get("required"), list) or not event["required"]:
            errors.append(f"{event.get('name')}: required fields are missing")
    return errors


if __name__ == "__main__":
    raise SystemExit(print_result("Analytics taxonomy validation", validate()))
