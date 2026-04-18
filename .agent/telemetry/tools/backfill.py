"""Backfill CLI — merge reconstructor candidates into a ``metrics.md``.

Usage::

    python -m telemetry.tools.backfill --adventure ADV-008 --dry-run
    python -m telemetry.tools.backfill --adventure ADV-008 --apply
    python -m telemetry.tools.backfill --all --dry-run
    python -m telemetry.tools.backfill --adventure ADV-008 --sources existing,log

Exit codes: 0 = success, 1 = error.

Algorithm
---------
1. Collect ``List[Candidate]`` from each enabled reconstructor for the adventure.
2. Group by ``task_id``.
3. Per task: field-level confidence merge — pick the value with the highest
   confidence for each MetricsRow field; ties broken by source priority
   (existing > log > task_log > git).
4. Compute a deterministic Run ID: ``sha1(adventure_id|agent|task|model|ts|)[:12]``.
5. Write the merged rows to ``metrics.md.new`` with fresh frontmatter totals.
6. Emit a unified diff to stdout.
7. If ``--apply``: rename original to ``metrics.md.backup.<ts>`` (atomic replace).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import difflib
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Imports from sibling packages
# ---------------------------------------------------------------------------

# Allow running from the repo root: ``python -m telemetry.tools.backfill``
# Path manipulation is not needed when the package is on sys.path.

from ..schema import MetricsRow, ROW_HEADER, ROW_SEPARATOR, serialize
from ..cost_model import cost_for, normalize_model
from .reconstructors import (
    Candidate,
    parse_existing_rows,
    parse_log,
    git_windows_for_adventure,
    parse_task_logs,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ADVENTURES_ROOT = Path(".agent/adventures")

ALL_SOURCES = ["existing", "log", "git", "task_log"]

# Higher number = higher confidence; used in the per-field merge.
CONFIDENCE_RANK: Dict[str, int] = {
    "high": 4,
    "medium": 3,
    "low": 2,
    "estimated": 1,
}

# Source priority for tie-breaking (lower index = higher priority).
SOURCE_PRIORITY = ["existing", "log", "task_log", "git"]

# YAML frontmatter key order for metrics.md output.
_FRONTMATTER_KEY_ORDER = [
    "adventure_id",
    "total_tokens_in",
    "total_tokens_out",
    "total_duration",
    "total_cost",
    "agent_runs",
]


# ---------------------------------------------------------------------------
# 2. Adventure discovery
# ---------------------------------------------------------------------------


def discover_adventures(
    adventure_filter: Optional[str],
    use_all: bool,
) -> List[Path]:
    """Return the list of adventure directory paths to process.

    Parameters
    ----------
    adventure_filter:
        A single adventure ID such as ``"ADV-008"``.  Mutually exclusive with
        *use_all*.
    use_all:
        When ``True``, glob for all ``ADV-*`` subdirectories under
        ``ADVENTURES_ROOT``.

    Raises
    ------
    SystemExit
        If *adventure_filter* does not correspond to an existing directory.
    """
    if adventure_filter:
        adv_path = ADVENTURES_ROOT / adventure_filter
        if not adv_path.is_dir():
            print(
                f"error: adventure directory not found: {adv_path}",
                file=sys.stderr,
            )
            sys.exit(1)
        return [adv_path]

    if use_all:
        paths = sorted(ADVENTURES_ROOT.glob("ADV-*"))
        return [p for p in paths if p.is_dir()]

    print("error: specify --adventure ADV-NNN or --all", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# 3. Candidate collection
# ---------------------------------------------------------------------------


def collect_candidates(
    adv_path: Path,
    sources: List[str],
) -> Dict[str, List[Candidate]]:
    """Call each enabled reconstructor and group results by task_id.

    Parameters
    ----------
    adv_path:
        Path to the adventure directory (e.g. ``.agent/adventures/ADV-008``).
    sources:
        Subset of ``ALL_SOURCES`` to enable.

    Returns
    -------
    dict[str, list[Candidate]]
        Map of task_id to all candidates for that task from all sources.
        Tasks whose ID is ``"-"`` (adventure-level rows) are stored under
        the key ``"-"``.
    """
    adventure_id = adv_path.name  # e.g. "ADV-008"
    all_candidates: List[Candidate] = []

    if "existing" in sources:
        metrics_path = adv_path / "metrics.md"
        all_candidates.extend(parse_existing_rows(metrics_path))

    if "log" in sources:
        log_path = adv_path / "adventure.log"
        all_candidates.extend(parse_log(log_path))

    if "git" in sources:
        try:
            all_candidates.extend(git_windows_for_adventure(adventure_id))
        except RuntimeError as exc:
            print(f"warning: git reconstructor skipped for {adventure_id}: {exc}", file=sys.stderr)

    if "task_log" in sources:
        tasks_dir = adv_path / "tasks"
        all_candidates.extend(parse_task_logs(tasks_dir))

    # Group by task_id (using the ``task`` field from Candidate).
    grouped: Dict[str, List[Candidate]] = {}
    for cand in all_candidates:
        key = cand.task or "-"
        grouped.setdefault(key, []).append(cand)

    return grouped


# ---------------------------------------------------------------------------
# 4. Per-task merge
# ---------------------------------------------------------------------------


def _source_priority(source: str) -> int:
    """Lower value = higher priority in tie-breaking."""
    try:
        return SOURCE_PRIORITY.index(source)
    except ValueError:
        return len(SOURCE_PRIORITY)


def _best_candidate_for_field(
    candidates: List[Candidate],
    field: str,
) -> Optional[Candidate]:
    """Return the candidate with the highest confidence for *field*.

    Among tied-confidence candidates, the one with the higher source priority
    (existing > log > task_log > git) wins.  Returns ``None`` if the list is
    empty.
    """
    if not candidates:
        return None

    def sort_key(c: Candidate):
        confidence = CONFIDENCE_RANK.get(c.confidence, 0)
        priority = _source_priority(c.source)
        return (-confidence, priority)

    return sorted(candidates, key=sort_key)[0]


def _generate_run_id(adventure_id: str, agent: str, task: str, model: str, timestamp: str) -> str:
    """Compute a deterministic 12-hex Run ID from the row's key fields."""
    canonical_key = f"{adventure_id}|{agent}|{task}|{model}|{timestamp}|"
    return hashlib.sha1(canonical_key.encode()).hexdigest()[:12]


