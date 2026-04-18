# Knowledge Base Extraction - Design

## Approach
Append distilled lessons from ADV-010 to the three knowledge base files (patterns.md, decisions.md, issues.md). Each entry is attributed to ADV-010 and preserves all existing content verbatim. The task reads the current knowledge files, identifies which ADV-010 lessons are not yet captured, and appends new entries at the end of each file.

## Target Files
- `.agent/knowledge/patterns.md` - Append 3 new pattern entries from ADV-010
- `.agent/knowledge/decisions.md` - Append 2 new decision entries from ADV-010
- `.agent/knowledge/issues.md` - Append 1 new entry + close 2 existing issues with ADV-010 attribution

## Implementation Steps

### 1. Read current knowledge files
Read `.agent/knowledge/patterns.md`, `decisions.md`, and `issues.md` to confirm current content and identify the last entry in each file.

### 2. Append to patterns.md (3 entries)

**Entry P1 — Row-schema pattern:**
The telemetry row schema uses a fixed-column pipe-separated format with a deterministic `Run ID` (truncated SHA-1 of event fields) for idempotency. Every column has a single canonical type and format. The `Confidence` column (`high`/`medium`/`low`/`estimated`) distinguishes live-captured data from reconstructed data. This pattern makes append-only rows machine-parseable and human-readable without requiring a database. (from ADV-010, design-capture-contract.md)

**Entry P2 — Exit-0-on-failure for sidecar processes:**
When a process runs as a sidecar to the main pipeline (e.g., telemetry capture hook), wrap the entire main() in a catch-all `except Exception` that logs to an append-only error file and always returns exit code 0. The sidecar must never abort the pipeline it instruments. Pair with a timeout budget (e.g., 5s) so even infinite loops are bounded. Justified only for observability/telemetry sidecars where data loss is acceptable but pipeline disruption is not. (from ADV-010, design-error-isolation.md)

**Entry P3 — Backup-before-rename reversibility guard:**
When a tool rewrites a shared file (e.g., backfill rewriting `metrics.md`), never write in-place. Instead: (1) write to `<file>.new`, (2) emit a diff for review, (3) on `--apply` rename original to `<file>.backup.<timestamp>` then rename `.new` to the original. Rollback is a single `mv`. Without `--apply` the original is untouched. This pattern makes destructive bulk operations safe for human review and instant rollback. (from ADV-010, design-backfill-strategy.md)

### 3. Append to decisions.md (2 entries)

**Entry D1 — Stdlib-only YAML-subset parser:**
Context: The telemetry cost model needs to read token rates from `.agent/config.md` YAML frontmatter, but Python stdlib has no YAML parser. Decision: Hand-roll a ~40 LOC YAML-subset reader that handles flat mappings and one level of nesting (2-space indent, `key: scalar` pairs). Rejects anything beyond the subset with a `CostModelError` including the line number. Rationale: avoids adding PyYAML as a dependency; the config surface is narrow enough that a full parser is unnecessary; the subset reader is fully tested with happy-path and error fixtures. (from ADV-010, design-cost-model.md)

**Entry D2 — Reconstruct-vs-fake for historical telemetry:**
Context: ADV-001..ADV-009 had incomplete or missing metrics rows. Options were (a) fabricate plausible-looking data, (b) reconstruct from available evidence with explicit confidence grading, (c) leave gaps. Decision: Reconstruct from four sources (existing rows, adventure.log, git history, task-file logs) with a mandatory `Confidence` column that is never `high` for backfilled rows. Unreconstructable tasks emit a row with `result: unrecoverable` and `confidence: estimated` rather than being silently skipped. Rationale: preserves data provenance; never confuses reconstructed data with live-captured data; the `unrecoverable` sentinel keeps `agent_runs > 0` (satisfies autotests) while making gaps visible. (from ADV-010, design-backfill-strategy.md)

### 4. Update issues.md (1 new entry + 2 closures)

**Close existing issue "Incomplete metrics tracking":**
Append to the existing bullet: `Status: fixed in ADV-010 — live capture hook (design-hook-integration.md) now writes a row on every SubagentStop/PostToolUse event; backfill tool (design-backfill-strategy.md) reconstructed historical rows for ADV-001..ADV-009.`

**Close existing issue "Metrics Frontmatter Aggregation Gap":**
Append to the existing bullet: `Status: fixed in ADV-010 — aggregator.py recomputes frontmatter totals from scratch on every row write; backfill tool triggers aggregation after writing rows.`

**New entry — YAML-subset parser fragility:**
The hand-rolled YAML-subset parser in `cost_model.py` covers only flat mappings and one nesting level. If `.agent/config.md` frontmatter grows beyond this subset (e.g., lists, multi-line strings, anchors), the parser will reject with `CostModelError`. Mitigation: the parser raises with a line number so the failure is diagnosable. Long-term fix: if config complexity grows, adopt PyYAML or migrate rates to a JSON sidecar. (from ADV-010)

### 5. Verify
- Confirm each knowledge file has at least 1 new ADV-010-attributed entry.
- Confirm all existing entries are preserved verbatim (no modifications above the new entries).
- Grep for `ADV-010` in each file to verify attribution.

## Testing Strategy
- After writing, read each file and verify the new entries appear at the end.
- Confirm existing content is byte-identical to the pre-edit version (compare line counts, spot-check first/last existing entries).
- Grep `from ADV-010` across all three files; expect >= 1 match per file.

## Risks
- **Stale issue references**: The two issues to close ("Incomplete metrics tracking", "Metrics Frontmatter Aggregation Gap") must still exist verbatim in issues.md. If prior tasks modified them, the edit will need adjustment.
- **Concurrent writes**: If another task writes to knowledge files simultaneously, content could be lost. Mitigated by dependency chain (T018 depends on T014 and T016, which should be complete).
