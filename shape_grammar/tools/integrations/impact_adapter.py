"""impact_adapter.py — Wrap ``ark impact`` and augment with rule-tree edges.

Public API
----------
::

    impact(ark_path, entity_name="") -> dict

Shells out to ``python ark/ark.py impact <file> <entity>`` and parses the
text output.  The result is augmented with rule-tree impact edges derived
from the shape-grammar IR: any rule that references ``entity_name`` (directly
or transitively via its operations or lhs symbol) is reported as an additional
impact edge.

Subcommand probe result (2026-04-14): ``ark impact`` is available but does
**not** accept a ``--json`` flag — output is human-readable text.  The adapter
parses the text format into a structured dict.  If the text format changes in
a way that breaks parsing, ``AdapterError`` is raised with a hint to
``research/ark-as-host-feasibility.md``.

If ``entity_name`` is omitted, the adapter runs impact analysis on the island
entity (from ``ir.island_name``) or falls back to ``"ShapeGrammar"``.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from shape_grammar.tools.integrations._errors import AdapterError
from shape_grammar.tools.ir import extract_ir, IRError
from shape_grammar.tools.semantic import propagate

# ---------------------------------------------------------------------------
# Locate Ark CLI
# ---------------------------------------------------------------------------

_PKG_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # R:/Sandbox/
_ARK_CLI = _PKG_ROOT / "ark" / "ark.py"

# Sentinel line that Ark always emits to open an impact block.
_IMPACT_HEADER_RE = re.compile(r"Impact Analysis:\s*(.+)")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_ark_impact(ark_path: Path, entity_name: str) -> str:
    """Run ``ark impact <file> <entity>`` and return stdout text.

    Raises ``AdapterError`` on subprocess failure or non-zero exit.
    """
    if not _ARK_CLI.exists():
        raise AdapterError(
            f"ark CLI not found at {_ARK_CLI}; "
            "see research/ark-as-host-feasibility.md"
        )
    try:
        result = subprocess.run(
            [sys.executable, str(_ARK_CLI), "impact", str(ark_path), entity_name],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        raise AdapterError(
            f"failed to launch ark impact: {exc}; "
            "see research/ark-as-host-feasibility.md"
        ) from exc

    if result.returncode != 0:
        raise AdapterError(
            f"ark impact exited {result.returncode}: {result.stderr[:500]}; "
            "see research/ark-as-host-feasibility.md"
        )

    return result.stdout


def _parse_impact_text(text: str, entity_name: str) -> dict[str, Any]:
    """Parse Ark's text-format impact output into a structured dict.

    Expected sections (any subset may be absent):
      - Islands Affected:   → <name> (<reason>)
      - Code Regeneration:  → <name> [<target>]
      - Dependencies:       → <name>

    If the text doesn't contain the expected header, raises ``AdapterError``
    with a feasibility hint (output shape may have changed).
    """
    if not text.strip():
        # Empty output is acceptable when Ark finds nothing.
        return {
            "entity": entity_name,
            "islands_affected": [],
            "code_regen": [],
            "dependencies": [],
            "raw": text,
        }

    # Validate header presence — if absent the format has changed.
    header_match = _IMPACT_HEADER_RE.search(text)
    if not header_match:
        raise AdapterError(
            "ark impact output is missing the expected 'Impact Analysis:' header; "
            "output shape may have changed — "
            "see research/ark-as-host-feasibility.md"
        )

    islands: list[str] = []
    code_regen: list[str] = []
    dependencies: list[str] = []

    current_section: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if "Islands Affected:" in stripped:
            current_section = "islands"
        elif "Code Regeneration:" in stripped:
            current_section = "code_regen"
        elif "Dependencies:" in stripped:
            current_section = "dependencies"
        elif stripped.startswith("→"):
            item = stripped.lstrip("→ ").strip()
            if current_section == "islands":
                islands.append(item)
            elif current_section == "code_regen":
                code_regen.append(item)
            elif current_section == "dependencies":
                dependencies.append(item)

    return {
        "entity": entity_name,
        "islands_affected": islands,
        "code_regen": code_regen,
        "dependencies": dependencies,
        "raw": text,
    }


def _rule_tree_edges(ark_path: Path, entity_name: str) -> list[dict[str, Any]]:
    """Compute rule-tree impact edges from the shape-grammar IR.

    Returns a list of dicts describing which rules reference ``entity_name``
    directly (via lhs or operations).  Returns empty list on IR failure.
    """
    try:
        ir = extract_ir(ark_path)
        propagated = propagate(ir)
    except IRError:
        return []

    edges: list[dict[str, Any]] = []
    entity_lower = entity_name.lower()

    for rule in propagated.rules:
        # Direct lhs reference.
        if rule.lhs and entity_name and (
            rule.lhs == entity_name or entity_lower in rule.lhs.lower()
        ):
            edges.append({
                "rule_id": rule.id,
                "edge_type": "lhs_reference",
                "label": rule.label,
                "is_terminal": rule.is_terminal,
            })
            continue

        # Operation-level reference.
        for op in rule.operations:
            op_str = str(op).lower()
            if entity_name and entity_lower in op_str:
                edges.append({
                    "rule_id": rule.id,
                    "edge_type": "operation_reference",
                    "label": rule.label,
                    "is_terminal": rule.is_terminal,
                })
                break

    return edges


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def impact(ark_path: str | Path, entity_name: str = "") -> dict:
    """Run ``ark impact`` and augment with shape-grammar rule-tree edges.

    Parameters
    ----------
    ark_path:
        Path to a ``.ark`` file.
    entity_name:
        The entity to analyse.  If empty, the adapter uses the island name
        from the extracted IR, or falls back to ``"ShapeGrammar"``.

    Returns
    -------
    dict
        A dict with keys:
        - ``"entity"`` — entity name analysed.
        - ``"islands_affected"`` — list of island strings from Ark's output.
        - ``"code_regen"`` — list of code-regen strings from Ark's output.
        - ``"dependencies"`` — list of dependency strings from Ark's output.
        - ``"rule_tree_edges"`` — shape-grammar rule-tree impact edges.
        - ``"raw"`` — raw Ark text output.
        - ``"meta"`` — summary counts.

    Raises
    ------
    AdapterError
        On subprocess failure, non-zero exit, or unexpected output shape.
    """
    ark_path = Path(ark_path)
    if not ark_path.exists():
        raise AdapterError(f"ark file not found: {ark_path}")

    # Resolve entity name if not provided.
    if not entity_name:
        try:
            ir = extract_ir(ark_path)
            entity_name = ir.island_name or "ShapeGrammar"
        except IRError:
            entity_name = "ShapeGrammar"

    raw_text = _run_ark_impact(ark_path, entity_name)
    parsed = _parse_impact_text(raw_text, entity_name)

    # Augment with rule-tree edges from the shape-grammar IR.
    rule_edges = _rule_tree_edges(ark_path, entity_name)
    parsed["rule_tree_edges"] = rule_edges

    parsed["meta"] = {
        "source_file": str(ark_path),
        "entity": entity_name,
        "islands_affected_count": len(parsed["islands_affected"]),
        "rule_tree_edge_count": len(rule_edges),
    }

    return parsed
