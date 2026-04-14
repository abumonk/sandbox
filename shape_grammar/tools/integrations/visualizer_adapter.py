"""visualizer_adapter.py — Wrap ``ark graph`` and augment with shape-grammar annotations.

Public API
----------
::

    visualize(ark_path) -> dict

Shells out to ``python ark/ark.py graph <file>`` (the ``ark graph``
subcommand), extracts the embedded JSON blob from the generated HTML, then
augments node entries with shape-grammar semantic labels and terminal counts
derived from the shape-grammar IR.

If Ark's HTML output shape changes (i.e. the ``const DATA =`` blob is absent
or has an unexpected key set), ``AdapterError`` is raised with a hint to
``research/ark-as-host-feasibility.md``.

Subcommand probe result (2026-04-14): ``ark graph`` is available.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict
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

# Keys that must be present in the Ark HTML JSON blob for us to trust the
# output shape.  If Ark's structure diverges, raise AdapterError with the
# feasibility hint.
_EXPECTED_DATA_KEY = "nodes"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_ark_graph(ark_path: Path) -> str:
    """Run ``ark graph`` and return the raw HTML content.

    Raises ``AdapterError`` on non-zero exit or if the CLI is absent.
    """
    if not _ARK_CLI.exists():
        raise AdapterError(
            f"ark CLI not found at {_ARK_CLI}; "
            "see research/ark-as-host-feasibility.md"
        )
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        out_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [sys.executable, str(_ARK_CLI), "graph", str(ark_path), "--out", str(out_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        raise AdapterError(
            f"failed to launch ark graph: {exc}; "
            "see research/ark-as-host-feasibility.md"
        ) from exc

    if result.returncode != 0:
        raise AdapterError(
            f"ark graph exited {result.returncode}: {result.stderr[:500]}; "
            "see research/ark-as-host-feasibility.md"
        )

    try:
        html = out_path.read_text(encoding="utf-8")
    finally:
        out_path.unlink(missing_ok=True)

    return html


def _extract_data_from_html(html: str) -> dict[str, Any]:
    """Parse the ``const DATA = {...};`` JSON blob embedded by ``ark graph``.

    Raises ``AdapterError`` if the blob is absent or malformed.
    """
    match = re.search(r"const DATA = (\{.*?\});\s*\n", html, re.DOTALL)
    if not match:
        raise AdapterError(
            "ark graph HTML output is missing the expected 'const DATA = {...}' "
            "JSON blob; output shape may have changed — "
            "see research/ark-as-host-feasibility.md"
        )
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise AdapterError(
            f"failed to parse ark graph JSON blob: {exc}; "
            "see research/ark-as-host-feasibility.md"
        ) from exc

    if _EXPECTED_DATA_KEY not in data:
        raise AdapterError(
            f"ark graph data blob missing expected key '{_EXPECTED_DATA_KEY}'; "
            "output shape may have changed — "
            "see research/ark-as-host-feasibility.md"
        )

    return data


def _build_semantic_index(ark_path: Path) -> dict[str, Any]:
    """Build a shape-grammar semantic annotation index for the given .ark file.

    Returns a dict keyed by entity/rule name with semantic info.
    Does not raise on IR extraction failure (returns empty dict).
    """
    try:
        ir = extract_ir(ark_path)
        propagated = propagate(ir)
    except IRError:
        return {}

    index: dict[str, Any] = {}

    # Entity-level annotations.
    for entity in propagated.entities:
        index[entity.name] = {
            "kind": entity.kind,
            "sg_type": "entity",
            "field_count": len(entity.fields),
            "invariant_count": len(entity.invariants),
        }

    # Rule-level annotations (populated from example grammars).
    terminal_count = sum(1 for r in propagated.rules if r.is_terminal)
    for rule in propagated.rules:
        index[rule.id] = {
            "kind": "rule",
            "sg_type": "rule",
            "label": rule.label,
            "is_terminal": rule.is_terminal,
            "operation_count": len(rule.operations),
        }

    index["__meta__"] = {
        "source_file": str(ark_path),
        "island_name": propagated.island_name,
        "total_rules": len(propagated.rules),
        "terminal_count": terminal_count,
        "semantic_label_count": len(propagated.semantic_labels),
    }

    return index


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def visualize(ark_path: str | Path) -> dict:
    """Run ``ark graph`` and augment the output with shape-grammar annotations.

    Parameters
    ----------
    ark_path:
        Path to a ``.ark`` file.

    Returns
    -------
    dict
        A dict with keys:
        - ``"ark_data"`` — the raw JSON data blob from Ark's HTML output
          (contains ``"nodes"``, ``"links"``, etc.).
        - ``"sg_annotations"`` — per-node shape-grammar semantic annotations
          keyed by node id.
        - ``"meta"`` — summary metadata (file, node count, terminal count, …).

    Raises
    ------
    AdapterError
        On subprocess failure, non-zero exit, JSON parse error, or if the
        Ark output shape has changed.  The message always contains the string
        ``"see research/ark-as-host-feasibility.md"`` when raised due to an
        unexpected shape change.
    """
    ark_path = Path(ark_path)
    if not ark_path.exists():
        raise AdapterError(f"ark file not found: {ark_path}")

    html = _run_ark_graph(ark_path)
    ark_data = _extract_data_from_html(html)
    sg_index = _build_semantic_index(ark_path)

    nodes: list[dict] = ark_data.get("nodes", [])

    # Augment each node with shape-grammar annotations when available.
    annotated_nodes: list[dict] = []
    for node in nodes:
        node_id = node.get("id", "")
        sg_info = sg_index.get(node_id, {})
        augmented = dict(node)
        if sg_info:
            augmented["sg_label"] = sg_info.get("label") or sg_info.get("kind", "")
            augmented["sg_type"] = sg_info.get("sg_type", "")
            augmented["sg_is_terminal"] = sg_info.get("is_terminal", False)
            augmented["sg_invariant_count"] = sg_info.get("invariant_count", 0)
        annotated_nodes.append(augmented)

    meta = sg_index.get("__meta__", {})
    meta["node_count"] = len(nodes)
    meta["source_file"] = str(ark_path)

    return {
        "ark_data": {**ark_data, "nodes": annotated_nodes},
        "sg_annotations": {k: v for k, v in sg_index.items() if k != "__meta__"},
        "meta": meta,
    }
