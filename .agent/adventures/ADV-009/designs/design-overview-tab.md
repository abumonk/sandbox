# Overview Tab — Design

## Overview

The first thing a reader sees when they open an adventure. Must answer
within 5 seconds: *what is this, where is it, what's next*.

## Target Files

- `.agent/adventure-console/index.html` (new `renderOverview`)

## Approach

Three stacked sections, in this order:

1. **Concept synopsis** — the first paragraph of `## Concept`, rendered as
   prose. Full concept behind a "Show more ▸" disclosure. No code-block
   frontmatter or raw paths.

2. **Target-conditions progress** — replace the current 9-column table with
   a horizontal progress bar:

   ```
   TCs  ████████░░░░░░░░  8 / 17 passed  |  2 failed  |  7 pending
   ```

   Hover tooltip shows per-status counts. Below: up to 5 TC rows whose
   `status != "passed"` (blockers first), each one line:
   `TC-012  [failed]  short description...`. A "Show all TCs ▸" disclosure
   reveals the full table (the same one v1 renders — kept behind-toggle).

3. **Next-action card** — a single card naming the one thing the reader
   should do. Content depends on state:

   | State | Card title | Action |
   |-------|-----------|--------|
   | `concept` | "Concept awaiting promotion." | Button: "Start planning" |
   | `planning` | "Planning in progress." | Link: "Open Decisions" |
   | `review` | "Awaiting Checkpoint 2 approval." | Button: "Approve permissions" / "Open plan" |
   | `active` | "N tasks in progress." | Link: "Open Tasks" |
   | `blocked` | "Blocked by {reason}." | Link: "Open Decisions" |
   | `completed` | "Completed on {date}." | Link: "Read report" |

`state_hint` is computed client-side from the adventure bundle already
returned by `/api/adventures/{id}` — no new endpoint strictly required,
but see `design-backend-endpoints.md` for optional server-computed hints.

## Dependencies

- `design-information-architecture`
- `design-backend-endpoints` (optional)

## Target Conditions

- TC-018: Overview renders a visible progress bar for target conditions
  that is not a table.
- TC-019: Overview lists non-passing TCs (up to 5) before the Show-all
  disclosure.
- TC-020: Overview renders a single "next-action" card whose content
  matches the adventure's `state`.
- TC-021: The full raw concept markdown is not visible until a user clicks
  "Show more".
