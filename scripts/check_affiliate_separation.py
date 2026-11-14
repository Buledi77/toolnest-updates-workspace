#!/usr/bin/env python3
"""Ensure affiliate metadata cannot replace official or editorial data."""

from decision_graph_common import print_result, validate_affiliate_separation


def main():
    return print_result("Affiliate separation validation", validate_affiliate_separation())


if __name__ == "__main__":
    raise SystemExit(main())
