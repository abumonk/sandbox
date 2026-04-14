---
task: ADV007-T021
adventure: ADV-007
phase: 6.2
target_conditions: [TC-024]
upstream:
  - .agent/adventures/ADV-007/research/phase6-autotest-strategy.md
  - .agent/adventures/ADV-007/research/phase6-1-complexity-analysis.md
  - .agent/adventures/ADV-007/research/phase6-1-refactoring-strategy.md
  - .agent/adventures/ADV-007/research/phase6-1-abstract-representation.md
  - .agent/adventures/ADV-007/research/phase6-mcp-operations.md
researched: 2026-04-14
---

# Phase 6.2 — Benchmark Design

This document defines the **benchmark specification** for the post-
reconstruction Claudovka ecosystem. A benchmark here is an autotest
that records numeric observations on a standard workload, compares them
against a stored baseline, and classifies the delta against a budget.
The specification covers: what is measured (§2), how it is measured
(§3), what the baseline and target values are (§4), the reproducibility
rules (§5), the report format (§6), and the automation hooks that tie
benchmarks into the MCP-only operations surface (§7).

The benchmark set is the numeric counterpart to the complexity targets
defined in TC-021 and the milestone gates in TC-022. Where the
refactoring strategy answers "is this milestone structurally done?",
the benchmark suite answers "did this milestone deliver the promised
performance improvement?". Both are required before a milestone is
closed.

---

## 1. Principles

Five principles govern the benchmark design. They are stated first so
that every subsequent section can be read as a consequence.

### 1.1 Benchmarks are autotests, not scripts

Every benchmark ships as a test function under `ark/tests/bench/`
discoverable by the `test` MCP tool (phase6 MCP-ops §2.4). A benchmark
that cannot be run under `pipeline.test(scope="bench")` does not exist
for the purposes of milestone gating. This eliminates the class of
"ran it once on my laptop" numbers from the decision record.

### 1.2 Every benchmark has a budget, not a target

A benchmark compares its observation against a **budget**: the maximum
acceptable value (for latency, token cost) or minimum acceptable value
(for throughput, success rate). A benchmark never "passes"; it either
stays within budget or it breaches. This framing prevents over-fitting
to a single good number and forces an explicit decision on every
regression.

### 1.3 Baselines are recorded artefacts

Every benchmark carries a baseline file under
`.agent/adventures/<id>/bench/<name>.baseline.json`. The baseline is
the numeric anchor; deltas are always `(current - baseline)`. Baselines
are updated by an explicit MCP call (`pipeline.bench_update_baseline`)
with a required justification string; they never drift silently.

### 1.4 Regressions are first-class events

A breach emits a `bench.regression` event on `events.jsonl` with the
delta, the budget, and the triggering commit. The event feeds the
autotest debt queue (phase6 autotest §2.3) and can escalate to lead
under the same rules as a failing test (phase6-automation-first §4).

### 1.5 The suite fits the 15-minute PR budget

The full benchmark run (every named benchmark, cold and warm) completes
in ≤ 15 minutes on the reference machine (§5.1). Benchmarks that would
individually exceed 60s at their scope are moved to the `nightly`
scope; they do not block PR merges.

---

## 2. Metric Axes

Five metric axes cover the dimensions a reviewer or lead actually
cares about. Every benchmark emits values on at least one axis; most
emit on three.

### 2.1 Latency

Wall-clock time from input to output, measured at three scopes:

| Scope | Operation | Reference workload |
|---|---|---|
| `op` | Single MCP-tool call | `task_create` with an average payload |
| `stage` | One pipeline stage (planning → implementing → review) | A single task through one stage |
| `adventure` | Full adventure end-to-end | `adventure.smoke` from T020 §M8 |

Latency is reported as p50, p95, p99 across the benchmark's iteration
count. Budgets are expressed against p95 (one bad outlier is permitted
per hundred; two are a breach). Wall-clock time is measured by the
benchmark harness using a monotonic clock, not by parsing log
timestamps.

### 2.2 Token cost

Inbound + outbound tokens per logical unit of work. Sources (per
phase6-automation-first §3 and T008 §18.2):

- **Spawn cost** — auto-injected prompt + system messages, per tier.
- **Task cost** — tokens consumed across every iteration for a task.
- **Adventure cost** — sum over all task costs for an adventure.

