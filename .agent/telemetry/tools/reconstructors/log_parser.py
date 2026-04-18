"""Parse ``adventure.log`` files to extract spawn/complete event pairs.

Usage::

    from pathlib import Path
    from telemetry.tools.reconstructors.log_parser import parse

    candidates = parse(Path(".agent/adventures/ADV-008/adventure.log"))

Each spawn event produces a ``Candidate``; if a matching complete event is
found for the same agent, ``duration_s`` is computed from the timestamp delta.
Unpaired spawns emit a candidate with ``duration_s=0`` and
``result="incomplete"``.  All candidates get ``confidence="low"`` and
``source="log"``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import Candidate

# Match a standard adventure.log line:
# [2026-04-14T12:00:00Z] agent-name | "message body"
# The message may be quoted or unquoted.
_RE_LOG_LINE = re.compile(
    r'^\[([^\]]+)\]\s+([\w][\w\-]*)\s+\|\s+"?(.+?)"?\s*$'
)

# Identify a spawn message: spawn: TASK_ID ...
_RE_SPAWN = re.compile(r'spawn:\s+(\S+)')

# Identify a complete message.
_RE_COMPLETE = re.compile(r'\bcomplete\b', re.IGNORECASE)


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp string to a UTC-aware datetime.

    Accepts ``YYYY-MM-DDTHH:MM:SSZ`` and ``YYYY-MM-DDTHH:MM:SS+HH:MM`` forms.
    Date-only strings (``YYYY-MM-DD``) are treated as midnight UTC.
    Returns ``None`` on failure.
    """
    ts_str = ts_str.strip()
    # Normalise trailing "Z" to "+00:00" for fromisoformat compatibility.
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(ts_str)
        # Ensure the result is always timezone-aware (assume UTC for naive datetimes).
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def parse(log_path: Path) -> List[Candidate]:
    """Parse *log_path* and return a list of ``Candidate`` objects.

    Parameters
    ----------
    log_path:
        Path to an ``adventure.log`` file.

    Returns
    -------
    list[Candidate]
        Empty list if the file does not exist or contains no spawn events.
        Lines that do not match the expected format are silently skipped.
    """
    if not log_path.exists():
        return []

    # Parse all lines first so we can sort by timestamp.
    events: List[Tuple[Optional[datetime], str, str]] = []  # (ts, agent, msg)
    for raw_line in log_path.read_text(encoding="utf-8").splitlines():
        m = _RE_LOG_LINE.match(raw_line.strip())
        if not m:
            continue
        ts = _parse_timestamp(m.group(1))
        agent = m.group(2)
        msg = m.group(3).strip()
        events.append((ts, agent, msg))

    # Sort by timestamp (None timestamps sort first).
    # Ensure all sort keys are timezone-aware to avoid comparison errors
    # when some timestamps are naive (e.g. date-only log lines like [2026-04-13]).
    def _sort_key(e):
        ts = e[0]
        if ts is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts

    events.sort(key=_sort_key)

    # Track open spawns per agent: agent -> (task_id, spawn_ts, spawn_ts_str)
    open_spawns: Dict[str, Tuple[str, Optional[datetime], str]] = {}

    candidates: List[Candidate] = []

    for ts, agent, msg in events:
        spawn_m = _RE_SPAWN.search(msg)
        if spawn_m:
            # Close any previously open spawn for this agent before opening
            # a new one (sequential task handling).
            if agent in open_spawns:
                prev_task, prev_ts, prev_ts_str = open_spawns.pop(agent)
                # Compute duration from this spawn's timestamp (acts as
                # an implicit close for the previous task).
                if ts is not None and prev_ts is not None:
                    dur = max(0, int((ts - prev_ts).total_seconds()))
                else:
                    dur = 0
                candidates.append(
                    Candidate(
                        run_id="",
                        timestamp=prev_ts_str,
                        agent=agent,
                        task=prev_task,
                        model="unknown",
                        tokens_in=0,
                        tokens_out=0,
                        duration_s=dur,
                        turns=0,
                        cost=0.0,
                        result="incomplete",
                        confidence="low",
                        source="log",
                    )
                )

            task_id = spawn_m.group(1)
            ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ") if ts else ""
            open_spawns[agent] = (task_id, ts, ts_str)

        elif _RE_COMPLETE.search(msg):
            if agent in open_spawns:
                task_id, spawn_ts, spawn_ts_str = open_spawns.pop(agent)
                if ts is not None and spawn_ts is not None:
                    dur = max(0, int((ts - spawn_ts).total_seconds()))
                else:
                    dur = 0
                candidates.append(
                    Candidate(
                        run_id="",
                        timestamp=spawn_ts_str,
                        agent=agent,
                        task=task_id,
                        model="unknown",
                        tokens_in=0,
                        tokens_out=0,
                        duration_s=dur,
                        turns=0,
                        cost=0.0,
                        result="complete",
                        confidence="low",
                        source="log",
                    )
                )

    # Emit unpaired spawns that never had a matching complete event.
    for agent, (task_id, spawn_ts, spawn_ts_str) in open_spawns.items():
        candidates.append(
            Candidate(
                run_id="",
                timestamp=spawn_ts_str,
                agent=agent,
                task=task_id,
                model="unknown",
                tokens_in=0,
                tokens_out=0,
                duration_s=0,
                turns=0,
                cost=0.0,
                result="incomplete",
                confidence="low",
                source="log",
            )
        )

    return candidates