def merge_candidates(
    task_id: str,
    candidates: List[Candidate],
    adventure_id: str,
) -> MetricsRow:
    """Merge multiple candidates into a single ``MetricsRow`` via field-level confidence ranking.

    Parameters
    ----------
    task_id:
        The task identifier (e.g. ``"ADV008-T001"`` or ``"-"``).
    candidates:
        All candidates for this task from all reconstructors.
    adventure_id:
        Adventure identifier (e.g. ``"ADV-008"``), used in Run ID generation.

    Returns
    -------
    MetricsRow
        Merged row with a deterministic Run ID.  Confidence is never
        ``"high"`` — if the best available confidence was ``"high"`` (from a
        prior hook-written row), it is downgraded to ``"medium"``.
    """
    # Per-field, select the best candidate.
    best_agent = _best_candidate_for_field(candidates, "agent")
    best_model = _best_candidate_for_field(candidates, "model")
    best_timestamp = _best_candidate_for_field(candidates, "timestamp")
    best_tokens_in = _best_candidate_for_field(candidates, "tokens_in")
    best_tokens_out = _best_candidate_for_field(candidates, "tokens_out")
    best_duration = _best_candidate_for_field(candidates, "duration_s")
    best_turns = _best_candidate_for_field(candidates, "turns")
    best_result = _best_candidate_for_field(candidates, "result")

    # Extract values, falling back to sensible defaults.
    agent = (best_agent.agent if best_agent else "unknown") or "unknown"
    model_raw = (best_model.model if best_model else "unknown") or "unknown"
    model = normalize_model(model_raw) if model_raw != "unknown" else "unknown"
    timestamp = (best_timestamp.timestamp if best_timestamp else "") or ""
    tokens_in = (best_tokens_in.tokens_in if best_tokens_in else 0) or 0
    tokens_out = (best_tokens_out.tokens_out if best_tokens_out else 0) or 0
    duration_s = (best_duration.duration_s if best_duration else 0) or 0
    turns = (best_turns.turns if best_turns else 0) or 0
    result = (best_result.result if best_result else "unknown") or "unknown"

    # Compute cost from model and tokens (silently zero if model is unknown).
    try:
        computed_cost = cost_for(model, tokens_in, tokens_out)
    except Exception:
        computed_cost = 0.0

    # Determine the overall row confidence = minimum across contributing candidates.
    # Backfill rows must never emit "high".
    all_confidences = [CONFIDENCE_RANK.get(c.confidence, 0) for c in candidates]
    if all_confidences:
        min_rank = min(all_confidences)
    else:
        min_rank = CONFIDENCE_RANK["estimated"]

    # Map rank back to name.
    rank_to_name = {v: k for k, v in CONFIDENCE_RANK.items()}
    row_confidence = rank_to_name.get(min_rank, "estimated")

    # Downgrade "high" to "medium" (backfill constraint).
    if row_confidence == "high":
        row_confidence = "medium"

    # If tokens came purely from estimation (zero from all sources), mark estimated.
    if tokens_in == 0 and tokens_out == 0 and all(c.tokens_in == 0 and c.tokens_out == 0 for c in candidates):
        row_confidence = "estimated"

    # Generate a stable Run ID.
    run_id = _generate_run_id(adventure_id, agent, task_id, model, timestamp)

    return MetricsRow(
        run_id=run_id,
        timestamp=timestamp,
        agent=agent,
        task=task_id,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        duration_s=duration_s,
        turns=turns,
        cost_usd=computed_cost,
        result=result,
        confidence=row_confidence,
    )


