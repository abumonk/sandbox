"""Derive per-task commit windows from ``git log``.

Usage::

    from telemetry.tools.reconstructors.git_windows import for_adventure

    candidates = for_adventure("ADV-008")

For each task ID discovered in the commit history of
``.agent/adventures/{adventure_id}/``, one ``Candidate`` is produced whose
``duration_s`` spans the first to last commit touching that task's files.
All candidates get ``confidence="low"`` and ``source="git"``.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Tuple

from . import Candidate

# Match a task ID in a file path, e.g. "tasks/ADV008-T01.md" or
# "designs/ADV008-T01-design.md".
_RE_TASK_IN_PATH = re.compile(r"(ADV\d{3}-T\d+)", re.IGNORECASE)


def _find_repo_root(start: Path) -> Path:
    """Walk up from *start* until a ``.git`` directory is found.

    Raises
    ------
    RuntimeError
        If no ``.git`` directory is found before reaching the filesystem root.
    """
    current = start.resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            raise RuntimeError(
                f"Could not find a git repository root starting from {start}"
            )
        current = parent


def _parse_git_output(output: str) -> List[Tuple[str, datetime, str, List[str]]]:
    """Parse the output of ``git log --pretty=format:"%H|%ai|%s" --name-only``.

    Returns a list of ``(hash, datetime, subject, file_paths)`` tuples.
    """
    commits: List[Tuple[str, datetime, str, List[str]]] = []
    current_commit: Optional[Tuple[str, datetime, str]] = None
    current_files: List[str] = []

    for line in output.splitlines():
        if "|" in line and not line.startswith(" "):
            # Attempt to parse as a commit header.
            parts = line.split("|", 2)
            if len(parts) >= 2 and len(parts[0]) == 40:
                # Save previous commit.
                if current_commit is not None:
                    commits.append((*current_commit, current_files))

                commit_hash = parts[0]
                ts_str = parts[1].strip()
                subject = parts[2].strip() if len(parts) > 2 else ""
                current_files = []

                # Parse timestamp; git --pretty="%ai" gives
                # "YYYY-MM-DD HH:MM:SS +HHMM" format.
                try:
                    # Normalise to a form datetime.fromisoformat can handle.
                    # "2026-04-14 12:00:00 +0000" -> "2026-04-14T12:00:00+00:00"
                    ts_normalized = ts_str[:10] + "T" + ts_str[11:19]
                    offset_raw = ts_str[20:].strip() if len(ts_str) > 19 else "+0000"
                    # "+0000" -> "+00:00"
                    if len(offset_raw) == 5 and ":" not in offset_raw:
                        offset_raw = offset_raw[:3] + ":" + offset_raw[3:]
                    ts_normalized += offset_raw
                    ts_dt = datetime.fromisoformat(ts_normalized)
                except (ValueError, IndexError):
                    ts_dt = datetime.min.replace(tzinfo=timezone.utc)

                current_commit = (commit_hash, ts_dt, subject)
                continue

        # File path line (or blank line between commits).
        if current_commit is not None and line.strip():
            current_files.append(line.strip())

    # Don't forget the last commit.
    if current_commit is not None:
        commits.append((*current_commit, current_files))

    return commits


def for_adventure(
    adventure_id: str,
    repo_root: Optional[Path] = None,
) -> List[Candidate]:
    """Return per-task commit windows for *adventure_id*.

    Parameters
    ----------
    adventure_id:
        Adventure identifier, e.g. ``"ADV-008"``.
    repo_root:
        Optional explicit path to the git repository root.  When ``None``,
        the function walks up from this module's location to find ``.git``.

    Returns
    -------
    list[Candidate]
        Empty list when the adventure path has no git history.

    Raises
    ------
    RuntimeError
        If *repo_root* cannot be determined or ``git log`` fails.
    """
    if repo_root is None:
        repo_root = _find_repo_root(Path(__file__).parent)

    # Use forward slashes for git path arguments regardless of OS.
    adventure_path = str(PurePosixPath(".agent/adventures") / adventure_id) + "/"

    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--pretty=format:%H|%ai|%s",
                "--name-only",
                "--",
                adventure_path,
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise RuntimeError("git executable not found; is git installed?")

    if result.returncode != 0:
        raise RuntimeError(
            f"git log failed (exit {result.returncode}): {result.stderr.strip()}"
        )

    if not result.stdout.strip():
        return []

    commits = _parse_git_output(result.stdout)

    # Group commits by task ID extracted from touched file paths.
    # task_id -> list of datetimes
    task_windows: Dict[str, List[datetime]] = {}

    for commit_hash, ts_dt, subject, file_paths in commits:
        seen_tasks_this_commit: set[str] = set()
        for fp in file_paths:
            m = _RE_TASK_IN_PATH.search(fp)
            if m:
                task_id = m.group(1).upper()
                # Only count each task once per commit.
                if task_id not in seen_tasks_this_commit:
                    seen_tasks_this_commit.add(task_id)
                    task_windows.setdefault(task_id, []).append(ts_dt)

    if not task_windows:
        return []

    candidates: List[Candidate] = []
    for task_id, timestamps in sorted(task_windows.items()):
        timestamps_sorted = sorted(timestamps)
        first_ts = timestamps_sorted[0]
        last_ts = timestamps_sorted[-1]

        duration_s = max(0, int((last_ts - first_ts).total_seconds()))
        ts_str = first_ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        candidates.append(
            Candidate(
                run_id="",
                timestamp=ts_str,
                agent="unknown",
                task=task_id,
                model="unknown",
                tokens_in=0,
                tokens_out=0,
                duration_s=duration_s,
                turns=0,
                cost=0.0,
                result="unknown",
                confidence="low",
                source="git",
            )
        )

    return candidates
