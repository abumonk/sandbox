# Test Fixtures — Design

## Approach

Author 14 test fixture files across three directories under
`.agent/adventures/ADV-010/tests/fixtures/`. Each fixture is crafted
to exercise specific validation paths in `schema.py`, cost computation
in `cost_model.py`, aggregation in `aggregator.py`, and task-actuals
propagation in `task_actuals.py`. Fixtures must be hand-computable so
that test assertions can hard-code expected values.

## Target Files

- `tests/fixtures/events/happy_opus.json` — Valid SubagentStop event using opus model; exercises the happy path for capture, cost computation, and row building.
- `tests/fixtures/events/happy_sonnet.json` — Valid SubagentStop event using sonnet model; proves multi-model support.
- `tests/fixtures/events/missing_tokens.json` — Event missing `tokens_in`; must fail validation with PayloadError.
- `tests/fixtures/events/bad_model.json` — Event with `model: "unknown-model-xyz"`; must fail validation with PayloadError (unknown model).
- `tests/fixtures/events/replay.json` — Identical to `happy_opus.json` (same fields, same session_id); used by TC-CC-3 to prove idempotent row append (same Run ID).
- `tests/fixtures/events/post_tool_use.json` — Valid PostToolUse event with `tool: "Task"` and nested usage; exercises the belt-and-braces capture path.
- `tests/fixtures/events/malformed.txt` — Not JSON at all (plain text garbage); exercises TC-HI-4 and TC-EI-1 (malformed stdin exits 0).
- `tests/fixtures/metrics/empty.md` — Valid metrics.md with frontmatter but zero rows; aggregation produces all-zero totals.
- `tests/fixtures/metrics/single_row.md` — One opus row with known values; frontmatter totals must equal that row exactly.
- `tests/fixtures/metrics/multi_model.md` — Three rows (opus, sonnet, haiku) with distinct token counts; tests cross-model aggregation sums.
- `tests/fixtures/metrics/with_tildes.md` — Rows containing tilde-prefixed approximate values (e.g. `~45000`); exercises backfill tilde-stripping (TC-BF-2).
- `tests/fixtures/metrics/tampered.md` — Rows are correct but frontmatter totals are intentionally wrong; tests that recompute_frontmatter heals (TC-EI-5, TC-AG-3).
- `tests/fixtures/manifests/minimal.md` — Manifest with `## Evaluations` table containing 2 tasks, Actual columns all `---`; exercises update_task_actuals write path.
- `tests/fixtures/manifests/with_estimates.md` — Manifest with Est. Tokens and Est. Cost populated; exercises Variance computation.

All paths are relative to `.agent/adventures/ADV-010/`.

## Implementation Steps

### Step 1: Create directory structure

Create empty directories:
- `.agent/adventures/ADV-010/tests/fixtures/events/`
- `.agent/adventures/ADV-010/tests/fixtures/metrics/`
- `.agent/adventures/ADV-010/tests/fixtures/manifests/`

### Step 2: Author event fixtures (7 files)

**happy_opus.json** — A complete, valid SubagentStop payload:
```json
{
  "event_type": "SubagentStop",
  "timestamp": "2026-04-15T10:30:00Z",
  "adventure_id": "ADV-010",
  "agent": "coder",
  "task": "ADV010-T005",
  "model": "claude-opus-4-6",
  "tokens_in": 85000,
  "tokens_out": 28000,
  "duration_ms": 720000,
  "turns": 12,
  "result": "done",
  "session_id": "sess-abc123"
}
```
Hand-computed cost: (85000 + 28000) / 1000 * 0.015 = 1.6950.
Run ID: sha1("ADV-010|coder|ADV010-T005|opus|2026-04-15T10:30:00Z|sess-abc123")[:12].
Duration(s): round(720000/1000) = 720.

**happy_sonnet.json** — Same structure, different model:
```json
{
  "event_type": "SubagentStop",
  "timestamp": "2026-04-15T11:00:00Z",
  "adventure_id": "ADV-010",
  "agent": "planner",
  "task": "ADV010-T003",
  "model": "claude-sonnet-4-6",
  "tokens_in": 20000,
  "tokens_out": 3500,
  "duration_ms": 90000,
  "turns": 7,
  "result": "ready",
  "session_id": "sess-def456"
}
```
Hand-computed cost: (20000 + 3500) / 1000 * 0.003 = 0.0705.

**missing_tokens.json** — Omit `tokens_in` entirely:
```json
{
  "event_type": "SubagentStop",
  "timestamp": "2026-04-15T12:00:00Z",
  "adventure_id": "ADV-010",
  "agent": "coder",
  "task": "ADV010-T006",
  "model": "claude-opus-4-6",
  "tokens_out": 5000,
  "duration_ms": 60000,
  "turns": 4,
  "result": "done"
}
```
Expected: validate_event raises PayloadError (missing required field `tokens_in`).

**bad_model.json** — Unknown model string:
```json
{
  "event_type": "SubagentStop",
  "timestamp": "2026-04-15T13:00:00Z",
  "adventure_id": "ADV-010",
  "agent": "coder",
  "task": "ADV010-T007",
  "model": "unknown-model-xyz",
  "tokens_in": 1000,
  "tokens_out": 500,
  "duration_ms": 30000,
  "turns": 2,
  "result": "done"
}
```
Expected: validate_event raises PayloadError (model not in known set).

