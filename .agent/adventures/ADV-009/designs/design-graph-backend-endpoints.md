# Graph Backend Endpoints — Design

## Overview

Two backend responsibilities for the Pipeline tab, both inside
`server.py`, both stdlib-only:

1. `GET /api/adventures/{id}/graph` — serves the node/edge payload the
   frontend renders.
2. `POST /api/adventures/{id}/tasks/{task_id}/depends_on` — the single new
   write endpoint (detailed in design-graph-edit-affordances).

This design is a sibling to the existing `design-backend-endpoints.md`
(which already covers `summary` and `documents`). We deliberately did
**not** fold these into that design because they (a) depend on the Ark
IR extractor — a new dependency — and (b) are scoped to the Pipeline
addendum, not the original four-tab plan.

## Target Files

- `.agent/adventure-console/server.py`

## Approach

### `GET /api/adventures/{id}/graph`

Handler:
1. Imports the IR extractor:
   `from adventure_pipeline.tools.ir import extract_ir` (path add at module top).
2. Calls `extract_ir(adventure_id)` → `AdventurePipelineIR`.
3. Transforms IR into the node/edge payload defined in
   design-pipeline-graph-view §"Graph data contract".
4. Composes `explanations` dict by rendering short strings from the
   IR: e.g. `"{task.id} depends on {dep.id} because {dep.title}"`. All
   text is deterministic — no LLM calls.
5. Returns `application/json`.

Caching: none in v1. IR extraction on ~15 tasks is sub-10ms; the poll
cadence is 5 s. Revisit only if profiling shows otherwise.

Error paths:
- Adventure id unknown → 404.
- IR extractor raises → 500 with `{"error": "...", "stage": "ir_extract"}`.

### `POST /api/adventures/{id}/tasks/{task_id}/depends_on`

Covered fully in design-graph-edit-affordances §"New endpoint". Shares a
`_rewrite_task_frontmatter` helper with the handlers already in
`server.py`.

### Shared helper: `_cycle_free(ir, task_id, new_dep)`

Walks `ir.tasks` edges from `new_dep` and fails if `task_id` is reachable.
Inserted as a module-level helper, reused by both this endpoint and any
future dependency-editing surface.

### Stdlib-only guarantee

- `json`, `http.server`, `urllib`, `re`, `pathlib` only.
- `adventure_pipeline.tools.ir` itself is stdlib-only (see design-ark-pipeline-spec).
- No new `import` of third-party packages in `server.py`.

## Dependencies

- design-ark-pipeline-spec (the IR extractor is a hard dependency).
- design-pipeline-graph-view (consumes the `/graph` JSON).
- design-graph-edit-affordances (consumes the `depends_on` POST).

## Affected existing tasks

- T003 / T004 (existing backend tasks): **unchanged**. The new endpoints
  are additive — they land in their own new task (T018).

## Target Conditions

- TC-058 — `server.py` imports `adventure_pipeline.tools.ir` and uses it
  from the `/graph` handler.
- TC-059 — `/graph` JSON payload shape passes a schema smoke test
  (has `nodes[]`, `edges[]`, `explanations{}`; node objects have `data.id`
  and `data.kind`).
- TC-060 — `server.py` remains stdlib-only after the new endpoints land
  (no new third-party imports).
- TC-061 — `_cycle_free` helper rejects direct self-cycles and transitive
  cycles (unit tested).
