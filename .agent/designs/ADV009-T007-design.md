# ADV009-T007 — Implement Overview tab — Design

## Approach

Replace the current `renderOverview(a)` in `.agent/adventure-console/index.html`
with a three-section reader-first layout that uses the `.card`, `.progress`,
`.disclosure`, and `.stack` primitives introduced in T005 and consumes the
`summary` block produced by the backend (per `design-backend-endpoints.md`).
The three sections, top to bottom, are:

1. **Concept synopsis card** — first paragraph of `a.concept` as prose, the
   rest gated behind a `<details class="disclosure">` labelled "Show more".
2. **Target-conditions progress card** — a horizontal `.progress` bar with a
   per-status count label, followed by up to 5 non-passing TC rows (blockers
   first), followed by a `<details class="disclosure">` labelled "Show all
   TCs" that contains the full TC table (reuse the v1 table markup verbatim
   to preserve the "table kept behind disclosure" acceptance criterion in the
   design doc).
3. **Next-action card** — a single `.card` whose title + action button is
   chosen from a `kind → {title, label, href/onclick}` switch keyed by
   `a.summary.next_action.kind`, with fallback for missing `summary`.

All three sections are stacked inside a top-level `<div class="stack">`.

Every interactive / asserted element gets a `data-testid` attribute per
`design-test-strategy.md` §Data-testid hooks:
- `tc-progress-bar`, `tc-progress-label`
- `next-action-card`, `next-action-button`
- `show-details-concept`, `show-details-tcs`

No backend calls are made inside `renderOverview` — all data comes from the
adventure bundle already loaded into `this.currentAdv` by `openAdventure`.

## Target Files

- `.agent/adventure-console/index.html` — rewrite the `renderOverview(a)`
  method (currently lines 449–483). No other methods are touched by this
  task. The legacy `.concept-box` CSS rule at line 214 stays; the new
  synopsis wraps its prose in the concept-box class so prose styling is
  reused. No new global CSS is added here (all needed classes arrive via
  T005).

## Implementation Steps

1. **Locate and delete the current `renderOverview` body** (lines 449–483 of
   `.agent/adventure-console/index.html`). Keep the method name and `(a)`
   signature — it is dispatched from `renderTab` at line 437 and any new
   signature would break T006's dispatcher.

2. **Build the root container.** Replace the method body with:
   ```js
   const root = h('div', {class: 'stack'});
   root.appendChild(this.renderConceptCard(a));
   root.appendChild(this.renderTcProgressCard(a));
   root.appendChild(this.renderNextActionCard(a));
   return root;
   ```
   Add three private helper methods on the same object literal immediately
   after `renderOverview`.

3. **Implement `renderConceptCard(a)`:**
   - Return a `.card` containing `<h3>Concept</h3>`.
   - Split `a.concept || ''` on the first blank line: `const [first, ...rest] = (a.concept || '').split(/\n\s*\n/);`.
   - Render `first` (or a fallback "(no concept recorded)") inside a
     `<div class="concept-box">` using `marked.parse(first)` so inline
     markdown works.
   - If `rest.length > 0`, append `<details class="disclosure" data-testid="show-details-concept"><summary>Show more</summary><div class="concept-box"></div></details>`
     with `innerHTML = marked.parse(rest.join('\n\n'))`.
   - If `rest.length === 0`, omit the disclosure entirely (AC-4 requires the
     disclosure only when additional concept markdown exists).

4. **Implement `renderTcProgressCard(a)`:**
   - Read the summary block safely: `const s = a.summary || this.deriveSummary(a);` — add a `deriveSummary(a)` fallback helper that counts `a.target_conditions` by `status` client-side so the overview still renders if the backend endpoint from T003 hasn't shipped yet.
   - Compute counts: `tc_total`, `tc_passed`, `tc_failed`, `tc_pending` from `s`.
   - Percent: `const pct = tc_total ? Math.round(100 * tc_passed / tc_total) : 0;`.
   - Return a `.card` containing:
     - `<h3>Target Conditions</h3>`
     - `<div class="progress" data-testid="tc-progress-bar"><span style="width:{pct}%"></span></div>`
     - `<div class="tc-progress-label" data-testid="tc-progress-label">{tc_passed} / {tc_total} passed · {tc_failed} failed · {tc_pending} pending</div>` with `title` attribute repeating the same text for hover tooltip.
   - Below the bar, filter `a.target_conditions` to `tc.status !== 'passed'`, sort failed first then pending, slice to first 5, and render each as a one-line `<div class="tc-row">` with an inline status pill (`<span class="pill status-{status}">`), `<code>{tc.id}</code>`, and `{tc.description}` truncated to 80 chars.
   - If there are any target_conditions, append a `<details class="disclosure" data-testid="show-details-tcs"><summary>Show all TCs</summary></details>` whose body is the full 5-column TC table copied from the v1 renderer (ID / Description / Task(s) / Proof / Status). This satisfies AC-1 (progress bar is the primary view, not the table) while preserving full-table access.
   - If `a.target_conditions.length === 0`, skip both the preview rows and the disclosure and instead show `<div class="empty">No target conditions defined.</div>`.

