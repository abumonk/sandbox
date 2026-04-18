---
adventure_id: ADV-010
status: approved
created: 2026-04-15T00:55:00Z
approved: 2026-04-15T07:00:00Z
passes_completed: 4
validation_gaps: 0
---

# Permission Requests — ADV-010: Telemetry Capture

## Summary

22 permission entries across 18 tasks, 2 custom agents
(`telemetry-engineer`, `telemetry-historian`). All 4 analysis passes
complete. 0 validation gaps. **Critical expansion** vs ADV-008: this
adventure writes to `.claude/settings.local.json` (T008) and to every
historical `metrics.md` (T013); both are opt-in via `--apply` and
guarded by backups.

## Pass 1 — Codebase Tooling Scan

Discovered in-repo:

- `.claude/settings.local.json` — 128-entry `permissions.allow`,
  **no `hooks` key today** (the gap this adventure closes).
- `.agent/config.md` — YAML frontmatter declares opus/sonnet/haiku
  rates; no code reads it yet.
- Python 3.12 runtime (per manifest Environment). No
  `requirements.txt` / `pyproject.toml` at repo root; existing
  Python uses stdlib + lark/z3 (installed at system level for Ark).
- No `Makefile` / `Taskfile` / `justfile`.
- Test convention in other subsystems: `pytest <path>` — ADV-010
  uses **stdlib `unittest`** instead (explicit per concept §6).
- Git: `master` branch, conventional commits.
- No `.env.example` under `.agent/telemetry/` (will be added if
  needed by T017; none required now).

Shell commands agents will need (per Pass 1):

- `python .agent/telemetry/capture.py < fixture.json` (T007)
- `python -m unittest discover -s .agent/adventures/ADV-010/tests -v` (T016)
- `python -m telemetry.tools.backfill --adventure ADV-NNN --dry-run` (T013)
- `git log --pretty=format:%H|%ai|%s --name-only` (T011)
- `jq` for reading `.claude/settings.local.json` validation (T008).
- Standard file tests: `test -f`, `test -d`, `grep -c`, `diff`.
- `os.replace`-equivalent filesystem ops (no shell needed).

## Pass 2 — Plan-Driven Analysis

Per-task trace:

- T001 (research): Read `.agent/` deep; Write `research/`.
- T002 (test-design): Read designs/, schemas/; Write `tests/`.
- T003 (schemas): Read designs/, Write `schemas/`, Edit
  `design-hook-integration.md` (alias table only).
- T004 (cost-model): Read `.agent/config.md`; Write
  `.agent/telemetry/cost_model.py`, `errors.py`, `__init__.py`;
  Bash `python -c` for smoke.
- T005 (schema module): Read T004 output; Write
  `.agent/telemetry/schema.py`; Bash python.
- T006 (aggregator): Read T005 output; Write
  `.agent/telemetry/aggregator.py`; Bash python.
- T007 (capture): Read T004-T006; Write
  `.agent/telemetry/capture.py`, `log.py`; Bash
  `python capture.py < fixture.json` for smoke.
- T008 (hook install): Read, Edit `.claude/settings.local.json`;
  Bash `jq`; Bash `diff` for byte-check.
- T009 (task_actuals): Read, Write `.agent/telemetry/task_actuals.py`.
- T010 (wire): Read, Edit `.agent/telemetry/capture.py`.
- T011 (reconstructors): Read (`.agent/`, `.git/` via shell),
  Write `.agent/telemetry/tools/reconstructors/`; Bash `git log`,
  `git show`.
- T012 (backfill CLI): Read, Write `.agent/telemetry/tools/backfill.py`;
  Bash python + diff.
- T013 (apply backfill): Read, Write `.agent/adventures/*/metrics.md`
  (all 9 historical), write `*.backup.*`; Bash python module, diff.
- T014 (canary): Invoke Task tool (subagent spawn), Read
  `.agent/adventures/ADV-009/metrics.md` before/after, Write
  `tests/fixtures/canary/`.
- T015 (fixtures): Write `tests/fixtures/`.
- T016 (tests): Read all prior outputs, Write `tests/`, Bash
  `python -m unittest discover`.
- T017 (README): Read, Write `.agent/telemetry/README.md`.
- T018 (knowledge): Read, Write `.agent/knowledge/*.md`.