Token cost is read authoritatively from the Anthropic SDK response
envelope (X11 resolution) via the TM `metrics_log`; estimated values
from the `turns × 1500` proxy are **not** acceptable bench inputs.
Legacy proxy numbers in historical baselines are flagged with a
`source: "proxy"` field and cannot be compared against post-M7
benchmarks without an explicit shim call (`bench_baseline_convert`).

### 2.3 Memory

Resident set size (RSS) at three checkpoints: harness start, workload
peak, harness exit. Memory budgets are coarse (±20% tolerance) because
OS-level measurement noise dominates below that band. Memory is
reported for TM, the Ark codegen, the orchestrator crate, and every
long-lived Python subprocess under the harness. One-shot tools
(`compile`, `verify`) report peak RSS from their own instrumentation
via the MCP tool's `resource_usage` response field.

### 2.4 Parallel speedup

The ratio `T(serial) / T(parallel_k)` for workloads that admit parallel
execution, measured for k ∈ {1, 2, 4, 8, 16}. Benchmarks include:

- `parallel.task_append` — N tasks appending to the same stream under
  ARL `append` semantics.
- `parallel.spawn_fanout` — k simultaneous planner/researcher spawns
  on independent tasks.
- `parallel.view_regen` — k consumers re-rendering views on k
  independent entities.

Speedup budgets are expressed as efficiency (`speedup / k`). Budget:
≥ 0.7 for k ≤ 8 on `task_append` (the primary parallelism guarantee
from T008 §18.1 and ARL §6.1); ≥ 0.5 for spawn fanout (Anthropic API
rate limits bound the ceiling).

### 2.5 Agent success rate

Fraction of agent-spawn tasks that reach `completed.done` without
human escalation, measured over a rolling window of the last 100
spawns per role. Complements the deterministic benchmarks by catching
regressions in the *judgement* layer — a change to the reviewer prompt
that marginally degrades pass-rate will not show up in latency or
token cost but will show up here within a single adventure.

Success-rate budgets per role: lead ≥ 0.95, planner ≥ 0.92, reviewer
≥ 0.88, researcher ≥ 0.90, implementer ≥ 0.85. Budgets drop by 5
points for any role whose prompt is touched in the PR; the PR must
then demonstrate recovery within two adventures. This is the
"regression latitude" clause for prompt engineering work.

---

## 3. Measurement Methodology

### 3.1 Workload fixtures

Every benchmark pairs with a **workload fixture** drawn from
phase6-2-test-profiles.md §3 (small / medium / large). The fixture is
a deterministic generator seeded on a fixed value; the same seed
produces the same workload across runs. Fixtures live under
`ark/tests/bench/fixtures/<name>.json` and are versioned; a fixture
change is a baseline-invalidating event (§5.3).

### 3.2 Iteration count and warm-up

Every benchmark runs N iterations with M warm-up iterations discarded.
Defaults: N = 30, M = 3 for op-scope benchmarks; N = 10, M = 1 for
stage-scope; N = 3, M = 0 for adventure-scope. Warm-ups exist to
absorb JIT / page-cache / connection-pool startup; the first several
observations typically contain first-run effects.

### 3.3 Isolation

Each benchmark runs in a fresh temp directory and a fresh subprocess.
Cross-benchmark state sharing is forbidden; the harness invokes each
benchmark via a separate `cargo test` or `pytest` subprocess. Shared
fixtures (e.g., a pre-generated 10k-event stream) are copied into the
temp dir, not referenced by path.

### 3.4 Concurrency controls

Benchmarks that measure parallel speedup set an explicit worker count
in their fixture config; they do not rely on ambient `$OMP_NUM_THREADS`
or Python `multiprocessing.cpu_count()`. This prevents a CI runner's
core count from silently changing results.

### 3.5 Clock discipline

- Latency: `time.monotonic_ns()` (Python) or `Instant::now()` (Rust).
- Timestamps in events: RFC 3339 UTC from `datetime.now(UTC)` — never
  used for latency math.
- CPU time: `time.process_time_ns()` as a cross-check for CPU-bound
  benchmarks; divergence > 15 % from wall-clock is an anomaly flag.

### 3.6 Statistical presentation

Each benchmark emits `{min, p50, p95, p99, max, mean, stdev, n}`.
Budgets are set against p95. The harness computes a Mann-Whitney U
test against the baseline sample; a p < 0.01 and a budget breach both
trigger a regression. A p < 0.01 without a budget breach is logged
as `bench.drift` (advisory, not blocking) so that slow erosion is
still visible even when no single run breaches.

---

## 4. Baseline and Target Metrics

