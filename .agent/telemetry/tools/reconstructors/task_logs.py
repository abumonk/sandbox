"""Extract telemetry candidates from task-file ``## Log`` sections.

Usage::

    from pathlib import Path
    from telemetry.tools.reconstructors.task_logs import parse

    candidates = parse(Path(".agent/adventures/ADV-008/tasks"))

For each ``*.md`` task file that has a ``## Log`` section, one ``Candidate``
is produced whose ``duration_s`` spans the first log timestamp to the last
log timestamp.  Tasks with fewer than two log entries get ``duration_s=0``.
All candidates get ``confidence="low"`` and ``source="task_log"``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from . import Candidate

# Match a log entry: - [TIMESTAMP] agent: message
_RE_LOG_ENTRY = re.compile(
    r'^\s*-\s*\[([^\]]+)\]\s+([\w][\w\-]*):\s+(.+)'
)

# Match frontmatter delimiters.
_RE_FM_DELIM = re.compile(r'^---\s*$')


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp string to a UTC-aware datetime."""
    ts_str = ts_str.strip()
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return None


def _extract_frontmatter(lines: List[str]) -> dict:
    """Extract simple key:value frontmatter from *lines*.

    Only scans between the first pair of ``---`` delimiters.  Returns a dict
    of lowercased keys to raw string values.
    """
    fm: dict = {}
    in_fm = False
    delim_count = 0
    for line in lines:
        if _RE_FM_DELIM.match(line):
            delim_count += 1
            if delim_count == 1:
                in_fm = True
                continue
            else:
                break
        if in_fm:
            if ":" in line:
                key, _, value = line.partition(":")
                fm[key.strip().lower()] = value.strip()
    return fm


def parse(tasks_dir: Path) -> List[Candidate]:
    """Parse all ``*.md`` task files in *tasks_dir*.

    Parameters
    ----------
    tasks_dir:
        Directory containing task markdown files.

    Returns
    -------
    list[Candidate]
        One candidate per task file that has a ``## Log`` section.  Files
        without a ``## Log`` section are skipped silently.
    """
    if not tasks_dir.exists():
        return []

    candidates: List[Candidate] = []

    for task_file in sorted(tasks_dir.glob("*.md")):
        # Derive task ID from filename: "ADV008-T01.md" -> "ADV008-T01"
        task_id = task_file.stem

        text = task_file.read_text(encoding="utf-8")
        lines = text.splitlines()

        # Extract frontmatter fields.
        fm = _extract_frontmatter(lines)
        assignee = fm.get("assignee", "unknown").strip('"').strip("'") or "unknown"
        status = fm.get("status", "unknown").strip('"').strip("'") or "unknown"

        # Locate the ## Log section.
        log_start = None
        for i, line in enumerate(lines):
            if re.match(r'^##\s+Log\b', line):
                log_start = i
                break

        if log_start is None:
            continue  # Skip files without a ## Log section.

        # Parse log entries after the ## Log header.
        timestamps: List[datetime] = []
        last_result = status

        for line in lines[log_start + 1:]:
            if re.match(r'^##\s+', line):
                break  # Start of next section.

            m = _RE_LOG_ENTRY.match(line)
            if m:
                ts = _parse_timestamp(m.group(1))
                if ts is not None:
                    timestamps.append(ts)
                msg_lower = m.group(3).lower()
                # Try to detect final status from the message.
                if any(kw in msg_lower for kw in ("status: done", "status=done", "done")):
                    last_result = "done"
                elif any(kw in msg_lower for kw in ("passed", "pass")):
                    last_result = "passed"
                elif any(kw in msg_lower for kw in ("complete",)):
                    last_result = "complete"
                elif any(kw in msg_lower for kw in ("failed", "fail")):
                    last_result = "failed"

        if not timestamps:
            continue

        timestamps_sorted = sorted(timestamps)
        first_ts = timestamps_sorted[0]
        last_ts = timestamps_sorted[-1]
        duration_s = max(0, int((last_ts - first_ts).total_seconds()))
        ts_str = first_ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        candidates.append(
            Candidate(
                run_id="",
                timestamp=ts_str,
                agent=assignee,
                task=task_id,
                model="unknown",
                tokens_in=0,
                tokens_out=0,
                duration_s=duration_s,
                turns=0,
                cost=0.0,
                result=last_result,
                confidence="low",
                source="task_log",
            )
        )

    return candidates
