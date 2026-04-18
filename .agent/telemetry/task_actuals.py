"""Task actuals module for telemetry.

Public API
----------
update(manifest_path: Path, task_id: str) -> None
    Read the adventure's ``metrics.md``, compute actuals for *task_id*,
    and rewrite the matching row in the manifest's ``## Evaluations``
    pipe-table.  All other bytes in the manifest are preserved.
    Atomic write via tmp+``os.replace()``.  No-op (with log warning)
    if no matching row exists.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .aggregator import format_duration, parse_rows
from .errors import AggregationError, TaskActualsError

logger = logging.getLogger(__name__)

# Set of terminal result values -- reference only (caller already checked).
TERMINAL_RESULTS = {"done", "complete", "passed", "ready", "failed", "error"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def update(manifest_path: Path, task_id: str) -> None:
    """Update the actuals columns for *task_id* in *manifest_path*.

    Parameters
    ----------
    manifest_path:
        Path to the adventure's ``manifest.md`` file.  The matching
        ``metrics.md`` is derived as a sibling file in the same directory.
    task_id:
        The task identifier to look up (e.g. ``"ADV010-T009"``).

    Raises
    ------
    TaskActualsError
        On any file I/O, parse, or write failure.
    """
    try:
        manifest_path = Path(manifest_path)

        # Derive metrics.md path as sibling of manifest.
        metrics_path = manifest_path.parent / "metrics.md"

        if not manifest_path.exists():
            raise TaskActualsError(f"Manifest not found: {manifest_path}")
        if not metrics_path.exists():
            raise TaskActualsError(f"Metrics not found: {metrics_path}")

        # Parse all rows from metrics.md.
        try:
            rows = parse_rows(metrics_path)
        except AggregationError as exc:
            raise TaskActualsError(f"Failed to parse metrics: {exc}") from exc

        # Filter to rows for this task.
        matching = [r for r in rows if r.task == task_id]
        if not matching:
            logger.warning(
                "task_actuals: no metrics rows found for task_id=%r in %s",
                task_id,
                metrics_path,
            )
            return

        # Compute actuals.
        actuals = _compute_actuals(matching)

        # Update the manifest row.
        _update_manifest_row(manifest_path, task_id, actuals)

    except TaskActualsError:
        raise
    except Exception as exc:
        raise TaskActualsError(f"Unexpected error in task_actuals.update: {exc}") from exc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _compute_actuals(rows: list) -> dict:
    """Compute aggregated actuals from *rows* (all must share the same task).

    Returns
    -------
    dict with keys:
        ``actual_duration`` (str), ``actual_tokens`` (int), ``actual_cost`` (str).
    """
    actual_duration_s = sum(r.duration_s for r in rows)
    actual_duration = format_duration(actual_duration_s)
    actual_tokens = sum(r.tokens_in + r.tokens_out for r in rows)
    actual_cost = sum(r.cost_usd for r in rows)
    return {
        "actual_duration": actual_duration,
        "actual_tokens": actual_tokens,
        "actual_cost": f"${actual_cost:.4f}",
    }


def _compute_variance(actual_tokens: int, est_tokens_str: str) -> str:
    """Compute signed percentage variance of *actual_tokens* vs *est_tokens_str*.

    Returns ``"--"`` if *est_tokens_str* is missing, non-numeric, or zero.
    Otherwise returns a string like ``"+12%"`` or ``"-8%"``.
    """
    if not est_tokens_str or est_tokens_str == "--":
        return "--"
    # Strip tilde prefix (e.g. "~45000").
    clean = est_tokens_str.lstrip("~").strip()
    try:
        est_tokens = int(clean)
    except (ValueError, TypeError):
        return "--"
    if est_tokens == 0:
        return "--"
    pct = (actual_tokens - est_tokens) / est_tokens * 100
    return f"{pct:+.0f}%"


def _update_manifest_row(manifest_path: Path, task_id: str, actuals: dict) -> None:
    """Rewrite the actuals cells for *task_id* in the manifest's Evaluations table.

    Only the single matched data row is modified; all other content is
    preserved verbatim (including whitespace, blank lines, etc.).
    Atomic write via a sibling ``.md.tmp`` file.

    Raises
    ------
    TaskActualsError
        If the manifest lacks an ``## Evaluations`` section, lacks a
        pipe-table under it, or if the write fails.
    """
    try:
        content = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TaskActualsError(f"Cannot read manifest {manifest_path}: {exc}") from exc

    lines = content.split("\n")

    # 1. Locate the "## Evaluations" header line.
    eval_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## Evaluations":
            eval_idx = i
            break

    if eval_idx is None:
        raise TaskActualsError(f"No ## Evaluations section in {manifest_path}")

    # 2. Find the first pipe-table header row after the section header.
    header_idx = None
    for i in range(eval_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            header_idx = i
            break
        # Allow blank lines; stop on non-blank non-table content.
        if stripped and not stripped.startswith("|"):
            break

    if header_idx is None:
        raise TaskActualsError(
            f"No pipe-table found under ## Evaluations in {manifest_path}"
        )

    # 3. Parse the header row to build a column-index map.
    header_parts = lines[header_idx].split("|")
    # parts[0] is "" (before first "|"), parts[-1] is "" (after last "|")
    header_cells = [c.strip() for c in header_parts[1:-1]]
    col_index: dict[str, int] = {name: idx for idx, name in enumerate(header_cells)}

    required_cols = {"Task", "Est. Tokens", "Actual Duration", "Actual Tokens", "Actual Cost", "Variance"}
    missing = required_cols - col_index.keys()
    if missing:
        raise TaskActualsError(
            f"Evaluations table missing required columns: {missing}"
        )

    # 4. The next line (header_idx + 1) should be the separator row.  Data rows start at header_idx + 2.
    data_start = header_idx + 2

    # 5. Iterate data rows looking for the matching task_id.
    matched = False
    for i in range(data_start, len(lines)):
        stripped = lines[i].strip()
        if not stripped:
            continue
        if not stripped.startswith("|"):
            break  # End of table.

        # Split the row on "|" keeping the full original structure.
        parts = lines[i].split("|")
        # parts[0] = "" (before first "|"), parts[-1] = "" (after last "|")
        # cells starts at index 1.
        cells = parts[1:-1]  # raw (may have leading/trailing spaces)

        task_cell = cells[col_index["Task"]].strip() if col_index["Task"] < len(cells) else ""
        if task_cell != task_id:
            continue

        # Found the matching row.
        est_tokens_str = (
            cells[col_index["Est. Tokens"]].strip()
            if col_index["Est. Tokens"] < len(cells)
            else "--"
        )
        variance = _compute_variance(actuals["actual_tokens"], est_tokens_str)

        # Rewrite the four actuals cells (single-space padding).
        cells[col_index["Actual Duration"]] = f" {actuals['actual_duration']} "
        cells[col_index["Actual Tokens"]] = f" {actuals['actual_tokens']} "
        cells[col_index["Actual Cost"]] = f" {actuals['actual_cost']} "
        cells[col_index["Variance"]] = f" {variance} "

        # Reassemble the row.
        lines[i] = "|" + "|".join(cells) + "|"
        matched = True
        break  # Task IDs are unique in the table.

    if not matched:
        logger.warning(
            "task_actuals: task_id=%r not found in ## Evaluations table of %s",
            task_id,
            manifest_path,
        )
        return

    # 6. Atomic write.
    new_content = "\n".join(lines)
    tmp_path = manifest_path.with_suffix(".md.tmp")
    try:
        tmp_path.write_text(new_content, encoding="utf-8")
        with open(tmp_path, "r+b") as fh:
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, manifest_path)
    except OSError as exc:
        raise TaskActualsError(
            f"Atomic write failed for {manifest_path}: {exc}"
        ) from exc
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
