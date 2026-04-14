# Information Architecture — Design

## Overview

Define the v2 tab structure, what lives in each tab, and how the header +
sidebar reshape around a reader-first hierarchy. This design is the
contract the frontend tasks implement against.

## Target Files

- `.agent/adventure-console/index.html` (rewrite sections: sidebar, header,
  tab bar, tab dispatch)

## Approach

### Final tab shape

Four tabs, in this left-to-right order:

| Tab | What it answers | Default first-paint |
|-----|-----------------|---------------------|
| **Overview** | "What's this adventure about and where is it?" | concept synopsis + TC progress bar + next-action card |
| **Tasks** | "What work exists, what's blocking it?" | grouped-by-status task cards |
| **Documents** | "Show me the writing — designs, plans, research, reviews." | type-filter chips + unified doc list |
| **Decisions** | "What does a human need to act on right now?" | pending approvals + state-transition controls + knowledge suggestions awaiting curation |

### Header (per adventure)

```
ADV-009 | Adventure Console UI v2 ...      [state pill]   [progress: 3/12 TCs]   [primary CTA]
```

- `[primary CTA]` is context-sensitive: if `state=review` and permissions
  unapproved → "Approve Permissions"; if `state=planning` → "Open Decisions";
  if `state=active` and blocked → "Review Blocker"; etc.
- Under the line, `updated` and a compact breadcrumb (no raw paths).

### Sidebar

Each adventure row stays compact: state badge + ID + title. Subtitle is a
one-liner derived from the concept (first sentence truncated to 80 chars).
No task count, no file count — those are one click away in the Overview.

### Removed / demoted from v1

- `Designs`, `Plans`, `Research`, `Reviews`, `Knowledge` as top-level tabs →
  all collapse into `Documents` (Knowledge moves to Decisions).
- `Log` tab → removed from default nav; log tail lives behind a "Show
  details" disclosure inside Overview (and inside Decisions' state widget).
- `Permissions` tab → folds into Decisions as one card.

## Dependencies

- `design-simplification-audit`: the audit verdicts confirm what survives.

## Target Conditions

- TC-004: v2 `index.html` renders exactly four top-level tabs for any
  adventure: Overview, Tasks, Documents, Decisions.
- TC-005: The `Log`, `Knowledge`, `Permissions`, `Designs`, `Plans`,
  `Research`, `Reviews` tabs do not appear in the top-level tab bar.
- TC-006: The header area contains, in order: adventure ID, title, state
  pill, TC progress indicator, primary action button.
- TC-007: Sidebar rows show state badge + ID + title + one-line subtitle,
  and no raw paths / file counts.
