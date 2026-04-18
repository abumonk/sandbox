# ADV009-T009 — Implement Documents tab with filter chips and per-type layouts — Design

## Approach

Adds a new `renderDocuments(pane, a)` entry point to
`.agent/adventure-console/index.html` that consumes the
`/api/adventures/{id}/documents` endpoint (shipped by ADV009-T004, per
`design-backend-endpoints`). It renders a chip-bar filter + unified list,
and four per-type detail renderers (design / plan / research / review)
following the layouts described in `design-document-layouts`. All
rendering uses the visual primitives introduced in ADV009-T005
(`.card`, `.pill`, `.chip-bar`, `.chip`, `.disclosure`, `.stack`).

The Documents tab is wired into the four-tab bar rebuilt in ADV009-T006
(`switchTab` already routes `documents` → this function). No backend
changes; no new external assets.

## Target Files

- `.agent/adventure-console/index.html` — add `renderDocuments`,
  `renderDocumentRow`, `renderDesignDoc`, `renderPlanDoc`,
  `renderResearchDoc`, `renderReviewDoc`, `parseDesignOneLiner`,
  `parsePlanWaves`, `parseReviewSummary`; wire into the tab dispatcher.
  (Legacy `renderFileBrowser` usage for designs/plans/research and the
  legacy `renderReviews` call stay in place until ADV009-T011 retires
  them.)

## Implementation Steps

1. **API helper** — in the `API` object near line 250, add:
   ```js
   documents: (id) => get('/api/adventures/' + id + '/documents')
   ```
   Keep existing `approveDes` helper; `renderDesignDoc` will reuse it.

2. **Tab dispatcher** — in `renderTab()` (around line 437), add a branch:
   ```js
   if (tab === 'documents') return this.renderDocuments(pane, a);
   ```
   Place the branch before the legacy `designs`/`plans`/`research`/`reviews`
   branches so the new code wins when T006 has re-shaped the tab bar.

3. **State** — extend the `Console` object with two fields:
   - `documentsFilter: 'all'` (current chip)
   - `documentsCache: null` (the last fetched doc array, scoped to
     `currentAdv.id`; invalidated in `reopen()` and `openAdv()`)

4. **`renderDocuments(pane, a)`** —
   - Fetch via `API.documents(a.id)` into `documentsCache` if empty.
   - Show a loading state (`<div class="empty">Loading documents…</div>`)
     until the fetch resolves; show an error card on failure.
   - Build a `.chip-bar` with five chips: `All`, `Designs`, `Plans`,
     `Research`, `Reviews`. Each chip is a `<button class="chip">`; the
     active chip gets `.chip.active`. Click handler updates
     `this.documentsFilter` and calls a pure `renderDocList(list, docs)`
     refresher — no network round-trip (satisfies TC-014). Keyboard
     activation: `role="tab"`, `tabindex="0"`, listen for `Enter`/`Space`.
   - Add `data-testid="documents-chips"` and per-chip
     `data-testid="chip-{kind}"` for the test strategy hooks.
   - Below the chip bar, create a unified list container
     (`<div class="stack" data-testid="documents-list">`) and a detail
     pane (`<div class="doc-view">`) in a two-column split: 280-320px
     list on the left, detail on the right. Reuse the existing `.split`
     flex layout.

5. **`renderDocumentRow(doc, onOpen)`** — one row per document:
   ```
   <div class="card doc-row" data-type="{type}">
     <span class="pill type-{type}">{Design|Plan|Research|Review}</span>
     <span class="doc-title">{filename-without-ext}</span>
     <span class="pill status-{status}">{PASSED|FAILED}</span>  // reviews only
     <span class="doc-sub muted">{one_liner | task_count/waves | title}</span>
   </div>
   ```
   Pill color variants: `type-design` (blue), `type-plan` (purple),
   `type-research` (grey), `type-review` (green/red per status). These
   colors reuse the badge classes already present; add four new CSS
   rules inside the existing `<style>` block (piggy-backing on tokens
   introduced in T005).

6. **`renderDocList(listEl, docs)`** — filters the documents array by
   `this.documentsFilter` (client-side) and re-paints the list. Preserves
   the currently open doc if it still passes the filter; otherwise shows
   an "empty" placeholder in the detail pane. Sort order: reviews by
   task_id descending, else alphabetical by filename.

7. **`renderDesignDoc(doc, text, viewEl)`** — (TC-015)
   - Parse `## Overview` section text; take the first sentence (split on
     `/(?<=[.!?])\s/`), trim, truncate to 160 chars. If empty, fall back
     to "This design documents " + filename.
   - Header card: `<div class="card design-header">` with a bold label
     "What this design decides:" followed by the parsed one-liner.
   - Parse `## Target Conditions` and `## Target Files` sections; each
     becomes its own small `.card` in a right-hand rail (CSS grid
     `1fr 220px`). Each item is a `<li>` — TCs get a muted monospace
     style, target files become `<code>` spans.
   - Main column: `marked.parse(body)` where `body` is the design text
     with the Overview / Target Conditions / Target Files sections
     stripped out (split on `^## ` headings). Use a helper
     `splitSections(md)` returning `{[heading]: body}` to avoid
     hand-rolling per call site.
   - Approve button: only when the adventure manifest exposes the design
     as unapproved (best effort: `doc.approved !== true`). Rendered as
     a compact `<button>` inside the header card, right-aligned. On
     success, call `this.reopen()` and flip the button to `✓ Approved`.

