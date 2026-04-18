# ADV009-T019 — Pipeline Tab Rendering (cytoscape + polling) — Design

## Approach

Extend `.agent/adventure-console/index.html` (a single-file app with no build
step) so that the v2 tab bar includes a fifth tab — **Pipeline** — positioned
between Documents and Decisions. Selecting it mounts a `cytoscape.js`
instance on `<div id="pipeline-canvas">`, polls
`GET /api/adventures/{id}/graph` (provided by ADV009-T018) every 5000 ms via
`setTimeout`, and draws nodes/edges whose status drives a colour mapping
sourced from the existing CSS custom-property palette. Tooltips are
rendered from the backend `explanations[id]` map only — no hardcoded
strings. A fixed-position legend in the canvas top-right identifies the
node kinds by colour swatch.

All new code lives inside the existing `<style>` block, the existing top-level
tabs array, the dispatcher `switch`, and a new `renderPipeline` + helper
block inside the existing `<script>` region. cytoscape.js (and
optionally cytoscape-dagre) are added as two `<script src="https://...">`
tags alongside the existing `marked.min.js` CDN tag — no bundler, no
local vendor copy.

Polling cadence is tunable at runtime via a `?poll=N` URL query parameter
(fall back to 5000 when absent/invalid). A single global `cy` instance is
kept in a module-scope variable; successive polls call `applyDiff(cy, g)`
which adds new nodes/edges, removes gone ones, and patches `status` on
survivors — preserving layout positions and selection. Leaving the tab
or switching adventures clears the polling timer and destroys `cy` so the
next mount starts clean.

## Target Files

- `.agent/adventure-console/index.html` — single file touched:
  - `<head>`: add two `<script src="https://cdn.jsdelivr.net/...">` tags
    for `cytoscape@3.28.1` and `cytoscape-dagre@2.5.0` (with its peer
    `dagre@0.8.5`). If dagre-layout is judged too heavy at implementation
    time, fall back to cytoscape's built-in `breadthfirst` layout and
    drop the two dagre scripts — no other change.
  - `<style>`: add `.pipeline-wrap`, `#pipeline-canvas`,
    `.pipeline-legend`, `.pipeline-tooltip` rules in the existing
    `<style>` block.
  - Tabs array (currently `[ 'overview', 'designs', ... 'log' ]`): insert
    `['pipeline', 'Pipeline']` immediately after the entry that will be
    renamed to "Documents" by ADV009-T006. Because T019 may land before
    T006's rename fully stabilises, the insertion point is keyed on
    "between Documents and Decisions" — insert after the `documents`
    entry (or, if T006 has not yet landed on this branch, after
    `research` as a best-effort placement and note in the task log).
  - `renderTab` switch: add `if (tab === 'pipeline') return
    pane.appendChild(this.renderPipeline(a));`
  - `App` object: add `renderPipeline(a)`, `mountCytoscape(pane, a)`,
    `pollGraph(advId)`, `applyGraphDiff(cy, payload)`, `stopPolling()`,
    `nodeStyleFor(kind, status)`, `showTooltip(node)`,
    `hideTooltip()`, `pipelinePollMs()` — all co-located in the file.
  - `switchTab` / adventure-switch cleanup: call `this.stopPolling()` and
    destroy any existing `cy` instance before re-rendering. Prevents
    orphaned pollers.

No other files change. (The `/graph` backend endpoint is owned by
ADV009-T018 and is a hard dependency of this task; T019 is purely the
frontend consumer.)

## Implementation Steps

1. **CDN script tags.** In `<head>`, below the existing `marked.min.js`
   tag, add:
   ```html
   <script src="https://cdn.jsdelivr.net/npm/cytoscape@3.28.1/dist/cytoscape.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
   ```
   Immediately after the third tag, guard-register the dagre layout so
   the file degrades cleanly if the CDN is unreachable:
   ```html
   <script>if (window.cytoscape && window.cytoscapeDagre) cytoscape.use(cytoscapeDagre);</script>
   ```

