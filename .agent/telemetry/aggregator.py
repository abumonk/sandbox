"""Aggregator module for telemetry metrics.md files.

Public API
----------
parse_rows(metrics_path: Path) -> list[MetricsRow]
    Parse the ``## Agent Runs`` pipe-table from a metrics.md file into
    a list of :class:`~schema.MetricsRow` instances.

recompute_frontmatter(metrics_path: Path) -> None
    Derive aggregate totals from all rows and atomically rewrite the YAML
    frontmatter via ``os.replace()``.  Idempotent: running twice produces
    byte-identical output.

format_duration(seconds: int) -> str
    Render an integer number of seconds as a human-friendly string
    (e.g. ``"16min"``, ``"95s"``, ``"2h 15min"``).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from .errors import AggregationError
from .schema import MetricsRow

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical key order for the metrics.md frontmatter.
_FRONTMATTER_KEY_ORDER = [
    "adventure_id",
    "total_tokens_in",
    "total_tokens_out",
    "total_duration",
    "total_cost",
    "agent_runs",
]

# Regex to strip leading tilde from approximate numeric values (e.g. "~45000").
_RE_TILDE = re.compile(r"^~")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def format_duration(seconds: int) -> str:
    """Render *seconds* as a human-friendly duration string.

    Rules:
    - ``seconds < 120``: ``"Xs"``  (raw seconds, up to 119)
    - ``120 <= seconds < 3600`` with no remainder: ``"Xmin"``
    - ``120 <= seconds < 3600`` with remainder: ``"Xmin Ys"``
    - ``seconds >= 3600`` with zero remaining minutes: ``"Xh"``
    - ``seconds >= 3600`` with remaining minutes: ``"Xh Ymin"``
    """
    if seconds < 0:
        raise AggregationError(f"format_duration requires a non-negative integer, got {seconds}")

    if seconds < 120:
        return f"{seconds}s"

    if seconds < 3600:
        mins = seconds // 60
        secs = seconds % 60
        if secs == 0:
            return f"{mins}min"
        return f"{mins}min {secs}s"

    hours = seconds // 3600
    remaining = seconds % 3600
    mins = remaining // 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}min"


def parse_rows(metrics_path: Path) -> list[MetricsRow]:
    """Parse the ``## Agent Runs`` pipe-table from *metrics_path*.

    Parameters
    ----------
    metrics_path:
        Path to a ``metrics.md`` file containing a YAML frontmatter block
        and a ``## Agent Runs`` section with a pipe-table.

    Returns
    -------
    list[MetricsRow]
        All data rows from the table.

    Raises
    ------
    AggregationError
        On file-not-found, unreadable file, or row parse failure.
    """
    text = _read_file(metrics_path)
    _frontmatter_text, body = _split_frontmatter(text, metrics_path)
    rows = _parse_table(body, metrics_path)
    return rows


def recompute_frontmatter(metrics_path: Path) -> None:
    """Recompute aggregate totals and atomically rewrite the frontmatter.

    Reads all rows via :func:`parse_rows`, derives the five aggregate fields
    (``total_tokens_in``, ``total_tokens_out``, ``total_duration``,
    ``total_cost``, ``agent_runs``), preserves the existing ``adventure_id``,
    and rewrites the frontmatter block in place using an atomic
    ``os.replace()`` (tmp file in the same directory).

    Parameters
    ----------
    metrics_path:
        Path to the ``metrics.md`` file to update.

    Raises
    ------
    AggregationError
        On any file I/O or parse failure.
    """
    metrics_path = Path(metrics_path)
    text = _read_file(metrics_path)
    frontmatter_text, body = _split_frontmatter(text, metrics_path)

    existing_fm = _parse_frontmatter(frontmatter_text)
    adventure_id = existing_fm.get("adventure_id", "")

    rows = _parse_table(body, metrics_path)

    total_tokens_in = sum(r.tokens_in for r in rows)
    total_tokens_out = sum(r.tokens_out for r in rows)
    total_duration = sum(r.duration_s for r in rows)
    total_cost = round(sum(r.cost_usd for r in rows), 4)
    agent_runs = len(rows)

    new_fm_data: dict[str, object] = {
        "adventure_id": adventure_id,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_duration": total_duration,
        "total_cost": total_cost,
        "agent_runs": agent_runs,
    }

    new_frontmatter = _serialize_frontmatter(new_fm_data, _FRONTMATTER_KEY_ORDER)
    new_text = new_frontmatter + body

    _atomic_write(metrics_path, new_text)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Read *path* as UTF-8 text, wrapping errors as :class:`AggregationError`."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise AggregationError(f"metrics file not found: {path}")
    except PermissionError as exc:
        raise AggregationError(f"permission denied reading {path}: {exc}") from exc
    except OSError as exc:
        raise AggregationError(f"error reading {path}: {exc}") from exc


def _split_frontmatter(text: str, path: Path) -> tuple[str, str]:
    """Split *text* into ``(frontmatter_content, body)`` around ``---`` fences.

    ``frontmatter_content`` is the raw text *between* the two fences (no
    leading/trailing ``---``).  ``body`` is everything after the closing
    ``---\\n`` (including the newline separator, if any).

    Raises :class:`AggregationError` if the file does not have a valid
    frontmatter block.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise AggregationError(f"missing opening '---' frontmatter fence in {path}")

    close_idx = None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            close_idx = i
            break

    if close_idx is None:
        raise AggregationError(f"missing closing '---' frontmatter fence in {path}")

    frontmatter_content = "".join(lines[1:close_idx])
    body = "".join(lines[close_idx + 1 :])
    return frontmatter_content, body