# ---------------------------------------------------------------------------
# 5. Unreconstructable task row
# ---------------------------------------------------------------------------


def make_unrecoverable_row(
    task_id: str,
    adventure_id: str,
    updated_ts: str,
) -> MetricsRow:
    """Create a sentinel row for a task with no reconstructable data.

    Parameters
    ----------
    task_id:
        Task identifier.
    adventure_id:
        Adventure identifier.
    updated_ts:
        The task file's ``updated`` timestamp or a fallback string.

    Returns
    -------
    MetricsRow
        Row with ``result="unrecoverable"``, ``confidence="estimated"``,
        and zero token/duration fields.
    """
    run_id = _generate_run_id(adventure_id, "unknown", task_id, "unknown", updated_ts)
    return MetricsRow(
        run_id=run_id,
        timestamp=updated_ts,
        agent="unknown",
        task=task_id,
        model="unknown",
        tokens_in=0,
        tokens_out=0,
        duration_s=0,
        turns=0,
        cost_usd=0.0,
        result="unrecoverable",
        confidence="estimated",
    )


# ---------------------------------------------------------------------------
# 6. Task discovery helpers
# ---------------------------------------------------------------------------

_RE_FM_DELIM = re.compile(r"^---\s*$")


def _parse_task_frontmatter(task_path: Path) -> dict:
    """Extract simple key:value frontmatter from a task file."""
    fm: dict = {}
    try:
        lines = task_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return fm

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
        if in_fm and ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip().lower()] = value.strip().strip('"').strip("'")
    return fm


def _discover_tasks(adv_path: Path) -> List[Path]:
    """Return all task files in *adv_path/tasks/*, sorted by name."""
    tasks_dir = adv_path / "tasks"
    if not tasks_dir.is_dir():
        return []
    return sorted(tasks_dir.glob("ADV*-T*.md"))


# ---------------------------------------------------------------------------
# 6. Full adventure reconstruction
# ---------------------------------------------------------------------------