2. **CSS primitives.** Append to the existing `<style>` block:
   ```
   .pipeline-wrap { position: relative; height: 72vh; }
   #pipeline-canvas { position: absolute; inset: 0;
     background: var(--bg-alt);
     border: 1px solid var(--border); border-radius: 4px; }
   .pipeline-legend { position: absolute; top: 10px; right: 10px;
     background: var(--bg); border: 1px solid var(--border);
     border-radius: 4px; padding: 8px 10px;
     font-size: 11px; z-index: 5; pointer-events: none; }
   .pipeline-legend .sw { display: inline-block; width: 10px; height: 10px;
     margin-right: 6px; vertical-align: middle;
     border-radius: 2px; border: 1px solid var(--border); }
   .pipeline-tooltip { position: absolute; z-index: 10;
     background: #000c; color: var(--text);
     border: 1px solid var(--border); border-radius: 3px;
     padding: 6px 10px; font-size: 12px; max-width: 320px;
     pointer-events: none; display: none; }
   ```
   Reuse the existing `--muted`, `--accent`, `--ok`, `--warn`, `--err`,
   `--ink` (or `--text` if `--ink` is absent — it is not declared in the
   current `:root`; map design's `--ink` → `--text`) custom properties.
   Do not add new colour tokens.

3. **Tabs array insertion.** Locate the `const tabs = [ ... ]` literal
   inside `renderDetail` (around line 397). Insert
   `['pipeline', 'Pipeline'],` after the Documents/Research entry so the
   final left-to-right order is `Overview · Tasks · Documents ·
   Pipeline · Decisions`. If the v2 Documents tab has not yet replaced
   the legacy `designs/plans/research` entries at implementation time,
   place the insertion immediately before `['log', …]` (or whatever the
   pre-T006 structure has at that position) so Pipeline still appears
   after documentation-family tabs — the coder should log the exact
   chosen position in the task log.

4. **Dispatcher branch.** In `renderTab` (around line 430), add:
   ```js
   if (tab === 'pipeline') return pane.appendChild(this.renderPipeline(a));
   ```
   before the final `log` branch.

5. **`renderPipeline(a)`.** Returns a wrapper element:
   ```js
   renderPipeline(a) {
     const wrap = h('div', {class: 'pipeline-wrap'});
     const canvas = h('div', {id: 'pipeline-canvas'});
     const legend = this.renderPipelineLegend();
     const tip    = h('div', {class: 'pipeline-tooltip', id: 'pipeline-tip'});
     wrap.appendChild(canvas);
     wrap.appendChild(legend);
     wrap.appendChild(tip);
     // defer cy init until element is in DOM
     queueMicrotask(() => this.mountCytoscape(canvas, a));
     return wrap;
   },
   ```

6. **`mountCytoscape(el, a)`.**
   - Tear down any previous `this.cy` (`this.cy && this.cy.destroy()`)
     and clear `this.pipelineTimer` (via `stopPolling()`).
   - Instantiate cytoscape with
     `layout: { name: cytoscape.prototype.layouts && window.cytoscapeDagre ? 'dagre' : 'breadthfirst', rankDir: 'LR' }`
     and a `style` array driven by `nodeStyleFor`.
   - Register event handlers:
     - `cy.on('mouseover', 'node', e => this.showTooltip(e.target))`
     - `cy.on('mouseout', 'node', () => this.hideTooltip())`
     - `cy.on('tap', 'node', e => this.showTooltip(e.target))` (pin on
       click — untaps hide).
   - Call `this.pollGraph(a.id)` to perform the first fetch + start
     the polling loop.

7. **`pollGraph(advId)`.**
   ```js
   async pollGraph(advId) {
     if (this.currentId !== advId || this.currentTab !== 'pipeline') return;
     try {
       const g = await fetch(`/api/adventures/${advId}/graph`).then(j);
       this.lastGraphExplanations = g.explanations || {};
       this.applyGraphDiff(this.cy, g);
     } catch (e) {
       // surface via existing toast, but keep polling
       toast('Pipeline poll error: ' + (e.message || e), 'error');
     }
     this.pipelineTimer = setTimeout(
       () => this.pollGraph(advId), this.pipelinePollMs());
   },
   ```

8. **`applyGraphDiff(cy, payload)`.**
   - Collect current node ids (`cy.nodes().map(n => n.id())`) and edge
     ids; compute `toAdd`, `toUpdate`, `toRemove`.
   - `cy.add` the new ones, `cy.$('#' + id).remove()` the gone ones,
     and for survivors set only `data('status', ...)` / `data('label', ...)`
     so layout positions persist.
   - Re-run layout only when node set changes (count the added/removed
     cardinality); skip relayout on status-only updates so the graph
     doesn't jiggle every 5 s.

9. **`nodeStyleFor(kind, status)` / cytoscape style array.** Emit a
   single style array mapping CSS-var-derived colours. Use
   `getComputedStyle(document.documentElement).getPropertyValue('--ok')`
   etc. once at mount so cytoscape receives hex strings. Mapping:

   | kind | pending | in_progress/running | passed/done | failed/blocked |
   |------|---------|----------------------|--------------|-----------------|
   | task | `--muted` | `--accent` (animated pulse via `style: line-color-pulse` — optional) | `--ok` | `--err` |
   | tc | `--muted` | — | `--ok` | `--err` |
   | decision | `--warn` | — | `--ok` | — |
   | document | `--muted` | — | `--text` | — |
   | adventure | `--accent` | `--accent` | `--ok` | `--err` |
   | phase | `--muted` (compound parent — semi-transparent fill) | — | `--ok` | — |

   Use cytoscape's selector syntax:
   `cy.style([{selector: 'node[kind = "task"][status = "done"]', style: {'background-color': colours.ok}}, ...])`.

10. **`showTooltip(node)` / `hideTooltip()`.** Tooltip text is
    `this.lastGraphExplanations[node.id()]` — if absent, show nothing.
    Position at node's rendered coordinates (`node.renderedPosition()`)
    plus a small offset, clamped inside `#pipeline-canvas`.

11. **`pipelinePollMs()`.** Read `new URLSearchParams(location.search).get('poll')`;
    parse to integer; return 5000 for NaN / ≤0.

12. **`stopPolling()`.** Clears `this.pipelineTimer` and sets it to null.
    Call from `switchTab` (when moving away from `pipeline`), from
    `refreshDetail` before re-rendering, and from the adventure-switch
    path in `refreshList`.

13. **Legend renderer.** Static swatches for task (accent), tc (ok),
    decision (warn), document (text), adventure (accent-dim), phase
    (muted). One DOM call; no dynamic data.

14. **Sanity scans (coder self-check before submit).** Run by inspection
    of the final `index.html`:
    - `grep -n "WebSocket\|EventSource" index.html` → zero hits.
    - `grep -n "cytoscape" index.html` → at least one CDN URL.
    - The tabs array literal contains exactly five entries for the v2
      flow (Overview, Tasks, Documents, Pipeline, Decisions); any legacy
      extras surviving from pre-T006 state should be called out in the
      task log so ADV009-T006's reviewer can reconcile.
    - No literal tooltip strings inside `showTooltip` or
      `renderPipeline` — tooltip source is solely
      `this.lastGraphExplanations`.

## Testing Strategy

This task does not author tests — ADV009-T021 owns the static-inspection
tests for the Pipeline tab (`test_pipeline_tab.py`). T019's acceptance
is proven by:

- Manual smoke: run `python .agent/adventure-console/server.py`,
  select ADV-007 in the sidebar, click the Pipeline tab, observe graph
  renders with the documented status colours; hover a task node and
  confirm the tooltip text matches the `explanations` entry returned by
  `curl localhost:{port}/api/adventures/ADV-007/graph`.
- `?poll=2000` query parameter visibly speeds up status transitions.
- Network panel shows `GET /api/adventures/{id}/graph` repeating every
  N ms with `setTimeout` cadence (no WebSocket/EventSource frames).
- Static `grep` checks in step 14 all pass.

Automated coverage arrives with T021 (TC-047 through TC-051).

## Risks

- **T018 backend not yet landed.** T019 depends on ADV009-T018. If the
  `/graph` endpoint is absent at implementation time, mount the
  cytoscape instance with an empty data set and surface a clear empty
  state in the canvas ("Pipeline graph unavailable — backend missing")
  rather than throwing. Implementer should verify T018 is in place;
  otherwise block and return via the pipeline.
- **T006 tab rebuild collision.** Both T006 and T019 edit the tabs
  array. Since T006 rewrites the array wholesale and T019 inserts one
  entry, merges are trivial but ordering matters: the canonical v2
  order is `Overview · Tasks · Documents · Pipeline · Decisions`. If
  T006 has already landed its 4-tab array, T019 inserts cleanly. If
  T006 is still pending on this branch, T019 must fall back to the
  pre-v2 structure and note the deviation in the task log.
- **cytoscape CDN availability.** The decision doc explicitly allows
  self-hosting under `.agent/adventure-console/vendor/` as a follow-up
  if the CDN ever becomes unreachable. Out of scope for this task;
  mention only if the live CDN fetch fails during smoke testing.
- **dagre plugin optional.** If `cytoscape-dagre` loads fail, the guard
  in step 1 leaves cytoscape's built-in `breadthfirst` as layout. No
  rework needed; only the layout aesthetic changes.
- **Polling while tab is hidden.** `stopPolling()` must be called on
  every exit path (tab switch, adventure switch, refreshList). Missing
  a path leaks a timer per switch. The coder should audit every
  `currentTab = ` assignment and every `refreshDetail` entry.
- **Tooltip wiring drift.** TC-051 is violated by any hardcoded
  string in the tooltip path. Keep `showTooltip` one-line-simple:
  `tip.textContent = this.lastGraphExplanations[id] || ''; tip.style.display = tip.textContent ? 'block' : 'none';`
  — any branch that synthesises text from node data would break the
  contract.
