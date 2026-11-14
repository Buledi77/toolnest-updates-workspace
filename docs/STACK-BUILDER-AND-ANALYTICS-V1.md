# Stack Builder and Analytics V1

## Stack Builder

`data/stack/stack-builder-v1.json` defines a small, explainable requirement
catalog. `scripts/build_stack.py` ranks only structured category, tag, and use
case fields and returns existing Decision Graph IDs. It never uses affiliate
status, popularity, fabricated ratings, or unsupported testing claims.

The output is an internal foundation. It is not connected to the public
homepage until browser parity, accessibility, consent, and performance QA are
complete.

## Analytics

`data/analytics/event-taxonomy-v1.json` defines the event names and required
fields needed for search, decision, source, stack, correction, and recommendation
measurement. It intentionally excludes raw personal data and does not create a
tracking implementation or change consent behavior.
