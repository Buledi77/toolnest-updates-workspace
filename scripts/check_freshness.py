#!/usr/bin/env python3
"""Fail when evidence or records are stale without an explicit stale state."""

import argparse

from decision_graph_common import print_result, validate_freshness


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", help="ISO date used for deterministic checks")
    args = parser.parse_args()
    return print_result("Freshness validation", validate_freshness(args.as_of))


if __name__ == "__main__":
    raise SystemExit(main())
