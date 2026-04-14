# Backend Endpoint Additions — Design

## Overview

Add a small number of backend conveniences to `server.py` so the frontend
doesn't have to re-parse files the server has already parsed. Minimal
surface: one new endpoint, one extension of an existing response.

## Target Files

- `.agent/adventure-console/server.py`

## Approach

### 1. Extend `/api/adventures/{id}` response

Augment the existing `get_adventure` return dict with a `summary` block
computed server-side:

```json
"summary": {
  "tc_total": 17,
  "tc_passed": 8,
  "tc_failed": 2,
  "tc_pending": 7,
  "tasks_by_status": {"pending": 4, "in_progress": 2, "passed": 5, "done": 1},
  "next_action": {
    "kind": "approve_permissions" | "open_plan" | "resolve_blocker" | "promote_concept" | "none",
    "label": "Approve Permissions",
    "state_hint": "review"
  }
}
```

`next_action` is computed from `state` + permissions status + TC progress
using a small deterministic helper `compute_next_action(meta, permissions,
tcs, tasks)`. No new fields are persisted to disk — purely derived.

### 2. New endpoint: `GET /api/adventures/{id}/documents`

Returns a unified list of `{designs, plans, research, reviews}` with
lightweight metadata:

```json
[
  {"type": "design", "file": "design-foo.md", "title": "Foo — Design", "one_liner": "What this design decides: ..."},
  {"type": "plan",   "file": "plan-bar.md",   "title": "Bar plan", "task_count": 7, "waves": 2},
  {"type": "review", "file": "ADV009-T005-review.md", "status": "PASSED", "task_id": "ADV009-T005"},
  {"type": "research","file":"audit.md", "title":"Simplification audit"}
]
```

Metadata parsing rules:
- For designs: `one_liner` = first sentence of `## Overview` (trimmed, ≤120
  chars).
- For plans: `task_count` = count of `^### ` headings under `## Tasks`;
  `waves` = count of `^## Wave ` or `^## Phase ` headings.
- For reviews: reuse existing frontmatter parse.
- For research: just the title (first `# ` heading) if present.

### 3. Keep existing endpoints unchanged

No edits to `/api/file`, `/state`, `/permissions/approve`, `/design/approve`,
`/knowledge/apply`, `/log`.

## Dependencies

- `design-information-architecture`
- `design-overview-tab` (consumes `summary`)
- `design-document-layouts` (consumes `documents`)

## Target Conditions

- TC-026: `GET /api/adventures/{id}` includes a `summary` object with
  `tc_total`, `tc_passed`, `tc_failed`, `tc_pending`, `tasks_by_status`,
  `next_action`.
- TC-027: `GET /api/adventures/{id}/documents` returns a unified list with
  one entry per design / plan / research / review file and a correct
  `type` field for each.
- TC-028: For a plan file containing `## Wave 1` and `## Wave 2`, the
  documents endpoint reports `"waves": 2`.
- TC-029: `next_action.kind` is `"approve_permissions"` when the adventure
  state is `review` and permissions.md status is unapproved.
- TC-030: `server.py` remains stdlib-only (no new third-party imports).
