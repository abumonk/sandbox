# Retire legacy renderers and dead CSS - Design

## Approach

This is a surgical cleanup task that runs *after* ADV009-T007..T010 have
replaced the v1 tab renderers with the four v2 tabs (Overview, Tasks,
Documents, Decisions). The goal is to excise v1-only code paths and CSS
that no other renderer references anymore, without removing anything the
v2 renderers still depend on.

Source of truth for what is dead:
- `design-information-architecture.md` — removed tabs: Designs, Plans,
  Research, Reviews, Knowledge, Log, Permissions.
- `design-visual-system.md` — `.split` is retired for v2 views;
  `.log-tail` is **kept** (used inside disclosures).
- `design-decisions-tab.md` — `parseKnowledgeSuggestions` is reused by
  `renderDecisions`, so it must stay.

## Target Files

- `.agent/adventure-console/index.html` — remove dead renderers, dead tab
  dispatch branches, and dead CSS. This is the only file touched.

## Legacy Code Inventory (from current index.html)

JavaScript renderers (locations at time of planning, may shift after T005-T010):

| Symbol | Lines (approx) | Verdict |
|---|---|---|
| `renderFileBrowser(pane, files, dirRel, kind)` | 530-578 | **Delete** — replaced by Documents tab |
| `renderPermissions(a)` | 581-611 | **Delete** — folded into Decisions card |
| `renderReviews(a)` | 614-666 | **Delete** — replaced by Documents `renderReviewDoc` |
| `renderKnowledge(pane, a)` | 669-725 | **Delete** — folded into Decisions card |
| `renderLog(a)` | 728-733 | **Delete** — log tail moved behind Overview/Decisions disclosures |
| `parseKnowledgeSuggestions(md)` | 760-~790 | **Keep** — still used by Decisions card (T010) |

Tab-dispatch branches in `renderTab()` (lines ~430-446):

| Branch | Verdict |
|---|---|
| `tab === 'overview'` | Keep (rewritten in T007) |
| `tab === 'designs'` / `'plans'` / `'research'` / `'reviews'` / `'permissions'` / `'knowledge'` / `'log'` | **Delete** — these tab keys no longer exist in the nav (T006) |
| `tab === 'tasks'` | Keep (rewritten in T008) |
| New branches for `'documents'` / `'decisions'` | Already added by T006/T009/T010 |

The fallback behavior in `switchTab(key)` (lines ~422-428) must be preserved so that an unknown key (e.g. an old bookmark pointing at `#knowledge`) does not crash — it should fall through to Overview. T006 introduces this fallback; this task leaves it intact.

There is also a stale cross-tab link in `renderOverview`:
```js
btn.onclick = () => this.currentTab = 'reviews' && this.switchTab('reviews');
```
(line 478). `'reviews'` is no longer a top-level tab. This button must be updated to navigate to `'documents'` (and ideally auto-select the adventure-report in the unified list) or removed. T007 owns the new Overview renderer; if T007 has already handled this, confirm; otherwise include the fix in this task.

CSS rules (in the `<style>` block ~lines 150-225):

| Selector | Verdict |
|---|---|
| `.split`, `.split .file-list` (lines 153-161) | **Delete** — retired per visual-system design |
| `.file-list .file-entry`, `.file-list .file-entry:hover`, `.file-list .file-entry.active` (lines 162-169) | **Delete with `.split`** — these only lived inside the two-column split browser |
| `.file-view`, `.file-view h1/h2/h3`, `.file-view table`, `.file-view table th` (lines 170-180) | **Conditional** — verify no v2 renderer (`renderDesignDoc`, `renderPlanDoc`, `renderResearchDoc`, `renderReviewDoc`, `renderDecisions` full-permissions disclosure) emits `<div class="file-view">`. If none do, delete; if any still do, keep the rules. |
| `.kb-item`, `.kb-item input[type=checkbox]`, `.kb-item .kb-body`, `.kb-item .kb-title`, `.kb-item .kb-meta`, `.kb-item .kb-content` (lines 183-195) | **Keep** — Decisions' knowledge card (T010) reuses the same checkbox form markup. Re-verify after T010 lands; delete only if T010 replaced them with new classes. |
| `.log-tail` (~line 221) | **Keep** — used inside Overview / Decisions disclosures. |

## Implementation Steps

