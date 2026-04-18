# ADV009-T013 — 5-Second-Glance Manual Verification — Design

## Approach

Task T013 is the only **manual** proof for TC-037: the manifest success
criterion ("open the console, glance at any adventure, and know within 5
seconds what state it's in, what's blocking it, and what action is
expected of you — without reading any frontmatter or shell command").

The verification is performed by a human operator after ADV009-T012
lands a green `unittest discover` run. The deliverable is a single
report at `.agent/adventures/ADV-009/research/5s-glance-report.md`
that records, per adventure and per tab, check/cross verdicts for the
four "no-clutter" invariants called out in the concept:

1. **No raw paths visible** — e.g. `.agent/adventures/ADV-007/…/foo.md`
   must not appear as primary text in any default view.
2. **No frontmatter visible by default** — YAML `---` blocks are hidden
   behind a "Show details" disclosure.
3. **No log tail visible by default** — `adventure.log` content does
   not appear on the default view of any tab.
4. **Next-action card is meaningful** — the Overview-tab next-action
   card names a single, actionable sentence that matches the adventure's
   current state.

Two adventures are exercised — ADV-007 and ADV-008 — because they are
the most content-rich in the tree (many tasks, designs, reviews), i.e.
the most likely to expose clutter.

## Target Files

- `.agent/adventures/ADV-009/research/5s-glance-report.md` — new report
  file. Contains per-adventure verdict matrices for Overview / Tasks /
  Documents / Decisions and a follow-up-issues section for any crosses.

## Implementation Steps

1. **Prerequisite sanity check.** Confirm ADV009-T012 is `done` (green
   `python -m unittest discover -s .agent/adventures/ADV-009/tests -p
   "test_*.py"`). If not, mark this task blocked on T012 — do not run
   the manual pass against unfinished UI.

2. **Start the server.** From `R:/Sandbox`:
   ```
   python .agent/adventure-console/server.py
   ```
   Open `http://127.0.0.1:7070` in a browser.

3. **Run the 5-second glance for ADV-007.** For each of the four tabs
   (Overview, Tasks, Documents, Decisions):
   - Close/refresh, select ADV-007 from the sidebar, land on the tab.
   - Wait no more than 5 seconds before forming the verdict.
   - Record one of `[check]` / `[cross]` / `n/a` in the matrix cell for
     each of the four invariants. `n/a` is allowed only where the
     invariant cannot apply (e.g. log-tail check on Decisions if that
     tab has no log-derived widget).
   - For the Overview tab specifically, also record whether the
     next-action card (invariant 4) names a single meaningful action
     appropriate to ADV-007's current `state`.

4. **Repeat for ADV-008.** Same procedure, independent verdicts.

5. **Write the report** at
   `.agent/adventures/ADV-009/research/5s-glance-report.md` using this
   skeleton (ASCII only — per repo convention, avoid unicode check
   marks; use `[check]` / `[cross]` / `n/a`):

   ```markdown
   # 5-Second-Glance Verification — ADV-009 / TC-037

   Date: 2026-04-15
   Operator: <name>
   Commit: <short SHA at time of run>
   Console URL: http://127.0.0.1:7070
   Prerequisite: ADV009-T012 green (discover exit 0)

   ## ADV-007

   | Tab       | No raw paths | No frontmatter default | No log tail default | Next-action meaningful |
   |-----------|--------------|------------------------|---------------------|------------------------|
   | Overview  |              |                        |                     |                        |
   | Tasks     |              |                        |                     | n/a                    |
   | Documents |              |                        |                     | n/a                    |
   | Decisions |              |                        |                     | n/a                    |

   ## ADV-008

   (same table)

   ## Follow-up issues

   (one bullet per `[cross]`, naming tab + invariant + observed clutter
    + proposed fix. Each bullet is NON-blocking for T013 itself —
    T013's contract is that the report exists and is honest, not that
    every cell is a check.)
   ```

6. **File follow-ups (non-blocking).** Any `[cross]` verdict spawns a
   one-line bullet in the "Follow-up issues" section naming: (a) which
   tab, (b) which invariant failed, (c) what was observed, (d) a
   proposed fix. These are *logged in the report*, per acceptance
   criterion 3 — they do not block task completion.

7. **Commit the report.** Single file add:
   `.agent/adventures/ADV-009/research/5s-glance-report.md`.

8. **Mark task done.** Flip task `status: done` and acceptance
   criteria to `[x]`, append a planner/operator `## Log` line.

## Testing Strategy

This task has no autotest — TC-037's `proof_method` is `manual` by
design. Verification is:

- **Report existence.** The file path above exists after execution.
- **Coverage.** The report contains both "## ADV-007" and "## ADV-008"
  sections, each with a populated 4x4 (or 4x3 with `n/a`) verdict
  matrix.
- **Honesty contract.** Every `[cross]` has a matching "Follow-up
  issues" bullet. No silent failures.

The reviewer agent (ADV009-T012 downstream / adventure-review) will
grep the report for these three structural invariants; any missing
section or orphan cross is a review failure, not a task-level
blocker.

## Risks

- **Subjectivity of "meaningful" next-action.** Mitigation: acceptance
  criterion 2 only requires a verdict, not unanimous agreement — one
  human operator's call is authoritative for this report. Follow-up
  issues capture disagreement for later triage.
- **5-second timer is loose.** Mitigation: the timer is directional,
  not hard. Operators should not retroactively change verdicts after
  studying a tab for longer; they should record "[cross] at 5s but
  [check] after 15s" in the follow-up bullet.
- **Adventure state drift.** ADV-007 and ADV-008's states may change
  between T013 scheduling and execution; record the observed `state`
  in the header of each adventure's section so reviewers can
  contextualize the next-action verdict.
- **n/a overuse.** Operators may mark invariants 2/3 (frontmatter /
  log) as `n/a` for Tasks/Documents/Decisions to shortcut work. Rule:
  only `n/a` when the tab *structurally* cannot expose that clutter.
  If the tab has a "Show details" disclosure, it is in scope.