Baselines are captured on the reference machine (§5.1) at the
pre-M0 checkpoint; targets are the post-M8 commitments. Budgets are
the blockable thresholds.

### 4.1 Latency table

| Benchmark | Baseline p95 | Target p95 | Budget (breach at) | Tie to |
|---|---:|---:|---:|---|
| `op.task_create` | ~120 ms | 40 ms | 80 ms | M2, ARL §9.3 |
| `op.metrics_append` | ~50 ms | 10 ms | 30 ms | M3, H6 (X6) |
| `op.view_regen (manifest)` | ~350 ms | 80 ms | 150 ms | M1, ARL §9.3 |
| `op.lesson_append` | ~60 ms | 15 ms | 40 ms | M4 |
| `op.hook_on_subagent_stop` | ~1500 ms | 50 ms | 200 ms | M5, H1 |
| `stage.planning` | ~45 s | 30 s | 60 s | M5, M7 |
| `stage.reviewing` | ~35 s | 20 s | 45 s | M5, M7 |
| `adventure.smoke` | n/a (new) | 6 min | 10 min | M8 |

The hook latency target reflects the 92% reduction promised by H1
(prose hook → deterministic tool); the view-regen target reflects the
ARL §9.3 budget of ≤100 ms/event on a 10k-event stream.

### 4.2 Token cost table

| Benchmark | Baseline | Target | Budget | Tie to |
|---|---:|---:|---:|---|
| `spawn.researcher` | ~45 KB | 6 KB | 10 KB | T008 §18.2, H10 |
| `spawn.reviewer` | ~30 KB | 6 KB | 10 KB | T008 §18.2, H10 |
| `spawn.planner` | ~35 KB | 10 KB | 14 KB | T008 §18.2 |
| `spawn.implementer` | ~25 KB | 8 KB | 12 KB | T008 §18.2 |
| `spawn.lead` | ~55 KB | 15 KB | 22 KB | T008 §18.2 |
| `task.total (median)` | ~70 KB | 35 KB | 55 KB | adventure budget |
| `adventure.smoke (total)` | n/a | 450 KB | 700 KB | M8 |

Spawn budgets are sized to the target +~50% so a single PR can add
one reasonable auto-injection without breaching; a second one forces
the change to be paid for by a reduction elsewhere.

### 4.3 Memory table

| Benchmark | Baseline RSS peak | Target RSS peak | Budget |
|---|---:|---:|---:|
| `mem.tm_idle` | ~180 MB | 120 MB | 160 MB |
| `mem.tm_under_load` (100 concurrent streams) | n/a | 350 MB | 500 MB |
| `mem.codegen_ark` (full spec set) | ~95 MB | 80 MB | 120 MB |
| `mem.orchestrator_crate` | ~60 MB | 50 MB | 80 MB |

### 4.4 Parallel-speedup table

| Benchmark | k | Target efficiency | Budget (breach at) | Tie to |
|---|---:|---:|---:|---|
| `parallel.task_append` | 2, 4, 8 | 0.85, 0.80, 0.72 | 0.70 | ARL §6.1 |
| `parallel.spawn_fanout` | 2, 4 | 0.70, 0.60 | 0.50 | TM concurrency |
| `parallel.view_regen` | 4, 8 | 0.80, 0.65 | 0.55 | ARL ViewType |

### 4.5 Agent success-rate table

| Role | Window | Baseline | Target | Budget |
|---|---|---:|---:|---:|
| lead | last 100 | 0.92 | 0.96 | 0.90 |
| planner | last 100 | 0.88 | 0.94 | 0.87 |
| reviewer | last 100 | 0.82 | 0.90 | 0.85 |
| researcher | last 100 | 0.89 | 0.94 | 0.88 |
| implementer | last 100 | 0.79 | 0.88 | 0.80 |

Baselines here are pulled from ADV-004 through ADV-007 retro logs;
targets reflect the fixes in phase3-1 role review and phase6-1
refactoring combined.

---

## 5. Reproducibility Rules

### 5.1 Reference machine specification

Every published benchmark number is labelled with the reference machine
it was measured on. The canonical reference for ADV-007's post-M8
numbers:

- CPU: 8 physical cores, 3.8 GHz nominal.
- RAM: 32 GB, baseline usage < 4 GB at harness start.
- Disk: NVMe SSD, ≥ 1 GB/s sustained sequential write.
- OS: Linux 6.x or Windows 11 (cross-checked — see §5.4).
- Python: 3.12.x; Rust: stable at pinned toolchain.
- Anthropic SDK: pinned version, no network-variance smoothing.