1. **Re-read `index.html` post-T010** to confirm which symbols and classes are actually referenced. The line numbers above will have shifted; grep is the ground truth.
2. **Delete the five legacy renderer methods** from the `App` object: `renderFileBrowser`, `renderPermissions`, `renderReviews`, `renderKnowledge`, `renderLog`. Leave the `// ----- Tasks -----` / `// ----- Overview -----` comment banners intact for their respective surviving renderers.
3. **Prune `renderTab()`**: remove the seven obsolete `if (tab === ...)` branches. Keep: `overview`, `tasks`, `documents`, `decisions`. The final `renderTab` should be straightforward dispatch with no fallthrough branches for legacy keys.
4. **Audit `switchTab(key)`**: confirm the T006 fallback coerces unknown keys to `overview`. If the current code still uses `el.textContent.toLowerCase().startsWith(key.slice(0,4))` for active-state detection, that brittle heuristic may now mismatch because Tasks/Decisions both start with different prefixes — T006 should have replaced it with explicit `data-tab` attributes; verify. If not fixed already, fix here: set active by matching `data-tab === key` and coerce unknown keys to `overview` before rendering.
5. **Fix the cross-tab link in Overview's adventure-report button** (if T007 hasn't): replace `this.currentTab = 'reviews' && this.switchTab('reviews')` with `this.switchTab('documents')` plus an optional client-side chip pre-selection. If T007 already owns this, skip.
6. **Delete dead CSS rules**: `.split`, `.split .file-list`, `.file-list .file-entry` (all three variants), in one block. Then check each of `.file-view` and `.kb-item` family via `grep -n "file-view" index.html` / `grep -n "kb-item\|kb-body\|kb-title\|kb-meta\|kb-content" index.html`. If all remaining matches are inside CSS (i.e. no `class: 'file-view'` / `class: 'kb-...'` in JS), delete those rules too; otherwise leave them.
7. **Verify with grep** (this is the acceptance check):
   - `grep -c "renderFileBrowser\|renderKnowledge\|renderLog\|renderPermissions\|renderReviews" index.html` should return 0. (`parseKnowledgeSuggestions` still present is fine — it contains neither `renderKnowledge` as a substring once the renderer method is gone, though the underlying regex is tight.)
   - `grep -n "'designs'\|'plans'\|'reviews'\|'permissions'\|'knowledge'\|'log'" index.html` should show no matches in the tab-dispatch area (matches elsewhere, e.g. in `a.designs`, `a.plans`, `a.reviews` array access from the new renderers, are expected and correct).
8. **Smoke test**: open the console, load each adventure, click each of the four tabs, confirm no JS console errors and no empty panes.

## Testing Strategy

- **Static grep checks** as listed above (this is the stated acceptance criterion).
- **Manual smoke test**: load the console; for a representative adventure with all doc types (e.g. ADV-009 itself), click Overview → Tasks → Documents → Decisions. Verify:
  - No errors in DevTools console.
  - The Overview adventure-report button (if present) navigates without throwing.
  - An old URL hash like `#knowledge` does not crash — falls back to Overview.
- **Line-count diff**: expect a net negative change of ~200 lines (approx. 150 JS + 50 CSS). A positive or near-zero diff indicates legacy code was kept by mistake.

## Risks

- **False-positive deletion of `.file-view` / `.kb-*`**: if a v2 renderer (T009's `renderDesignDoc`, or T010's permissions disclosure) uses `<div class="file-view">` to style a markdown block, removing the CSS would silently break formatting. Mitigation: grep for `class: 'file-view'` (or `class="file-view"`) *before* deleting, and delete the rules only if there are zero JS callers.
- **Brittle `switchTab` active-detection**: the legacy `startsWith(key.slice(0,4))` heuristic may work for `overview`/`tasks`/`decisions` but collide on `documents` vs `decisions` (both start with `dec`/`doc` — actually distinct at char 1, but the 4-char prefix coincidentally still works). This is an existing bug class; T006 is expected to have replaced it with explicit attributes. Verify rather than assume.
- **Stale `'reviews'` link in Overview**: if T007 shipped without rewriting the adventure-report button, this task's cleanup would leave a dangling reference to the retired `'reviews'` tab key. The task description doesn't explicitly name this, but step 5 covers it.
- **Scope creep**: the task is pure removal. Resist adding new features (e.g. a proper URL-hash router for tab state) — those belong in a separate task.
