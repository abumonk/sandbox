"""CLI entry point for adventure_pipeline.tools.

Usage:
    python -m adventure_pipeline.tools ADV-NNN
    python -m adventure_pipeline.tools ADV-NNN --adventures-root /path/to/adventures
    python -m adventure_pipeline.tools /absolute/path/to/adventure/dir

Prints to_json(extract_ir(...)) to stdout and exits 0.
Writes errors to stderr and exits 2 on bad input / missing directory.
"""

import argparse
import sys

from .ir import extract_ir, to_json


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="adventure_pipeline.tools",
        description="Extract a JSON IR from a live adventure directory.",
    )
    p.add_argument(
        "adventure",
        help="Adventure ID (e.g. ADV-007) or path to adventure directory.",
    )
    p.add_argument(
        "--adventures-root",
        default=None,
        metavar="PATH",
        help=(
            "Root directory containing adventure subdirectories "
            "(default: <repo_root>/.agent/adventures)."
        ),
    )
    args = p.parse_args(argv)
    try:
        ir = extract_ir(args.adventure, args.adventures_root)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(to_json(ir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