5. **Implement `renderNextActionCard(a)`:**
   - Determine the `next_action` object: `const na = (a.summary && a.summary.next_action) || this.deriveNextAction(a);`.
   - Add a `deriveNextAction(a)` fallback keyed off `a.state` with the six-row mapping from `design-overview-tab.md`:
     | `a.state` | title | label | kind |
     |-----------|-------|-------|------|
     | `concept` | "Concept awaiting promotion." | "Start planning" | `promote_concept` |
     | `planning` | "Planning in progress." | "Open Decisions" | `open_plan` |
     | `review` | "Awaiting Checkpoint 2 approval." | "Approve permissions" | `approve_permissions` |
     | `active` | "{tasks_in_progress} tasks in progress." | "Open Tasks" | `open_tasks` |
     | `blocked` | "Blocked by {reason}." | "Open Decisions" | `resolve_blocker` |
     | `completed` | "Completed on {a.completed_at || 'unknown date'}." | "Read report" | `open_report` |
     If `a.state` is unknown, render a `none` card ("No action required.") with no button.
   - Return a `.card` with `data-testid="next-action-card"` containing:
     - `<h3>{title}</h3>`
     - A single `<button class="primary" data-testid="next-action-button">{label}</button>` whose `onclick` routes by `kind`:
       - `approve_permissions`, `open_plan`, `resolve_blocker` → `this.switchTab('decisions')`.
       - `open_tasks` → `this.switchTab('tasks')`.
       - `open_report` → `this.switchTab('documents')` (the report lives under Documents in v2).
       - `promote_concept` → POST `/api/adventures/{id}/state` with `{state: 'planning'}` via existing `API.setState` if available, else `this.switchTab('decisions')` as a safe default.
       - `none` → omit the button entirely.

6. **Wire CSS classes.** No new CSS is added in this task — all styles
   (`.card`, `.progress`, `.pill`, `.stack`, `.disclosure`) arrive from
   T005. Add only two inline style adjustments:
   - `.tc-progress-label { font-size: 11px; color: var(--muted); margin-top: 4px; }`
   - `.tc-row { display: flex; gap: 8px; align-items: center; padding: 2px 0; }`
   If T005 already declared these, skip; grep first.

7. **Add fallback helpers** (`deriveSummary`, `deriveNextAction`) as private
   methods on the same object literal, placed after `renderNextActionCard`.
   These let the Overview tab render correctly even before the T003 backend
   extension ships, which keeps T007 decoupled from T003 for the purposes
   of manual smoke testing.

8. **Remove the legacy "Adventure Report" button block** (lines 475–480 of
   the current `renderOverview`). In v2 the report is accessed via the
   `open_report` next-action kind when `state === 'completed'`, and via
   the Documents tab otherwise. The button here is redundant.

9. **Self-review** against the five target conditions (TC-018, TC-019,
   TC-020, TC-021, TC-033) before marking the task ready for review:
   - TC-018: progress bar element carries `data-testid="tc-progress-bar"`
     and is a `<div class="progress">`, not a table.
   - TC-019: non-passing preview rows exist above the Show-all disclosure,
     capped at 5, sorted failed→pending.
   - TC-020: `data-testid="next-action-card"` exists with a title that
     differs per state per the mapping table.
   - TC-021: raw concept markdown beyond the first paragraph lives only
     inside `<details data-testid="show-details-concept">`.
   - TC-033: every card uses `class="card"` — no ad-hoc inline card chrome.

## Testing Strategy

- **Manual smoke:** open each adventure state the team has on disk
  (`concept`, `planning`, `review`, `active`, `completed`) and confirm the
  next-action card title and button label match the mapping table above,
  and the progress bar width matches `tc_passed / tc_total`.
- **Tier 2 static assertions (T016 will author these):** verify the
  `data-testid` attributes listed in step 2 of the test-strategy hooks are
  all present in the rendered DOM after `switchTab('overview')` on a
  fixture adventure.
- **Regression:** confirm the Tasks/Documents/Decisions tabs (T006) still
  route correctly — `renderOverview` must not mutate any shared state
  outside the pane DOM.

## Risks

1. **`summary` shape coupling:** if T003 (backend `summary` extension) is
   not merged when T007 lands, the page breaks. Mitigated by the
   `deriveSummary`/`deriveNextAction` fallbacks — T007 can ship ahead of
   T003 and upgrade silently once the server field appears.
2. **Concept splitting heuristic:** splitting on `/\n\s*\n/` can over-split
   if the concept opens with a front-matter-ish block. Mitigated by
   falling back to show the entire concept in-line if `first` is shorter
   than 20 chars (treat as "no real first paragraph" and skip the
   disclosure rather than hiding content behind it — this protects AC-4
   from accidentally hiding the only paragraph).
3. **Unknown `a.state`:** the `deriveNextAction` fallback must not throw;
   the `none` branch returns a card with no button.
4. **CSS collision with legacy `.concept-box`:** the existing rule at line
   214 has dark-background styling that may clash with the new card
   palette. Leave `.concept-box` alone; if it looks wrong inside a
   `.card`, the fix belongs in T011 (retire legacy CSS), not here.
