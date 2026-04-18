# Implement Automated Tests (ADV010-T016) - Design

## Approach

Create 11 test files (9 test modules + conftest.py + __init__.py) under `.agent/adventures/ADV-010/tests/` using stdlib `unittest` only. Each file maps directly to the TC-to-function table in `design-test-strategy.md`. Tests import from `.agent.telemetry.*` modules (schema, cost_model, capture, aggregator, task_actuals, errors, tools.backfill). File-writing tests use `tempfile.TemporaryDirectory`. Subprocess tests drive `capture.py` via `subprocess.run` with stdin piping. The live canary test (`test_live_canary.py`) uses `@unittest.skipUnless` to gate on fixture presence.

## Target Files

- `.agent/adventures/ADV-010/tests/__init__.py` - Empty package init to enable `unittest discover`.
- `.agent/adventures/ADV-010/tests/conftest.py` - Shared helpers: `FIXTURES_DIR`, `load_event_fixture(name)`, `make_temp_metrics(rows, frontmatter)`, `make_temp_manifest(task_rows)`, `REPO_ROOT`, `TELEMETRY_DIR`. Also a `sys.path` insert so telemetry modules are importable.
- `.agent/adventures/ADV-010/tests/test_schema.py` - 3 tests covering TC-S-1..TC-S-3: row header column order, frontmatter key set, type coercion rejection.
- `.agent/adventures/ADV-010/tests/test_cost_model.py` - 4 tests covering TC-CM-1..TC-CM-4: opus cost fixture, unknown model error, alias normalization (6+ cases), config.md rate loading.
- `.agent/adventures/ADV-010/tests/test_capture.py` - 7 tests covering TC-CC-1..TC-CC-4, TC-HI-1..TC-HI-3: payload validation rejects (10 bad fixtures), valid event writes one row, replay idempotency, cost match, settings.json hooks presence, permissions preservation, subprocess happy path.
- `.agent/adventures/ADV-010/tests/test_aggregator.py` - 4 tests covering TC-AG-1..TC-AG-3, TC-AG-6: tokens_in sum, all frontmatter totals, recompute idempotency, format_duration table-driven (6+ cases).
- `.agent/adventures/ADV-010/tests/test_task_actuals.py` - 2 tests covering TC-AG-4..TC-AG-5: actuals values match hand-computed, other rows byte-equal.
- `.agent/adventures/ADV-010/tests/test_error_isolation.py` - 6 tests covering TC-EI-1..TC-EI-5, TC-HI-4: payload error exit 0, write error exit 0 + log line, KeyboardInterrupt propagates, error log JSONL validity, frontmatter heals after partial fail, malformed JSON exits 0.
- `.agent/adventures/ADV-010/tests/test_backfill.py` - 6 tests covering TC-BF-1..TC-BF-6: completed adventures have runs, ADV-008 rows preserved/tildes stripped, idempotency, no high confidence, unreconstructable row emitted, no-apply does not modify original.
- `.agent/adventures/ADV-010/tests/test_live_canary.py` - 1 test covering TC-LC-1: ADV-009 canary row populated. Gated by `@unittest.skipUnless(os.path.exists(CANARY_FIXTURE_PATH))`.
- `.agent/adventures/ADV-010/tests/test_regression.py` - 1 test covering TC-RG-1: subprocess-invokes `python -m unittest discover` and asserts exit 0.

## Implementation Steps

### Step 1: `__init__.py` and `conftest.py`

1. Create empty `__init__.py`.
2. Create `conftest.py` with:
   - `REPO_ROOT = Path(__file__).resolve().parents[4]` (navigates up from tests/ to Sandbox/).
   - `sys.path.insert(0, str(REPO_ROOT))` so `from .agent.telemetry import ...` works, or set up the import path so modules under `.agent/telemetry/` are importable (may need a `telemetry` package-style import or direct path manipulation).
   - `FIXTURES_DIR = Path(__file__).parent / "fixtures"`.
   - `TELEMETRY_DIR = REPO_ROOT / ".agent" / "telemetry"`.
   - Helper: `load_event_fixture(name: str) -> dict` - reads and parses `fixtures/events/{name}.json`.
   - Helper: `make_temp_metrics(tmpdir: Path, rows: list[str], frontmatter: dict) -> Path` - creates a `metrics.md` in a temp directory with given frontmatter and rows.
   - Helper: `make_temp_manifest(tmpdir: Path, task_rows: list[dict]) -> Path` - creates a manifest with an `## Evaluations` pipe-table.

