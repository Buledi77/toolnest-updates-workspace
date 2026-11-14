#!/usr/bin/env python3
"""Validate evidence sources, claims, dates, currencies, and references."""

from decision_graph_common import print_result, validate_ledger_shape


def main():
    return print_result("Evidence ledger validation", validate_ledger_shape())


if __name__ == "__main__":
    raise SystemExit(main())
