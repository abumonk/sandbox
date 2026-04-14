# Entities — ADV-009

Entities introduced or shaped by this adventure. None require persisted
schema changes; the substrate on disk is unchanged.

## Entities

### AdventureSummary (server-derived)
- `tc_total: int`
- `tc_passed: int`
- `tc_failed: int`
- `tc_pending: int`
- `tasks_by_status: map<string,int>` — keys: `pending`, `in_progress`,
  `passed`, `failed`, `done`
- `next_action: NextAction`
- Relations: part of the `/api/adventures/{id}` response payload.

### NextAction
- `kind: enum` — one of `approve_permissions`, `open_plan`,
  `resolve_blocker`, `promote_concept`, `read_report`, `open_tasks`, `none`
- `label: string` — CTA button text
- `state_hint: string` — source adventure state that produced this action

### DocumentEntry (server-derived)
- `type: enum` — `design` | `plan` | `research` | `review`
- `file: string` — basename
- `title: string` — parsed heading or frontmatter title
- `one_liner: string?` — design-only; first sentence of `## Overview`
- `task_count: int?` — plan-only
- `waves: int?` — plan-only; count of `## Wave ` / `## Phase ` headings
- `status: string?` — review-only; PASSED / FAILED
- `task_id: string?` — review-only
- Relations: emitted by `/api/adventures/{id}/documents`.

### AuditEntry (planning artifact)
- `element: string` — short name
- `current_tab: string` — where it is today
- `verdict: enum` — `keep` | `hide-behind-toggle` | `remove`
- `reason: string`
- `new_home: string` — v2 target surface
- Relations: rows in `research/audit.md`.

### TabView (frontend)
- `id: enum` — `overview` | `tasks` | `documents` | `decisions`
- `label: string`
- `render: function(adventure) -> DOMNode`
- Relations: registered in the tab dispatcher in `index.html`.

### FilterChipState (frontend)
- `active: enum` — `all` | `designs` | `plans` | `research` | `reviews`
- Relations: client-side state inside the Documents tab renderer.
