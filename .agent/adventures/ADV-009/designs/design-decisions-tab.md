# Decisions Tab — Design

## Overview

A single action surface merging v1's Permissions + Knowledge tabs and the
header's state-transition buttons. The Decisions tab answers: "what does a
human need to approve, transition, or curate, right now?"

## Target Files

- `.agent/adventure-console/index.html` (new `renderDecisions`)

## Approach

Three cards, rendered only when relevant (empty cards are hidden):

### Card 1 — State transitions

Shows the current state as a pill plus the valid next-state buttons, using
the existing `STATE_TRANSITIONS` map. Includes a "log tail (last 20 lines)"
disclosure for audit context when the user is about to transition.

### Card 2 — Pending permissions

If `permissions.md` exists and `status != approved`:
- Summary strip: N shell requests · N file requests · N MCP tools.
- Numbers parsed from the `## Requests` tables client-side.
- Full permissions markdown behind a "Show full request ▸" disclosure.
- Single prominent "Approve Permissions" button.

If `status == approved`: a small neutral line "Permissions approved on
{date}" with a disclosure for the full document.

### Card 3 — Knowledge suggestions

Only renders when `adventure_report.md` exists. Reuses the existing
`parseKnowledgeSuggestions` parser and checkbox form, plus "Record
Selection" button. Removed cruft: no raw section-6 markdown, no "Run
`/adventure-review {id}`" hint text — those move behind "Show details".

### Design approvals (per-document)

The per-design **Approve** button moves from the v1 file-list entry to the
design's detail layout (`design-document-layouts.md`). It is not duplicated
in Decisions because a design approval is per-file and naturally lives with
the design content.

## Dependencies

- `design-information-architecture`
- `design-document-layouts` (design-approval button lives there, not here)

## Target Conditions

- TC-022: Decisions tab renders three cards (state transitions, pending
  permissions, knowledge suggestions); cards with no actionable content
  are not rendered.
- TC-023: Decisions' permissions card shows counts of shell/file/MCP
  requests parsed client-side; the full permissions markdown is hidden by
  default.
- TC-024: Clicking a state-transition button from the Decisions card calls
  `POST /api/adventures/{id}/state` with the correct `new_state`.
- TC-025: Knowledge suggestions checklist writes the same
  `reviews/knowledge-selection.json` payload as v1 (regression guard).
