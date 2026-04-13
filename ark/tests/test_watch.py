"""Tests for the Watcher class (FileWatcherTask).

Focuses on `poll_once()` — the testable unit of the watcher. The
blocking `watch()` loop is exercised with a stop predicate that
short-circuits after a deterministic number of iterations.
"""

import os
import time

import pytest

from ark_watch import Watcher


def _write(path, content):
    path.write_text(content, encoding="utf-8")


def _bump_mtime(path, delta=1.0):
    """Forcibly advance the file's mtime so the watcher sees a change
    even on filesystems whose mtime resolution is coarse."""
    st = path.stat()
    os.utime(path, (st.st_atime + delta, st.st_mtime + delta))


def test_poll_once_baseline_first_call_returns_false(tmp_path):
    """The very first poll captures the baseline mtime and must NOT
    report a change — otherwise every startup fires a spurious event."""
    f = tmp_path / "spec.ark"
    _write(f, "class A {}")
    w = Watcher(f)
    assert w.poll_once() is False


def test_poll_once_detects_mtime_change(tmp_path):
    f = tmp_path / "spec.ark"
    _write(f, "class A {}")
    w = Watcher(f)
    assert w.poll_once() is False  # baseline
    _write(f, "class A { $data x: Int = 0 }")
    _bump_mtime(f, delta=2.0)
    assert w.poll_once() is True
    # Subsequent poll without further change returns False.
    assert w.poll_once() is False


def test_poll_once_missing_file_returns_false(tmp_path):
    f = tmp_path / "ghost.ark"
    w = Watcher(f)
    # No file yet — baseline hasn't been set either, but the watcher
    # must not crash.
    assert w.poll_once() is False
    assert w.poll_once() is False


def test_watch_loop_invokes_callback_and_stops(tmp_path):
    """Use the `stop` predicate to run watch() for a bounded number
    of iterations and assert the callback was called when the file
    actually changed in between polls."""
    f = tmp_path / "spec.ark"
    _write(f, "class A {}")
    w = Watcher(f, poll_interval=0.01)
    w.poll_once()  # prime the baseline

    calls = []
    iterations = {"n": 0}

    def stop():
        iterations["n"] += 1
        # On the 2nd iteration, mutate the file so the 3rd poll fires.
        if iterations["n"] == 2:
            _write(f, "class A { $data x: Int = 0 }")
            _bump_mtime(f, delta=2.0)
        # Exit after the 4th iteration regardless.
        return iterations["n"] >= 4

    w.watch(lambda: calls.append(True), stop=stop)
    assert len(calls) >= 1, "callback should have fired at least once"


def test_poll_interval_is_configurable(tmp_path):
    """Cheap sanity check that the poll_interval value is surfaced on
    the instance — watchers built with different intervals must retain
    that setting for downstream tooling to introspect."""
    f = tmp_path / "spec.ark"
    _write(f, "class A {}")
    w_fast = Watcher(f, poll_interval=0.05)
    w_slow = Watcher(f, poll_interval=1.5)
    assert w_fast.poll_interval == 0.05
    assert w_slow.poll_interval == 1.5
