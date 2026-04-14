"""
Cron-based task scheduler for ARK agent tools.

Provides:
- ScheduledTask dataclass
- CronParser (parse_cron, matches_time, compute_next_run)
- Scheduler class (add_task, remove_task, get_due_tasks, execute_task, tick)
- scheduler_from_spec factory
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# ScheduledTask
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    """A task that runs on a cron schedule."""
    name: str
    cron_expression: str
    agent_ref: str
    platform_delivery: str
    action: str
    enabled: bool = True
    last_run: str | None = None   # ISO-8601 timestamp or None
    next_run: str | None = None   # ISO-8601 timestamp or None


# ---------------------------------------------------------------------------
# CronParser
# ---------------------------------------------------------------------------

def _parse_field(field_str: str, min_val: int, max_val: int) -> set[int]:
    """
    Parse a single cron field into the set of matching integer values.

    Supports:
    - ``*``            — every value
    - ``*/N``          — every N-th value (step)
    - ``A-B``          — range
    - ``A-B/N``        — range with step
    - ``A,B,C``        — list of any of the above
    - ``N``            — specific value
    """
    values: set[int] = set()

    for part in field_str.split(","):
        part = part.strip()
        if "/" in part:
            range_part, step_str = part.split("/", 1)
            step = int(step_str)
            if range_part == "*":
                start, end = min_val, max_val
            elif "-" in range_part:
                a, b = range_part.split("-", 1)
                start, end = int(a), int(b)
            else:
                start = int(range_part)
                end = max_val
            values.update(range(start, end + 1, step))
        elif "-" in part:
            a, b = part.split("-", 1)
            values.update(range(int(a), int(b) + 1))
        elif part == "*":
            values.update(range(min_val, max_val + 1))
        else:
            values.add(int(part))

    return values


def parse_cron(expression: str) -> dict[str, set[int]]:
    """
    Parse a standard 5-field cron expression.

    Fields (left to right): minute hour day_of_month month day_of_week

    Returns a dict with keys:
        minute, hour, day_of_month, month, day_of_week
    each mapping to a set of matching integer values.

    Raises ValueError for malformed expressions.
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(
            f"Cron expression must have exactly 5 fields, got {len(parts)}: {expression!r}"
        )
    minute_f, hour_f, dom_f, month_f, dow_f = parts

    return {
        "minute":       _parse_field(minute_f, 0, 59),
        "hour":         _parse_field(hour_f,   0, 23),
        "day_of_month": _parse_field(dom_f,    1, 31),
        "month":        _parse_field(month_f,  1, 12),
        "day_of_week":  _parse_field(dow_f,    0,  6),  # 0=Sunday … 6=Saturday
    }


def matches_time(parsed_cron: dict[str, set[int]], dt: datetime) -> bool:
    """
    Return True if *dt* matches the pre-parsed cron expression.

    ``day_of_week`` uses the POSIX convention: 0 = Sunday, 6 = Saturday.
    Python's ``datetime.weekday()`` uses 0 = Monday; we convert accordingly.
    """
    # Python weekday: Mon=0 … Sun=6  →  POSIX: Sun=0 … Sat=6
    posix_dow = (dt.weekday() + 1) % 7

    return (
        dt.minute      in parsed_cron["minute"]
        and dt.hour    in parsed_cron["hour"]
        and dt.day     in parsed_cron["day_of_month"]
        and dt.month   in parsed_cron["month"]
        and posix_dow  in parsed_cron["day_of_week"]
    )


