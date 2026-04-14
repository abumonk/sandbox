# Task Card Layout — Design

## Overview

Replace the generic "render task markdown blob" with a bespoke task layout
that is scannable in under two seconds. Applies both to task rows in the
Tasks tab and to the expanded detail panel.

## Target Files

- `.agent/adventure-console/index.html` (new `renderTaskCard` and
  `renderTaskDetail` components, new CSS classes)

## Approach

### Card (list view)

```
+----------------------------------------------------------+
|  [status pill]   ADV009-T005   (stage)                   |
|  Title of the task                                        |
|  depends_on: T001 · T003   |   TCs: TC-012, TC-013       |
+----------------------------------------------------------+
```

- Status pill colors match v1 (`passed`=green, `failed`=red, `pending`/
  `in_progress`=amber, `done`=green).
- Clicking the card expands the detail panel inline.
- Raw `file:` path, `assignee`, `iterations` are **not** shown in the card.

### Detail panel (when expanded)

Sections in this order, each rendered as a dedicated component (not
markdown):

1. **Status strip** — pill + stage + assignee badge + iteration count.
2. **Depends-on chain** — small inline nodes `T001 → T003 → (this)` with
   status dot coloring each predecessor.
3. **Target-conditions checklist** — for each TC linked to the task: `[✓]`
   / `[ ]` + TC ID + description.  Checkbox reflects TC status from the
   manifest (`passed`/`pending`/`failed`).
4. **Description** — prose from the task's `## Description` heading (not the
   entire markdown file, not the frontmatter).
5. **Acceptance Criteria** — rendered as a bullet list from
   `## Acceptance Criteria`.
6. **Show details ▸** disclosure — contains raw frontmatter, file path,
   `## Log` tail, full markdown source.

Parse strategy: client-side, from `API.file(t.file)`. Use the same minimal
frontmatter splitter as the server and a section-header regex
(`^## Description`, `^## Acceptance Criteria`, `^## Log`).

### Grouping (list view)

Tasks are grouped by `status` into columns/buckets: `pending`,
`in_progress`, `passed`, `failed`, `done`. Empty buckets are hidden. This
replaces the current flat sortable table.

## Dependencies

- `design-information-architecture`: task tab is one of the four.
- `design-backend-task-summary`: relies on `target_conditions` already being
  in the `/api/adventures/{id}` payload (today's server returns them).

## Target Conditions

- TC-008: Tasks tab groups tasks into status buckets; empty buckets are not
  rendered.
- TC-009: A task card shows status pill, ID, title, depends-on list, and
  TC list — and does not show raw file path or assignee.
- TC-010: Expanded task detail renders the `## Description` and
  `## Acceptance Criteria` sections as structured components, not as a raw
  markdown blob.
- TC-011: Task detail hides frontmatter, `## Log`, and raw file path by
  default; all of those become visible after clicking "Show details".
- TC-012: Each TC row in a task's checklist shows a checkbox reflecting the
  TC's `status` field from the manifest.
