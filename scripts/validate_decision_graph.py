#!/usr/bin/env python3
"""Validate Decision Graph records, schemas, references, and publishing rules."""

from decision_graph_common import (
    validate_change_ledger,
    validate_schema_documents,
    validate_tool_records,
    print_result,
)


def main():
    errors = validate_schema_documents()
    errors.extend(validate_tool_records())
    errors.extend(validate_change_ledger())
    return print_result("Decision Graph validation", errors)


if __name__ == "__main__":
    raise SystemExit(main())
