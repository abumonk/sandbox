# Document Layouts (Design / Plan / Research / Review) — Design

## Overview

The `Documents` tab hosts four document types under one filter bar. Each
type gets a bespoke layout rather than a generic markdown dump.

## Target Files

- `.agent/adventure-console/index.html` (new `renderDocuments`,
  `renderDesignDoc`, `renderPlanDoc`, `renderResearchDoc`, `renderReviewDoc`)

## Approach

### Filter bar

Chips: **All** · **Designs** · **Plans** · **Research** · **Reviews**. Chip
click updates the currently visible list but does **not** change tabs.
Current chip is highlighted.

### Unified list

One sorted list, each row:

```
[type-badge]  filename-without-ext            [status-badge if any]
              one-line summary (custom per type, see below)
```

Type-badge color differentiates Design (blue) / Plan (purple) / Research
(grey) / Review (green/red).

### Per-type detail layouts

**Design document**

- One-line header parsed from the `## Overview` section (first sentence,
  truncated): "**What this design decides:** ..."
- Rendered prose from `## Approach` and following sections.
- Separate, small boxes for: Target Conditions (list) and Target Files
  (list). Both come from the design's `## Target Conditions` / `## Target
  Files` sections.
- Approve button stays (calls existing `/design/approve` endpoint) but is
  compact and off to the right, not inline with each file-list row.

**Plan document**

- Parse `## Tasks` subsections (`### {Task Title}`) as cards.
- Parse wave / phase markers if present (e.g. `## Wave 1`, `## Phase A`)
  and render those as visual groups — a horizontal band with the wave title
  and the task cards underneath.
- Fallback: plain rendered markdown if neither phases nor waves are present.

**Research document**

- Just rendered prose with a small "source/doc-type: research" tag at the
  top. No special decomposition required beyond markdown rendering.

**Review document**

- Top strip: task ID + PASSED/FAILED badge + timestamp.
- Summary table (`## Summary`) rendered as a compact key-value strip.
- Issues section rendered as a list with severity colors.
- "Show full review ▸" disclosure for the long-form body.

### Layout switching

All four renderers share a signature `render(doc, text) -> DOMNode`. The
dispatcher inspects the doc's type (derived from which array it came from:
`designs`/`plans`/`research`/`reviews`).

## Dependencies

- `design-information-architecture`
- `design-simplification-audit`: verdicts determine which fields are
  visible by default.

## Target Conditions

- TC-013: Documents tab shows a chip filter bar with "All", "Designs",
  "Plans", "Research", "Reviews".
- TC-014: Clicking a filter chip narrows the list client-side without a
  network request.
- TC-015: Opening a design document shows a "What this design decides:"
  one-line header parsed from the design's Overview section.
- TC-016: Opening a plan with explicit `## Wave N` or `## Phase X` headings
  renders each wave/phase as a distinct visual group.
- TC-017: Opening a review document shows a PASSED/FAILED badge and a
  summary strip before any long-form prose.
