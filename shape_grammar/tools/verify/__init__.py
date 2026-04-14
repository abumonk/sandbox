"""shape_grammar.tools.verify — Z3-backed verifier passes for shape grammars.

Three passes, each consuming a `ShapeGrammarIR` and returning a `Result`:

  termination  -- derivation depth bounded by max_depth (Z3 UNSAT proof).
  determinism  -- same seed => same output; no wall-clock / env / unordered.
  scope        -- every scope.get(attr) has attr defined on every path.

CLI:
    python -m shape_grammar.tools.verify {termination|determinism|scope|all} <file.ark>

Exit codes:
    0  -- PASS or PASS_OPAQUE (all passes green / conservatively safe).
    1  -- FAIL (at least one pass found a violation; counterexample printed).
    2  -- PASS_UNKNOWN (Z3 timeout) or IR load error.
"""

from __future__ import annotations

import enum
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class Status(enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PASS_OPAQUE = "PASS_OPAQUE"
    PASS_UNKNOWN = "PASS_UNKNOWN"


@dataclass
class Result:
    """Verifier pass result."""

    status: Status
    message: str = ""
    counterexample: Optional[Any] = None

    @property
    def is_ok(self) -> bool:
        """True when the pass did not find a violation (PASS or PASS_OPAQUE)."""
        return self.status in (Status.PASS, Status.PASS_OPAQUE)

    @property
    def exit_code(self) -> int:
        if self.status == Status.FAIL:
            return 1
        if self.status == Status.PASS_UNKNOWN:
            return 2
        return 0


# ---------------------------------------------------------------------------
# Pass registry (lazy import to avoid circular imports)
# ---------------------------------------------------------------------------

_PASS_NAMES = ("termination", "determinism", "scope")


def run_termination(ir) -> Result:
    from . import termination  # noqa: PLC0415
    return termination.run(ir)


def run_determinism(ir) -> Result:
    from . import determinism  # noqa: PLC0415
    return determinism.run(ir)


def run_scope(ir) -> Result:
    from . import scope as _scope  # noqa: PLC0415
    return _scope.run(ir)


def run_all(ir) -> dict[str, Result]:
    """Run all three passes and return a mapping of name -> Result."""
    return {
        "termination": run_termination(ir),
        "determinism": run_determinism(ir),
        "scope": run_scope(ir),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_USAGE = (
    "usage: python -m shape_grammar.tools.verify "
    "{termination|determinism|scope|all} <file.ark>"
)

_DISPATCH = {
    "termination": run_termination,
    "determinism": run_determinism,
    "scope": run_scope,
}


def _cli_main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(_USAGE, file=sys.stderr)
        return 2

    subcommand = argv[1].lower()
    ark_file = argv[2]

    # Load IR — import here to avoid circular dep.
    from ..ir import extract_ir, IRError  # noqa: PLC0415

    try:
        ir = extract_ir(ark_file)
    except IRError as exc:
        print(f"ERROR loading IR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if subcommand == "all":
        results = run_all(ir)
        worst_exit = 0
        for name, result in results.items():
            tag = result.status.value
            print(f"  {name:15s} {tag}")
            if result.message:
                print(f"               {result.message}")
            if result.counterexample:
                print(f"               counterexample: {json.dumps(result.counterexample, default=str)}")
            if result.exit_code > worst_exit:
                worst_exit = result.exit_code
        return worst_exit

    if subcommand not in _DISPATCH:
        print(f"unknown subcommand: {subcommand!r}", file=sys.stderr)
        print(_USAGE, file=sys.stderr)
        return 2

    result = _DISPATCH[subcommand](ir)
    tag = result.status.value
    print(f"[{tag}] {subcommand}: {result.message}")
    if result.counterexample:
        print(f"counterexample: {json.dumps(result.counterexample, default=str)}")
    return result.exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli_main(sys.argv))