**replay.json** — Byte-identical to happy_opus.json:
Same content as `happy_opus.json` to produce the same Run ID. Used by
TC-CC-3 to verify idempotent row append (second write is a no-op).

**post_tool_use.json** — PostToolUse event variant:
```json
{
  "event_type": "PostToolUse",
  "timestamp": "2026-04-15T14:00:00Z",
  "adventure_id": "ADV-010",
  "agent": "adventure-planner",
  "task": null,
  "model": "claude-opus-4-6",
  "tokens_in": 48000,
  "tokens_out": 14000,
  "duration_ms": 900000,
  "turns": 1,
  "result": "complete",
  "session_id": "sess-ghi789"
}
```
Task is null, so row Task column = "-". Cost: (48000+14000)/1000*0.015 = 0.9300.

**malformed.txt** — Plain text, not JSON:
```
This is not JSON at all.
It is just some random text that should cause a parse error.
The capture pipeline must exit 0 when it encounters this.
```

### Step 3: Author metrics fixtures (5 files)

All metrics fixtures use the canonical row schema with 12 columns:
`| Run ID | Timestamp | Agent | Task | Model | Tokens In | Tokens Out | Duration (s) | Turns | Cost (USD) | Result | Confidence |`

**empty.md** — Zero rows, all-zero frontmatter:
```markdown
---
adventure_id: ADV-099
total_tokens_in: 0
total_tokens_out: 0
total_duration: 0
total_cost: 0.0000
agent_runs: 0
---

## Agent Runs

| Run ID | Timestamp | Agent | Task | Model | Tokens In | Tokens Out | Duration (s) | Turns | Cost (USD) | Result | Confidence |
|--------|-----------|-------|------|-------|-----------|------------|--------------|-------|------------|--------|------------|
```

**single_row.md** — One row, frontmatter matches exactly:
One opus row: tokens_in=85000, tokens_out=28000, duration=720s, cost=1.6950.
Frontmatter: total_tokens_in=85000, total_tokens_out=28000, total_duration=720, total_cost=1.6950, agent_runs=1.

**multi_model.md** — Three rows across opus/sonnet/haiku:
- Row 1 (opus): tokens_in=85000, tokens_out=28000, duration=720, cost=1.6950
- Row 2 (sonnet): tokens_in=20000, tokens_out=3500, duration=90, cost=0.0705
- Row 3 (haiku): tokens_in=10000, tokens_out=2000, duration=45, cost=0.0120
Frontmatter sums: total_tokens_in=115000, total_tokens_out=33500, total_duration=855, total_cost=1.7775, agent_runs=3.

**with_tildes.md** — Rows with tilde-prefixed approximate values:
Mimics the legacy format seen in existing metrics.md files (e.g. `~45000`).
Two rows with tildes on token columns. Used by TC-BF-2 to verify
that backfill strips tildes and converts to integers.

**tampered.md** — Correct rows but wrong frontmatter:
Same rows as single_row.md but frontmatter has total_tokens_in=99999,
total_cost=9.9999. Used by TC-EI-5 and TC-AG-3 to verify that
recompute_frontmatter heals the frontmatter to match row data.

### Step 4: Author manifest fixtures (2 files)

**minimal.md** — Manifest with Evaluations table, no estimates:
```markdown
---
id: ADV-099
title: Test Fixture Adventure
state: completed
---

## Evaluations

| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |
|------|---------------------|-----------|---------------|-------------|-----------|-----------------|---------------|-------------|----------|
| ADV099-T001 | Read, Write | coding | 20min | 30000 | --- | --- | --- | --- | --- |
| ADV099-T002 | Read, Write | testing | 15min | 20000 | --- | --- | --- | --- | --- |
```
Used by TC-AG-4 to verify update_task_actuals fills Actual columns.

**with_estimates.md** — Manifest with Est. Cost populated:
Same structure but Est. Cost = `$0.6750` and Est. Tokens = 45000 for
task T001. After actuals are written (e.g. actual tokens = 113000),
Variance = `+151%`. Used by TC-AG-4 Variance computation test.

### Step 5: Validate fixtures against design contracts

Cross-check every fixture against the design docs:
- Event fixtures: field names match SubagentEvent dataclass exactly.
- Metrics fixtures: column order matches row_schema.md exactly (12 columns).
- Manifest fixtures: column order matches ManifestEvaluationRow (10 columns).
- Hand-compute all expected values and document them as comments or in the design.

## Testing Strategy

- Each fixture is consumed by the test file that owns its TC. The
  fixture itself is not executable; correctness is validated by the
  test that loads it.
- Self-check during implementation: load each JSON fixture with
  `json.loads()` to confirm it parses (except malformed.txt which
  must NOT parse).
- Metrics fixtures: manually verify frontmatter-to-row agreement
  using the formulas from design-aggregation-rules.md.

## Risks

- **Schema drift**: If T005 (schema.py) changes field names or adds
  new required fields before T015 runs, fixtures will need updating.
  Mitigated by reading the implemented schema.py at implementation
  time.
- **Rate changes**: Fixtures hard-code cost values based on current
  config.md rates (opus=0.015, sonnet=0.003, haiku=0.001). If rates
  change, fixture costs must be recalculated.
- **Column count mismatch**: The existing metrics.md files in the repo
  use an 8-column format without Run ID, Cost, or Confidence. The
  fixtures use the new 12-column schema from row_schema.md. Tests
  must use the fixture format, not the legacy format.
