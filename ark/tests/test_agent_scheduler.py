"""Tests for tools/agent/scheduler.py — cron parsing, due tasks, tick execution.

Covers TC-019 through TC-021.
"""

import sys
import pathlib
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "agent"))

from scheduler import (  # noqa: E402
    ScheduledTask,
    parse_cron,
    matches_time,
    compute_next_run,
    Scheduler,
    scheduler_from_spec,
)


# ---------------------------------------------------------------------------
# parse_cron
# ---------------------------------------------------------------------------

def test_parse_cron_wildcard():
    """parse_cron('* * * * *') returns all values for each field."""
    parsed = parse_cron("* * * * *")
    assert 0 in parsed["minute"]
    assert 59 in parsed["minute"]
    assert 0 in parsed["hour"]
    assert 23 in parsed["hour"]
    assert 1 in parsed["day_of_month"]
    assert 31 in parsed["day_of_month"]
    assert 1 in parsed["month"]
    assert 12 in parsed["month"]
    assert 0 in parsed["day_of_week"]
    assert 6 in parsed["day_of_week"]


def test_parse_cron_specific_values():
    """parse_cron parses specific values correctly."""
    parsed = parse_cron("30 9 15 6 3")
    assert parsed["minute"] == {30}
    assert parsed["hour"] == {9}
    assert parsed["day_of_month"] == {15}
    assert parsed["month"] == {6}
    assert parsed["day_of_week"] == {3}


def test_parse_cron_range():
    """parse_cron parses range expressions."""
    parsed = parse_cron("0-5 * * * *")
    assert parsed["minute"] == {0, 1, 2, 3, 4, 5}


def test_parse_cron_step():
    """parse_cron parses step expressions (*/N)."""
    parsed = parse_cron("*/15 * * * *")
    assert 0 in parsed["minute"]
    assert 15 in parsed["minute"]
    assert 30 in parsed["minute"]
    assert 45 in parsed["minute"]
    assert 1 not in parsed["minute"]


def test_parse_cron_list():
    """parse_cron parses comma-separated lists."""
    parsed = parse_cron("0,15,30,45 * * * *")
    assert parsed["minute"] == {0, 15, 30, 45}


def test_parse_cron_invalid_raises():
    """parse_cron raises ValueError for malformed expressions."""
    try:
        parse_cron("* * *")
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# matches_time
# ---------------------------------------------------------------------------

def test_matches_time_exact():
    """matches_time() returns True for exact matching datetime."""
    parsed = parse_cron("30 9 1 1 *")
    # Jan 1, 2024 09:30 — day_of_week is Monday (1 in POSIX = Monday)
    dt = datetime(2024, 1, 1, 9, 30)
    assert matches_time(parsed, dt)


def test_matches_time_wildcard_always_matches():
    """matches_time() with '* * * * *' matches any datetime."""
    parsed = parse_cron("* * * * *")
    for hour in [0, 12, 23]:
        dt = datetime(2024, 6, 15, hour, 0)
        assert matches_time(parsed, dt)


def test_matches_time_wrong_minute():
    """matches_time() returns False when minute does not match."""
    parsed = parse_cron("0 9 * * *")
    dt = datetime(2024, 6, 15, 9, 1)
    assert not matches_time(parsed, dt)


# ---------------------------------------------------------------------------
# compute_next_run
# ---------------------------------------------------------------------------

def test_compute_next_run_advances_at_least_one_minute():
    """compute_next_run() returns a time strictly after from_dt."""
    from_dt = datetime(2024, 1, 1, 0, 0)
    next_dt = compute_next_run("* * * * *", from_dt=from_dt)
    assert next_dt > from_dt


def test_compute_next_run_daily_9am():
    """compute_next_run() for '0 9 * * *' returns next 9:00 AM."""
    # Start just before 9am
    from_dt = datetime(2024, 6, 15, 8, 59)
    next_dt = compute_next_run("0 9 * * *", from_dt=from_dt)
    assert next_dt.hour == 9
    assert next_dt.minute == 0


def test_compute_next_run_weekday_only():
    """compute_next_run() for '0 9 * * 1-5' skips weekends."""
    # Wednesday June 12 2024 at 20:00 — next weekday 9am is Thursday June 13
    from_dt = datetime(2024, 6, 12, 20, 0)
    next_dt = compute_next_run("0 9 * * 1-5", from_dt=from_dt)
    # Should be a weekday (Mon=0..Fri=4 in Python weekday)
    assert next_dt.weekday() < 5  # 0=Mon...4=Fri


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

def _make_task(name, next_run=None, enabled=True, action="do_something"):
    return ScheduledTask(
        name=name,
        cron_expression="0 9 * * *",
        agent_ref="test_agent",
        platform_delivery="terminal",
        action=action,
        enabled=enabled,
        next_run=next_run,
    )