Benchmarks run on a non-reference machine must mark their output
with `machine_class: "divergent"` and cannot be used to update a
baseline. The benchmark report (§6) always prints the machine class.

### 5.2 Seed discipline

Every fixture generator accepts a numeric seed. The seed is written
into the baseline file. A baseline's seed cannot change without a
baseline-reset ceremony (§5.3). Non-deterministic sources (network,
OS scheduler) are documented per benchmark with the expected noise
floor.

### 5.3 Baseline reset ceremony

Updating a baseline is a named operation:

1. Run the benchmark 10 times on the reference machine; capture p95
   and stdev.
2. Open a PR with the new baseline JSON + a `baseline_change` label.
3. The PR body cites the justification (e.g., "M5 landed; hook
   latency target re-set to 200 ms / 50 ms budget / target split").
4. Reviewer checklist includes "is the new baseline consistent with
   the milestone's promised delta?".
5. On merge, the baseline file is committed alongside a
   `baseline.update` event in the adventure's events.jsonl with the
   prior baseline retained for rollback.

This ceremony is the only mutation path for baselines.

### 5.4 Cross-OS parity

Where Linux and Windows diverge materially (> 20 % on any metric),
the benchmark emits two baseline values and two budgets. Latency
budgets on Windows are generally 10-15 % looser than on Linux for
filesystem-bound ops (ARL jsonl append); CPU-bound ops should be
within 5 %. Divergence outside these bands is a bug in the harness
(or in the platform-dependent code path), not an acceptable baseline
split.

### 5.5 Repeated-run variance

A benchmark whose stdev exceeds 20 % of its p95 is marked `unstable`.
Unstable benchmarks are tracked but do not gate merges until their
variance drops below the threshold. The `unstable` marker is a bug
on the benchmark, not on the subject (mirror of the flakiness policy
in phase6 autotest §4.3).

---

## 6. Report Format

The benchmark harness emits two artefacts per run: a machine-readable
JSON and a human-readable markdown summary.

### 6.1 JSON report

```
{
  "run_id": "bench-2026-04-14T02:30:00Z",
  "machine_class": "reference",
  "schema_version": 1,
  "benchmarks": [
    {
      "name": "op.task_create",
      "axis": "latency",
      "n": 30, "warmup": 3,
      "min_ms": 35, "p50_ms": 42, "p95_ms": 58, "p99_ms": 68,
      "mean_ms": 44.2, "stdev_ms": 7.1,
      "baseline": { "p95_ms": 40, "seed": 42, "run_id": "..." },
      "delta_pct": 45.0,
      "budget": { "p95_ms": 80, "breach": false },
      "mannwhitney_p": 0.002
    }
    // ...
  ],
  "environment": { "os": "...", "cpu": "...", "python": "...", "sdk": "..." }
}
```

The JSON report is committed to
`.agent/adventures/<id>/bench/reports/<run_id>.json`. It is the
authoritative record; markdown is a rendered view.

### 6.2 Markdown summary

The markdown view groups benchmarks by axis and flags breaches with
an explicit marker. It includes a `## Regressions` section that lists
only the breaches, a `## Drift` section that lists p < 0.01 changes
without breaches, and a `## Improvements` section that lists the
deltas ≥ 10 % in the favourable direction. This format is the default
attached body of the `bench.regression` event and the default paste
into review comments.

### 6.3 Dashboard view

A cumulative view, `bench.dashboard.md`, tracks the last 30 runs per
benchmark as a sparkline-style table. It is regenerated by the view
layer (ARL `ViewType`) on every new report; no hand editing. The
dashboard is the surface a lead reviews during the phase-7 monthly
health check.

---

## 7. Automation Hooks

### 7.1 MCP tool surface

Three benchmark-facing MCP tools (part of the 7 operational tools in
phase6 MCP-ops §2):

- `pipeline.bench_run(scope, filter?)` — execute benchmarks in the
  named scope; emits `bench.started` and `bench.finished` events.
- `pipeline.bench_update_baseline(name, justification)` — perform
  the §5.3 ceremony; writes the baseline file and emits a
  `baseline.update` event.
- `pipeline.bench_report(run_id, format)` — fetch a prior report in
  `json` or `md` format.

These are the only mutators of the bench tree; direct filesystem
edits to `bench/` are rejected by the pre-commit hook (M7 fence).

### 7.2 CI triggers

The trigger matrix extends the autotest matrix (phase6 autotest §5.1):

| Event | Scope | Duration budget |
|---|---|---:|
| PR opened (affected subsystem) | `bench.quick` (≤ 8 benchmarks) | 3 min |
| PR approved, pre-merge | `bench.affected` | 8 min |
| Nightly main | `bench.full` | 15 min |
| Milestone close | `bench.full` + delta-vs-prior-milestone | 20 min |

A PR that touches files under `ark/src/` or `team-mcp/lib/` triggers
the `affected` scope; a PR that only touches docs triggers `quick`
(smoke-only). The exact mapping is a static table in
`bench/triggers.json`, also read by the M7 trigger registry.

### 7.3 Budget escalation

A budget breach on a PR run:

1. Emits `bench.regression` on the adventure's events.jsonl.
2. Flips the PR's `bench-gate` status check to red.
3. The lead's next spawn receives a view-slice with the breach; the
   lead can either request a targeted fix (default) or declare a
   baseline-reset justified by the change.

On a nightly run, a breach additionally opens a GitHub issue via the
github MCP and labels it `bench-regression`; the issue auto-closes
when the next nightly's benchmark stays within budget for three
consecutive runs.

### 7.4 Integration with autotest debt

A benchmark without a `proof_method: autotest` classification, or one
whose harness depends on a `manual` step, is logged as autotest debt
under phase6 autotest §2.3 and shows in the adventure's manifest as a
flagged TC. No benchmark ships `manual`; a benchmark that cannot be
automated is not a benchmark (§1.1).

### 7.5 Token-economy self-check

The benchmark suite itself is subject to the auto-inject budget. The
harness records its own token cost when it invokes the SDK (any
LLM-in-the-loop benchmark, §2.5); the bench-harness budget is fixed
at ≤ 5 % of the adventure's total token budget. A harness that exceeds
this budget is a benchmark-design bug.

---

## 8. Relation to Other Phase-6 Docs

- **phase6-autotest-strategy** (TC-019): every benchmark is a
  subclass of autotest; the autotest budgets (§5 there) and the
  benchmark budgets (§5 here) are in the same envelope.
- **phase6-1-complexity-analysis** (TC-021): the baseline numbers in
  §4 were derived from the complexity hotspot measurements (H1, H10,
  H11). The targets are the numeric deltas promised there.
- **phase6-1-refactoring-strategy** (TC-022): each milestone M0-M8
  has a named benchmark that certifies the milestone's promised
  numeric delta. The `bench.full` run at milestone close is the
  authoritative evidence for milestone completion criterion §6.1(2).
- **phase6-1-abstract-representation** (TC-023): ARL §9.3 names
  three runtime benchmarks (`render_jsonl` throughput, `view` regen,
  `replay` cold start) — all three are folded into the benchmark
  suite here with budgets aligned to the values declared there.
- **phase6-2-test-profiles** (TC-025): provides the small/medium/large
  workload fixtures that the benchmarks exercise.
- **phase6-2-migration-strategy** (TC-026): references the
  `baseline.update` ceremony as the migration artefact for each
  milestone transition.

---

## 9. Success Criteria for Phase 6.2 Benchmark Suite

- 100 % of benchmarks listed in §4 are implemented and green on the
  reference machine at M8 close.
- 0 benchmarks in the `unstable` bucket at M8 close.
- Baseline files committed and referenced for every benchmark.
- `bench.full` scope runs deterministically in ≤ 15 minutes on 10
  consecutive main-branch commits.
- `bench.regression` event rate < 1 per adventure (any higher rate
  indicates a specification problem, not a real regression).
- Dashboard view (`bench.dashboard.md`) regenerates without error on
  every report ingest.
- Every milestone-close event cites at least one benchmark result
  supporting the close.

These criteria feed TC-024 proof. Phase 7 shifts from benchmark
*adoption* to benchmark *evolution* — adding new budgets as new
subsystems land.

---

## 10. Acceptance Checklist (this document)

- [x] Principles articulated (§1).
- [x] Metric axes defined (latency, token, memory, parallel, success)
  (§2).
- [x] Measurement methodology: fixtures, iteration, isolation, clocks
  (§3).
- [x] Baseline and target metrics tables for all five axes (§4).
- [x] Reproducibility rules with reference machine spec and baseline
  reset ceremony (§5).
- [x] Report format (JSON + markdown + dashboard) (§6).
- [x] Automation hooks with MCP tool surface and CI trigger matrix
  (§7).
- [x] Relation to other Phase-6 docs (§8).
- [x] Success criteria for TC-024 proof (§9).
