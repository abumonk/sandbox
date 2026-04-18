# Backfill Merge + CLI + Reversibility - Design

## Approach
Implement `.agent/telemetry/tools/backfill.py` as a single-file CLI module that:
1. Collects `List[Candidate]` from each reconstructor (T011's output)
2. Merges candidates per-task using field-level confidence ranking
3. Emits a complete `metrics.md.new` with frontmatter via the aggregator
4. Produces a unified diff for review
5. Optionally applies via atomic rename with timestamped backup

The module is stdlib-only Python. It imports from sibling packages: `reconstructors.*`, `../schema.py`, `../cost_model.py`, `../aggregator.py`.

## Target Files
- `.agent/telemetry/tools/backfill.py` - New file. The entire CLI and merge logic.

## Implementation Steps

### 1. Imports and constants
- Import `argparse`, `datetime`, `difflib`, `os`, `shutil`, `hashlib`, `pathlib`
- Import from `..schema` (`MetricsRow`, `serialize_row`, `parse_row`)
- Import from `..cost_model` (`cost_for`)
- Import from `..aggregator` (`recompute_frontmatter`, `parse_rows`)
- Import from `.reconstructors` (`existing_rows`, `log_parser`, `git_windows`, `task_logs`)
- Define `ADVENTURES_ROOT = Path(".agent/adventures")`
- Define `ALL_SOURCES = ["existing", "log", "git", "task_log"]`
- Define confidence ranking: `CONFIDENCE_RANK = {"high": 4, "medium": 3, "low": 2, "estimated": 1}`

### 2. Adventure discovery
```python
def discover_adventures(adventure_filter: str | None) -> List[Path]:
```
- If `--adventure ADV-NNN`: return `[ADVENTURES_ROOT / "ADV-NNN"]` (validate exists)
- If `--all`: glob `ADVENTURES_ROOT / "ADV-*"`, sort, return all

### 3. Candidate collection
```python
def collect_candidates(adv_path: Path, sources: List[str]) -> Dict[str, List[Candidate]]:
```
- For each enabled source, call the corresponding reconstructor
- Group results by `task_id` into a `Dict[str, List[Candidate]]`
- Each reconstructor returns `List[Candidate]` per T011's contract

### 4. Per-task merge (field-level confidence ranking)
```python
def merge_candidates(task_id: str, candidates: List[Candidate], adventure_id: str) -> MetricsRow:
```
- For each field in MetricsRow (agent, model, tokens_in, tokens_out, duration_s, turns, cost_usd, result):
  - Pick the value from the candidate with the highest confidence for that field
  - If tied, prefer source priority: existing > log > task_log > git
- Confidence of the merged row = minimum confidence across all contributing fields
- Never emit `confidence: high` (backfill constraint from role doc)
  - If an existing row had `high`, downgrade to `medium`
- Run ID generation: `sha1(f"{adventure_id}|{agent}|{task_id}|{model}|{timestamp}|")[:12]`
  - Deterministic from row content, so stable across runs (idempotency)
- If tokens came from prior estimation (not a source), set confidence to `estimated`
- Cost: call `cost_for(model, tokens_in, tokens_out)` from cost_model

### 5. Unreconstructable task handling
```python
def make_unrecoverable_row(task_id: str, adventure_id: str, updated_ts: str) -> MetricsRow:
```
- If a task file exists with `status: done/complete` but zero candidates from any source:
  - Emit row with `result: unrecoverable`, `confidence: estimated`, all token/duration fields = 0
  - Use `adventure.updated` timestamp as the row timestamp
  - Model = `unknown`, Agent = `unknown`

### 6. Full adventure reconstruction
```python
def reconstruct_adventure(adv_path: Path, sources: List[str]) -> List[MetricsRow]:
```
- Discover all tasks for the adventure (glob `tasks/ADVNNN-T*.md`)
- Collect candidates, merge per-task
- Sort rows by timestamp
- Return the complete row set

### 7. Metrics file generation
```python
def write_metrics_new(adv_path: Path, rows: List[MetricsRow]) -> Path:
```
- Compute frontmatter totals from rows (same logic as aggregator.recompute_frontmatter)
- Write YAML frontmatter + `## Agent Runs` header + pipe-table header/separator + rows
- Output to `adv_path / "metrics.md.new"`
- Return the path

### 8. Diff generation
```python
def generate_diff(original: Path, new: Path) -> str:
```
- Read both files as line lists
- Use `difflib.unified_diff(original_lines, new_lines, fromfile=str(original), tofile=str(new))`
- Return the diff string

### 9. Apply with backup
```python
def apply_with_backup(adv_path: Path) -> Path:
```
- `ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")`
- `backup_path = adv_path / f"metrics.md.backup.{ts}"`
- `os.rename(adv_path / "metrics.md", backup_path)`
- `os.rename(adv_path / "metrics.md.new", adv_path / "metrics.md")`
- Return `backup_path`

### 10. CLI argument parser
```python
def build_parser() -> argparse.ArgumentParser:
```
- `--adventure ADV-NNN` (mutually exclusive with `--all`)
- `--all` (process all adventures)
- `--apply` (apply changes; default is preview-only)
- `--dry-run` (synonym for no-apply; explicit intent signal)
- `--sources existing,log,git,task_log` (comma-separated; default all)

### 11. Main entry point
```python
def main(argv: List[str] | None = None) -> int:
```
- Parse args
- Discover adventures
- For each adventure:
  - Reconstruct rows
  - Write `metrics.md.new`
  - Generate and print diff to stdout
  - If `--apply`: call `apply_with_backup`, print backup path
  - If not `--apply`: print "dry run complete, review metrics.md.new"
- Print summary: total adventures processed, total rows, unrecoverable count
- Return 0 on success, 1 on error

```python
if __name__ == "__main__":
    sys.exit(main())
```

### 12. Idempotency guarantee
- Run ID is computed deterministically from row content fields (adventure_id, agent, task_id, model, timestamp, empty session_id)
- Same input always produces the same Run ID
- `metrics.md.new` content is deterministic given the same source data
- Second run on unchanged sources produces byte-identical output

## Testing Strategy
- TC-BF-3 (idempotency): Run backfill twice on a fixture adventure; assert second `metrics.md.new` is byte-identical to first
- TC-BF-4 (confidence never high): Assert every row in output has confidence in {medium, low, estimated}
- TC-BF-5 (unreconstructable): Create a fixture task with status:done but no log/git/row evidence; assert output row has `result: unrecoverable`
- TC-BF-6 (reversibility): Run without `--apply`; assert original `metrics.md` is byte-identical to pre-run copy
- Manual smoke test: `python -m telemetry.tools.backfill --adventure ADV-008 --dry-run` should emit a diff showing tilde-stripped tokens and added Confidence/Run ID columns

## Risks
- **Reconstructor interface drift**: If T011's `Candidate` shape differs from what this merge logic expects, integration will break. Mitigated by the shared design-backfill-strategy.md contract and the `Candidate` type being defined in T011's `__init__.py`.
- **Windows path handling**: `os.rename` on Windows may fail if target exists. Use `os.replace()` for atomic rename semantics (as specified in design-aggregation-rules.md).
- **Large adventure row counts**: ADV-008 has 34 existing rows. The merge must handle this without performance issues (trivial at this scale).
- **Timestamp ordering**: If reconstructed timestamps from different sources disagree, the row ordering may vary. The merge picks highest-confidence timestamp per task, so this is deterministic.
