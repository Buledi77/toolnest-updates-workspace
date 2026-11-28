#!/usr/bin/env python3
"""Validate Decision Graph records, schemas, references, and publishing rules."""

import re

from decision_graph_common import (
    ROOT,
    validate_change_ledger,
    validate_schema_documents,
    validate_tool_records,
    load_json,
    print_result,
)


def main():
    errors = validate_schema_documents()
    errors.extend(validate_tool_records())
    errors.extend(validate_change_ledger())

    # Expansion-only records are staged for a future catalog expansion and are
    # governed by validate_production_scope.py. They are not production pages.
    reconciliation = ROOT / "data" / "catalog-reconciliation.json"
    expansion = set()
    if reconciliation.is_file():
        expansion = set(load_json(reconciliation).get("expansion_only_tools", []))
    if expansion:
        errors = [
            e for e in errors
            if not any(re.search(rf"\b{re.escape(tid)}\b", e) for tid in expansion)
        ]
    return print_result("Decision Graph validation", errors)


if __name__ == "__main__":
    raise SystemExit(main())