def reconstruct_adventure(
    adv_path: Path,
    sources: List[str],
) -> List[MetricsRow]:
    """Discover tasks, collect candidates, merge per task, sort by timestamp.

    Parameters
    ----------
    adv_path:
        Path to the adventure directory.
    sources:
        Which reconstructors to use.

    Returns
    -------
    list[MetricsRow]
        Complete set of merged rows, sorted by timestamp (empty timestamps sort
        last).  Adventure-level rows (task ``"-"``) appear first.
    """
    adventure_id = adv_path.name
    task_files = _discover_tasks(adv_path)

    # Collect all candidates grouped by task_id.
    grouped = collect_candidates(adv_path, sources)

    rows: List[MetricsRow] = []
    processed_tasks: set = set()

    # Process per-task rows discovered from task files.
    for task_file in task_files:
        task_id = task_file.stem  # e.g. "ADV010-T001"
        fm = _parse_task_frontmatter(task_file)
        status = fm.get("status", "").lower()

        candidates = grouped.get(task_id, [])

        if candidates:
            row = merge_candidates(task_id, candidates, adventure_id)
        else:
            # No candidates from any source — emit unrecoverable row only for
            # completed tasks; skip open/in-progress tasks entirely.
            if status in ("done", "complete", "completed"):
                updated_ts = fm.get("updated", "")
                row = make_unrecoverable_row(task_id, adventure_id, updated_ts)
            else:
                # Task is not complete — skip.
                continue

        rows.append(row)
        processed_tasks.add(task_id)

    # Also include any adventure-level (task="-") rows from the existing metrics.
    for task_id, candidates in grouped.items():
        if task_id in processed_tasks:
            continue
        if not candidates:
            continue
        row = merge_candidates(task_id, candidates, adventure_id)
        rows.append(row)

    # Sort rows: non-empty timestamps first, then by timestamp string; empty last.
    def _sort_key(r: MetricsRow):
        return (0 if r.timestamp else 1, r.timestamp or "")

    rows.sort(key=_sort_key)
    return rows


# ---------------------------------------------------------------------------
# 7. Metrics file generation
# ---------------------------------------------------------------------------


def _serialize_frontmatter(data: dict) -> str:
    """Serialize *data* to a ``---``-fenced YAML-subset block."""
    lines = ["---\n"]
    emitted: set = set()
    for key in _FRONTMATTER_KEY_ORDER:
        if key in data:
            value = data[key]
            if isinstance(value, float):
                lines.append(f"{key}: {value:.4f}\n")
            else:
                lines.append(f"{key}: {value}\n")
            emitted.add(key)
    for key in sorted(data.keys()):
        if key not in emitted:
            value = data[key]
            if isinstance(value, float):
                lines.append(f"{key}: {value:.4f}\n")
            else:
                lines.append(f"{key}: {value}\n")
    lines.append("---\n")
    return "".join(lines)


def write_metrics_new(adv_path: Path, rows: List[MetricsRow]) -> Path:
    """Write the merged rows to ``metrics.md.new``.

    Parameters
    ----------
    adv_path:
        Adventure directory path.
    rows:
        Merged MetricsRow instances to write.

    Returns
    -------
    Path
        The path of the newly written ``metrics.md.new`` file.
    """
    adventure_id = adv_path.name

    # Compute frontmatter aggregates.
    total_tokens_in = sum(r.tokens_in for r in rows)
    total_tokens_out = sum(r.tokens_out for r in rows)
    total_duration_s = sum(r.duration_s for r in rows)
    total_cost = round(sum(r.cost_usd for r in rows), 4)
    agent_runs = len(rows)

    # Format total_duration as a human-friendly string.
    total_duration = _format_duration(total_duration_s)

    frontmatter = _serialize_frontmatter({
        "adventure_id": adventure_id,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_duration": total_duration,
        "total_cost": total_cost,
        "agent_runs": agent_runs,
    })

    # Build the table.
    table_lines = ["\n## Agent Runs\n\n", ROW_HEADER + "\n", ROW_SEPARATOR + "\n"]
    for row in rows:
        table_lines.append(serialize(row) + "\n")

    content = frontmatter + "".join(table_lines)

    new_path = adv_path / "metrics.md.new"
    new_path.write_text(content, encoding="utf-8")
    return new_path


def _format_duration(seconds: int) -> str:
    """Render *seconds* as a human-friendly duration string."""
    if seconds < 0:
        seconds = 0
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


# ---------------------------------------------------------------------------
# 8. Diff generation
# ---------------------------------------------------------------------------


def generate_diff(original: Path, new: Path) -> str:
    """Produce a unified diff between *original* and *new*.

    If *original* does not exist, the diff shows all lines as additions.

    Parameters
    ----------
    original:
        Existing ``metrics.md`` (may not exist).
    new:
        Newly generated ``metrics.md.new``.

    Returns
    -------
    str
        Unified diff string (empty string if no changes).
    """
    if original.exists():
        original_lines = original.read_text(encoding="utf-8").splitlines(keepends=True)
    else:
        original_lines = []

    new_lines = new.read_text(encoding="utf-8").splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=str(original),
            tofile=str(new),
        )
    )
    return "".join(diff_lines)


