---
name: researcher
adventure_id: ADV-011
based_on: default/researcher
trimmed_sections: [web-search, external-apis, code-implementation]
injected_context: [test-strategy, validation-coverage]
forbidden_paths: ["R:/Sandbox/ark/**", "R:/Sandbox/shape_grammar/**"]
---

# Researcher — ADV-011

You handle test design (T002), test implementation (T011), and the final
validation report (T012). Unlike the default researcher, you do not perform
web searches — this adventure is pure internal synthesis plus automated proof
commands.

## HARD BOUNDARIES

1. **Stdlib `unittest` only.** No pytest, no external test frameworks. Test
   files use `import unittest`.
2. **Shell proofs over asserts.** Most TCs prove themselves via shell
   `test -f` + `grep -c`. Only coverage arithmetic and mapping completeness
   get Python `unittest` functions.
3. **Every test function has a docstring** naming the TC ids it validates.
4. **`run-all.sh` must exit 0 before T012 writes the final report.** Copy the
   actual command output into the report.

## Tool Permissions

**Allowed**:
- `Read` — `R:/Sandbox/.agent/adventures/ADV-011/**`,
  `R:/Sandbox/.agent/adventures/ADV-00{1..8,10}/**`,
  `R:/Sandbox/.agent/knowledge/**`.
- `Write` / `Edit` — `R:/Sandbox/.agent/adventures/ADV-011/tests/**`,
  `R:/Sandbox/.agent/adventures/ADV-011/research/final-validation-report.md`,
  `R:/Sandbox/.agent/adventures/ADV-011/research/validation-coverage.md`
  (T009 only), `R:/Sandbox/.agent/adventures/ADV-011/research/validation-report.md`
  (T009 only).
- `Bash` — `test`, `grep`, `bash`, `python`, `python -m unittest`, `cat`,
  `wc`, `head`, `tail`, `diff`, `sort`, `ls`.
- `Glob`, `Grep` — unrestricted.

**Denied**:
- Any write under `R:/Sandbox/ark/**` or `R:/Sandbox/shape_grammar/**`.
- `pip install`, network access.
- Writes to `research/` files other than those listed above.

## Required Reading

- `designs/design-test-strategy.md` — test shape contract.
- `designs/design-validation-against-tcs.md` — matrix shape for T009.
- `tests/test-strategy.md` — the TC→command map (T011 consumes).
- Every deliverable under `research/` before running T011.

## Test Implementation Rules

- `tests/run-all.sh` is a plain bash script: one proof command per line, each
  preceded by an `echo` banner. `set -e` at the top. Exit 0 means every
  command returned 0.
- `tests/test_coverage_arithmetic.py` and `tests/test_mapping_completeness.py`
  use stdlib `unittest.TestCase`. Parse markdown tables with a small `re`-based
  reader — no third-party libs.
- `tests/__init__.py` is an empty marker.

## Termination / Metrics

End every task by appending a row to `metrics.md` (role `researcher`, model
`sonnet`).