def compute_next_run(expression: str, from_dt: datetime | None = None) -> datetime:
    """
    Compute the next datetime (after *from_dt*) that matches *expression*.

    Iterates minute-by-minute up to 48 hours ahead. Raises RuntimeError if
    no match is found within that window.
    """
    parsed = parse_cron(expression)
    if from_dt is None:
        from_dt = datetime.utcnow()

    # Advance one full minute past from_dt, then truncate to minute precision
    candidate = (from_dt + timedelta(minutes=1)).replace(second=0, microsecond=0)

    limit = from_dt + timedelta(hours=48)
    while candidate <= limit:
        if matches_time(parsed, candidate):
            return candidate
        candidate += timedelta(minutes=1)

    raise RuntimeError(
        f"No matching time found within 48 hours for cron expression {expression!r}"
    )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Tick-based cron scheduler."""

    def __init__(self, tasks: list[ScheduledTask] | None = None) -> None:
        self._tasks: list[ScheduledTask] = list(tasks) if tasks else []

    # -- task management -----------------------------------------------------

    def add_task(self, task: ScheduledTask) -> None:
        """Add a ScheduledTask to the scheduler."""
        self._tasks.append(task)

    def remove_task(self, name: str) -> None:
        """Remove the first task whose name equals *name*."""
        self._tasks = [t for t in self._tasks if t.name != name]

    # -- scheduling logic ----------------------------------------------------

    def get_due_tasks(self, now: datetime | None = None) -> list[ScheduledTask]:
        """
        Return all enabled tasks whose next_run has arrived or passed.

        A task with ``next_run=None`` is considered not yet scheduled and is
        **not** returned as due.
        """
        if now is None:
            now = datetime.utcnow()

        due: list[ScheduledTask] = []
        for task in self._tasks:
            if not task.enabled:
                continue
            if task.next_run is None:
                continue
            next_run_dt = datetime.fromisoformat(task.next_run)
            if now >= next_run_dt:
                due.append(task)
        return due

    def execute_task(self, task: ScheduledTask) -> str:
        """
        Simplified task execution — returns the task's action string.

        In a full implementation this would dispatch to an agent runner.
        """
        return task.action

    def tick(self, now: datetime | None = None) -> list[str]:
        """
        Process one scheduler tick.

        For every due task:
        1. Execute it (returning its action string).
        2. Update ``last_run`` to *now*.
        3. Compute and store the next ``next_run``.

        Returns the list of action strings that were executed.
        """
        if now is None:
            now = datetime.utcnow()

        results: list[str] = []
        for task in self.get_due_tasks(now):
            result = self.execute_task(task)
            results.append(result)
            task.last_run = now.isoformat()
            try:
                next_dt = compute_next_run(task.cron_expression, from_dt=now)
                task.next_run = next_dt.isoformat()
            except RuntimeError:
                # Leave next_run unchanged if we cannot compute the next slot
                pass
        return results

    # -- convenience ---------------------------------------------------------

    @property
    def tasks(self) -> list[ScheduledTask]:
        """Read-only view of registered tasks."""
        return list(self._tasks)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def scheduler_from_spec(cron_task_specs: list[dict[str, Any]]) -> Scheduler:
    """
    Build a Scheduler from a list of parsed spec dicts.

    Each dict may contain the following keys (all optional except *name* and
    *cron_expression*):

    .. code-block:: python

        {
            "name":              "daily_report",
            "cron_expression":   "0 9 * * 1",
            "agent_ref":         "reporter_agent",
            "platform_delivery": "slack",
            "action":            "generate_weekly_report",
            "enabled":           True,
        }
    """
    tasks: list[ScheduledTask] = []
    for spec in cron_task_specs:
        expression = spec.get("cron_expression", "* * * * *")
        # Pre-compute the initial next_run so tasks are immediately schedulable
        try:
            next_run_dt = compute_next_run(expression)
            next_run_str: str | None = next_run_dt.isoformat()
        except (ValueError, RuntimeError):
            next_run_str = None

        task = ScheduledTask(
            name=spec.get("name", "unnamed"),
            cron_expression=expression,
            agent_ref=spec.get("agent_ref", ""),
            platform_delivery=spec.get("platform_delivery", ""),
            action=spec.get("action", ""),
            enabled=spec.get("enabled", True),
            last_run=spec.get("last_run"),
            next_run=spec.get("next_run", next_run_str),
        )
        tasks.append(task)

    return Scheduler(tasks)
