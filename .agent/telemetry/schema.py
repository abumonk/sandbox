"""Schema dataclasses, validator, row builder, and pipe-table serializer.

Public API
----------
validate_event(payload: dict) -> SubagentEvent
    Validate a raw hook payload dict.  Raises ``PayloadError`` for any of the
    10 documented rejection cases.

build_row(event: SubagentEvent, cost: float) -> MetricsRow
    Construct a ``MetricsRow`` from a validated event and a pre-computed cost.
    Run ID is the first 12 hex characters of the SHA-1 of the canonical key.

serialize(row: MetricsRow) -> str
    Render a ``MetricsRow`` as a pipe-separated table line (no trailing newline).

parse_row(line: str) -> MetricsRow
    Parse a pipe-separated table line back into a ``MetricsRow``.
    Raises ``SchemaError`` on column count mismatch or type coercion failure.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Optional

from .cost_model import known_models, normalize_model
from .errors import PayloadError, SchemaError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_EVENT_TYPES = {"SubagentStop", "PostToolUse"}
VALID_RESULTS = {"complete", "ready", "done", "passed", "failed", "error"}
VALID_CONFIDENCE = {"high", "medium", "low", "estimated"}

RE_ADVENTURE_ID = re.compile(r"^ADV-\d{3}$")
RE_TASK_ID = re.compile(r"^ADV\d{3}-T\d{3}$")
RE_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
RE_RUN_ID = re.compile(r"^[0-9a-f]{12}$")

# Fixed-order column headers matching row_schema.md
ROW_COLUMNS = (
    "Run ID",
    "Timestamp",
    "Agent",
    "Task",
    "Model",
    "Tokens In",
    "Tokens Out",
    "Duration (s)",
    "Turns",
    "Cost (USD)",
    "Result",
    "Confidence",
)

ROW_HEADER = "| " + " | ".join(ROW_COLUMNS) + " |"
ROW_SEPARATOR = "| " + " | ".join("---" for _ in ROW_COLUMNS) + " |"

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubagentEvent:
    """Validated, normalized representation of a subagent hook payload."""

    event_type: str
    timestamp: str
    adventure_id: str
    agent: str
    task: Optional[str]
    model: str          # normalized canonical short name (opus/sonnet/haiku)
    tokens_in: int
    tokens_out: int
    duration_ms: int
    turns: int
    result: str
    session_id: Optional[str] = None


@dataclass(frozen=True)
class MetricsRow:
    """One data row in the ``## Agent Runs`` pipe-table of a ``metrics.md``."""

    run_id: str          # 12 lowercase hex chars
    timestamp: str
    agent: str
    task: str            # task ID or literal "-"
    model: str
    tokens_in: int
    tokens_out: int
    duration_s: int      # max(1, round(duration_ms / 1000))
    turns: int
    cost_usd: float      # pinned at write time, formatted to 4dp
    result: str
    confidence: str      # "high" for hook-written rows


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def validate_event(payload: dict) -> SubagentEvent:
    """Validate *payload* and return a frozen :class:`SubagentEvent`.

    Exactly 10 rejection cases raise :class:`~errors.PayloadError`:

    1.  ``event_type`` missing or not in ``VALID_EVENT_TYPES``
    2.  ``timestamp`` missing or does not match ``YYYY-MM-DDTHH:MM:SSZ``
    3.  ``adventure_id`` missing or does not match ``^ADV-\\d{3}$``
    4.  ``agent`` missing or empty
    5.  ``model`` missing or not a recognised model identifier
    6.  ``tokens_in`` missing or not a non-negative integer
    7.  ``tokens_out`` missing or not a non-negative integer
    8.  ``duration_ms`` missing or not a positive integer (> 0)
    9.  ``turns`` missing or not a non-negative integer
    10. ``task`` is present but does not match ``^ADV\\d{3}-T\\d{3}$``

    ``result`` is validated against ``VALID_RESULTS`` (raises ``PayloadError``
    but is not counted among the 10 named cases above).
    """
    if not isinstance(payload, dict):
        raise PayloadError("payload must be a dict")

    # Case 1: event_type
    event_type = payload.get("event_type")
    if event_type not in VALID_EVENT_TYPES:
        raise PayloadError(
            f"missing or invalid event_type: {event_type!r}; "
            f"expected one of {sorted(VALID_EVENT_TYPES)}"
        )

    # Case 2: timestamp
    timestamp = payload.get("timestamp")
    if not isinstance(timestamp, str) or not RE_TIMESTAMP.match(timestamp):
        raise PayloadError(
            f"missing or invalid timestamp: {timestamp!r}; "
            "expected YYYY-MM-DDTHH:MM:SSZ"
        )

    # Case 3: adventure_id
    adventure_id = payload.get("adventure_id")
    if not isinstance(adventure_id, str) or not RE_ADVENTURE_ID.match(adventure_id):
        raise PayloadError(
            f"missing or invalid adventure_id: {adventure_id!r}; "
            "expected pattern ADV-NNN"
        )

    # Case 4: agent
    agent = payload.get("agent")
    if not isinstance(agent, str) or not agent.strip():
        raise PayloadError(
            f"missing or empty agent: {agent!r}"
        )

    # Case 5: model
    model_raw = payload.get("model")
    if not isinstance(model_raw, str) or model_raw not in known_models():
        raise PayloadError(
            f"missing or unknown model: {model_raw!r}; "
            f"expected one of the known model identifiers"
        )
    model = normalize_model(model_raw)

    # Case 6: tokens_in
    tokens_in = payload.get("tokens_in")
    if not isinstance(tokens_in, int) or isinstance(tokens_in, bool) or tokens_in < 0:
        raise PayloadError(
            f"tokens_in must be a non-negative integer, got: {tokens_in!r}"
        )

    # Case 7: tokens_out
    tokens_out = payload.get("tokens_out")
    if not isinstance(tokens_out, int) or isinstance(tokens_out, bool) or tokens_out < 0:
        raise PayloadError(
            f"tokens_out must be a non-negative integer, got: {tokens_out!r}"
        )

    # Case 8: duration_ms
    duration_ms = payload.get("duration_ms")
    if not isinstance(duration_ms, int) or isinstance(duration_ms, bool) or duration_ms <= 0:
        raise PayloadError(
            f"duration_ms must be a positive integer (> 0), got: {duration_ms!r}"
        )

    # Case 9: turns
    turns = payload.get("turns")
    if not isinstance(turns, int) or isinstance(turns, bool) or turns < 0:
        raise PayloadError(
            f"turns must be a non-negative integer, got: {turns!r}"
        )

    # Case 10: task (optional, but if present must match pattern)
    task_raw = payload.get("task")
    if task_raw is not None:
        if not isinstance(task_raw, str) or not RE_TASK_ID.match(task_raw):
            raise PayloadError(
                f"task is present but does not match ADV###-T### pattern: {task_raw!r}"
            )
    task: Optional[str] = task_raw

    # result: additional check (not counted among the 10)
    result = payload.get("result")
    if result not in VALID_RESULTS:
        raise PayloadError(
            f"invalid result: {result!r}; expected one of {sorted(VALID_RESULTS)}"
        )

    # session_id: optional, no format constraint
    session_id: Optional[str] = payload.get("session_id")
    if session_id is not None and not isinstance(session_id, str):
        session_id = str(session_id)

    return SubagentEvent(
        event_type=event_type,
        timestamp=timestamp,
        adventure_id=adventure_id,
        agent=agent.strip(),
        task=task,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        duration_ms=duration_ms,
        turns=turns,
        result=result,
        session_id=session_id,
    )


