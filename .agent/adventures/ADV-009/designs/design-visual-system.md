# Visual System (CSS / Typography) — Design

## Overview

A small set of shared visual primitives that every v2 component uses:
pills, progress bars, cards, disclosures, chip filters. Defined once;
reused across Overview, Tasks, Documents, Decisions.

## Target Files

- `.agent/adventure-console/index.html` (CSS inside the existing `<style>`
  block — no external stylesheet)

## Approach

### Design tokens (add to existing `:root`)

```
--card-bg:       #1a222d;
--card-border:   #2a343f;
--pill-bg:       #243040;
--chip-bg:       #1d2731;
--chip-active:   #2d6ca8;
--progress-bg:   #243040;
--progress-fill: #5ab0ff;
```

Existing state/status color variables stay as-is.

### New components

**`.card`** — rounded-corner container, 12px padding, 1px border, medium
shadow. Replaces most `.split` / ad-hoc boxes in v2 views.

**`.pill`** — inline, rounded, compact. Variants: `.pill.state-*`,
`.pill.status-*` reuse existing color classes.

**`.progress`** — `<div class="progress"><span style="width:N%"></span></div>`.
Colors: fill = `--progress-fill`, track = `--progress-bg`. Height 8px.

**`.chip-bar` / `.chip`** — horizontal row of filter chips. Active chip
uses `--chip-active`. Keyboard-navigable (tab + enter/space).

**`<details class="disclosure">`** — standard HTML disclosure; styled with
a chevron icon that rotates on open. Used everywhere "Show details" / "Show
full" appears.

**`.stack`** — vertical flex with 16px gap for stacking cards in Overview
and Decisions.

### Typography scale

- Page title: 20px / 600 (unchanged)
- Card title: 15px / 600 (new)
- Card body: 13px / 1.45 (unchanged base)
- Muted meta: 11px / 400 (unchanged)

### Removals

- `.log-tail` black terminal style is kept but only used inside disclosures.
- `.split` (sidebar file browser) is retired for v2 views — Documents uses
  the unified list pattern instead. The class may stay in the stylesheet
  if any legacy view needs it temporarily.

## Dependencies

- All other frontend designs consume these primitives.

## Target Conditions

- TC-031: `.card`, `.pill`, `.progress`, `.chip-bar`, `.chip`, `.stack`,
  and `.disclosure` CSS rules exist in `index.html`.
- TC-032: No external CSS or font file is added (no new `<link>` or
  `<style src>` tag); the CDN-loaded `marked.js` remains the only external
  dependency.
- TC-033: Every primary card component in v2 uses the `.card` class (no
  ad-hoc inline styles for card chrome).
