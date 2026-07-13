"""Command line entrypoint for public watch-generator patterns."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .patterns.pattern_01_central_display import generate_pattern_01
from .patterns.pattern_02_separate_serial_display import generate_pattern_02
from .patterns.pattern_03_independent_display import generate_pattern_03


GENERATORS = {
    "pattern-01": generate_pattern_01,
    "pattern-02": generate_pattern_02,
    "pattern-03": generate_pattern_03,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ontology-watch")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate", help="generate a certified watch pattern")
    generate.add_argument("pattern", choices=sorted(GENERATORS))
    generate.add_argument("--seed", required=True, type=int)
    generate.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    record = GENERATORS[args.pattern](args.seed, args.output)
    print(json.dumps(record.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