# ---------------------------------------------------------------------------
# Row builder
# ---------------------------------------------------------------------------


def build_row(event: SubagentEvent, cost: float) -> MetricsRow:
    """Build a :class:`MetricsRow` from a validated event and pre-computed cost.

    Parameters
    ----------
    event:
        A validated :class:`SubagentEvent` (from :func:`validate_event`).
    cost:
        USD cost as returned by ``cost_model.cost_for()``.  The caller is
        responsible for computing this value; ``schema.py`` does not call
        ``cost_for`` itself so that it remains decoupled from cost computation.

    Returns
    -------
    MetricsRow
        Frozen row with a deterministic 12-hex-char Run ID.
    """
    task_str = event.task or "-"

    canonical_key = (
        f"{event.adventure_id}|{event.agent}|{task_str}"
        f"|{event.model}|{event.timestamp}|{event.session_id or ''}"
    )
    run_id = hashlib.sha1(canonical_key.encode()).hexdigest()[:12]

    duration_s = max(1, round(event.duration_ms / 1000))

    return MetricsRow(
        run_id=run_id,
        timestamp=event.timestamp,
        agent=event.agent,
        task=task_str,
        model=event.model,
        tokens_in=event.tokens_in,
        tokens_out=event.tokens_out,
        duration_s=duration_s,
        turns=event.turns,
        cost_usd=cost,
        result=event.result,
        confidence="high",
    )


