# ADV009-T020 — Add graph edit affordances — Design

## Approach

T020 layers interactive editing on top of the Pipeline canvas mounted by
T019. All client logic lives inside a new `PipelineEdit` module in
`index.html` and attaches itself to the cytoscape instance (`cy`) exposed
by T019. No new library is loaded — we use cytoscape's native event API
(`tap`, `cxttap`, `taphold`, `mouseup`) plus a hand-rolled DOM context
menu styled with existing `.card` / `.stack` primitives.

All mutation paths route through the existing `API.*` helpers
(`setState`, `approveDes`, `approvePerm`, `applyKB`) except for one new
helper `API.addDepends(advId, taskId, depTaskId)` that POSTs to the
endpoint added by T018. No other new routes are introduced.

Authoritative contract: `.agent/adventures/ADV-009/designs/design-graph-edit-affordances.md`.

## Target Files

- `.agent/adventure-console/index.html` — add `API.addDepends`, add
  `PipelineEdit` module (event wiring, optimistic edge + rollback, DOM
  context menu, 500 ms double-submit guard), invoke
  `PipelineEdit.attach(cy, adv)` from the end of `renderPipeline()`
  (landed by T019).

## Implementation Steps

1. **Add `addDepends` to the `API` object** (near line 256, alongside
   `log`):
   ```js
   addDepends: (id, taskId, depTaskId) =>
     post('/api/adventures/' + id + '/tasks/' + taskId + '/depends_on',
          {depends_on: depTaskId}),
   ```

2. **Introduce a double-submit guard helper** shared across all mutation
   gestures. A single `PipelineEdit._busy` flag + 500 ms window is
   simpler than per-button spinners and matches the design's "button
   disables + spinner for 500 ms" intent without needing per-gesture DOM.
   ```js
   const EDIT_GUARD_MS = 500;
   function guardOnce(fn) {
     if (PipelineEdit._busy) return;
     PipelineEdit._busy = true;
     try { return fn(); } finally {
       setTimeout(() => PipelineEdit._busy = false, EDIT_GUARD_MS);
     }
   }
   ```

3. **State-transition edge click** — bind `cy.on('tap', 'edge[kind = "state_transition"]', ...)`:
   - Extract target node id of shape `state:<name>` → parse `<name>`.
   - Call `guardOnce(async () => { await API.setState(adv.id, name); toast('State -> ' + name, 'ok'); })`.
   - On reject: `toast('Error: ' + e, 'error')`; no rollback needed (no
     optimistic change for state edges — server is authoritative and next
     poll tick re-renders).

4. **Drag-to-depend (task A → task B)** — cytoscape has no built-in
   edge-draw mode, so implement minimal drag-connector:
   - `cy.on('taphold', 'node[kind = "task"]', evt => beginDragFromNode(evt.target))` starts a tentative edge with `cy.add({group:'edges', data:{id:'_tentative', source, target:source, kind:'depends_on', optimistic:true}})` and a `mousemove` handler on the cytoscape container that updates the ghost edge target to the hovered node (or resets to source if none).
   - On `mouseup` over a task node `B != A`: remove the tentative edge, immediately add the final optimistic edge `{id:'_opt-<A>-<B>', source:A, target:B, kind:'depends_on', optimistic:true}`, then call `guardOnce(async () => {...})` invoking `API.addDepends(adv.id, A, B)`.
   - On success: stamp the edge id to its real id (or leave `_opt-*` in place — next poll tick replaces it); `toast('Added depends_on: ' + A + ' -> ' + B, 'ok')`.
   - On 4xx/5xx: `cy.remove('#_opt-<A>-<B>')` (rollback); `toast(err.error || err || 'Server unreachable — retry?', 'error')`.
   - If `mouseup` lands on empty canvas or source === target: remove tentative edge, no POST.
   - **Single-fire guarantee**: `mouseup` handler attaches once per `taphold`, removes itself on completion, and is wrapped in `guardOnce` so a double `mouseup` (rare, from synthetic events) cannot produce two POSTs.

