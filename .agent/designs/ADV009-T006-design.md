# ADV009-T006: Rebuild Tab Bar and Header to v2 Shape - Design

## Approach

Edit `.agent/adventure-console/index.html` to replace the v1 nine-tab bar
with the v2 four-tab bar (Overview / Tasks / Documents / Decisions),
rebuild the header strip to the v2 shape (ID + title + state pill +
TC progress + primary CTA), compact the sidebar rows to the v2 shape
(state badge + ID + title + one-line subtitle), and harden `switchTab`
so unrecognized legacy keys route to `overview`.

This task is *structural only*. Full tab contents (Overview body,
Tasks cards, Documents chips, Decisions cards) are delivered in
T007-T010 — this task leaves those panes as empty placeholders that
the later tasks fill in. The v1 renderers for tabs that are going away
(`renderFileBrowser`, `renderPermissions`, `renderReviews`,
`renderKnowledge`, `renderLog`) remain in the source so the page
still loads; they are retired in T011.

Every interactive or asserted element gets a `data-testid` per the
test-strategy contract so T016+ UI tests can hook in.

## Target Files

- `.agent/adventure-console/index.html` — the only file modified:
  - `render()` method: new header, new tab list, new pane shell.
  - `switchTab()` method: fallback to `overview` for unknown keys.
  - `renderTab()` method: reduce to four branches + overview fallback.
  - `refreshList()` method: new sidebar row shape with subtitle.
  - `<style>` block: minor additions for `.adv-subtitle`,
    `.header-strip`, `.progress-inline`, `.cta-primary` (only if
    not already provided by T005's visual system).

## Implementation Steps

1. **Sidebar row rewrite** (`App.refreshList`)
   - For each adventure `a`:
     - Outer element: `<div class="adv-item" data-testid="adv-item-{id}">`.
     - Line 1: `<span class="badge state-{state}">{state}</span>
       <span class="adv-id">{id}</span> <span class="adv-title">{title}</span>`.
     - Line 2 (new): `<div class="adv-subtitle">{subtitle}</div>` where
       `subtitle` is computed client-side as:
       `firstSentence(a.subtitle || a.concept || '').slice(0, 80)`.
       Truncate with `…` if >80 chars. Use `a.subtitle` if the backend
       supplies it (T003/T004 may add it); otherwise derive from
       `a.concept`. When neither exists, omit the line entirely.
   - Remove any existing "Tasks: N" / file-count badges from the row.
   - Preserve click handler (`this.open(a.id)`) and `active` toggle.

2. **Header strip rewrite** (`App.render` → top of `content`)
   - Build a single `<div class="adv-header header-strip"
     data-testid="adv-header">` containing, in order:
     1. `<span class="adv-id" data-testid="header-id">{a.id}</span>`
     2. `<h1 data-testid="header-title">{a.title}</h1>`
     3. `<span class="pill state-{a.state}" data-testid="header-state-pill">{a.state}</span>`
     4. Progress block (see step 3).
     5. Primary CTA (see step 4).
   - Below the strip, keep a small meta row:
     `<div class="adv-meta"><span>Updated {a.updated}</span></div>`.
     Drop `Created` and `Tasks: N` from the default header (task count
     is now one click away in Tasks).
   - Remove the old free-standing "Transition →" button row from the
     header — state-transition buttons move to the Decisions tab (T010).

3. **TC progress indicator**
   - Compute counts from `a.summary` when present
     (`{tc_total, tc_passed, tc_failed, tc_pending}` per
     `design-backend-endpoints`). Fallback to counting
     `a.target_conditions` client-side if `summary` is absent
     (defensive — lets this task land before T003 if waves are
     reordered).
   - Render:
     ```html
     <div class="progress-inline" data-testid="tc-progress-bar">
       <div class="progress">
         <span style="width:{pct}%"></span>
       </div>
       <span class="progress-label"
             data-testid="tc-progress-label">{passed}/{total} TCs</span>
     </div>
     ```
   - `pct = total ? Math.round(100 * passed / total) : 0`.
   - When `total === 0`, render a dimmed label "No TCs" with empty bar.

4. **Primary CTA**
   - Read `a.summary?.next_action` (shape from
     `design-backend-endpoints`: `{kind, label, state_hint}`).
   - If `next_action` is missing or `kind === 'none'`, render nothing
     (the CTA slot collapses).
   - Otherwise render:
     `<button class="cta-primary" data-testid="header-cta">{label}</button>`.
   - Click behavior maps `kind` to a local action:
     - `approve_permissions` → `App.switchTab('decisions')`
     - `open_plan`           → `App.switchTab('tasks')`
     - `resolve_blocker`     → `App.switchTab('decisions')`
     - `promote_concept`     → `App.switchTab('decisions')`
     - unknown kind          → `App.switchTab('overview')` (defensive)
   - No network calls here — the Decisions tab owns the actual
     approve/transition verbs.

5. **Tab bar rewrite** (`App.render` → tab list)
   - Replace the nine-entry `tabs` array with exactly:
     ```js
     const tabs = [
       ['overview',  'Overview'],
       ['tasks',     'Tasks'],
       ['documents', 'Documents'],
       ['decisions', 'Decisions'],
     ];
     ```
   - For each `[key, label]`, emit:
     `<div class="tab" data-testid="tab-{key}">{label}</div>`.
   - No inline counts in the tab labels (counts were v1 noise per the
     simplification audit); badge-style counters can be added later
     if UX requires them — out of scope here.
   - Keep the existing CSS `.tab` / `.tab.active` styling.

6. **`switchTab` hardening**
   - Replace the fragile `el.textContent.toLowerCase().startsWith(key.slice(0,4))`
     active-class toggle with an explicit map driven by `data-testid`:
     ```js
     const KNOWN_TABS = ['overview', 'tasks', 'documents', 'decisions'];
     switchTab(key) {
       if (!KNOWN_TABS.includes(key)) key = 'overview';
       this.currentTab = key;
       document.querySelectorAll('.tab').forEach(el => {
         el.classList.toggle('active',
           el.getAttribute('data-testid') === 'tab-' + key);
       });
       this.renderTab();
     }
     ```
   - This fulfils "Route unrecognized legacy tab keys to Overview"
     (TC-005 defensively) and fixes the existing brittle prefix match.

7. **`renderTab` reduction**
   - Shrink to:
     ```js
     renderTab() {
       const pane = $('#pane');
       if (!pane) return;
       pane.innerHTML = '';
       const a = this.currentAdv;
       const tab = this.currentTab;
       if (tab === 'overview')  return pane.appendChild(this.renderOverview(a));
       if (tab === 'tasks')     return pane.appendChild(this.renderTasks(a));
       if (tab === 'documents') return pane.appendChild(this.renderDocuments(a));
       if (tab === 'decisions') return pane.appendChild(this.renderDecisions(a));
     }
     ```
   - Add placeholder stubs for `renderDocuments` and `renderDecisions`
     that return a `<div class="empty">Coming in T009/T010.</div>`
     element. T007/T008/T009/T010 replace these stubs; T006 only owns
     the routing shell.
   - Leave `renderOverview` and `renderTasks` *as they are* — T007/T008
     replace their bodies. They must still return a valid DOM node so
     the page doesn't crash between waves.

8. **Minor CSS additions** (inside existing `<style>` block; skip any
   rule already present from T005's visual system)
   ```css
   .header-strip { gap: 14px; align-items: center; }
   .header-strip .pill { margin-left: 4px; }
   .progress-inline {
     display: inline-flex; align-items: center; gap: 8px;
     min-width: 160px;
   }
   .progress-inline .progress { flex: 1; }
   .progress-inline .progress-label {
     font-size: 11px; color: var(--muted);
     font-family: "Cascadia Mono", monospace;
   }
   .cta-primary { margin-left: auto; }
   .adv-subtitle {
     font-size: 11px; color: var(--muted);
     margin-top: 2px;
     white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
   }
   ```
   - If T005 already defines `.progress` / `.pill`, rely on those and
     add only the `-inline` / `-subtitle` / `-strip` / `cta-primary`
     helpers.

9. **Data-testid inventory added this task**
   - `adv-item-{id}` (sidebar row)
   - `adv-header`
   - `header-id`, `header-title`, `header-state-pill`, `header-cta`
   - `tc-progress-bar`, `tc-progress-label`
   - `tab-overview`, `tab-tasks`, `tab-documents`, `tab-decisions`
   - All exactly as enumerated in `design-test-strategy.md`.

## Testing Strategy

- **Tier 2 static assertions** (T016 will author these):
  - `index.html` contains exactly four `data-testid="tab-*"` tab
    attributes (`overview|tasks|documents|decisions`). No occurrences
    of `data-testid="tab-log"`, `tab-knowledge`, `tab-permissions`,
    `tab-designs`, `tab-plans`, `tab-research`, `tab-reviews`.
  - `index.html` contains the five required header testids in order:
    `header-id` before `header-title` before `header-state-pill`
    before `tc-progress-bar` before `header-cta` (regex on the source
    establishes ordering without a browser).
  - `adv-subtitle` class selector exists in the stylesheet and is used
    inside the sidebar row emit.
  - `KNOWN_TABS` constant appears in the source and lists exactly the
    four tab keys.

- **Tier 3 smoke** (if Playwright available):
  - Open the page against an ADV-TEST fixture, assert four tab
    elements are visible.
  - Click `tab-decisions`, verify `renderDecisions` stub text, click
    back to `tab-overview`.
  - Set `window.App.switchTab('log')` → assert the active class lands
    on `tab-overview` (legacy-key routing).

- **Manual smoke** (no build step, so a human loads the console):
  - Confirm real adventures still load (header renders for any state).
  - Confirm the sidebar row collapses to the compact form.

## Risks

- **Dependency slip on T003's `summary` block.** If T003 has not yet
  landed when this task is implemented, `a.summary` will be undefined
  and the progress bar / CTA would crash. Mitigation: every read of
  `a.summary` uses optional chaining with a client-side fallback
  (count `a.target_conditions`; hide CTA if no `next_action`). The
  depends_on list still includes T003 so the scheduler prefers the
  correct order.
- **Legacy renderers still defined.** Leaving `renderFileBrowser`,
  `renderPermissions`, `renderReviews`, `renderKnowledge`, `renderLog`
  in the source is deliberate (T011 retires them). Make sure
  `renderTab` no longer *calls* them; otherwise a stale v1 code path
  could resurrect a removed tab. Verify by grep: only the four v2
  renderers appear inside `renderTab`.
- **Active-class toggle brittleness.** The v1 prefix-matcher caused
  subtle bugs (e.g., `knowledge` and `log` share no prefix but the
  old code happened to work). Switching to an explicit `data-testid`
  comparison (step 6) is a hard requirement for this task, not an
  optional cleanup.
- **CSS collision with T005.** T005 adds `.pill`, `.progress`,
  `.chip-bar`, `.chip`, `.card`, `.stack`, `.disclosure`. This task
  must not redefine those selectors — only add the four helpers
  listed in step 8. If T005 has not merged yet, fall back to
  duplicating `.pill`/`.progress` locally and flag the duplication
  in the Log so T005 can dedup.