# ---------------------------------------------------------------------------
# Serializer / parser
# ---------------------------------------------------------------------------


def serialize(row: MetricsRow) -> str:
    """Render *row* as a pipe-separated table line (no trailing newline).

    ``cost_usd`` is formatted to exactly 4 decimal places.  All other fields
    use their natural ``str()`` representation.  The line matches the format
    produced by the ``ROW_HEADER`` / ``ROW_SEPARATOR`` constants above.
    """
    cells = [
        row.run_id,
        row.timestamp,
        row.agent,
        row.task,
        row.model,
        str(row.tokens_in),
        str(row.tokens_out),
        str(row.duration_s),
        str(row.turns),
        f"{row.cost_usd:.4f}",
        row.result,
        row.confidence,
    ]
    return "| " + " | ".join(cells) + " |"


def parse_row(line: str) -> MetricsRow:
    """Parse a pipe-separated table line into a :class:`MetricsRow`.

    Parameters
    ----------
    line:
        A data line from an ``## Agent Runs`` pipe-table, e.g.::

            | a1b2c3d4e5f6 | 2026-04-15T01:23:45Z | ... |

    Returns
    -------
    MetricsRow

    Raises
    ------
    SchemaError
        If the line does not contain exactly 12 data cells, or if any numeric
        cell cannot be coerced to the expected type.
    """
    # Split on "|" and drop the leading/trailing empty strings produced by the
    # outer pipe characters.
    parts = line.split("|")
    # parts[0] is "" (before first "|"), parts[-1] is "" (after last "|")
    cells = [p.strip() for p in parts[1:-1]]

    if len(cells) != 12:
        raise SchemaError(
            f"expected 12 columns, got {len(cells)}: {line!r}"
        )

    run_id, timestamp, agent, task, model = cells[0], cells[1], cells[2], cells[3], cells[4]

    # Validate Run ID format
    if not RE_RUN_ID.match(run_id):
        raise SchemaError(
            f"column 'Run ID' is not a 12-hex-char string: {run_id!r}"
        )

    # Integer columns: tokens_in, tokens_out, duration_s, turns
    int_columns = {
        "Tokens In": cells[5],
        "Tokens Out": cells[6],
        "Duration (s)": cells[7],
        "Turns": cells[8],
    }
    coerced_ints: dict[str, int] = {}
    for col_name, raw in int_columns.items():
        try:
            coerced_ints[col_name] = int(raw)
        except (ValueError, TypeError):
            raise SchemaError(
                f"column '{col_name}' is not a valid integer: {raw!r}"
            )

    # Float column: cost_usd
    try:
        cost_usd = float(cells[9])
    except (ValueError, TypeError):
        raise SchemaError(
            f"column 'Cost (USD)' is not a valid float: {cells[9]!r}"
        )

    result = cells[10]
    confidence = cells[11]

    return MetricsRow(
        run_id=run_id,
        timestamp=timestamp,
        agent=agent,
        task=task,
        model=model,
        tokens_in=coerced_ints["Tokens In"],
        tokens_out=coerced_ints["Tokens Out"],
        duration_s=coerced_ints["Duration (s)"],
        turns=coerced_ints["Turns"],
        cost_usd=cost_usd,
        result=result,
        confidence=confidence,
    )
