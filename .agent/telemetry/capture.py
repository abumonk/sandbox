"""Telemetry capture entrypoint with error isolation.

Intended usage
--------------
    echo '{...}' | python -m telemetry.capture

Or from a Claude hook command::

    python .agent/telemetry/capture.py

Public API (importable for testing)
------------------------------------
read_stdin() -> str
normalize_payload(raw: dict) -> dict
resolve_adventure_id(payload: dict) -> str
append_row(adventure_id: str, row: MetricsRow) -> pathlib.Path
metrics_path(adventure_id: str) -> pathlib.Path
manifest_path(adventure_id: str) -> pathlib.Path
main(argv=None) -> int
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys

from . import aggregator, cost_model, schema
from .errors import PayloadError
from .log import log_capture_error
from .schema import MetricsRow

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

# Repo root is two directories above this file:
#   .agent/telemetry/capture.py  ->  two parents up = repo root
_REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[2]

_RE_ADVENTURE_ID = re.compile(r"^ADV-\d{3}$")
_RE_ADVENTURE_ID_COMPACT = re.compile(r"ADV(\d{3})")


def metrics_path(adventure_id: str) -> pathlib.Path:
    """Return the absolute path to ``metrics.md`` for *adventure_id*."""
    return _REPO_ROOT / ".agent" / "adventures" / adventure_id / "metrics.md"


def manifest_path(adventure_id: str) -> pathlib.Path:
    """Return the absolute path to ``manifest.md`` for *adventure_id*."""
    return _REPO_ROOT / ".agent" / "adventures" / adventure_id / "manifest.md"


# ---------------------------------------------------------------------------
# Stdin reader
# ---------------------------------------------------------------------------


def read_stdin() -> str:
    """Read all of stdin and return it as a string.

    Raises
    ------
    PayloadError
        If stdin is empty (zero bytes / only whitespace).
    """
    raw = sys.stdin.read()
    if not raw.strip():
        raise PayloadError("empty stdin")
    return raw


# ---------------------------------------------------------------------------
# Payload normalisation
# ---------------------------------------------------------------------------

_USAGE_FIELDS = {
    "input_tokens": "tokens_in",
    "output_tokens": "tokens_out",
}


def normalize_payload(raw: dict) -> dict:
    """Alias wire-format fields to the internal schema names.

    Transformations applied (only when internal name is not already present):
    - ``event``          -> ``event_type``
    - ``task_id``        -> ``task``
    - ``usage.input_tokens``  -> ``tokens_in``
    - ``usage.output_tokens`` -> ``tokens_out``
    - ``model``          normalised via :func:`cost_model.normalize_model`
    - ``adventure_id``   resolved via :func:`resolve_adventure_id`

    The transformation is idempotent: calling it twice on an already-normalised
    dict is a no-op.
    """
    payload = dict(raw)  # shallow copy so we don't mutate the caller's dict

    # event -> event_type
    if "event_type" not in payload and "event" in payload:
        payload["event_type"] = payload.pop("event")

    # task_id -> task
    if "task" not in payload and "task_id" in payload:
        payload["task"] = payload.pop("task_id")

    # usage.input_tokens / usage.output_tokens
    usage = payload.pop("usage", None)
    if isinstance(usage, dict):
        for wire_name, internal_name in _USAGE_FIELDS.items():
            if internal_name not in payload and wire_name in usage:
                payload[internal_name] = usage[wire_name]

    # model normalisation
    if "model" in payload and isinstance(payload["model"], str):
        payload["model"] = cost_model.normalize_model(payload["model"])

    # adventure_id resolution (may raise PayloadError)
    payload["adventure_id"] = resolve_adventure_id(payload)

    return payload


# ---------------------------------------------------------------------------
# Adventure ID resolution
# ---------------------------------------------------------------------------


def resolve_adventure_id(payload: dict) -> str:
    """Resolve ``adventure_id`` from *payload* using a 5-step fallback chain.

    Resolution order (first hit wins):
    1. ``payload["adventure_id"]`` matches ``^ADV-\\d{3}$``.
    2. ``payload["task_id"]`` or ``payload["task"]`` — extract ``ADV\\d{3}``
       prefix, format as ``ADV-NNN``.
    3. ``os.environ["ADVENTURE_ID"]`` if set and valid.
    4. Parse ``payload["cwd"]`` for a ``.agent/adventures/ADV-NNN/`` segment.
    5. Raise ``PayloadError("cannot resolve adventure_id")``.

    Raises
    ------
    PayloadError
        If none of the 5 steps yields a valid adventure ID.
    """
    # Step 1: explicit field
    candidate = payload.get("adventure_id")
    if isinstance(candidate, str) and _RE_ADVENTURE_ID.match(candidate):
        return candidate

    # Step 2: task_id / task prefix
    for key in ("task_id", "task"):
        task_val = payload.get(key)
        if isinstance(task_val, str):
            m = _RE_ADVENTURE_ID_COMPACT.match(task_val)
            if m:
                return f"ADV-{m.group(1)}"

    # Step 3: environment variable
    env_val = os.environ.get("ADVENTURE_ID", "")
    if env_val and _RE_ADVENTURE_ID.match(env_val):
        return env_val

    # Step 4: cwd path segment
    cwd_val = payload.get("cwd", "")
    if isinstance(cwd_val, str):
        # Look for .agent/adventures/ADV-NNN/ pattern in the path
        m = re.search(r"\.agent[/\\]adventures[/\\](ADV-\d{3})", cwd_val)
        if m and _RE_ADVENTURE_ID.match(m.group(1)):
            return m.group(1)

    # Step 5: fail
    raise PayloadError("cannot resolve adventure_id")


# ---------------------------------------------------------------------------
# Idempotent row append
# ---------------------------------------------------------------------------


def _ensure_metrics_file(mp: pathlib.Path, adventure_id: str) -> None:
    """Create a minimal new-format ``metrics.md`` if *mp* does not exist."""
    if mp.exists():
        return
    mp.parent.mkdir(parents=True, exist_ok=True)
    from .schema import ROW_HEADER, ROW_SEPARATOR
    content = (
        f"---\n"
        f"adventure_id: {adventure_id}\n"
        f"total_tokens_in: 0\n"
        f"total_tokens_out: 0\n"
        f"total_duration: 0\n"
        f"total_cost: 0.0000\n"
        f"agent_runs: 0\n"
        f"---\n"
        f"\n"
        f"## Agent Runs\n"
        f"\n"
        f"{ROW_HEADER}\n"
        f"{ROW_SEPARATOR}\n"
    )
    mp.write_text(content, encoding="utf-8")


def append_row(adventure_id: str, row: MetricsRow) -> pathlib.Path:
    """Idempotently append *row* to the metrics.md for *adventure_id*.

    The function is a no-op if a row with the same Run ID already exists
    (idempotency guarantee).  Returns the path of the metrics file.

    Parameters
    ----------
    adventure_id:
        Validated adventure ID string (e.g. ``"ADV-010"``).
    row:
        A :class:`~schema.MetricsRow` as produced by :func:`~schema.build_row`.

    Returns
    -------
    pathlib.Path
        Absolute path to the metrics file (for subsequent aggregation).
    """
    mp = metrics_path(adventure_id)
    _ensure_metrics_file(mp, adventure_id)

    # Parse existing rows to check idempotency.
    try:
        existing_rows = aggregator.parse_rows(mp)
    except Exception:
        existing_rows = []

    for existing in existing_rows:
        if existing.run_id == row.run_id:
            # Duplicate detected — no-op.
            return mp

    # Append the new row.
    serialized = schema.serialize(row)
    text = mp.read_text(encoding="utf-8")

    # Append after last pipe-table row (or after separator if table is empty).
    # We simply append to the end of the file, preserving a trailing newline.
    if not text.endswith("\n"):
        text += "\n"
    text += serialized + "\n"
    mp.write_text(text, encoding="utf-8")

    return mp


# ---------------------------------------------------------------------------
# Task actuals update (optional, guarded import)
# ---------------------------------------------------------------------------

# Result values that indicate a task run has finished.  Only terminal results
# trigger task-actuals recomputation; intermediate states are skipped.
TERMINAL_RESULTS: frozenset[str] = frozenset(
    {"done", "complete", "passed", "ready", "failed", "error"}
)


def _update_task_actuals(manifest_p: pathlib.Path, task_id: str) -> None:
    """Call ``task_actuals.update()`` if the module is available.

    Wrapped in a broad exception guard so that a missing or broken
    ``task_actuals`` module never causes capture to fail.
    """
    try:
        from . import task_actuals  # type: ignore[import]
        task_actuals.update(manifest_p, task_id)
    except ImportError:
        pass  # task_actuals not yet implemented — acceptable
    except Exception:
        pass  # propagate nothing; task actuals are a secondary concern


# ---------------------------------------------------------------------------
# Main guardrail
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entrypoint with a catch-all guardrail.

    All ``Exception`` subclasses are caught, logged to ``capture-errors.log``
    via :func:`~log.log_capture_error`, and the function returns 0.

    ``KeyboardInterrupt`` and ``SystemExit`` propagate normally (they are not
    subclasses of ``Exception`` in Python 3).

    Parameters
    ----------
    argv:
        Command-line arguments (currently unused; reserved for future flags
        such as ``--event SubagentStop``).

    Returns
    -------
    int
        Always 0.
    """
    raw_payload: str | None = None
    try:
        raw_payload = read_stdin()
        payload_dict = json.loads(raw_payload)
        payload_dict = normalize_payload(payload_dict)
        event = schema.validate_event(payload_dict)
        cost = cost_model.cost_for(
            event.model,
            event.tokens_in,
            event.tokens_out,
        )
        row = schema.build_row(event, cost)
        mp = append_row(event.adventure_id, row)
        aggregator.recompute_frontmatter(mp)
        if event.task and event.result in TERMINAL_RESULTS:
            _update_task_actuals(manifest_path(event.adventure_id), event.task)
    except Exception as exc:  # noqa: BLE001 -- intentional catch-all
        log_capture_error(exc, raw_payload=raw_payload)
    return 0  # always 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