# ---------------------------------------------------------------------------
# 9. Apply with backup
# ---------------------------------------------------------------------------


def apply_with_backup(adv_path: Path) -> Path:
    """Atomically apply ``metrics.md.new`` to ``metrics.md`` with a backup.

    Steps:
    1. Rename ``metrics.md`` to ``metrics.md.backup.<timestamp>``.
    2. Rename ``metrics.md.new`` to ``metrics.md``.

    Parameters
    ----------
    adv_path:
        Adventure directory path.

    Returns
    -------
    Path
        The backup path (``metrics.md.backup.<timestamp>``).

    Raises
    ------
    SystemExit
        If ``metrics.md.new`` does not exist.
    """
    new_path = adv_path / "metrics.md.new"
    if not new_path.exists():
        print(f"error: {new_path} does not exist; nothing to apply", file=sys.stderr)
        sys.exit(1)

    ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = adv_path / f"metrics.md.backup.{ts}"
    original_path = adv_path / "metrics.md"

    if original_path.exists():
        os.replace(str(original_path), str(backup_path))

    os.replace(str(new_path), str(original_path))
    return backup_path


# ---------------------------------------------------------------------------
# 10. CLI parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the backfill CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m telemetry.tools.backfill",
        description=(
            "Reconstruct and backfill metrics.md from multiple evidence sources. "
            "By default, writes metrics.md.new and prints a diff (dry-run). "
            "Use --apply to rename the original and apply the new file."
        ),
    )

    adventure_group = parser.add_mutually_exclusive_group(required=True)
    adventure_group.add_argument(
        "--adventure",
        metavar="ADV-NNN",
        help="Process a single adventure (e.g. ADV-008).",
    )
    adventure_group.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Process all ADV-* adventures under .agent/adventures/.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help=(
            "Apply the generated metrics.md.new (rename original to "
            "metrics.md.backup.<ts> and rename .new to metrics.md)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview-only mode (default behaviour; explicit intent signal).",
    )
    parser.add_argument(
        "--sources",
        default=",".join(ALL_SOURCES),
        help=(
            f"Comma-separated list of sources to use "
            f"(default: {','.join(ALL_SOURCES)}). "
            "Valid values: existing, log, git, task_log."
        ),
    )

    return parser


# ---------------------------------------------------------------------------
# 11. Main entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point.

    Parameters
    ----------
    argv:
        Argument list (defaults to ``sys.argv[1:]``).

    Returns
    -------
    int
        Exit code: 0 = success, 1 = error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Parse sources.
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    invalid = [s for s in sources if s not in ALL_SOURCES]
    if invalid:
        print(f"error: unknown sources: {invalid}; valid: {ALL_SOURCES}", file=sys.stderr)
        return 1

    # Discover adventures.
    adventures = discover_adventures(
        adventure_filter=args.adventure,
        use_all=args.all,
    )

    if not adventures:
        print("No adventures found to process.", file=sys.stderr)
        return 1

    total_rows = 0
    total_unrecoverable = 0
    adventures_processed = 0

    for adv_path in adventures:
        adventure_id = adv_path.name
        print(f"\n=== Processing {adventure_id} ===")

        try:
            rows = reconstruct_adventure(adv_path, sources)
        except Exception as exc:
            print(f"error: failed to reconstruct {adventure_id}: {exc}", file=sys.stderr)
            return 1

        unrecoverable = sum(1 for r in rows if r.result == "unrecoverable")

        try:
            new_path = write_metrics_new(adv_path, rows)
        except Exception as exc:
            print(f"error: failed to write metrics.md.new for {adventure_id}: {exc}", file=sys.stderr)
            return 1

        original_path = adv_path / "metrics.md"
        diff = generate_diff(original_path, new_path)

        if diff:
            print(diff, end="")
        else:
            print("(no changes)")

        if args.apply and not args.dry_run:
            try:
                backup_path = apply_with_backup(adv_path)
                print(f"Applied: original backed up to {backup_path}")
            except SystemExit:
                return 1
        else:
            print(f"Dry run complete — review {new_path}")

        total_rows += len(rows)
        total_unrecoverable += unrecoverable
        adventures_processed += 1

    print(
        f"\nSummary: {adventures_processed} adventure(s) processed, "
        f"{total_rows} row(s) total, {total_unrecoverable} unrecoverable."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