### Step 2: `test_schema.py` (TC-S-1, TC-S-2, TC-S-3)

1. `test_row_header_columns_exact`: Import the row header constant/function from `schema.py`, assert it equals the exact 12-column pipe-separated header string from `row_schema.md`.
2. `test_frontmatter_keys_exact`: Assert the set of frontmatter keys is exactly `{adventure_id, total_tokens_in, total_tokens_out, total_duration, total_cost, agent_runs}`.
3. `test_row_type_coercion`: Feed rows with non-int token columns, bad Run ID format, duplicate Run ID to the row parser. Assert each raises `SchemaError`.

### Step 3: `test_cost_model.py` (TC-CM-1..TC-CM-4)

1. `test_cost_for_opus_known_fixture`: `cost_for("opus", 85000, 28000)` == `round((85000+28000)/1000.0 * 0.015, 4)` == `1.6950`. Assert to 4dp.
2. `test_unknown_model_raises`: `cost_for("unknown-model-xyz", 1, 1)` raises `UnknownModelError`.
3. `test_normalize_model_aliases`: Table-driven test with >= 6 aliases: `claude-opus-4-6` -> `opus`, `claude-sonnet-4` -> `sonnet`, `sonnet-4` -> `sonnet`, `claude-haiku-3` -> `haiku`, `haiku-3` -> `haiku`, `opus` -> `opus`.
4. `test_load_rates_from_config_md`: Load rates from actual `.agent/config.md`, assert result == `{"opus": 0.015, "sonnet": 0.003, "haiku": 0.001}`.

### Step 4: `test_capture.py` (TC-CC-1..TC-CC-4, TC-HI-1..TC-HI-3)

1. `test_validate_event_rejects_invalid`: Load 10 bad fixture variants (missing field, negative tokens, zero duration, bad model, bad adventure_id format, bad task format, etc.). Each must raise `CaptureError` or subclass.
2. `test_valid_event_writes_one_row`: In a temp dir, run capture logic with `happy_opus.json` fixture. Assert exactly one row appended with correct column values.
3. `test_replay_same_event_idempotent`: Run capture twice with the same event. Assert still one row (Run ID dedup).
4. `test_row_cost_matches_cost_model`: After capture, parse the row's Cost column and compare to `cost_for(model, tokens_in, tokens_out)`.
5. `test_settings_json_has_both_hooks`: Read `.claude/settings.local.json`, assert `hooks.SubagentStop` and `hooks.PostToolUse` keys exist and point to `capture.py`.
6. `test_settings_json_preserves_permissions`: Read settings, assert `permissions.allow` has exactly 128 entries (or the known count).
7. `test_capture_subprocess_happy_path`: Pipe `happy_opus.json` to `python .agent/telemetry/capture.py` via subprocess. Assert exit 0 and a row appears in the target metrics.md. Use a temp dir with `ADVENTURE_ID` env var or mock the metrics path.

### Step 5: `test_aggregator.py` (TC-AG-1..TC-AG-3, TC-AG-6)

1. `test_total_tokens_in_matches_rows`: Create a metrics fixture with known rows, run `recompute_frontmatter`, assert `total_tokens_in` equals row sum.
2. `test_all_frontmatter_totals_match_rows`: Same fixture, check all 5 frontmatter fields.
3. `test_recompute_idempotent`: Run `recompute_frontmatter` twice on the same file, assert byte-identical output.
4. `test_format_duration_table_driven`: 6+ cases including `0 -> "0s"`, `95 -> "95s"`, `960 -> "16min"`, `3600 -> "1h 0min"`, `8100 -> "2h 15min"`, `60 -> "1min"`.

### Step 6: `test_task_actuals.py` (TC-AG-4, TC-AG-5)

1. `test_update_task_actuals_values`: Create temp manifest + metrics fixtures with known values. Run `update_task_actuals`. Assert Actual Duration, Actual Tokens, Actual Cost, Variance match hand-computed values.
2. `test_update_leaves_other_rows_byte_equal`: Same setup with multiple tasks. Update one task. Assert all other rows unchanged byte-for-byte.

