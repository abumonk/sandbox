"""ark_watch — tiny stdlib-only file watcher for .ark specs.

Polls the target file's mtime on a fixed interval and fires a callback
whenever it changes. No `watchdog` dependency, no platform-specific
event APIs — just `os.stat` + sleep. Good enough for the ARK dev loop:
edit → parse → verify → codegen → feedback in under a second.

Design notes
------------
- Polling, not inotify/FSEvents. Keeps the dep surface at zero and
  makes tests deterministic (no async, no threads).
- `poll_once()` is the unit under test. The blocking `watch()` loop
  is just `while True: sleep; if poll_once(): callback()` and is
  exercised through a manual CLI invocation.
- First `poll_once()` call after construction returns False and
  captures the baseline mtime. Otherwise you'd fire a spurious event
  on startup for an unchanged file.
- Missing files are tolerated (returns False) so temporary editor
  `save → rename` dance doesn't crash the loop.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional


class Watcher:
    """Poll a single file's mtime and notify on change."""

    def __init__(self, path: Path, poll_interval: float = 0.3):
        self.path = Path(path)
        self.poll_interval = poll_interval
        self._last_mtime: Optional[int] = None

    def _current_mtime(self) -> Optional[int]:
        try:
            return self.path.stat().st_mtime_ns
        except FileNotFoundError:
            return None

    def poll_once(self) -> bool:
        """Return True if the file has changed since the last poll.

        First call after construction captures the baseline and returns
        False (no false-positive 'change' at startup).
        Missing file → False (tolerated; the editor may be mid-save).
        """
        mtime = self._current_mtime()
        if mtime is None:
            return False
        if self._last_mtime is None:
            self._last_mtime = mtime
            return False
        if mtime != self._last_mtime:
            self._last_mtime = mtime
            return True
        return False

    def watch(self, on_change: Callable[[], None],
              stop: Optional[Callable[[], bool]] = None) -> None:
        """Block and invoke `on_change()` whenever the file changes.

        `stop` is an optional predicate polled alongside; when it returns
        True the loop exits. Used by tests to break out deterministically.
        """
        while True:
            if stop is not None and stop():
                return
            time.sleep(self.poll_interval)
            if self.poll_once():
                on_change()
