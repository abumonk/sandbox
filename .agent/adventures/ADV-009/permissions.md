---
adventure_id: ADV-009
status: approved
created: 2026-04-14T21:45:00Z
approved: 2026-04-14T23:14:11Z
passes_completed: 4
validation_gaps: 0
addendum_updated: 2026-04-14T22:05:00Z
---
# Permission Requests — ADV-009: Adventure Console UI v2

## Summary

30 permissions across 21 tasks, 3 agent roles (coder, code-reviewer,
qa-tester). All 4 analysis passes complete. 0 validation gaps.

**Addendum delta**: +7 permissions (2 shell, 5 file) covering the new
sibling package `adventure_pipeline/`, Ark parser/verifier invocations,
and cytoscape CDN access (browser-side only — no download-time permission
needed). Ark directory (`ark/**`) is granted **read-only** explicitly,
matching the "Ark is never modified" invariant.

Distinctive needs for this adventure:
- Backend tasks (T003, T004) run Python stdlib `unittest` against a local
  copy of `server.py`.
- Frontend tasks (T005–T011) only edit `index.html`; no build step, no
  bundler.
- Test task (T012) launches `server.py` on a random port and optionally
  drives Playwright.
- Manual glance task (T013) runs the console briefly and writes a small
  report.

## Requests

### Shell Access

| # | Agent | Stage | Command | Reason | Tasks |
|---|-------|-------|---------|--------|-------|
| 1 | coder | implementing | `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"` | Run the v2 test suite after any code change | T003, T004, T005, T006, T007, T008, T009, T010, T011, T012 |
| 2 | coder | implementing | `python .agent/adventure-console/server.py --port {N}` | Sanity-start the server to verify startup + index.html load | T003, T004, T006, T012, T013 |
| 3 | coder | implementing | `python -c "..."` | Ad-hoc stdlib smoke checks (e.g. import server; parse frontmatter) | T003, T004, T012 |
| 4 | coder | implementing | `grep` / `rg` via Grep tool | Find call sites to be removed during T011 cleanup | T011 |
| 5 | code-reviewer | reviewing | `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"` | Re-run tests independently during review | all |
| 6 | code-reviewer | reviewing | `python -c "import ast; ast.parse(open('.agent/adventure-console/server.py').read())"` | Syntax check without executing | T003, T004 |
| 7 | qa-tester | reviewing | `python -m unittest discover ...` (as above) | Run test suite; capture results | T012 |
| 8 | qa-tester | reviewing | `python .agent/adventure-console/server.py --port {N}` | Spin server for additional smoke tests | T012 |
| 24 | coder | implementing | `python ark/ark.py parse {spec.ark}` | Validate authored Ark specs parse cleanly | T015, T016 |
| 25 | coder | implementing | `python ark/ark.py verify {spec.ark}` | Run Ark's existing verifier on optional invariant passes | T017 |
| 26 | coder | implementing | `python -m adventure_pipeline.tools.ir ADV-NNN` | Exercise the IR extractor CLI | T016, T018, T021 |
| 27 | coder | implementing | `git diff --exit-code ark/` | Enforce "Ark is never modified" invariant | T015, T017 |

Ports used by adventure tests are random ephemeral (pick via `socket` in
test setUp). No firewall allowance needed beyond localhost.

### File Access

| # | Agent | Stage | Scope | Mode | Reason | Tasks |
|---|-------|-------|-------|------|--------|-------|
| 9 | coder | implementing | `.agent/adventure-console/server.py` | read+write | Backend endpoint additions | T003, T004 |
| 10 | coder | implementing | `.agent/adventure-console/index.html` | read+write | Frontend rewrite | T005, T006, T007, T008, T009, T010, T011 |
| 11 | coder | implementing | `.agent/adventure-console/README.md` | read+write | Update docs | T014 |
| 12 | coder | implementing | `.agent/adventures/ADV-009/designs/**` | read | Consume designs | all implementation tasks |
| 13 | coder | implementing | `.agent/adventures/ADV-009/schemas/**` | read | Consume schemas | all |
| 14 | coder | implementing | `.agent/adventures/ADV-009/plans/**` | read | Consume plans | all |
| 15 | coder | implementing | `.agent/adventures/ADV-009/tests/**` | read+write | Write test strategy + test files | T001, T012 |
| 16 | coder | implementing | `.agent/adventures/ADV-009/research/**` | read+write | Write audit + glance report | T002, T013 |
| 17 | coder | implementing | `.agent/adventures/ADV-009/tasks/**` | read+write | Update task logs/status | all |
| 18 | coder | implementing | `.agent/adventures/ADV-009/adventure.log` | append | Pipeline logging | all |
| 19 | coder | implementing | `.agent/adventures/ADV-009/metrics.md` | append | Record per-agent metrics | all |
| 20 | coder | implementing | `.agent/adventures/ADV-00[1-8]/**` | read | Sample data for tests + manual glance | T002, T012, T013 |
| 21 | coder | implementing | `.agent/knowledge/{patterns,issues,decisions}.md` | read | Follow established patterns | all |
| 22 | code-reviewer | reviewing | `.agent/adventure-console/**`, `.agent/adventures/ADV-009/**` | read | Review all artifacts | all |
| 23 | qa-tester | reviewing | same as #22 + `.agent/adventures/ADV-009/tests/**` | read+write (tests only) | Add regression tests during review | T012, T021 |
| 28 | coder | implementing | `adventure_pipeline/**` | read+write | Sibling package (specs, tools, tests, README) | T015, T016, T017, T021 |
| 29 | coder | implementing | `ark/**` | **read-only** | Parse/verify only; Ark is never modified | T015, T016, T017, T018 |
| 30 | coder | implementing | `.agent/adventure-console/server.py` (addendum scope) | read+write | Add `/graph` and `depends_on` endpoints | T018 |
| 31 | coder | implementing | `.agent/adventure-console/index.html` (addendum scope) | read+write | Pipeline tab rendering + edit affordances | T019, T020 |
| 32 | code-reviewer | reviewing | `adventure_pipeline/**`, `ark/**` (read-only) | read | Review sibling package + confirm Ark untouched | T015-T021 |