5. **Right-click DOM context menu**:
   - Add `<div id="pipeline-ctx" class="card" style="position:absolute; display:none; z-index:1000; min-width:180px;"></div>` near the canvas mount.
   - On `cy.on('cxttap', node => showCtxMenu(node, evt.renderedPosition))`:
     - Build items from the affordance matrix in
       `design-graph-edit-affordances.md` based on `node.data('kind')`:
       - `document` → "Open document" (link to `/files/<path>` stored in `node.data('path')`).
       - `document` with `docKind === 'design'` → adds "Approve design" (calls `API.approveDes(adv.id, node.data('name'))`).
       - `decision` with label containing `permissions` → "Approve permissions" (calls `API.approvePerm(adv.id)`).
       - `decision` with label containing `knowledge` → "Apply knowledge suggestion" (calls `API.applyKB(adv.id, [...indices from node.data('indices')])`).
       - `task` → "Open task detail" (client-side: `App.showTab('tasks'); App.openTaskDrawer(node.data('taskId'))` — `openTaskDrawer` is supplied by T008's Tasks tab).
     - Each item click runs inside `guardOnce(...)` for the mutation ones; menu hides on any click or on `document` `click` outside.
   - Position menu at `evt.originalEvent.clientX / clientY` relative to the viewport. Hide on `Escape` and on cytoscape `tap` (left-click anywhere).

6. **Tooltip hook** already exists (T019 wires `explanations[id]` on hover). T020 adds no tooltip code; it only adds event handlers. This keeps TC-051 unaffected.

7. **Wire-up call from T019's `renderPipeline(adv)`** — after T019's
   `mountCytoscape('#pipeline-canvas')` call, add one line:
   ```js
   PipelineEdit.attach(cy, adv);
   ```
   (T019 owns the tab; T020 provides this module. T019 merges this call
   because the merge is additive and T020 depends on T019.)

## Testing Strategy

Covered by T021's `tests/test_pipeline_tab.py`:
- **TC-055** (single POST per gesture): pattern-grep `index.html` for
  `API.addDepends` call sites — must be exactly one invocation inside
  `guardOnce`.
- **TC-056** (rollback on 4xx): pattern-grep for `cy.remove` in the
  catch-branch adjacent to `addDepends`, plus `toast(...'error')`.
- **TC-057** (context menu routes): pattern-grep the `PipelineEdit`
  block for any `fetch(` or `post(` call — all mutation gestures must go
  through the `API.*` helpers or `API.addDepends`. No raw `/api/...`
  strings inside `PipelineEdit`.

Manual smoke (documented in task log after implementation):
- Start `server.py`, load `http://localhost:<port>/?adv=ADV-007`, open
  Pipeline tab.
- Drag one task onto another → edge appears → no error toast → edge
  survives next poll.
- Drag to self → no POST fires (verified in DevTools network tab).
- Right-click a design node → menu shows "Approve design" → click →
  toast "Design approved".

## Risks

- **Cytoscape does not ship drag-to-create-edge as a baseline API.**
  Mitigation: hand-roll with `taphold` + `mousemove` + `mouseup` on the
  container. Alternative (heavier): add `cytoscape-edgehandles` plugin
  via CDN — avoid unless the hand-rolled version proves flaky in review.
- **Poll-tick racing with optimistic edge.** If the poll tick completes
  between optimistic-add and server reply, the next `applyDiff` may
  remove the optimistic edge before reply resolves. Mitigation: tag
  optimistic edges with `data.optimistic: true`; `applyDiff` (in T019)
  skips edges with that flag when reconciling. Document this assumption
  in the T019 merge note; if T019 does not honour the flag, T020
  temporarily pauses polling during an in-flight gesture (`cy.data('paused', true)` + T019 reads it).
- **Context menu z-index vs cytoscape canvas**. Cytoscape renders to
  `<canvas>` which is `position: static`; giving the menu `position:
  absolute; z-index: 1000` is sufficient. No new stacking-context
  parents needed.
- **Tests check patterns, not runtime.** Static pattern tests cannot
  fully prove "exactly one POST per gesture". Accept this limitation; a
  manual smoke is documented instead.
