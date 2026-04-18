# Plan — Wave B: Capture Mechanism

## Designs Covered

- designs/design-capture-contract.md
- designs/design-cost-model.md
- designs/design-hook-integration.md
- designs/design-aggregation-rules.md
- designs/design-error-isolation.md

The core of the adventure. Ships the Python writer, the cost model,
the aggregator, and wires the Claude Code hook.

## Tasks

### Cost model module

- **ID**: ADV010-T004
- **Description**: Implement `.agent/telemetry/cost_model.py`:
  hand-rolled YAML frontmatter reader for `.agent/config.md`,
  `normalize_model`, `known_models`, `cost_for`. Raise
  `UnknownModelError` on unknown model IDs. Memoise `load_rates`.
- **Files**:
  - `.agent/telemetry/cost_model.py` (new)
  - `.agent/telemetry/errors.py` (new — also used by T005)
  - `.agent/telemetry/__init__.py` (new)
- **Acceptance Criteria**:
  - `load_rates()` returns `{"opus":0.015, "sonnet":0.003,
    "haiku":0.001}` from current config.
  - `cost_for("opus", 85000, 28000)` returns 1.695 (= 113 × 0.015).
  - `cost_for("unknown", 1, 1)` raises `UnknownModelError`.
  - `normalize_model("claude-opus-4-6") == "opus"`.
- **Target Conditions**: TC-CM-1, TC-CM-2, TC-CM-3, TC-CM-4
- **Depends On**: ADV010-T003
- **Evaluation**:
  - Access requirements: Read (.agent/config.md), Write (.agent/telemetry/)
  - Skill set: Python, YAML subset parsing
  - Estimated duration: 25min
  - Estimated tokens: 40000

### Schema + validator module

- **ID**: ADV010-T005
- **Description**: Implement `.agent/telemetry/schema.py`: the
  `SubagentEvent` dataclass, `MetricsRow` dataclass,
  `validate_event(dict) -> SubagentEvent`, `build_row(event,
  cost)`, row serialization/parsing for pipe-table format. Re-use
  `errors.py` from T004.
- **Files**:
  - `.agent/telemetry/schema.py` (new)
- **Acceptance Criteria**:
  - Every documented invalid payload variant raises a specific
    exception (10 cases).
  - `build_row(event)` produces a row whose Run ID is the 12-hex
    SHA-1 prefix of the canonical key.
  - Round-trip: `serialize(row)` then `parse_row(line)` returns
    byte-equivalent row for all numeric columns.
- **Target Conditions**: TC-CC-1 (partial), TC-S-3
- **Depends On**: ADV010-T004
- **Evaluation**:
  - Access requirements: Read, Write (.agent/telemetry/)
  - Skill set: dataclasses, hashlib, strict validators
  - Estimated duration: 25min
  - Estimated tokens: 45000

### Aggregator module

- **ID**: ADV010-T006
- **Description**: Implement `.agent/telemetry/aggregator.py`:
  `parse_rows(metrics_path)`, `recompute_frontmatter(metrics_path)`,
  `format_duration(seconds)`. Atomic write via
  `metrics.md.tmp` + `os.replace`.
- **Files**:
  - `.agent/telemetry/aggregator.py` (new)
- **Acceptance Criteria**:
  - Given a fixture metrics.md with N rows, frontmatter `total_*`
    equals the row sum after `recompute_frontmatter()`.
  - `format_duration(16*60) == "16min"`,
    `format_duration(95) == "95s"`,
    `format_duration(2*3600 + 15*60) == "2h 15min"`.
  - Running the recompute twice produces byte-identical file.
- **Target Conditions**: TC-AG-1, TC-AG-2, TC-AG-3, TC-AG-6
- **Depends On**: ADV010-T005
- **Evaluation**:
  - Access requirements: Read, Write (.agent/telemetry/)
  - Skill set: file I/O, atomic renames on Windows
  - Estimated duration: 25min
  - Estimated tokens: 40000

### Capture entrypoint with error isolation

- **ID**: ADV010-T007
- **Description**: Implement `.agent/telemetry/capture.py` with a
  `main()` guardrail that catches every exception, logs to
  `capture-errors.log`, and exits 0. Wire T004..T006. Implement
  `normalize_payload`, `adventure_id` resolution from cwd/env.
  Implement idempotent `append_row`.
- **Files**:
  - `.agent/telemetry/capture.py` (new)
  - `.agent/telemetry/log.py` (new — error-log helpers)
- **Acceptance Criteria**:
  - Subprocess test: valid JSON on stdin → new row in correct
    metrics.md, exit 0.
  - Subprocess test: malformed JSON → exit 0, one line in
    capture-errors.log.
  - Subprocess test: same event twice → one row (idempotency).
  - Subprocess test: `KeyboardInterrupt` propagates.
- **Target Conditions**: TC-CC-1, TC-CC-2, TC-CC-3, TC-CC-4,
  TC-HI-3, TC-HI-4, TC-EI-1, TC-EI-2, TC-EI-3, TC-EI-4
- **Depends On**: ADV010-T006
- **Evaluation**:
  - Access requirements: Read, Write (.agent/telemetry/), Bash
    (python)
  - Skill set: stdin/stdout, subprocess semantics, defensive
    exception handling
  - Estimated duration: 30min
  - Estimated tokens: 60000

### Hook registration in settings.local.json

- **ID**: ADV010-T008
- **Description**: Extend `.claude/settings.local.json` with
  `hooks.SubagentStop` and `hooks.PostToolUse` blocks per
  `design-hook-integration.md`, preserving the existing 128-entry
  `permissions.allow` list byte-for-byte. Write a small
  one-shot merger script (run locally by the implementer, not
  shipped) so the merge is reviewable.
- **Files**:
  - `.claude/settings.local.json` (edit — add `hooks` key only)
- **Acceptance Criteria**:
  - `jq '.hooks.SubagentStop | length'` returns `>= 1`.
  - `jq '.hooks.PostToolUse[0].matcher'` returns `"Task"`.
  - Byte diff on `.permissions.allow` is empty.
  - Autotest parses the file and asserts both hooks point at
    `python .agent/telemetry/capture.py`.
- **Target Conditions**: TC-HI-1, TC-HI-2
- **Depends On**: ADV010-T007
- **Evaluation**:
  - Access requirements: Read, Edit (`.claude/settings.local.json`)
  - Skill set: JSON editing without clobbering
  - Estimated duration: 10min
  - Estimated tokens: 12000