### Step 7: `test_error_isolation.py` (TC-EI-1..TC-EI-5, TC-HI-4)

1. `test_payload_error_exit_zero`: Subprocess with invalid payload -> assert returncode == 0.
2. `test_write_error_logs_and_exits_zero`: Create read-only metrics.md in temp dir, pipe valid event, assert exit 0 and one line in capture-errors.log.
3. `test_keyboard_interrupt_propagates`: Patch `main()` internals to raise KeyboardInterrupt, assert it propagates (not caught).
4. `test_error_log_is_valid_jsonl`: After triggering errors, read capture-errors.log, parse each line as JSON, assert keys `ts`, `exc`, `msg`.
5. `test_frontmatter_heals_after_partial_fail`: Write a metrics.md with a row but stale frontmatter (wrong totals). Run capture with a new event. Assert frontmatter now matches all rows.
6. `test_malformed_json_exits_zero`: Pipe `malformed.txt` (not valid JSON) to capture.py subprocess. Assert exit 0.

### Step 8: `test_backfill.py` (TC-BF-1..TC-BF-6)

All tests operate on temp directories with synthetic adventure structures, not real `.agent/adventures/` directories.

1. `test_every_completed_adventure_has_runs`: Create temp adventure dirs (mimicking ADV-001..ADV-009 structure) with log files and task files. Run backfill. Assert each metrics.md has `agent_runs > 0`.
2. `test_adv008_rows_preserved_tildes_stripped`: Create a metrics fixture mimicking ADV-008's 34-row corpus with tildes. Run backfill. Assert numeric values preserved, tildes removed from output.
3. `test_backfill_idempotent`: Run backfill twice. Assert second output is byte-identical to first.
4. `test_backfill_rows_never_high_confidence`: After backfill, parse all rows. Assert no row has `Confidence == "high"`.
5. `test_unreconstructable_row_emitted`: Create a task file with `status: done` but no log/git/row evidence. Run backfill. Assert a row with `result=unrecoverable` exists.
6. `test_no_apply_does_not_modify_original`: Run backfill without `--apply`. Assert original metrics.md is unmodified (byte-compare).

### Step 9: `test_live_canary.py` (TC-LC-1)

1. `test_adv009_canary_row_populated`: Gated by `@unittest.skipUnless(os.path.exists(...canary fixture path...))`. When present, read the canary fixture snapshot (pre/post metrics.md). Assert the post-snapshot has a new row with non-zero tokens and frontmatter totals match row sums.

### Step 10: `test_regression.py` (TC-RG-1)

1. `test_full_discover_exits_zero`: `subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", TESTS_DIR, "-v"], capture_output=True, timeout=60)`. Assert returncode == 0.

### Step 11: Run full suite and verify

Run `python -m unittest discover -s .agent/adventures/ADV-010/tests -v` and confirm exit 0. If any test fails, fix and re-run.

## Testing Strategy

The tests ARE the deliverable. Verification is:
1. `python -m unittest discover -s .agent/adventures/ADV-010/tests -v` exits 0.
2. Grep all test files for TC IDs to confirm every `autotest` TC appears.
3. `test_regression.py` itself re-invokes discover as a meta-test.

## Risks

1. **Import path complexity**: `.agent` directory has a leading dot, which complicates Python imports. `conftest.py` must handle `sys.path` manipulation carefully. May need to use `importlib` or path-based imports.
2. **Fixture availability**: T015 (test fixtures) is still in `planning` stage. The implementer must either wait for T015 to complete or create minimal inline fixtures within each test.
3. **Subprocess tests on Windows**: Path separators and `sys.executable` must be used consistently. All subprocess calls should use `[sys.executable, "-m", ...]` form.
4. **Backfill test complexity**: TC-BF-1 requires recreating adventure directory structures in temp dirs, which adds setup complexity. Keep fixtures minimal.
5. **Token budget**: At 90K estimated tokens, this is the largest task. The checkpoint-at-3-files strategy should be followed; if budget pressure mounts, split into T016a/T016b per the task's NOTE.