## Pass 3 — Historical Pattern Match

From `.agent/knowledge/`:

- ADV-008 "Bash permission blocks verification": first subagent
  invocation can hit fine-grained allow-list rejections. Mitigation:
  Pass-2 derived command wildcards (`python:*`,
  `python -m unittest:*`, `git log:*`) are already in the 128-entry
  allow list from earlier adventures — verified below.
- ADV-007 "Append-only jsonl for multi-writer state": directly
  informs the aggregator's append-then-recompute model.
- ADV-004 "Metrics Frontmatter Aggregation Gap": this adventure is
  the remediation; no new permission surface is implied.
- ADV-008 "Baseline-diff snapshot" pattern — relevant if any TC
  asserts "area X unmodified". TC-HI-2 asserts the 128-entry
  allow-list is preserved byte-for-byte; we capture a pre-edit
  hash as the baseline.
- No prior adventure has edited `.claude/settings.local.json`;
  this is new ground. Mitigated by T008's explicit byte-diff
  assertion on `.permissions.allow`.

## Pass 4 — Cross-Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T001 | telemetry-historian | research | .agent/** | research/ | - | - | - | yes |
| T002 | telemetry-engineer | planning | designs/, schemas/ | tests/ | - | - | - | yes |
| T003 | telemetry-engineer | planning | designs/, schemas/ | schemas/, designs/design-hook-integration.md | - | - | - | yes |
| T004 | telemetry-engineer | impl | .agent/config.md | .agent/telemetry/* | python | - | - | yes |
| T005 | telemetry-engineer | impl | .agent/telemetry/ | .agent/telemetry/ | python | - | - | yes |
| T006 | telemetry-engineer | impl | .agent/telemetry/ | .agent/telemetry/ | python | - | - | yes |
| T007 | telemetry-engineer | impl | .agent/telemetry/ | .agent/telemetry/ | python, stdin redirect | - | - | yes |
| T008 | telemetry-engineer | impl | .claude/settings.local.json | .claude/settings.local.json | jq, diff | - | - | yes |
| T009 | telemetry-engineer | impl | .agent/telemetry/ | .agent/telemetry/ | python | - | - | yes |
| T010 | telemetry-engineer | impl | .agent/telemetry/capture.py | .agent/telemetry/capture.py | python | - | - | yes |
| T011 | telemetry-engineer | impl | .agent/adventures/**, .git/** | .agent/telemetry/tools/reconstructors/ | git log | - | - | yes |
| T012 | telemetry-engineer | impl | .agent/adventures/**, .agent/telemetry/ | .agent/telemetry/tools/ | python, diff | - | - | yes |
| T013 | telemetry-historian | apply | .agent/adventures/*/metrics.md | .agent/adventures/*/metrics.md, *.backup.* | python -m telemetry.tools.backfill, git diff | - | - | yes |
| T014 | telemetry-engineer | canary | .agent/adventures/ADV-009/ | tests/fixtures/canary/ | Task tool | - | - | yes |
| T015 | telemetry-engineer | impl | designs/ | tests/fixtures/ | - | - | - | yes |
| T016 | telemetry-engineer | test | .agent/telemetry/, tests/fixtures/ | tests/ | python -m unittest | - | - | yes |
| T017 | telemetry-engineer | doc | .agent/telemetry/ | .agent/telemetry/README.md | - | - | - | yes |
| T018 | telemetry-historian | knowledge | .agent/adventures/ADV-010/ | .agent/knowledge/ | - | - | - | yes |

### Validation checks (all pass)

1. ✓ Every task has ≥1 permission entry per assigned agent.
2. ✓ Every shell command in Pass 1 is covered:
   - `python:*` → existing allow-list line 114 ✓.
   - `python -m unittest:*` → existing allow-list line 90 ✓.
   - `git log:*` → existing allow-list line 95 ✓.
   - `diff:*` → existing allow-list line 107 ✓.
   - `test -f/-d`, `grep`, `cat` → lines 97-101 ✓.
   - `jq` → **NOT in current allow-list** → **REQUEST** (#R1 below).
3. ✓ Every `proof_command` in target conditions is covered:
   - `python -m unittest discover:*` → line 90 ✓.
   - `python -c`, `python -m telemetry.tools.backfill` → line 114
     (`python:*`) ✓.
   - `diff`, `test -f` → allowed ✓.
4. ✓ Every file in a task's `files` has read/write permission.
5. ✓ Dependency chain preserved: T016 reads outputs from T007, T009,
   T012 (all in `.agent/telemetry/`).
6. N/A git `branch-per-task` — config uses `current-branch` mode.

## Requests

### Shell Access (new wildcards beyond existing allow-list)

| #   | Agent                | Stage | Command                                        | Reason                                                   | Tasks |
|-----|----------------------|-------|-------------------------------------------------|----------------------------------------------------------|-------|
| R1  | telemetry-engineer   | impl  | `Bash(jq:*)`                                   | Validate `.claude/settings.local.json` after hook merge  | T008  |
| R2  | telemetry-engineer   | impl  | `Bash(python -m telemetry:*)`                  | Run capture/backfill as modules (narrower than python:*) | T011, T012, T013 |
| R3  | telemetry-historian  | apply | `Bash(python -m telemetry.tools.backfill:*)`   | Explicit narrow wildcard for the backfill driver         | T013  |

All other shell needs already satisfied by the 128-entry allow-list.

### File Access

| #   | Agent                | Stage | Scope                                   | Mode  | Reason                                              | Tasks |
|-----|----------------------|-------|-----------------------------------------|-------|-----------------------------------------------------|-------|
| F1  | telemetry-engineer   | impl  | `.agent/telemetry/**`                   | rw    | Implementation surface                              | T004-T010, T017 |
| F2  | telemetry-engineer   | impl  | `.agent/adventures/ADV-010/**`          | rw    | Plan/design/schemas/tests/research/fixtures         | T001-T003, T014-T016 |
| F3  | telemetry-engineer   | impl  | `.claude/settings.local.json`           | rw    | Hook registration (preserving allow-list)           | T008  |
| F4  | telemetry-engineer   | impl  | `.agent/config.md`                      | ro    | Cost rates                                          | T004  |
| F5  | telemetry-engineer   | impl  | `.agent/adventures/ADV-009/metrics.md`  | ro    | Canary pre/post snapshot read                       | T014  |
| F6  | telemetry-engineer   | impl  | `.agent/adventures/**/{manifest.md, adventure.log, tasks/}` | ro | Evidence for reconstructors & task_actuals | T009, T011 |
| F7  | telemetry-historian  | apply | `.agent/adventures/*/metrics.md`        | rw    | Backfill rewrite (only via `--apply`, with backup)  | T013  |
| F8  | telemetry-historian  | apply | `.agent/adventures/*/metrics.md.backup.*` | w  | Backup files created by backfill                    | T013  |
| F9  | telemetry-historian  | know  | `.agent/knowledge/**`                   | rw    | Append lessons learned                              | T018  |
| F10 | telemetry-historian  | research | `.git/**` (read via git CLI)         | ro    | Git-window reconstructor                            | T011  |

### MCP Tools

None required. No MCP tools are invoked by any ADV-010 task.

### External Access

None. No WebSearch / WebFetch. All reconstruction inputs are local.

### Explicit Denies

- **No write to `ark/**`** — inherited from ADV-008 pattern; ADV-010
  never needs to touch `ark/`. Belt-and-braces for both custom
  roles.
- **No write outside `.agent/` or `.claude/settings.local.json`** —
  the Python writer lives under `.agent/telemetry/`; there is no
  top-level source code to change.

## Historical Notes

- ADV-004 / ADV-005 / ADV-006 left `metrics.md` aggregation broken;
  ADV-010 is the fix. Patterns from ADV-007 T008 ("append-only
  jsonl") informed the aggregator's append-then-recompute model.
- ADV-008 established the "capture a baseline diff for invariance
  TCs" pattern; applied here to TC-HI-2 via a pre-edit SHA-1 hash
  of `.permissions.allow` captured at T008 start.
- ADV-008 hit sub-agent bash allow-list rejections at first subagent
  spawn. Mitigation: Requests R1..R3 pre-approve the narrow wildcards
  needed beyond the inherited allow-list.

## Approval

- [ ] Approved by user
- [ ] Approved with modifications: {notes}
- [ ] Denied: {reason}