8. **`renderPlanDoc(doc, text, viewEl)`** — (TC-016)
   - Split on `^## ` to find top-level sections. Any section whose
     heading matches `/^(Wave|Phase)\s+\S+/i` becomes a wave group.
   - Within `## Tasks` (or within a Wave/Phase section), parse `^### `
     subsections as task cards. Each card renders:
     `<div class="card"><strong>{title}</strong><div class="muted">{first line after heading}</div></div>`.
   - Wave grouping: wrap the wave's task cards in
     `<section class="wave-group"><h3 class="wave-title">Wave 1</h3>…</section>`.
     Add a `.wave-group` CSS rule (background tint + left border) inside
     the `<style>` block.
   - Fallback: if no waves/phases and no `## Tasks`, just
     `marked.parse(text)`.

9. **`renderResearchDoc(doc, text, viewEl)`** —
   - Prepend a small tag strip:
     `<div class="pill type-research">research</div>` plus
     the document's `## Summary` or first paragraph as a one-liner.
   - Main body: `marked.parse(text)` — no decomposition.

10. **`renderReviewDoc(doc, text, viewEl)`** — (TC-017)
    - Top strip: `<div class="card review-strip">` with
      `<strong>{doc.task_id}</strong>` +
      `<span class="pill status-{PASSED|FAILED}">{status}</span>` +
      muted timestamp parsed from the `---` frontmatter (`completed_at`
      or `updated`).
    - Summary strip: parse the `## Summary` table (pipe table); render
      as a compact horizontal key-value strip
      (`<div class="kv-strip"><span>key:</span><code>value</code>…</div>`).
    - Issues list: parse the `## Issues` section's bullet list; each
      issue gets a `<li class="issue sev-{severity}">` with color-coded
      left border (green/warn/err reusing existing tokens).
    - `<details class="disclosure"><summary>Show full review ▸</summary>
      {marked.parse(entireText)}</details>` — full text kept behind the
      disclosure per TC-017.

11. **Dispatcher `renderDoc(doc)`** — inside `renderDocuments`, when a
    row is clicked:
    ```js
    const fileRel = `.agent/adventures/${a.id}/${doc.type}s/${doc.file}`;
    // research lives in /research (no trailing s)
    const dir = doc.type === 'research' ? 'research' : doc.type + 's';
    const text = await API.file(`.agent/adventures/${a.id}/${dir}/${doc.file}`);
    const renderers = {
      design: this.renderDesignDoc, plan: this.renderPlanDoc,
      research: this.renderResearchDoc, review: this.renderReviewDoc,
    };
    viewEl.innerHTML = '';
    renderers[doc.type].call(this, doc, text, viewEl);
    ```

12. **Helpers** — at the bottom of the file, next to
    `parseKnowledgeSuggestions`, add:
    - `splitSections(md)` → `{ heading: body }` keyed by `## ` heading.
    - `parseSummaryTable(md)` → object from a pipe-table with `Key|Value`.
    - `parseIssuesList(md)` → `[{severity, text}]` from `- [sev] text`
      bullets (sev ∈ `blocker|major|minor|note`, default `note`).

13. **CSS additions** (inside the existing `<style>` block; no new file):
    - `.chip-bar`, `.chip`, `.chip.active`, `.chip:focus-visible` (reuse
      tokens from T005).
    - `.pill.type-design`, `.pill.type-plan`, `.pill.type-research`,
      `.pill.type-review` color variants.
    - `.doc-row`, `.doc-title`, `.doc-sub` (flex row inside `.card`).
    - `.wave-group`, `.wave-title`, `.kv-strip`, `.issue.sev-*`,
      `.review-strip`, `.design-header`, `.doc-view`.
    - Keep the right-rail grid on the design view:
      `.design-layout { display:grid; grid-template-columns: 1fr 220px; gap: 16px; }`.

14. **Wire-up sanity** — ensure `renderTab('documents')` works even if
    `a.documents` is absent in cached responses by falling through to
    `API.documents(a.id)` at render time (not at `openAdv` time); this
    keeps the tab decoupled from the manifest shape.

## Testing Strategy

Manual verification against TC-013..TC-017 (from `design-test-strategy`):
- Open an adventure with at least one design, plan with `## Wave 1`, a
  research doc, and a PASSED review.
- **TC-013**: inspect DOM for `data-testid="documents-chips"` containing
  exactly five `.chip` children labelled All/Designs/Plans/Research/Reviews.
- **TC-014**: click a chip and observe the list narrowing without a
  network request (Network tab shows no new `/documents` GET).
- **TC-015**: open a design → detail pane's first card contains the
  literal text "What this design decides:".
- **TC-016**: open a plan with two `## Wave N` headings → DOM contains
  two `.wave-group` elements.
- **TC-017**: open a review → top of detail contains a `.pill.status-*`
  element and a `.kv-strip`.

Smoke: open ADV-009 in the console and walk each chip; every design in
the repo should render without throwing, confirmed via browser console.

## Risks

- **Backend dependency**: this task depends on ADV009-T004 having shipped
  `/api/adventures/{id}/documents`. If T004 is not yet landed, the
  coder should stub the endpoint by deriving the list client-side from
  `a.designs + a.plans + a.research + a.reviews` and log a TODO; the
  chip+layout logic is independent of the fetch shape.
- **Markdown section parsing drift**: designs that omit `## Overview`
  or use a different heading (`## Summary`, `## Intent`) will hit the
  fallback one-liner. Keep the fallback non-destructive.
- **Review frontmatter variance**: reviews from older adventures may
  lack `status:` — render "UNKNOWN" pill instead of throwing.
- **Pipe-table parsing**: the review summary table may include
  multi-line cells; scope `parseSummaryTable` to the first two-column
  table found and fall back to raw markdown if the shape is unexpected.
- **Cache invalidation**: remember to clear `documentsCache` in
  `reopen()` and when a different adventure is selected, otherwise a
  just-added design won't appear after an approval.
