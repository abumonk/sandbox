"""diff_adapter.py — Wrap ``ark diff`` and augment with rule-tree structural diff.

Public API
----------
::

    diff(ark_path_a, ark_path_b) -> dict

Shells out to ``python ark/ark.py diff <old> <new> --json`` and parses the
JSON array output.  The result is augmented with a rule-tree-level diff
computed from both shape-grammar IRs: which rules were added/removed/modified,
which semantic labels shifted, and which operation sequences changed.

Subcommand probe result (2026-04-14): ``ark diff`` is available and accepts
a ``--json`` flag that emits a JSON array of change objects, each with keys
``change`` (added/removed/modified), ``item_type``, ``name``, and ``details``.

If the JSON output is not a list, or if each item is missing the ``change``
key, ``AdapterError`` is raised with a hint to
``research/ark-as-host-feasibility.md``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from shape_grammar.tools.integrations._errors import AdapterError
from shape_grammar.tools.ir import extract_ir, IRError, IRRule
from shape_grammar.tools.semantic import propagate

# ---------------------------------------------------------------------------
# Locate Ark CLI
# ---------------------------------------------------------------------------

_PKG_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # R:/Sandbox/
_ARK_CLI = _PKG_ROOT / "ark" / "ark.py"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_ark_diff(path_a: Path, path_b: Path) -> list[dict[str, Any]]:
    """Run ``ark diff <a> <b> --json`` and return the parsed JSON list.

    Raises ``AdapterError`` on subprocess failure, non-zero exit, or
    unexpected output shape.
    """
    if not _ARK_CLI.exists():
        raise AdapterError(
            f"ark CLI not found at {_ARK_CLI}; "
            "see research/ark-as-host-feasibility.md"
        )
    try:
        result = subprocess.run(
            [sys.executable, str(_ARK_CLI), "diff", str(path_a), str(path_b), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        raise AdapterError(
            f"failed to launch ark diff: {exc}; "
            "see research/ark-as-host-feasibility.md"
        ) from exc

    if result.returncode != 0:
        raise AdapterError(
            f"ark diff exited {result.returncode}: {result.stderr[:500]}; "
            "see research/ark-as-host-feasibility.md"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AdapterError(
            f"ark diff output is not valid JSON: {exc}; "
            "see research/ark-as-host-feasibility.md"
        ) from exc

    if not isinstance(data, list):
        raise AdapterError(
            f"ark diff JSON output is {type(data).__name__}, expected list; "
            "output shape may have changed — "
            "see research/ark-as-host-feasibility.md"
        )

    # Validate item shape: each entry should have a 'change' key.
    for item in data[:5]:  # sample first five
        if isinstance(item, dict) and "change" not in item:
            raise AdapterError(
                "ark diff output items are missing the 'change' key; "
                "output shape may have changed — "
                "see research/ark-as-host-feasibility.md"
            )

    return data


def _load_ir_safe(ark_path: Path) -> Any:
    """Extract and propagate IR; return propagated IR or None on failure."""
    try:
        ir = extract_ir(ark_path)
        return propagate(ir)
    except IRError:
        return None


def _compute_rule_tree_diff(ir_a: Any, ir_b: Any) -> dict[str, Any]:
    """Compute a structural diff at the rule-tree level between two IRs.

    Compares rules by id and reports added, removed, and modified rules.
    Modifications include: label changes, is_terminal changes, and operation
    count changes.
    """
    rules_a: dict[str, IRRule] = {}
    rules_b: dict[str, IRRule] = {}

    if ir_a is not None:
        rules_a = {r.id: r for r in ir_a.rules}
    if ir_b is not None:
        rules_b = {r.id: r for r in ir_b.rules}

    ids_a = set(rules_a)
    ids_b = set(rules_b)

    added = [
        {"rule_id": rid, "label": rules_b[rid].label, "is_terminal": rules_b[rid].is_terminal}
        for rid in sorted(ids_b - ids_a)
    ]
    removed = [
        {"rule_id": rid, "label": rules_a[rid].label, "is_terminal": rules_a[rid].is_terminal}
        for rid in sorted(ids_a - ids_b)
    ]
    modified = []
    for rid in sorted(ids_a & ids_b):
        ra, rb = rules_a[rid], rules_b[rid]
        changes: list[dict[str, Any]] = []
        if ra.label != rb.label:
            changes.append({"field": "label", "old": ra.label, "new": rb.label})
        if ra.is_terminal != rb.is_terminal:
            changes.append({"field": "is_terminal", "old": ra.is_terminal, "new": rb.is_terminal})
        if len(ra.operations) != len(rb.operations):
            changes.append({
                "field": "operation_count",
                "old": len(ra.operations),
                "new": len(rb.operations),
            })
        if changes:
            modified.append({"rule_id": rid, "changes": changes})

    # Entity-level label changes.
    entities_a: dict[str, str] = {}
    entities_b: dict[str, str] = {}
    if ir_a is not None:
        entities_a = {e.name: e.kind for e in ir_a.entities}
    if ir_b is not None:
        entities_b = {e.name: e.kind for e in ir_b.entities}

    label_shifts: list[dict[str, Any]] = []
    for name in sorted(set(entities_a) & set(entities_b)):
        if entities_a[name] != entities_b[name]:
            label_shifts.append({
                "entity": name,
                "old_kind": entities_a[name],
                "new_kind": entities_b[name],
            })

    return {
        "rules_added": added,
        "rules_removed": removed,
        "rules_modified": modified,
        "label_shifts": label_shifts,
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "modified": len(modified),
            "label_shifts": len(label_shifts),
        },
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def diff(ark_path_a: str | Path, ark_path_b: str | Path) -> dict:
    """Run ``ark diff`` and augment with rule-tree structural diff.

    Parameters
    ----------
    ark_path_a:
        Path to the *old* ``.ark`` file.
    ark_path_b:
        Path to the *new* ``.ark`` file.

    Returns
    -------
    dict
        A dict with keys:
        - ``"ark_changes"`` — the raw change list from Ark's ``--json`` output
          (list of ``{change, item_type, name, details}`` dicts).
        - ``"rule_tree_diff"`` — shape-grammar rule-tree structural diff.
        - ``"meta"`` — summary counts.

    Raises
    ------
    AdapterError
        On subprocess failure, non-zero exit, JSON parse error, or if the
        Ark output shape has changed.  The message always contains the string
        ``"see research/ark-as-host-feasibility.md"`` on shape-change errors.
    """
    path_a = Path(ark_path_a)
    path_b = Path(ark_path_b)

    for p in (path_a, path_b):
        if not p.exists():
            raise AdapterError(f"ark file not found: {p}")

    ark_changes = _run_ark_diff(path_a, path_b)

    ir_a = _load_ir_safe(path_a)
    ir_b = _load_ir_safe(path_b)

    rule_tree_diff = _compute_rule_tree_diff(ir_a, ir_b)

    # Aggregate Ark change counts by change type.
    ark_summary: dict[str, int] = {}
    for item in ark_changes:
        if isinstance(item, dict):
            ctype = item.get("change", "unknown")
            ark_summary[ctype] = ark_summary.get(ctype, 0) + 1

    return {
        "ark_changes": ark_changes,
        "rule_tree_diff": rule_tree_diff,
        "meta": {
            "file_a": str(path_a),
            "file_b": str(path_b),
            "ark_change_count": len(ark_changes),
            "ark_change_summary": ark_summary,
            "rule_tree_summary": rule_tree_diff["summary"],
        },
    }