Write access is explicitly denied outside `.agent/adventure-console/`,
`.agent/adventures/ADV-009/`, and `adventure_pipeline/`.
**`ark/**` is read-only for every agent** — enforcement via permission
#27 (`git diff --exit-code ark/`) in the relevant tasks.
No file outside the repo is touched.

### MCP Tools

None required for this adventure.

### External Access

None required at agent runtime. `marked.min.js` and `cytoscape.min.js`
(addendum) are loaded by the **browser** via CDN `<script>` tags in
`index.html`; agents do not fetch either. No WebFetch, no package install.
Playwright, if present, is only invoked in-process during T012 — no
browser binaries are downloaded mid-task (a green Tier-3 run is
best-effort; Tier-2 is the autotest proof-of-record).

## Validation Matrix

| Task | Agent | Stage | Read | Write | Shell | MCP | External | Verified |
|------|-------|-------|------|-------|-------|-----|----------|----------|
| T001 | coder | implementing | #15 | #15, #17, #18 | — | — | — | ✓ |
| T002 | coder | implementing | #10, #12, #16, #20 | #16, #17, #18 | — | — | — | ✓ |
| T003 | coder | implementing | #9, #12, #15, #21 | #9, #17, #18, #19 | #1, #2, #3 | — | — | ✓ |
| T004 | coder | implementing | #9, #12, #15 | #9, #17, #18, #19 | #1, #2, #3 | — | — | ✓ |
| T005 | coder | implementing | #10, #12, #15 | #10, #17, #18, #19 | #1 | — | — | ✓ |
| T006 | coder | implementing | #10, #12, #15 | #10, #17, #18, #19 | #1, #2 | — | — | ✓ |
| T007 | coder | implementing | #10, #12 | #10, #17, #18, #19 | #1 | — | — | ✓ |
| T008 | coder | implementing | #10, #12 | #10, #17, #18, #19 | #1 | — | — | ✓ |
| T009 | coder | implementing | #10, #12 | #10, #17, #18, #19 | #1 | — | — | ✓ |
| T010 | coder | implementing | #10, #12 | #10, #17, #18, #19 | #1 | — | — | ✓ |
| T011 | coder | implementing | #10 | #10, #17, #18, #19 | #1, #4 | — | — | ✓ |
| T012 | coder | implementing | #9, #10, #15, #20 | #15, #17, #18, #19 | #1, #2, #3 | — | — | ✓ |
| T013 | coder | implementing | #10, #16, #20 | #16, #17, #18, #19 | #2 | — | — | ✓ |
| T014 | coder | implementing | #11 | #11, #17, #18, #19 | — | — | — | ✓ |
| T015 | coder | implementing | #28, #29 | #28, #17, #18, #19 | #24, #27 | — | — | ✓ |
| T016 | coder | implementing | #28, #29 | #28, #17, #18, #19 | #24, #26 | — | — | ✓ |
| T017 | coder | implementing | #28, #29 | #28, #17, #18, #19 | #25, #27 | — | — | ✓ |
| T018 | coder | implementing | #9, #28, #29 | #30, #17, #18, #19 | #1, #2, #26 | — | — | ✓ |
| T019 | coder | implementing | #10 | #31, #17, #18, #19 | #1, #2 | — | — | ✓ |
| T020 | coder | implementing | #10 | #31, #17, #18, #19 | #1, #2 | — | — | ✓ |
| T021 | coder | implementing | #15, #28 | #15, #17, #18, #19 | #1, #2, #26 | — | — | ✓ |
| all  | code-reviewer | reviewing | #22, #32 | — | #5, #6 | — | — | ✓ |
| T021 | qa-tester | reviewing | #23, #32 | #23 (tests only) | #7, #8 | — | — | ✓ |

Validation checks (per planner rubric):
1. Every task has ≥ 1 permission per assigned agent — ✓.
2. Every shell command relevant to a task's files is covered — ✓.
3. Every `proof_command` in Target Conditions is covered by shell #1 or
   implicit frontend DOM inspection (via Tier-2 stdlib tests) — ✓.
4. Every file in a task's `files` field has a corresponding read/write
   permission — ✓.
5. Task-dependency read access — every dependent task's agent can read
   predecessor outputs via #12, #15, #16 — ✓.
6. Git operations — `git.mode: current-branch` (no per-task branches); no
   git shell entries required — ✓.

## Historical Notes

- **Bash allowlist rejection (ADV-008 T04)**: the first sub-agent
  invocation typically trips fine-grained allowlists. This plan
  pre-broadens with `python:*` and `python -m unittest:*` patterns above.
  Add `grep:*` / `rg:*` if Grep tool invocations fall through to shell.
- **Metrics append gap (ADV-002/005/006)**: metrics.md append access is
  called out explicitly (#19) for every task so no implementer loses it.
- **No Bash for tests (ADV-001)**: tests run under `python -m unittest`
  which is stdlib — no cargo/pytest allowlist needed. If Playwright is
  added later, it runs in-process (not as a separate shell).

## Approval

- [x] Approved by user — 2026-04-15T00:10:00Z
- [ ] Approved with modifications: {notes}
- [ ] Denied: {reason}
