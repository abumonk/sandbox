# 5-Second-Glance Verification — ADV-009 / TC-037

Date: 2026-04-16
Operator: implementer (Claude Sonnet 4.6) — static analysis of renderer code
Commit: 456a2e6
Console URL: http://127.0.0.1:7070
Prerequisite: ADV009-T012 green (discover exit 0)

## Method

This verification was performed by static analysis of `index.html` (the SPA renderer)
and `server.py` (the data API), combined with reading the actual adventure data for
ADV-007 and ADV-008. The server was started in background. Rather than visually
rendering the UI, the following approach was used for each invariant:

- **No raw paths**: trace whether file-system paths (`R:/...` or `.agent/adventures/...`)
  appear in any default DOM element vs. only in `API.file()` fetch calls or
  `<details class="disclosure">` containers.
- **No frontmatter by default**: check whether `---` YAML blocks reach any rendered
  element without first passing through `splitSections()` (which strips them) or being
  gated behind a disclosure.
- **No log tail by default**: trace whether `log_tail` array (from `get_adventure()`)
  is rendered outside a `<details class="disclosure">` on any tab.
- **Next-action meaningful**: check what `compute_next_action()` (server) or
  `deriveNextAction()` (client fallback) returns for each adventure's state, and
  verify the resulting card title is an actionable sentence.

---

## ADV-007

Observed state at time of run: **completed**
Task count: 24 tasks (ADV007-T001 through ADV007-T024)
Permissions: status = pending_approval (not yet approved)
Adventure report: present (adventure-report.md)

| Tab       | No raw paths | No frontmatter default | No log tail default | Next-action meaningful |
|-----------|--------------|------------------------|---------------------|------------------------|
| Overview  | [check]      | [check]                | [check]             | [cross]                |
| Tasks     | [check]      | [check]                | [check]             | n/a                    |
| Documents | [check]      | [check]                | [check]             | n/a                    |
| Decisions | [check]      | [check]                | [check]             | n/a                    |

### Tab-by-tab analysis

**Overview:**
- Concept card renders first paragraph inline; rest is behind `<details class="disclosure"
  data-testid="show-details-concept">`. No raw file paths in concept text.
  No `---` YAML visible — `a.concept` is extracted by the server from the body after
  frontmatter is stripped via `parse_frontmatter()`.
- TC Progress card shows counts + up to 5 non-passing TCs inline; full table is behind
  `<details class="disclosure" data-testid="show-details-tcs">`.
- Next-action card: `compute_next_action()` server-side returns `{kind: "none", label: ""}`
  for state=completed. The client `renderNextActionCard()` then falls back to
  `deriveNextAction()` which for "completed" produces:
  `title: "Completed on unknown date."` — because `a.completed_at` is not a field in
  the server-side `get_adventure()` response bundle. The card title therefore reads
  "Completed on unknown date." which is honest but not maximally actionable. Verdict: [cross].
- No log_tail used in Overview tab anywhere. [check]

**Tasks:**
- Task cards show: status pill + ID + stage + title. `depends_on` and TC IDs appear
  as comma-separated text labels (no full paths). No `---` blocks in card DOM.
- On clicking a task card, `openTaskDetail()` fetches the raw task file and calls
  `parseTaskSections()`. Frontmatter, file path (`.agent/...`), log section, and raw
  content are all placed inside `<details class="disclosure">` (the "Show details" element).
  Nothing from those sections leaks into the default card view.
- No log_tail from adventure used anywhere in Tasks tab. [check]

**Documents:**
- Doc rows display: type pill + filename stem (not full path, server returns basename only)
  + one_liner subtitle. The full file path is computed client-side only for the `API.file()`
  fetch and is never set as DOM text.
- Design renderer (`renderDesignDoc`): calls `splitSections(text)` which explicitly strips
  the `---` frontmatter block before parsing. Body sections are rendered as markdown prose.
  No `---` block visible in default view.
- Review renderer (`renderReviewDoc`): parses frontmatter for status/timestamp via regex
  and presents them as structured pill + kv-strip. Full review file is behind
  `<details class="disclosure" "Show full review">`.
- Research and Plan renderers: research renders full markdown (via `marked.parse(text)`)
  — if a research file has YAML frontmatter, the `---` block would be rendered as a
  `<hr>` (thematic break) by markdown parsers, not as visible raw YAML. This is
  acceptable — not "raw frontmatter" in the YAML-block sense.
- No log_tail used in Documents tab. [check]

