"""obj_writer.py — Wavefront OBJ writer for shape-grammar terminals.

Converts a list of `Terminal` leaf nodes (from `tools/evaluator.py`) into a
Wavefront OBJ file with one ``g <label>`` group per distinct semantic label.
Each terminal is rendered as a unit-cube-sized axis-aligned box, positioned
by ``scope.translation`` and sized by ``scope.size`` (falls back to
``scope.scale`` when all size components are zero).

No third-party dependencies. Text is emitted with ``\n`` line endings in
binary-safe mode (``open(..., "w", newline="\n")`` is not universally
available; we write via bytes with explicit ``\n``).

CLI
---
::

    python -m shape_grammar.tools.obj_writer <terminals.json> --out <file.obj>

The JSON input must be a list of terminal dicts serialisable from
``dataclasses.asdict(terminal)``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from shape_grammar.tools.evaluator import Terminal
from shape_grammar.tools.scope import Scope


# ---------------------------------------------------------------------------
# Label sanitisation
# ---------------------------------------------------------------------------

_LABEL_RE = re.compile(r"[^\w\-.]")


def _sanitise_label(label: Optional[str]) -> str:
    """Convert a semantic label to a safe OBJ group name.

    Returns ``"default"`` for empty/None labels. Replaces any character that
    is not alphanumeric, ``-``, or ``.`` with ``_``.
    """
    if not label:
        return "default"
    sanitised = _LABEL_RE.sub("_", label.strip())
    return sanitised or "default"


# ---------------------------------------------------------------------------
# Cube geometry helpers
# ---------------------------------------------------------------------------

def _cube_vertices(tx: float, ty: float, tz: float,
                   sx: float, sy: float, sz: float) -> list[tuple[float, float, float]]:
    """Return 8 vertices of an axis-aligned box.

    The box origin is ``(tx, ty, tz)`` and its extents are ``(sx, sy, sz)``.
    Vertex order (0-indexed):
      0: (tx,    ty,    tz   )
      1: (tx+sx, ty,    tz   )
      2: (tx+sx, ty+sy, tz   )
      3: (tx,    ty+sy, tz   )
      4: (tx,    ty,    tz+sz)
      5: (tx+sx, ty,    tz+sz)
      6: (tx+sx, ty+sy, tz+sz)
      7: (tx,    ty+sy, tz+sz)
    """
    return [
        (tx,       ty,       tz      ),
        (tx + sx,  ty,       tz      ),
        (tx + sx,  ty + sy,  tz      ),
        (tx,       ty + sy,  tz      ),
        (tx,       ty,       tz + sz ),
        (tx + sx,  ty,       tz + sz ),
        (tx + sx,  ty + sy,  tz + sz ),
        (tx,       ty + sy,  tz + sz ),
    ]


# 6 quad faces of a unit cube, using 1-based vertex offsets relative to the
# first vertex of this terminal's block in the OBJ file.
_CUBE_FACES: list[tuple[int, int, int, int]] = [
    (1, 2, 3, 4),   # bottom  (−Z)
    (5, 6, 7, 8),   # top     (+Z)
    (1, 2, 6, 5),   # front   (−Y)
    (4, 3, 7, 8),   # back    (+Y)
    (1, 4, 8, 5),   # left    (−X)
    (2, 3, 7, 6),   # right   (+X)
]


# ---------------------------------------------------------------------------
# Core writer
# ---------------------------------------------------------------------------


def write_obj(terminals: list[Terminal], path: "str | Path",
              seed: Optional[int] = None) -> None:
    """Write a Wavefront OBJ file from a list of Terminal nodes.

    Parameters
    ----------
    terminals:
        List of `Terminal` instances produced by `evaluate()`.
    path:
        Destination file path. Parent directories are created if needed.
    seed:
        Optional seed integer that was used during evaluation — written to
        the header comment for traceability.

    File structure
    --------------
    - Header comment block with generation timestamp and seed.
    - One ``g <label>`` group per distinct semantic label in encounter order.
    - Within each group: 8 ``v`` lines then 6 ``f`` lines per terminal.
    - Empty ``terminals`` list produces a file with just the header comment.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect lines to write.
    lines: list[str] = []

    # --- Header ---
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append(f"# shape_grammar OBJ output")
    lines.append(f"# generated: {timestamp}")
    if seed is not None:
        lines.append(f"# seed: {seed}")
    lines.append(f"# terminals: {len(terminals)}")
    lines.append("")

    if not terminals:
        # Empty terminal list — write header only (file is still non-empty).
        _write_lines(out_path, lines)
        return

    # Group terminals by label (preserve encounter order for groups).
    from collections import OrderedDict
    groups: "OrderedDict[str, list[Terminal]]" = OrderedDict()
    for t in terminals:
        key = _sanitise_label(t.label)
        if key not in groups:
            groups[key] = []
        groups[key].append(t)

    # Global vertex counter (OBJ uses absolute 1-based indices).
    vertex_offset = 1

    for group_name, group_terminals in groups.items():
        lines.append(f"g {group_name}")

        for t in group_terminals:
            # Resolve position and size from scope.
            tx, ty, tz = t.scope.translation
            sx, sy, sz = t.scope.size

            # Fall back to scale when size is zero (unit cube by default).
            if sx == 0.0 and sy == 0.0 and sz == 0.0:
                sx, sy, sz = t.scope.scale
                # If scale is also zero/one-unit default, use 1.0 cube.
                if sx == 0.0 or sy == 0.0 or sz == 0.0:
                    sx, sy, sz = 1.0, 1.0, 1.0

            verts = _cube_vertices(tx, ty, tz, sx, sy, sz)

            # Emit comment for traceability.
            lines.append(f"# terminal tag={t.tag!r} label={t.label!r}")

            # Emit vertices.
            for vx, vy, vz in verts:
                lines.append(f"v {vx:.6f} {vy:.6f} {vz:.6f}")

            # Emit faces (absolute 1-based indices).
            for a, b, c, d in _CUBE_FACES:
                i0 = vertex_offset + a - 1
                i1 = vertex_offset + b - 1
                i2 = vertex_offset + c - 1
                i3 = vertex_offset + d - 1
                lines.append(f"f {i0} {i1} {i2} {i3}")

            vertex_offset += 8
            lines.append("")

    _write_lines(out_path, lines)


