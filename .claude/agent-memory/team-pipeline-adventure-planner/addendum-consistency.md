---
name: Addendum consistency with task AC text
description: When an adventure manifest is extended with an addendum that changes scope (added tabs, new TCs, new tasks), retroactively update task AC text in existing task files so reviewers don't flag cosmetic drift.
type: feedback
---

**Rule**: When an addendum changes scope that affects already-written task files (new tab count, altered CTA routing, additional fields), update the affected task AC bullets at the same time the addendum is merged.

**Why**: In ADV-009, the manifest addendum added a 5th Pipeline tab after T006's AC had been written saying "exactly four tabs". Tests were updated to match the new 5-tab state, but T006's AC text was not. The reviewer correctly passed the task (structural intent met) but filed a low-severity flag; this costs review attention that should be spent on substantive issues.

**How to apply**: At addendum-merge time, grep `tasks/` for language affected by the scope change (tab counts, endpoint names, tab order) and update AC bullets in place. Consider a short "Addendum reconciliation" pass as a first-class planner step after any addendum.