def _parse_frontmatter(text: str) -> dict:
    """Parse a YAML-subset frontmatter block (no PyYAML).

    Only handles simple ``key: value`` pairs.  String values are returned as
    strings; integer and float literals are coerced automatically.
    """
    result: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, raw_value = line.partition(":")
        key = key.strip()
        value_str = raw_value.strip()
        # Remove optional surrounding quotes
        if (value_str.startswith('"') and value_str.endswith('"')) or (
            value_str.startswith("'") and value_str.endswith("'")
        ):
            result[key] = value_str[1:-1]
            continue
        # Try int
        try:
            result[key] = int(value_str)
            continue
        except ValueError:
            pass
        # Try float
        try:
            result[key] = float(value_str)
            continue
        except ValueError:
            pass
        # Plain string
        result[key] = value_str
    return result


def _serialize_frontmatter(data: dict, key_order: list[str]) -> str:
    """Serialize *data* to a ``---``-fenced YAML-subset block.

    Keys are emitted in *key_order*; any extra keys in *data* not listed in
    *key_order* are appended alphabetically.  The returned string starts with
    ``---\\n`` and ends with ``---\\n``.
    """
    lines = ["---\n"]
    emitted = set()
    for key in key_order:
        if key in data:
            lines.append(_format_fm_line(key, data[key]))
            emitted.add(key)
    for key in sorted(data.keys()):
        if key not in emitted:
            lines.append(_format_fm_line(key, data[key]))
    lines.append("---\n")
    return "".join(lines)


def _format_fm_line(key: str, value: object) -> str:
    """Render a single ``key: value`` frontmatter line."""
    if isinstance(value, float):
        # Render floats to 4 decimal places for cost fields.
        return f"{key}: {value:.4f}\n"
    return f"{key}: {value}\n"


def _parse_table(body: str, path: Path) -> list[MetricsRow]:
    """Locate the ``## Agent Runs`` pipe-table in *body* and parse all rows."""
    lines = body.splitlines(keepends=True)

    # Find the "## Agent Runs" header.
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## Agent Runs":
            header_idx = i
            break

    if header_idx is None:
        # No table section — return empty list rather than raising.
        return []

    # Find the first pipe-table header row after the section header.
    table_start = None
    for i in range(header_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_start = i
            break
        # Allow blank lines between section header and table.
        if stripped and not stripped.startswith("|"):
            break

    if table_start is None:
        return []

    # Skip the header row (table_start) and the separator row.
    data_start = table_start + 2  # header + separator

    rows: list[MetricsRow] = []
    for i in range(data_start, len(lines)):
        line = lines[i].rstrip("\r\n")
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("|"):
            break  # End of table

        # Parse the row, handling tilde-prefixed approximate values.
        try:
            row = _parse_row_line(stripped, line_number=i + 1)
        except AggregationError:
            raise
        except Exception as exc:
            raise AggregationError(
                f"failed to parse row at line {i + 1} in {path}: {stripped!r}"
            ) from exc
        rows.append(row)

    return rows


def _parse_row_line(line: str, line_number: int) -> MetricsRow:
    """Parse a single pipe-table data line into a :class:`MetricsRow`.

    Strips tilde prefixes from numeric cells before coercing.  Raises
    :class:`AggregationError` on column count mismatch or type failure.
    """
    parts = line.split("|")
    # parts[0] is "" (before first "|"), parts[-1] is "" (after last "|")
    cells = [p.strip() for p in parts[1:-1]]

    if len(cells) != 12:
        raise AggregationError(
            f"line {line_number}: expected 12 columns, got {len(cells)}: {line!r}"
        )

    run_id = cells[0]
    timestamp = cells[1]
    agent = cells[2]
    task = cells[3]
    model = cells[4]

    def _parse_int(raw: str, col: str) -> int:
        clean = _RE_TILDE.sub("", raw)
        try:
            return int(clean)
        except (ValueError, TypeError):
            raise AggregationError(
                f"line {line_number}: column '{col}' is not a valid integer: {raw!r}"
            )

    def _parse_float(raw: str, col: str) -> float:
        clean = _RE_TILDE.sub("", raw)
        try:
            return float(clean)
        except (ValueError, TypeError):
            raise AggregationError(
                f"line {line_number}: column '{col}' is not a valid float: {raw!r}"
            )

    tokens_in = _parse_int(cells[5], "Tokens In")
    tokens_out = _parse_int(cells[6], "Tokens Out")
    duration_s = _parse_int(cells[7], "Duration (s)")
    turns = _parse_int(cells[8], "Turns")
    cost_usd = _parse_float(cells[9], "Cost (USD)")
    result = cells[10]
    confidence = cells[11]

    return MetricsRow(
        run_id=run_id,
        timestamp=timestamp,
        agent=agent,
        task=task,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        duration_s=duration_s,
        turns=turns,
        cost_usd=cost_usd,
        result=result,
        confidence=confidence,
    )


def _atomic_write(path: Path, content: str) -> None:
    """Write *content* to *path* atomically via a sibling tmp file."""
    tmp_path = path.with_suffix(".md.tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        # Flush and fsync via low-level file handle for durability.
        with open(tmp_path, "r+b") as fh:
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except OSError as exc:
        raise AggregationError(f"atomic write failed for {path}: {exc}") from exc
    finally:
        # Clean up tmp file if replace failed.
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