def _write_lines(path: Path, lines: list[str]) -> None:
    """Write lines to *path* using binary mode with explicit ``\\n`` endings."""
    content = "\n".join(lines) + "\n"
    path.write_bytes(content.encode("utf-8"))


# ---------------------------------------------------------------------------
# CLI __main__
# ---------------------------------------------------------------------------


def _cli_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m shape_grammar.tools.obj_writer",
        description="Write a Wavefront OBJ file from terminal JSON.",
    )
    parser.add_argument(
        "terminals_json",
        help="Path to a JSON file containing a list of terminal dicts "
             "(as produced by dataclasses.asdict on Terminal instances). "
             "Pass '-' to read from stdin.",
    )
    parser.add_argument("--out", default="/tmp/shape_grammar_out.obj",
                        help="Output OBJ path (default: /tmp/shape_grammar_out.obj)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed used during evaluation (written to header comment).")
    args = parser.parse_args(argv[1:])

    # Load terminal dicts.
    try:
        if args.terminals_json == "-":
            raw = json.load(sys.stdin)
        else:
            with open(args.terminals_json, encoding="utf-8") as fh:
                raw = json.load(fh)
    except Exception as exc:
        print(f"ERROR loading terminals JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(raw, list):
        print("ERROR: terminals JSON must be a list", file=sys.stderr)
        return 1

    # Reconstruct Terminal instances from dicts.
    terminals: list[Terminal] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        scope_d = item.get("scope", {})
        scope = Scope(
            translation=tuple(scope_d.get("translation", (0.0, 0.0, 0.0))),
            rotation=tuple(scope_d.get("rotation", (0.0, 0.0, 0.0))),
            scale=tuple(scope_d.get("scale", (1.0, 1.0, 1.0))),
            size=tuple(scope_d.get("size", (0.0, 0.0, 0.0))),
            attrs=tuple(scope_d.get("attrs", [])),
        )
        terminals.append(Terminal(
            scope=scope,
            tag=item.get("tag", ""),
            label=item.get("label", ""),
            provenance=item.get("provenance", []),
        ))

    write_obj(terminals, args.out, seed=args.seed)
    print(f"OK: wrote {len(terminals)} terminal(s) -> {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli_main(sys.argv))
