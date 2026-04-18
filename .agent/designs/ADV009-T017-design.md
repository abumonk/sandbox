# ADV009-T017 — Wire optional verifier passes (mark deferrable) — Design

## Approach

Run Ark's **unchanged** verifier (`python ark/ark.py verify <spec>`) against
each of the three verifier specs authored in ADV009-T015 and decide, per
spec, between three outcomes:

1. **Verify clean** (exit 0, zero failed invariants) — acceptance criterion
   for that spec is met by the command alone. No README edit required.
2. **Verify reports failures that are genuine modelling gaps** (the
   invariant is sound but vanilla Ark cannot express it at useful
   precision — e.g. multi-step reachability over `State`, aggregate
   coverage predicates over heterogeneous collections) — record a
   **deferral** in `adventure_pipeline/README.md` § "Deferred invariants"
   with rationale + the exact invariant that was skipped / weakened.
3. **Verify reports real bugs in the `.ark` spec we authored** — refine
   the verifier spec under `adventure_pipeline/specs/verify/` only.
   **Never patch `ark/`.**

Per the parent plan this task is **optional/deferrable**: if Ark's
verifier fundamentally cannot model the adventure-pipeline domain, the
task still passes provided every gap is documented. TC-045 is satisfied
by (clean verify) OR (documented deferral) per spec.

## Target Files

- `adventure_pipeline/README.md` — append / extend § "Deferred invariants"
  only if any of the three verifier passes surfaces an inexpressible
  invariant. One bullet per deferral, each carrying: spec filename,
  invariant name, rationale ("vanilla Ark lacks X"), and follow-up
  pointer (future adventure id or "wait for Ark extension").
- `adventure_pipeline/specs/verify/state_transitions.ark` — may be
  refined (tighten predicates, drop inexpressible invariants with a
  comment referencing the README deferral). Authored by T015.
- `adventure_pipeline/specs/verify/permission_coverage.ark` — same.
- `adventure_pipeline/specs/verify/tc_traceability.ark` — same.

Files under `ark/**` are **read-only** for this task. Proof is
`git diff --exit-code -- ark/` (exit 0).

## Implementation Steps

1. **Preflight — snapshot ark/ cleanliness.**
   Run `git diff --name-only -- ark/`. If non-empty, STOP and log a
   blocker ("ark/ has pre-existing drift; baseline-diff required per
   patterns.md Baseline-diff snapshot"). Otherwise record the HEAD SHA
   for step 6's final diff check.

2. **Run each verifier pass in isolation.** For each of the three specs,
   capture stdout+stderr and the exit code:
   ```
   python ark/ark.py verify adventure_pipeline/specs/verify/state_transitions.ark
   python ark/ark.py verify adventure_pipeline/specs/verify/permission_coverage.ark
   python ark/ark.py verify adventure_pipeline/specs/verify/tc_traceability.ark
   ```
   Classify each into: CLEAN / SPEC_BUG / MODELLING_GAP.

3. **Disposition tree per spec:**
   - CLEAN (exit 0): mark the AC checkbox, move on.
   - SPEC_BUG: edit the `.ark` verifier spec (not `ark/`) until the
     verifier runs clean. Re-run step 2 for that spec only.
   - MODELLING_GAP: add a README deferral entry (template below) and
     optionally weaken the affected `verify` block to a comment with
     `// deferred: see README § Deferred invariants — <slug>`.
     Re-run step 2 so the remaining invariants verify clean.

4. **README deferral template.** Append under § "Deferred invariants":
   ```
   - **<spec-filename>** — invariant `<name>` deferred.
     Rationale: <one-sentence: what vanilla Ark cannot express>.
     Follow-up: <future-ADV id | "awaiting Ark verifier extension">.
   ```
   If the § does not yet exist, create it directly below the package
   overview section.

5. **Re-run all three commands end-to-end** to confirm each now either
   exits 0 or is justified by a README deferral. Capture final command
   output in the task log entry.

6. **Confirm Ark untouched.** Run `git diff --exit-code -- ark/`.
   Expect exit 0. If non-zero, revert the Ark-side edits — they do not
   belong in this task. This satisfies AC #3.

7. **Append task log.** One line per verifier pass (CLEAN / DEFERRED /
   REFINED) plus the final ark-diff check.

## Testing Strategy

- **Per-spec proof commands** — the three `ark verify` invocations
  enumerated above, each returning exit 0 OR matched by a README deferral
  entry that names the spec file.
- **Ark-isolation proof** — `git diff --exit-code -- ark/` exits 0.
- **README lint (manual)** — if any deferral was added, eyeball the
  new bullet for: spec filename, invariant name, rationale clause,
  follow-up clause. A missing field is grounds for review rejection.

No pytest cases are added by this task; the verifier CLI is the test.

## Risks

- **Ark verifier does not understand `process` blocks well.** The three
  verifier specs rely on `verify { … }` invariant blocks over process
  state. If Ark's Z3 translator only supports `$data` constraints (see
  `ark/tools/verify/ark_verify.py` module docstring — "Инварианты не
  нарушаются переходами (pre ∧ body → post → invariant)"), the
  `AdventureStateMachine` multi-step reachability invariants are very
  likely to land in MODELLING_GAP and be deferred. This is explicitly
  anticipated by the plan — deferral is a valid outcome.

- **Temptation to patch `ark/`.** Any Z3 enum-coverage or
  collection-traversal gap will be tempting to fix in the verifier.
  **Do not.** The task header says "Under no circumstances should this
  task patch `ark/`." If the coder feels a patch is unavoidable, stop
  and escalate — a separate Ark adventure should own that work.

- **Silent deferral.** An invariant that quietly disappears from the
  spec without a README entry is worse than a loud failure. Reviewer
  should cross-check: every `verify {` block present in T015 either
  still verifies clean today, or has a matching README deferral bullet.
  AC #1 and #2 are phrased to make either branch auditable.

- **This task depends on T015.** If T015 slipped or is still in
  progress, the `.ark` files this task runs against do not yet exist
  and the verify commands will fail at parse time. Do not start until
  T015 is `passed`.

## Pattern notes

- This task is the inverse of the usual pattern: the "primary" outcome
  (clean verify) is the *hoped-for* one, and the "fallback" outcome
  (documented deferral) is the *acceptable* one. Both are passes.
- Mirrors patterns.md "Design-pinned integers need runtime recalc
  fallback" (ADV-011 T009): don't fight reality, log and accept.
