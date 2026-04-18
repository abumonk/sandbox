# Design — Test Strategy

## Overview

Every ADV-010 target condition with `Proof Method: autotest` maps to
a specific `unittest` function in `.agent/adventures/ADV-010/tests/`.
The single CI entrypoint is:

```
python -m unittest discover -s .agent/adventures/ADV-010/tests -v
```

Exit code 0 means the adventure is provable. There is no `poc` path
for capture-mechanism claims; every behaviour is asserted in code.

## Target files

- `.agent/adventures/ADV-010/tests/__init__.py`
- `.agent/adventures/ADV-010/tests/conftest.py` — shared fixtures.
- `.agent/adventures/ADV-010/tests/test_schema.py`
- `.agent/adventures/ADV-010/tests/test_cost_model.py`
- `.agent/adventures/ADV-010/tests/test_capture.py`
- `.agent/adventures/ADV-010/tests/test_aggregator.py`
- `.agent/adventures/ADV-010/tests/test_task_actuals.py`
- `.agent/adventures/ADV-010/tests/test_error_isolation.py`
- `.agent/adventures/ADV-010/tests/test_backfill.py`
- `.agent/adventures/ADV-010/tests/test_live_canary.py`
- `.agent/adventures/ADV-010/tests/test_regression.py` — discovers
  the full suite and asserts exit 0 end-to-end.
- `.agent/adventures/ADV-010/tests/fixtures/` — JSON event payloads
  (happy + adversarial), sample metrics.md files, sample manifest.

## TC → test function mapping

| TC      | Test file                | Function                                  |
|---------|--------------------------|-------------------------------------------|
| TC-S-1  | test_schema.py           | test_row_header_columns_exact             |
| TC-S-2  | test_schema.py           | test_frontmatter_keys_exact               |
| TC-S-3  | test_schema.py           | test_row_type_coercion                    |
| TC-CC-1 | test_capture.py          | test_validate_event_rejects_invalid       |
| TC-CC-2 | test_capture.py          | test_valid_event_writes_one_row           |
| TC-CC-3 | test_capture.py          | test_replay_same_event_idempotent         |
| TC-CC-4 | test_capture.py          | test_row_cost_matches_cost_model          |
| TC-CM-1 | test_cost_model.py       | test_cost_for_opus_known_fixture          |
| TC-CM-2 | test_cost_model.py       | test_unknown_model_raises                 |
| TC-CM-3 | test_cost_model.py       | test_normalize_model_aliases              |
| TC-CM-4 | test_cost_model.py       | test_load_rates_from_config_md            |
| TC-HI-1 | test_capture.py          | test_settings_json_has_both_hooks         |
| TC-HI-2 | test_capture.py          | test_settings_json_preserves_permissions  |
| TC-HI-3 | test_capture.py          | test_capture_subprocess_happy_path        |
| TC-HI-4 | test_error_isolation.py  | test_malformed_json_exits_zero            |
| TC-AG-1 | test_aggregator.py       | test_total_tokens_in_matches_rows         |
| TC-AG-2 | test_aggregator.py       | test_all_frontmatter_totals_match_rows    |
| TC-AG-3 | test_aggregator.py       | test_recompute_idempotent                 |
| TC-AG-4 | test_task_actuals.py     | test_update_task_actuals_values           |
| TC-AG-5 | test_task_actuals.py     | test_update_leaves_other_rows_byte_equal  |
| TC-AG-6 | test_aggregator.py       | test_format_duration_table_driven         |
| TC-EI-1 | test_error_isolation.py  | test_payload_error_exit_zero              |
| TC-EI-2 | test_error_isolation.py  | test_write_error_logs_and_exits_zero      |
| TC-EI-3 | test_error_isolation.py  | test_keyboard_interrupt_propagates        |
| TC-EI-4 | test_error_isolation.py  | test_error_log_is_valid_jsonl             |
| TC-EI-5 | test_error_isolation.py  | test_frontmatter_heals_after_partial_fail |
| TC-BF-1 | test_backfill.py         | test_every_completed_adventure_has_runs   |
| TC-BF-2 | test_backfill.py         | test_adv008_rows_preserved_tildes_stripped|
| TC-BF-3 | test_backfill.py         | test_backfill_idempotent                  |
| TC-BF-4 | test_backfill.py         | test_backfill_rows_never_high_confidence  |
| TC-BF-5 | test_backfill.py         | test_unreconstructable_row_emitted        |
| TC-BF-6 | test_backfill.py         | test_no_apply_does_not_modify_original    |
| TC-LC-1 | test_live_canary.py      | test_adv009_canary_row_populated          |
| TC-RG-1 | test_regression.py       | test_full_discover_exits_zero             |

## Fixtures strategy

- All file-writing tests use `tempfile.TemporaryDirectory`. No test
  ever touches a real `.agent/adventures/*` directory — the canary
  test in `test_live_canary.py` is the single exception and it uses
  a read-only assertion.
- Event payloads live in
  `tests/fixtures/events/{happy_opus.json, happy_sonnet.json,
  missing_tokens.json, bad_model.json, replay.json,
  post_tool_use.json, malformed.txt}`.
- Metrics fixtures live in `tests/fixtures/metrics/{empty.md,
  single_row.md, multi_model.md, with_tildes.md, tampered.md}`.
- Manifest fixtures live in `tests/fixtures/manifests/{minimal.md,
  with_estimates.md}`.

## CI one-liner (recorded in test-strategy.md for discovery)

```
python -m unittest discover -s .agent/adventures/ADV-010/tests -v
```

No env vars, no special cwd requirement (tests `os.chdir` into
their tempdirs). Must exit 0.

## Target Conditions

- TC-TS-1: The test-strategy file records every autotest TC with a
  named function — verified by grepping this file for every TC ID
  from the manifest.
- TC-RG-1: Full discover + run exits 0 (tautology — it IS the CI
  check; see `test_regression.py` which re-invokes discover via
  subprocess).

## Dependencies

- Every other ADV-010 design document (this maps TCs from all of
  them).
