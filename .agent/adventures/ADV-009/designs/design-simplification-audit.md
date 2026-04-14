# Simplification Audit — Design

## Overview

Before any rewrite, catalog every element of the current console (9 tabs,
per-tab controls, sidebar rows, overview table, log tail, raw paths, etc.)
and classify each as **Keep**, **Hide-behind-toggle**, or **Remove**. This
audit is the single source of truth that drives every frontend task —
nothing gets a new custom layout until it has an audit verdict.

## Target Files

- `.agent/adventures/ADV-009/research/audit.md` (new) — the catalog table
- Read-only inputs: `.agent/adventure-console/index.html`,
  `.agent/adventure-console/server.py`

## Approach

1. Enumerate every visible UI element in `index.html` currently rendered for
   a typical adventure (Overview/Designs/Plans/Tasks/Permissions/Reviews/
   Knowledge/Research/Log).
2. For each element, record:
   - **Element**: short name (e.g. "Log tail pane", "Command column in TC
     table", "Raw path under file-entry").
   - **Current tab**: where it lives today.
   - **Verdict**: `keep` · `hide-behind-toggle` · `remove`.
   - **Reason**: why (e.g. "5-second glance content" vs "debug only").
   - **New home**: which v2 tab/component will host it (Overview, Tasks,
     Documents, Decisions, Show-details drawer, or deleted).
3. Group the verdicts into a summary (X kept, Y hidden, Z removed) so
   subsequent tasks consume a single catalog rather than re-deriving verdicts.

## Dependencies

None. This is the first design and gates every implementation design.

## Target Conditions

- TC-001: `research/audit.md` exists and enumerates ≥ 30 distinct UI
  elements from the current console.
- TC-002: every row in the audit has a non-empty `verdict` cell from the
  set `{keep, hide-behind-toggle, remove}`.
- TC-003: every element mentioned in index.html's `renderTab` dispatch has a
  corresponding audit row (no element is un-classified).
