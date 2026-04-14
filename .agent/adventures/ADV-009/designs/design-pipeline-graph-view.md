# Pipeline Tab — Interactive Graph View Design

## Overview

Add a new tab to the v2 console — provisional name **Pipeline** — rendering
the running adventure as a live, interactive node-edge graph. Supersedes
the original four-tab proposal. Updated tab bar:

**Overview · Tasks · Documents · Pipeline · Decisions**

The graph is *spec-driven*: nodes and edges come from the Ark IR extractor
(design-ark-pipeline-spec), not from bespoke frontend parsing. This keeps
tooltips and explanations anchored to the spec definitions.

## Target Files

- `.agent/adventure-console/index.html` — new tab dispatch branch, new
  `<script>` `<link>` tag for cytoscape CDN, `renderPipeline()` function
- `.agent/adventure-console/server.py` — new `GET /api/adventures/{id}/graph`
  endpoint (lives in design-graph-backend-endpoints.md)

Existing `index.html` sections edited: tab bar (already being rebuilt in
T006) and tab dispatcher switch. **We do not edit T006's task file** — the
graph tab rendering is a separate new task that depends on T006. T006's
tab list must be extended from 4 to 5 tabs as part of graph-tab wiring
(graph-tab task inserts a new `<button>` + case in dispatch rather than
asking T006 to include it ahead of time).

## Approach

### Library choice: cytoscape.js (CDN)

Selected because:
- Native CDN build exists (`https://cdn.jsdelivr.net/npm/cytoscape@3.28.1/dist/cytoscape.min.js`),
  ~300 KB minified, single script tag — honours the no-build-step
  constraint.
- First-class editable-graph support (drag-to-create-edge plugins, but the
  baseline API already emits the events we need).
- Renderer is HTML5 canvas → fine for ~500 nodes (comfortably more than
  any adventure will have).
- Stable API, actively maintained.

Alternatives considered:
- **vis-network**: simpler but less flexible styling and weaker event API
  for right-click context menus.
- **D3**: most flexible but implementing layout + hit-testing + context
  menus from scratch multiplies code for no meaningful gain here.

**Decision: cytoscape.js via CDN.** If cytoscape's CDN ever becomes
unreachable we can self-host the file under `.agent/adventure-console/vendor/`
without changing the integration code — we still never run a bundler.

### Graph data contract (from backend `/graph` endpoint)

```json
{
  "nodes": [
    {"data": {"id": "adv", "kind": "adventure", "label": "ADV-007 ...",
              "status": "active"}},
    {"data": {"id": "phase:waveA", "kind": "phase", "label": "Wave A",
              "parent": "adv"}},
    {"data": {"id": "task:ADV007-T003", "kind": "task",
              "label": "T003 — Build map bar", "status": "in_progress",
              "parent": "phase:waveA"}},
    {"data": {"id": "doc:design-ir", "kind": "document",
              "label": "design-ir", "docKind": "design", "parent": "adv"}},
    {"data": {"id": "tc:TC-012", "kind": "tc", "label": "TC-012",
              "status": "pending", "parent": "adv"}},
    {"data": {"id": "decision:permissions",
              "kind": "decision", "label": "Approve permissions",
              "status": "pending", "parent": "adv"}}
  ],
  "edges": [
    {"data": {"id": "e1", "source": "task:ADV007-T004",
              "target": "task:ADV007-T003", "kind": "depends_on"}},
    {"data": {"id": "e2", "source": "task:ADV007-T003",
              "target": "tc:TC-012", "kind": "satisfies"}},
    {"data": {"id": "e3", "source": "adv", "target": "state:active",
              "kind": "state_transition"}}
  ],
  "explanations": {
    "task:ADV007-T003": "Depends on T002 — T002's audit verdicts gate all frontend tasks."
  }
}
```

### Node status → colour mapping

| Kind | `pending` | `in_progress`/`running` | `passed`/`done` | `failed`/`blocked` |
|------|-----------|--------------------------|------------------|--------------------|
| task | `--muted` | `--accent` (pulsing) | `--ok` | `--danger` |
| tc | `--muted` | — | `--ok` | `--danger` |
| decision | `--warn` (needs action) | — | `--ok` | — |
| document | `--muted` | — | `--ink` (plain) | — |

Colours pulled from the existing CSS custom-property palette
(`design-visual-system.md`) — no new tokens required.

### Rendering + polling

```js
function renderPipeline(adv) {
  mountCytoscape('#pipeline-canvas');
  pollGraph(adv.id, 5000);           // default; read ?poll= from URL
}

async function pollGraph(advId, ms) {
  const g = await fetch(`/api/adventures/${advId}/graph`).then(r => r.json());
  applyDiff(cy, g);                  // idempotent update, preserves layout
  setTimeout(() => pollGraph(advId, ms), ms);
}
```

- Poll interval configurable via `?poll=N` query param (default 5000 ms).
- `applyDiff` preserves node positions and selection state so polling is
  unobtrusive. No websockets — preserves the stdlib-only server constraint.

### Interaction model

See **design-graph-edit-affordances.md** for the full contract. Summary:

- Hover/click → tooltip from `explanations[id]` (spec-driven).
- Click state-transition edge → POST `/api/adventures/{id}/state`.
- Drag task A → task B → POST new
  `/api/adventures/{id}/tasks/{task_id}/depends_on`.
- Right-click → context menu (open doc, approve design, etc.) — routes
  exclusively through existing or newly-added endpoints.

### Legend + layout

Small static legend (node-kind colour swatches) fixed in the top-right of
the canvas. Layout: `dagre` via `cytoscape-dagre` plugin CDN (depends_on
flows left-to-right, phases as compound parents). If dagre adds a second
CDN dependency the author considers too heavy, fall back to cytoscape's
built-in `breadthfirst` layout — still acceptable.

## Dependencies

- **Hard**: design-ark-pipeline-spec (the IR is the source of truth for
  nodes/edges/explanations).
- **Soft**: design-information-architecture (tab-bar contract — the
  graph tab adds a fifth button).

## Affected existing tasks (observe only — do not edit)

- T006 (Rebuild tab bar): will need a 5th tab slot when the graph-tab task
  lands. The graph-tab task (T019) takes responsibility for adding the
  `<button>` and the dispatcher case; T006 stays as written and the merge
  will fast-forward because the dispatcher is additive.
- T008/T009/T010 (Tasks/Documents/Decisions): unaffected.

Capture this in the plan; the lead decides whether to amend T006 or let
the graph-tab task carry the fifth-tab edit.

## Target Conditions

- TC-046 — `GET /api/adventures/{id}/graph` returns a JSON shape matching
  the contract above (has `nodes[]`, `edges[]`, `explanations{}`).
- TC-047 — index.html loads cytoscape from a `<script src="https://...cytoscape...">`
  CDN tag; no local copy, no bundler artifact.
- TC-048 — Pipeline tab appears as the 4th top-level tab, between
  Documents and Decisions.
- TC-049 — Graph status-colour mapping matches the table above (verified
  by inspecting cytoscape stylesheet rules).
- TC-050 — Polling uses `setTimeout` cadence (default 5000 ms) — no
  WebSocket / EventSource code paths in `server.py` or `index.html`.
- TC-051 — Tooltip text for any node comes from the backend
  `explanations` map (no hardcoded strings in `renderPipeline`).
