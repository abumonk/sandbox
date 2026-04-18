# Backfill Tool -- Reconstructors - Design

## Approach
Implement four reconstructor submodules under `.agent/telemetry/tools/reconstructors/`, each responsible for extracting telemetry candidates from a different data source. All reconstructors share a common interface: they accept a path or adventure ID and return `List[Candidate]`. A `Candidate` is a `MetricsRow` (from T005's `schema.py`) extended with a `source: str` field and a `confidence: str` override. The reconstructors are pure data extractors with no side effects -- the merge/write logic lives in T012's `backfill.py`.

Stdlib-only constraint: all parsing uses `re`, `datetime`, `subprocess`, `pathlib`, `dataclasses`. No third-party dependencies.

## Target Files
- `.agent/telemetry/tools/__init__.py` - Empty package init to make `telemetry.tools` importable
- `.agent/telemetry/tools/reconstructors/__init__.py` - Package init exporting `Candidate` dataclass and the four parse functions
- `.agent/telemetry/tools/reconstructors/existing_rows.py` - Parse existing `metrics.md` pipe-tables into candidates
- `.agent/telemetry/tools/reconstructors/log_parser.py` - Parse `adventure.log` to extract spawn/complete event pairs
- `.agent/telemetry/tools/reconstructors/git_windows.py` - Shell out to `git log` to derive per-task commit windows
- `.agent/telemetry/tools/reconstructors/task_logs.py` - Read task-file `## Log` sections for status transitions

## Implementation Steps

### Step 1: Define `Candidate` dataclass in `reconstructors/__init__.py`

```python
@dataclasses.dataclass(frozen=True)
class Candidate:
    run_id: str          # 12-hex or empty (generated later by merge)
    timestamp: str       # ISO-8601 UTC
    agent: str
    task: str
    model: str
    tokens_in: int
    tokens_out: int
    duration_s: int
    turns: int
    cost: float
    result: str
    confidence: str      # medium | low | estimated (never high)
    source: str          # "existing" | "log" | "git" | "task_log"
```

Export the four parse functions from `__init__.py` for convenience:
```python
from .existing_rows import parse as parse_existing_rows
from .log_parser import parse as parse_log
from .git_windows import for_adventure as git_windows_for_adventure
from .task_logs import parse as parse_task_logs
```

### Step 2: Implement `existing_rows.py`

**Function**: `parse(metrics_path: Path) -> List[Candidate]`

Algorithm:
1. Read the file, locate the `## Agent Runs` section.
2. Find the pipe-table header row; validate column count.
3. Skip separator row (`|---|---|...`).
4. For each data row:
   a. Split on `|`, strip whitespace from each cell.
   b. Strip leading `~` from numeric fields (Tokens In, Tokens Out, Duration, Turns, Cost).
   c. Parse duration: handle `NNmin`, `NNs`, `NNmin NNs` formats, convert to integer seconds.
   d. Coerce tokens to `int`, cost to `float` (4dp).
   e. Set `confidence = "medium"` (existing rows with tildes were estimates; without tildes they are recorded but still not live-hook, so medium).
   f. Set `source = "existing"`.
   g. `run_id` left empty -- the merge step (T012) generates stable Run IDs.
   h. `timestamp` left empty -- no timestamp column in legacy format.
5. Return `List[Candidate]`.

**Edge cases**:
- Rows with `~` prefix on tokens (e.g. `~18000`) -- strip the `~`, keep the number, note confidence stays `medium`.
- Duration as `95s`, `4min`, `120s`, `16min` -- regex: `r'(\d+)min|(\d+)s'`, sum all matches.
- Missing `## Agent Runs` section -- return empty list.
- Empty file or no pipe-table -- return empty list.

### Step 3: Implement `log_parser.py`

**Function**: `parse(log_path: Path) -> List[Candidate]`

Algorithm:
1. Read the adventure.log file line by line.
2. Parse each line with regex: `r'\[([^\]]+)\]\s+(\S+)\s+\|\s+"(.+)"'`
   - Group 1: timestamp (ISO-8601)
   - Group 2: agent name
   - Group 3: message body
3. Identify spawn events: message matches `r'spawn:\s+(\S+)\s+'` -- extract task ID.
4. Identify complete events: message starts with `"complete:"` or contains `"complete:"`.
5. Pair spawn+complete by agent identity (same agent, sequential):
   - Track open spawns: `Dict[str, (task_id, timestamp)]`.
   - On complete for an agent: compute `duration_s = complete_ts - spawn_ts`.
6. For each paired event, produce a Candidate:
   - `timestamp` = spawn timestamp.
   - `agent` = agent name from log line.
   - `task` = extracted task ID (or `-` if not a task-specific spawn).
   - `model` = `"unknown"` (logs do not record model).
   - `tokens_in = 0`, `tokens_out = 0` (no token data in logs).
   - `duration_s` = computed delta in seconds.
   - `turns = 0` (not available from logs).
   - `cost = 0.0`.
   - `confidence = "low"` (single source, only duration is concrete).
   - `source = "log"`.
7. Return all candidates including unpaired spawns (with `duration_s = 0`, `result = "incomplete"`).

**Edge cases**:
- Agents that spawn multiple tasks sequentially (close previous on next spawn).
- Out-of-order timestamps in log (sort by timestamp before pairing).
- Log lines not matching the pattern -- skip silently.

### Step 4: Implement `git_windows.py`

**Function**: `for_adventure(adventure_id: str, repo_root: Path | None = None) -> List[Candidate]`

Algorithm:
1. Resolve `repo_root` (default: walk up from `__file__` to find `.git`).
2. Determine the adventure path prefix: `.agent/adventures/{adventure_id}/`.
3. Run: `git log --pretty=format:"%H|%ai|%s" --name-only -- {adventure_path_prefix}` via `subprocess.run`.
4. Parse output into commit records: `(hash, datetime, subject, [file_paths])`.
5. For each file path, extract task ID if it matches `r'tasks/({adventure_id_prefix}-T\d+)\.md'` or similar patterns (designs, tests referencing a task).
6. Group commits by task ID.
7. For each task:
   - `first_commit_ts` = earliest commit touching that task's files.
   - `last_commit_ts` = latest commit touching that task's files.
   - `duration_s = (last - first).total_seconds()`, minimum 1.
8. Produce a Candidate per task:
   - `timestamp` = first_commit_ts (ISO-8601 UTC).
   - `agent = "unknown"` (git does not record agent identity).
   - `task` = task ID.
   - `model = "unknown"`.
   - `tokens_in = 0`, `tokens_out = 0`.
   - `duration_s` = computed window.
   - `turns = 0`, `cost = 0.0`.
   - `confidence = "low"` (single source, only duration bounds).
   - `source = "git"`.
9. Return list.

**Edge cases**:
- Task with only one commit -- duration_s = 0, still emit candidate.
- No git history for adventure path -- return empty list.
- `subprocess` failure (not a git repo) -- raise a descriptive error.
- Adventure path prefix must use forward slashes for git regardless of OS.

### Step 5: Implement `task_logs.py`

**Function**: `parse(tasks_dir: Path) -> List[Candidate]`

Algorithm:
1. Glob `tasks_dir / "*.md"` to find all task files.
2. For each task file:
   a. Extract task ID from filename (e.g. `ADV008-T01.md` -> `ADV008-T01`).
   b. Read the file; locate the `## Log` section.
   c. Parse each log entry with regex: `r'\[([^\]]+)\]\s+(\w[\w-]*):\s+(.+)'`.
      - Group 1: timestamp, Group 2: author/agent, Group 3: message.
   d. Identify the `created:` entry (first timestamp) and the last status-changing entry (e.g. containing `status=done`, `PASSED`, `complete`).
   e. Compute `duration_s = last_ts - first_ts`.
   f. Extract `assignee` from frontmatter (YAML `assignee:` field) as agent name.
   g. Extract `status` from frontmatter as result hint.
3. Produce a Candidate per task:
   - `timestamp` = created timestamp.
   - `agent` = assignee from frontmatter (or first log entry author).
   - `task` = task ID.
   - `model = "unknown"`.
   - `tokens_in = 0`, `tokens_out = 0`.
   - `duration_s` = computed delta.
   - `turns = 0`, `cost = 0.0`.
   - `confidence = "low"` (single source).
   - `source = "task_log"`.
4. Return list.

**Edge cases**:
- Task file with no `## Log` section -- skip, return no candidate for that task.
- Task file with only a `created:` entry and no subsequent entries -- `duration_s = 0`.
- Frontmatter parsing: simple line-by-line scan for `assignee:` and `status:` between `---` delimiters.

### Step 6: Wire up `tools/__init__.py`

Minimal package init. May optionally re-export key symbols but primarily exists to make `python -m telemetry.tools.backfill` work as a package path.

```python
"""Telemetry tools — backfill reconstructors and CLI."""
```

## Testing Strategy

Each reconstructor gets at least one fixture-based unit test using actual data from ADV-008:

1. **`test_existing_rows_parse`**: Feed `ADV-008/metrics.md` to `existing_rows.parse()`. Assert:
   - Returns exactly 34 candidates (matching the 34 data rows).
   - No candidate has `~` in any field.
   - All `tokens_in` and `tokens_out` are integers.
   - All `confidence` values are `"medium"`.
   - All `source` values are `"existing"`.
   - Duration fields are integer seconds (e.g. `"4min"` -> 240, `"95s"` -> 95).

2. **`test_log_parser_parse`**: Feed `ADV-008/adventure.log` to `log_parser.parse()`. Assert:
   - Returns >= 19 candidates (one per spawn event in the log).
   - Each candidate has a non-empty `task` or agent identifier.
   - Paired candidates have `duration_s > 0`.

3. **`test_git_windows_for_adventure`**: Call `git_windows.for_adventure("ADV-008")`. Assert:
   - Returns a non-empty list of candidates.
   - Each candidate has `source = "git"` and `confidence = "low"`.
   - Per-task windows have `duration_s >= 0`.

4. **`test_task_logs_parse`**: Feed `ADV-008/tasks/` to `task_logs.parse()`. Assert:
   - Returns candidates for tasks that have `## Log` sections.
   - Each candidate has a valid task ID matching `ADV008-T\d+`.
   - Duration is computed from log timestamps.

Tests live in `.agent/adventures/ADV-010/tests/test_reconstructors.py` (created by T016).

## Risks

1. **Duration format variability**: ADV-008 metrics.md uses `NNmin`, `NNs`, and mixed formats. The regex parser must handle all variants. Mitigation: comprehensive test with all observed formats.
2. **Git history depth**: Older adventures may have squashed commits, reducing the accuracy of git windows. Mitigation: `confidence = "low"` for git-sourced candidates; the merge step prefers higher-confidence sources.
3. **Log format drift**: Adventure logs across ADV-001..ADV-009 may have slightly different formats (quote styles, pipe placement). Mitigation: permissive regex with fallback to skip unparseable lines.
4. **subprocess on Windows**: `git log` invocation must use forward slashes in path arguments and handle Windows line endings. Mitigation: normalize paths with `pathlib.PurePosixPath` for the git filter argument; use `text=True` in subprocess.
5. **Circular dependency with schema.py (T005)**: Reconstructors depend on T005 for `MetricsRow` shape knowledge. Since T005 defines the schema, reconstructors import from it. Mitigation: T005 is listed as a dependency; the `Candidate` dataclass is self-contained (not a subclass of `MetricsRow`) to decouple at the type level.