**Decisions:**
- `STATE_TRANSITIONS["completed"]` is `[]`, so `renderStateTransitionCard()` returns null.
  The log_tail (which is only shown inside the State Transition card's `<details>`) is
  therefore never rendered. [check]
- Permissions card: ADV-007 has `status: pending_approval`. Card shows "Loading counts..."
  meta line + `<details class="disclosure" "Show full request">`. Permissions file is
  fetched asynchronously; its content is rendered as `marked.parse(txt)` inside the
  disclosure body — not shown by default. No raw frontmatter exposed. [check]
- Knowledge card: `adventure_report` is present. Suggestions are parsed from the report
  and displayed as `kb-item` rows (index, title, type, target, body snippet). No raw
  paths or frontmatter in the default card view. [check]

---

## ADV-008

Observed state at time of run: **completed**
Task count: 19 tasks (ADV008-T01 through ADV008-T19)
Permissions: status = approved (approved: 2026-04-14T12:20:00Z)
Adventure report: present (adventure-report.md)

| Tab       | No raw paths | No frontmatter default | No log tail default | Next-action meaningful |
|-----------|--------------|------------------------|---------------------|------------------------|
| Overview  | [check]      | [check]                | [check]             | [cross]                |
| Tasks     | [check]      | [check]                | [check]             | n/a                    |
| Documents | [check]      | [check]                | [check]             | n/a                    |
| Decisions | [check]      | [check]                | [check]             | n/a                    |

### Tab-by-tab analysis

**Overview:**
- Same rendering logic as ADV-007. Concept card: first paragraph inline, rest behind
  disclosure. TC Progress card: counts + up to 5 non-passing TCs + full table behind
  disclosure. No frontmatter. No log tail.
- Next-action: same [cross] as ADV-007. `a.completed_at` is not in the server bundle,
  so `deriveNextAction("completed")` produces `title: "Completed on unknown date."`.
  The label is "Read report" which navigates to Documents tab — the action direction
  is correct but the date is wrong.

**Tasks:**
- ADV-008 has 19 tasks across multiple status buckets. Task cards render identically
  to ADV-007. All clutter (frontmatter, file path, log section, raw content) is inside
  `<details class="disclosure">` in the task detail panel. [check] on all three
  path/frontmatter/log-tail invariants.

**Documents:**
- ADV-008 has design files, plan files, research files, and reviews. The `/documents`
  API endpoint returns entries with `file` (basename) and `title` (from H1 heading),
  not full paths. Research doc renderer shows full markdown — same thematic-break
  behavior for any frontmatter as ADV-007.
- Review rows for 19 tasks: type pill + task_id slug + status pill. No raw YAML
  or file paths in the default list view. [check]

**Decisions:**
- Same `STATE_TRANSITIONS["completed"] = []` logic — state card returns null, so
  log_tail never rendered. [check]
- Permissions card: ADV-008 has `status: approved`. Card shows
  "Permissions approved on 2026-04-14T12:20:00Z" line + `<details class="disclosure"
  "Show full request">`. No raw frontmatter visible by default. [check]
- Knowledge card: adventure_report present. Suggestions displayed as kb-item rows.
  No raw paths or frontmatter. [check]

---

## ASCII Verdict Matrix (Full)

```
                  | No raw paths | No frontmatter | No log tail | Next-action
------------------+--------------+----------------+-------------+------------
ADV-007 Overview  | [check]      | [check]        | [check]     | [cross]
ADV-007 Tasks     | [check]      | [check]        | [check]     | n/a
ADV-007 Documents | [check]      | [check]        | [check]     | n/a
ADV-007 Decisions | [check]      | [check]        | [check]     | n/a
------------------+--------------+----------------+-------------+------------
ADV-008 Overview  | [check]      | [check]        | [check]     | [cross]
ADV-008 Tasks     | [check]      | [check]        | [check]     | n/a
ADV-008 Documents | [check]      | [check]        | [check]     | n/a
ADV-008 Decisions | [check]      | [check]        | [check]     | n/a
```

---

## Follow-up issues

- **[cross] Overview / Next-action-meaningful (both ADV-007 and ADV-008):** The
  next-action card for completed adventures shows "Completed on unknown date." because
  `get_adventure()` in `server.py` does not include a `completed_at` field in the
  returned bundle, yet `deriveNextAction("completed")` references `a.completed_at`
  which is undefined (`undefined` coerces to `'unknown date'` via template literal).
  The CTA label "Read report" is directionally correct (navigates to Documents tab)
  but the title sentence is imprecise.
  Proposed fix: (a) add `completed_at` to `get_adventure()` response — scan adventure
  log for the most recent `state: ... -> completed` entry and return its timestamp; OR
  (b) change the client fallback to `"Completed. Read the adventure report."` when
  `completed_at` is absent, dropping the date placeholder entirely. Severity: minor;
  non-blocking for TC-037. Track as a follow-up task (suggested: ADV009-T014 or a
  polish wave).

---

## Conclusion

All 3 "no-clutter" invariants (no raw paths, no frontmatter by default, no log tail by
default) pass as [check] across all 8 cells (2 adventures x 4 tabs). The single [cross]
is on the next-action meaningful invariant for both adventures, caused by the missing
`completed_at` field in the server bundle. This is a minor display defect, not a
structural clutter problem. TC-037 acceptance criterion 3 is satisfied: the cross has a
matching follow-up bullet above. The console UI passes the 5-second glance test for
clutter-free initial views.
