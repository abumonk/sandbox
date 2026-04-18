# Test Strategy — ADV-010 Telemetry Capture

## Discovery one-liner (CI)

```
python -m unittest discover -s .agent/adventures/ADV-010/tests -v
```

Exit 0 = adventure provable. This is the sole gate.

## Frameworks

- `unittest` (stdlib).
- `subprocess` (stdlib) for end-to-end tests that drive
  `capture.py` via stdin.
- `tempfile.TemporaryDirectory` for all file I/O.

No third-party test dependencies. Consistent with the
Python-stdlib-only constraint.

## Fixtures

Tests load static fixtures rather than generating data at runtime.
Three fixture categories live under `tests/fixtures/`:

| Category | Directory | Representative files |
|----------|-----------|----------------------|
| Event payloads (SubagentStop JSON) | `tests/fixtures/events/` | `valid_opus.json`, `missing_task_id.json`, `bad_run_id.json`, `duplicate_run_id.json` |
| metrics.md snapshots | `tests/fixtures/metrics/` | `single_row.md`, `multi_model.md`, `empty_rows.md`, `adv008_real.md`, `partial_write.md` |
| manifest snapshots | `tests/fixtures/manifests/` | `manifest_with_evals.md`, `manifest_canary_pre.md` |

Fixture files contain hand-computed expected values (token sums, cost
totals, frontmatter fields) so assertions are pure comparisons with no
live computation dependency.

## Per-file coverage

### `tests/test_schema.py`

Covers row schema and frontmatter key contract.

| Function | Asserts | TC |
|----------|---------|----|
| `test_row_header_columns_exact` | Header line equals the 12-column order | TC-S-1 |
| `test_frontmatter_keys_exact` | Frontmatter has exactly {adventure_id, total_tokens_in, total_tokens_out, total_duration, total_cost, agent_runs} | TC-S-2 |
| `test_row_type_coercion` | Parser rejects non-int in token column, bad Run ID format, duplicate Run ID | TC-S-3 |

### `tests/test_cost_model.py`

| Function | Asserts | TC |
|----------|---------|----|
| `test_cost_for_opus_known_fixture` | `cost_for("opus",85000,28000)` == hand-computed value to 4dp | TC-CM-1 |
| `test_unknown_model_raises` | `UnknownModelError` raised, not zero cost | TC-CM-2 |
| `test_normalize_model_aliases` | Table-driven over 6 aliases | TC-CM-3 |
| `test_load_rates_from_config_md` | Parses current `.agent/config.md` into exact expected dict | TC-CM-4 |

### `tests/test_capture.py`

End-to-end subprocess-driven tests. `capture.py` invoked with stdin.

| Function | Asserts | TC |
|----------|---------|----|
| `test_validate_event_rejects_invalid` | 10 bad fixtures, each raises or exits with 1 error-log line | TC-CC-1 |
| `test_valid_event_writes_one_row` | One row appended with every column correct | TC-CC-2 |
| `test_replay_same_event_idempotent` | Running twice leaves one row | TC-CC-3 |
| `test_row_cost_matches_cost_model` | Row's cost column equals cost_model output | TC-CC-4 |
| `test_settings_json_has_both_hooks` | `.claude/settings.local.json` contains SubagentStop + PostToolUse | TC-HI-1 |
| `test_settings_json_preserves_permissions` | 128-entry allow list preserved byte-for-byte after hook install | TC-HI-2 |
| `test_capture_subprocess_happy_path` | Subprocess stdin → row in fixture metrics.md | TC-HI-3 |

### `tests/test_aggregator.py`

| Function | Asserts | TC |
|----------|---------|----|
| `test_total_tokens_in_matches_rows` | Sum | TC-AG-1 |
| `test_all_frontmatter_totals_match_rows` | All 5 frontmatter fields sum | TC-AG-2 |
| `test_recompute_idempotent` | Byte-identical second run | TC-AG-3 |
| `test_format_duration_table_driven` | 6+ cases | TC-AG-6 |

### `tests/test_task_actuals.py`

| Function | Asserts | TC |
|----------|---------|----|
| `test_update_task_actuals_values` | Hand-computed Actual/Variance | TC-AG-4 |
| `test_update_leaves_other_rows_byte_equal` | Diff == 1 row | TC-AG-5 |

### `tests/test_error_isolation.py`

| Function | Asserts | TC |
|----------|---------|----|
| `test_payload_error_exit_zero` | Subprocess exits 0 | TC-EI-1 |
| `test_write_error_logs_and_exits_zero` | Read-only target → exit 0 + 1 log line | TC-EI-2 |
| `test_keyboard_interrupt_propagates` | KI not caught | TC-EI-3 |
| `test_error_log_is_valid_jsonl` | All lines parse as JSON with {ts,exc,msg} | TC-EI-4 |
| `test_frontmatter_heals_after_partial_fail` | Simulated partial failure heals on next capture | TC-EI-5 |
| `test_malformed_json_exits_zero` | stdin is not JSON → exit 0 | TC-HI-4 |

### `tests/test_backfill.py`

| Function | Asserts | TC |
|----------|---------|----|
| `test_every_completed_adventure_has_runs` | After backfill, every completed ADV has `agent_runs > 0` | TC-BF-1 |
| `test_adv008_rows_preserved_tildes_stripped` | 34 existing rows preserved (numerics), no tildes in output | TC-BF-2 |
| `test_backfill_idempotent` | Byte-identical second run | TC-BF-3 |
| `test_backfill_rows_never_high_confidence` | No `high` confidence in backfill-emitted rows | TC-BF-4 |
| `test_unreconstructable_row_emitted` | Task with no sources → `result=unrecoverable` row | TC-BF-5 |
| `test_no_apply_does_not_modify_original` | Reversibility guard | TC-BF-6 |

### `tests/test_live_canary.py`

| Function | Asserts | TC |
|----------|---------|----|
| `test_adv009_canary_row_populated` | After wiring + a real subagent run on ADV-009, `metrics.md` has a new row with non-zero tokens and frontmatter totals match the rows sum | TC-LC-1 |

### `tests/test_regression.py`

| Function | Asserts | TC |
|----------|---------|----|
| `test_strategy_coverage` | Grep-count of TC rows in this file equals grep-count of autotest TCs in manifest (35 == 35); detects strategy drift | TC-TS-1 |
| `test_full_discover_exits_zero` | `subprocess.run([..., unittest, discover, ...])` returns 0 | TC-RG-1 |

## Self-check

If the count of TC rows in this file does not equal the count of
`autotest` TCs in the manifest, CI fails via `test_regression.py`
preamble that grep-counts both.

`test_regression.TestStrategyCoverage.test_strategy_coverage` performs
this check at runtime: it greps `manifest.md` for rows where the
`Proof Method` column contains `autotest` (expected: 35), then greps
this file (`test-strategy.md`) for TC-identifier cells in pipe-table
rows (pattern `| TC-`), and asserts the two counts are equal.