def test_scheduler_add_task():
    """Scheduler.add_task() adds a task to the registry."""
    scheduler = Scheduler()
    task = _make_task("t1")
    scheduler.add_task(task)
    assert len(scheduler.tasks) == 1


def test_scheduler_remove_task():
    """Scheduler.remove_task() removes a task by name."""
    scheduler = Scheduler()
    scheduler.add_task(_make_task("t1"))
    scheduler.add_task(_make_task("t2"))
    scheduler.remove_task("t1")
    names = [t.name for t in scheduler.tasks]
    assert "t1" not in names
    assert "t2" in names


def test_scheduler_get_due_tasks_past_next_run():
    """Scheduler.get_due_tasks() returns tasks whose next_run has passed."""
    past = "2020-01-01T00:00:00"
    task = _make_task("due_task", next_run=past)
    scheduler = Scheduler(tasks=[task])
    due = scheduler.get_due_tasks(now=datetime(2024, 1, 1, 0, 0))
    assert task in due


def test_scheduler_get_due_tasks_future_next_run():
    """Scheduler.get_due_tasks() does not return tasks with future next_run."""
    future = "2099-01-01T00:00:00"
    task = _make_task("future_task", next_run=future)
    scheduler = Scheduler(tasks=[task])
    due = scheduler.get_due_tasks(now=datetime(2024, 1, 1, 0, 0))
    assert task not in due


def test_scheduler_get_due_tasks_disabled_excluded():
    """Scheduler.get_due_tasks() does not return disabled tasks."""
    past = "2020-01-01T00:00:00"
    task = _make_task("disabled_task", next_run=past, enabled=False)
    scheduler = Scheduler(tasks=[task])
    due = scheduler.get_due_tasks(now=datetime(2024, 1, 1, 0, 0))
    assert task not in due


def test_scheduler_get_due_tasks_none_next_run():
    """Scheduler.get_due_tasks() skips tasks with next_run=None."""
    task = _make_task("no_schedule", next_run=None)
    scheduler = Scheduler(tasks=[task])
    due = scheduler.get_due_tasks(now=datetime(2024, 1, 1, 0, 0))
    assert task not in due


def test_scheduler_execute_task_returns_action():
    """Scheduler.execute_task() returns the task's action string."""
    scheduler = Scheduler()
    task = _make_task("t1", action="run_report")
    result = scheduler.execute_task(task)
    assert result == "run_report"


def test_scheduler_tick_executes_due_tasks():
    """Scheduler.tick() executes due tasks and returns action strings."""
    past = "2020-01-01T00:00:00"
    task = _make_task("daily", next_run=past, action="send_report")
    scheduler = Scheduler(tasks=[task])
    now = datetime(2024, 6, 15, 9, 0)
    results = scheduler.tick(now=now)
    assert "send_report" in results


def test_scheduler_tick_updates_last_run():
    """Scheduler.tick() updates last_run timestamp after execution."""
    past = "2020-01-01T00:00:00"
    task = _make_task("t1", next_run=past)
    scheduler = Scheduler(tasks=[task])
    now = datetime(2024, 6, 15, 9, 0)
    scheduler.tick(now=now)
    assert task.last_run is not None
    assert "2024" in task.last_run


def test_scheduler_tick_updates_next_run():
    """Scheduler.tick() computes and updates next_run after execution."""
    past = "2020-01-01T00:00:00"
    task = _make_task("t1", next_run=past)
    scheduler = Scheduler(tasks=[task])
    now = datetime(2024, 6, 15, 9, 0)
    scheduler.tick(now=now)
    # next_run should be in the future relative to `now`
    assert task.next_run is not None
    next_dt = datetime.fromisoformat(task.next_run)
    assert next_dt > now


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def test_scheduler_from_spec_builds_scheduler():
    """scheduler_from_spec() constructs a Scheduler with tasks."""
    specs = [
        {
            "name": "daily",
            "cron_expression": "0 9 * * *",
            "agent_ref": "bot",
            "platform_delivery": "telegram",
            "action": "run_daily",
        }
    ]
    scheduler = scheduler_from_spec(specs)
    assert isinstance(scheduler, Scheduler)
    assert len(scheduler.tasks) == 1
    t = scheduler.tasks[0]
    assert t.name == "daily"
    assert t.agent_ref == "bot"
    assert t.next_run is not None  # pre-computed


def test_scheduler_from_spec_empty():
    """scheduler_from_spec() with empty list returns empty Scheduler."""
    scheduler = scheduler_from_spec([])
    assert isinstance(scheduler, Scheduler)
    assert len(scheduler.tasks) == 0
