# Graph Edit Affordances — Design

## Overview

Specify every user-driven mutation the Pipeline tab can trigger, the
exact HTTP route + payload, and the idempotency/rollback behaviour.
Everything routes through the existing `server.py` API surface; we add
exactly **one** new endpoint
(`POST /api/adventures/{id}/tasks/{task_id}/depends_on`).

## Target Files

- `.agent/adventure-console/index.html` — graph event handlers, context
  menu DOM, optimistic update logic
- `.agent/adventure-console/server.py` — new `depends_on` POST handler

## Approach

### Affordance matrix

| Gesture | Target node | Route | Payload | Existing? |
|--------|-------------|-------|---------|-----------|
| Click state-transition edge | adventure | `POST /api/adventures/{id}/state` | `{"to": "<state>"}` | existing |
| Drag from Task A → Task B | task | `POST /api/adventures/{id}/tasks/{task_a}/depends_on` | `{"depends_on": "<task_b>"}` | **new** |
| Right-click → Open document | document | — (link to `/files/...`) | — | existing |
| Right-click → Approve design | design doc | `POST /api/adventures/{id}/designs/{name}/approve` | `{}` | existing |
| Right-click → Approve permissions | decision/permissions | `POST /api/adventures/{id}/permissions/approve` | `{}` | existing |
| Right-click → Apply knowledge suggestion | decision/knowledge | `POST /knowledge/apply` | existing payload | existing |
| Right-click task → Open detail | task | client-side tab switch to Tasks + open drawer | — | internal |

### New endpoint: `POST /api/adventures/{id}/tasks/{task_id}/depends_on`

Request:
```json
{ "depends_on": "ADV009-T002" }
```
Behaviour:
1. Loads `tasks/{task_id}.md`, reads frontmatter.
2. Appends `{depends_on_new}` to the existing `depends_on:` list (dedup).
3. Rewrites the file preserving all other frontmatter and body.
4. Returns `{ "ok": true, "depends_on": [...merged list...] }`.

Rejections (HTTP 400):
- `task_id` does not exist.
- `depends_on` value equals `task_id` (self-cycle).
- `depends_on` references a task not in this adventure.
- Addition would create a cycle (detected by walking existing
  depends_on edges — O(n) BFS on the IR).

All logic lives inline in `server.py`; uses only stdlib.

### Optimistic UI + rollback

1. Drag gesture finishes → client adds the edge visually immediately.
2. POST is fired; on success: no change (edge stays).
3. On 4xx: edge is removed; a toast `.toast` element is shown with the
   server's error message.
4. On 5xx / network error: same as 4xx but message reads "Server
   unreachable — retry?".

No silent failures.

### Context menu

A tiny DOM-only menu (no third-party library) attached at right-click
coordinates. Items resolve to the routes in the affordance matrix.
Styled with the existing `.card` + `.stack` primitives.

### Safety rails

- No deletion affordances in v1 (no "remove depends_on", no "cancel
  adventure"). All additive. Rationale: destructive edits need a
  confirmation model that's out of scope for this wave.
- No bulk operations (drag-select, multi-edit). Single-target only.
- Double-submit guard: button disables + spinner for 500 ms after any
  mutation POST.

## Dependencies

- design-pipeline-graph-view (the canvas on which these affordances live)
- design-ark-pipeline-spec (cycle-detection walks the IR)

## Affected existing tasks

- T006 (tab bar): unchanged. The graph-edit task (T020) owns any tab-bar
  diff its handlers need.
- Existing backend tasks T003/T004: **unchanged**. The new `depends_on`
  endpoint is a fresh handler block inserted alongside, not a rewrite.

## Target Conditions

- TC-052 — `POST /api/adventures/{id}/tasks/{task_id}/depends_on` returns
  200 with updated list on valid input.
- TC-053 — Same endpoint returns 400 on self-cycle attempts.
- TC-054 — Same endpoint returns 400 on cycle-creating inputs.
- TC-055 — Drag-to-connect emits exactly one POST per gesture (no
  double-fire on `mouseup`).
- TC-056 — On 4xx response the client rolls the visual edge back (no
  stale edge remains).
- TC-057 — Context menu items route to existing endpoints only (no new
  routes besides `depends_on`).
