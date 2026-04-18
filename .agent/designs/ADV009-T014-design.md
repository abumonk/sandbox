# Update README for v2 - Design

## Approach

Documentation-only refresh of `.agent/adventure-console/README.md` to align it
with the v2 adventure-console UI (four tabs) and the extended backend API
(`summary` block + `/documents` endpoint).

No code changes. No new files. No restructuring of the README's top-level
heading sequence — only bodies of specific sections are rewritten so any
external links pointing at anchors like `#what-it-does` or `#safety` keep
working.

Source-of-truth documents:
- `.agent/adventures/ADV-009/designs/design-information-architecture.md` — tab names, order, sidebar row shape.
- `.agent/adventures/ADV-009/designs/design-backend-endpoints.md` — `summary` block fields and `/documents` response shape.
- `.agent/adventures/ADV-009/designs/design-decisions-tab.md` — location of knowledge-suggestion curation in v2.

## Target Files

- `.agent/adventure-console/README.md` — rewrite the "What it does" tab table, update the "How the backend works" endpoints table, refresh the "Knowledge extraction" section. Leave "Run", "Safety", "Files" bodies intact.

## Implementation Steps

1. **Baseline read.** Open the current README to pin exact section boundaries. Preserve every `## ` heading verbatim.
2. **"What it does" rewrite.**
   - Replace the current nine-row "Main pane — tabs per adventure" table with this four-row table:
     | Tab | Purpose |
     |-----|---------|
     | Overview | Concept synopsis, target-condition progress bar, next-action card |
     | Tasks | Grouped-by-status task cards; click to open the full task file |
     | Documents | Unified browser for designs / plans / research / reviews with type-filter chips |
     | Decisions | Pending approvals, state-transition controls, permissions status, knowledge-suggestion curation |
   - Rewrite the Sidebar paragraph: "Each row shows state badge + ID + title + one-line subtitle (first sentence of the concept, truncated to ~80 chars). No task counts, no file counts — those live one click away in Overview."
   - Rewrite the "State transitions" paragraph so it notes the buttons now live inside the **Decisions** tab; the API contract (`POST /api/adventures/{id}/state`) is unchanged.
3. **Endpoints table update.**
   - Add exactly one row to the table under "How the backend works":
     `| GET | /api/adventures/{id}/documents | — | Unified list of designs/plans/research/reviews with lightweight metadata |`
   - Keep all existing rows. Preserve column order.
4. **`summary` block note.**
   - Below the endpoints table, add a short paragraph (2–3 sentences):
     > `GET /api/adventures/{id}` now also returns a derived `summary` block with `tc_total`, `tc_passed`, `tc_failed`, `tc_pending`, `tasks_by_status`, and a `next_action` hint (`kind`, `label`, `state_hint`). The values are computed on every request; nothing new is persisted to disk.
5. **"Knowledge extraction" section refresh.**
   - Change the opening sentence from "The **Knowledge** tab parses..." to "The **Decisions** tab parses...".
   - Keep the rest of the section (`reviews/knowledge-selection.json` payload, extractor-agent disclaimer) verbatim.
6. **Scrub v1 tab residue.**
   - Search the README for `Designs`, `Plans`, `Permissions`, `Reviews`, `Knowledge`, `Research`, `Log` and verify none appear as top-level tab names in the "What it does" section.
   - It is OK for those words to appear as *document categories* (inside the Documents tab description) or as *section names in the Decisions tab* (permissions, knowledge-suggestion curation). The forbidden pattern is: listing them as rows of a tab table.
7. **Leave alone.** Do not edit:
   - "Run" (the command, the host/port defaults, the override example).
   - "Safety" bullets.
   - "Files" tree listing.
   - The intro paragraph ("A lightweight web UI ...").

## Testing Strategy

TC-038 is manual. Verification steps:

1. **Four-tab presence.** `grep -E "(Overview|Tasks|Documents|Decisions)" README.md` returns at least one hit per tab name, and the "What it does" table has exactly four rows.
2. **No v1 tab rows.** Visual inspection: the "What it does" section does not contain rows for Designs / Plans / Permissions / Reviews / Knowledge / Research / Log as separate tabs.
3. **Endpoints table coverage.** `grep "/api/adventures/{id}/documents" README.md` returns 1+ hit inside the endpoints table.
4. **`summary` block documented.** `grep -i "summary" README.md` returns a hit in the prose near the endpoints table with the field list.
5. **Run command intact.** `grep "python .agent/adventure-console/server.py" README.md` still matches (and it is still inside the "Run" section).
6. **Diff discipline.** `git diff .agent/adventure-console/README.md` touches only the "What it does", "How the backend works" endpoints-table region, and "Knowledge extraction" sections (plus any trivial whitespace).

## Risks

- **Drift from the UI implementation (ADV009-T011).** If T011 ships different tab labels or ordering, the README will be wrong. Mitigation: treat `design-information-architecture` as the source of truth for this doc-refresh; if T011 diverged from the design, that is a T011 bug, not a T014 bug.
- **Anchor breakage.** Any project doc linking to `#designs` or `#plans` as README anchors will 404. Mitigation: keep top-level heading text unchanged; only the Tab table and sub-sentences are rewritten. No `## ` headings are renamed or removed.
- **Over-editing.** Temptation to refactor the Safety or Files sections at the same time. Mitigation: scope is explicitly doc-refresh-for-v2; unrelated edits are out of scope.
- **Knowledge-extraction wording.** The Decisions tab hosts the knowledge-selection UI, but the extractor agent (`knowledge-extractor`) has not changed. Ensure only the *location* of the checkbox UI is updated, not the description of the agent workflow.
