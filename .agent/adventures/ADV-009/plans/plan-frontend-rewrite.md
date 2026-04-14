# Plan: Frontend Rewrite (Wave B)

## Designs Covered
- design-information-architecture
- design-visual-system
- design-task-card-layout
- design-document-layouts
- design-overview-tab
- design-decisions-tab

## Tasks

### Install visual system (CSS tokens + primitives)
- **ID**: ADV009-T005
- **Description**: Add the new CSS tokens and component classes from
  design-visual-system (`.card`, `.pill`, `.progress`, `.chip-bar`,
  `.chip`, `.stack`, `.disclosure`) to `index.html`'s existing `<style>`
  block. No external CSS files. Keep all legacy class rules in place
  (they will be removed in T010 after the rewrite is wired up).
- **Files**: `.agent/adventure-console/index.html`
- **Acceptance Criteria**:
  - All seven new classes exist.
  - No new `<link rel="stylesheet">` or external font imports.
  - Existing v1 styles still resolve (no visual breakage yet).
- **Target Conditions**: TC-031, TC-032
- **Depends On**: [ADV009-T002]
- **Evaluation**:
  - Access requirements: Read, Edit
  - Skill set: CSS
  - Estimated duration: 12 min
  - Estimated tokens: 18000

### Rebuild tab bar and header to v2 shape
- **ID**: ADV009-T006
- **Description**: Replace the 9-tab bar with the four tabs Overview /
  Tasks / Documents / Decisions. Rebuild the header (ID, title, state
  pill, TC progress indicator, primary-action button from
  `summary.next_action`). Rebuild the sidebar row to show state-badge +
  ID + title + one-line subtitle. Route unrecognized legacy tab keys to
  Overview. Add `data-testid` hooks per test-strategy.
- **Files**: `.agent/adventure-console/index.html`
- **Acceptance Criteria**:
  - Exactly four top-level tabs render.
  - The Log / Knowledge / Permissions / Designs / Plans / Research /
    Reviews tabs are gone from the nav.
  - Header contains, in order: ID, title, state pill, progress bar,
    primary CTA.
  - Sidebar rows do not show task counts or paths.
- **Target Conditions**: TC-004, TC-005, TC-006, TC-007
- **Depends On**: [ADV009-T002, ADV009-T005, ADV009-T003]
- **Evaluation**:
  - Access requirements: Read, Edit
  - Skill set: Vanilla JS DOM construction, CSS
  - Estimated duration: 25 min
  - Estimated tokens: 70000

### Implement Overview tab
- **ID**: ADV009-T007
- **Description**: Render concept synopsis (first paragraph + Show more),
  TC progress bar with non-passing rows preview, and the next-action
  card driven by `summary.next_action`. Use `.card`, `.progress`, and
  `.disclosure` primitives. Add `data-testid` hooks.
- **Files**: `.agent/adventure-console/index.html`
- **Acceptance Criteria**:
  - Progress bar renders (not a 9-column table).
  - Up to 5 non-passing TCs appear above the Show-all disclosure.
  - Next-action card exists and differs by state as specified.
  - Raw concept markdown is hidden behind a "Show more" disclosure.
- **Target Conditions**: TC-018, TC-019, TC-020, TC-021, TC-033
- **Depends On**: [ADV009-T006]
- **Evaluation**:
  - Access requirements: Read, Edit
  - Skill set: Vanilla JS, DOM
  - Estimated duration: 22 min
  - Estimated tokens: 55000

### Implement Tasks tab with custom task cards
- **ID**: ADV009-T008
- **Description**: Group tasks by `status` into buckets (hide empty ones).
  Render each task as the new card (status pill + ID + title + depends-on
  + TC list). Build the expanded detail panel with status strip,
  depends-on chain, TC checklist, description, acceptance criteria, and
  "Show details" disclosure for frontmatter/log/raw. Parse Description
  and Acceptance Criteria sections client-side from the task file.
- **Files**: `.agent/adventure-console/index.html`
- **Acceptance Criteria**:
  - Tasks group by status bucket; empty buckets hidden.
  - Task card hides file path, assignee, iterations by default.
  - Detail panel renders Description and Acceptance Criteria as
    structured components (not a markdown dump).
  - Show-details disclosure contains frontmatter + log + raw source.
  - TC checklist reflects each TC's current status.
- **Target Conditions**: TC-008, TC-009, TC-010, TC-011, TC-012
- **Depends On**: [ADV009-T006]
- **Evaluation**:
  - Access requirements: Read, Edit
  - Skill set: Vanilla JS, regex section parsing
  - Estimated duration: 28 min
  - Estimated tokens: 85000

### Implement Documents tab with filter chips and per-type layouts
- **ID**: ADV009-T009
- **Description**: Build `renderDocuments` consuming
  `/api/adventures/{id}/documents`. Render chip bar + unified list.
  Implement per-type detail renderers: `renderDesignDoc` (one-line
  header from Overview + prose + TC/target-file side boxes + Approve
  button), `renderPlanDoc` (wave-grouped task cards), `renderResearchDoc`
  (prose + tag), `renderReviewDoc` (status strip + summary key-value +
  issues list + Show-full disclosure).
- **Files**: `.agent/adventure-console/index.html`
- **Acceptance Criteria**:
  - Chip bar renders with All/Designs/Plans/Research/Reviews chips.
  - Chip click filters client-side (no network).
  - Design opened → shows "What this design decides:" header.
  - Plan with `## Wave N` headings → renders waves as visual groups.
  - Review → shows PASSED/FAILED badge and summary strip.
- **Target Conditions**: TC-013, TC-014, TC-015, TC-016, TC-017
- **Depends On**: [ADV009-T004, ADV009-T006]
- **Evaluation**:
  - Access requirements: Read, Edit
  - Skill set: Vanilla JS, DOM, regex
  - Estimated duration: 28 min
  - Estimated tokens: 90000

### Implement Decisions tab (merges Permissions + Knowledge + state transitions)
- **ID**: ADV009-T010
- **Description**: Build `renderDecisions` with three conditionally
  rendered cards: state transitions, pending permissions (with parsed
  request counts), and knowledge suggestions (reusing
  `parseKnowledgeSuggestions` and the `/knowledge/apply` POST). Hide
  cards that have no actionable content. Move the per-design Approve
  button into `renderDesignDoc` (T009), not here.
- **Files**: `.agent/adventure-console/index.html`
- **Acceptance Criteria**:
  - Three cards render when applicable; empty cards hidden.
  - Permissions card shows counts of shell/file/MCP requests parsed
    client-side; full doc behind disclosure.
  - State-transition buttons post to `/api/adventures/{id}/state`.
  - Knowledge card writes same JSON payload as v1 (regression parity).
- **Target Conditions**: TC-022, TC-023, TC-024, TC-025
- **Depends On**: [ADV009-T006]
- **Evaluation**:
  - Access requirements: Read, Edit
  - Skill set: Vanilla JS, DOM
  - Estimated duration: 22 min
  - Estimated tokens: 60000

### Retire legacy renderers and dead CSS
- **ID**: ADV009-T011
- **Description**: Remove v1-only code paths that the four new tabs
  replaced: `renderFileBrowser` for designs/plans/research, legacy
  `renderPermissions`, legacy `renderReviews`, `renderKnowledge` (moved
  to Decisions), `renderLog` (moved into disclosures), and any now-dead
  CSS (legacy `.split` if unused). Keep `parseKnowledgeSuggestions`
  (still used). Preserve the switchTab fallback for unknown keys.
- **Files**: `.agent/adventure-console/index.html`
- **Acceptance Criteria**:
  - No references remain to the removed renderers.
  - `grep -c "renderFileBrowser\|renderKnowledge\|renderLog" index.html`
    is 0 (or only comments).
  - Page still loads and all four tabs work.
- **Target Conditions**: TC-005
- **Depends On**: [ADV009-T007, ADV009-T008, ADV009-T009, ADV009-T010]
- **Evaluation**:
  - Access requirements: Read, Edit, Bash (grep)
  - Skill set: JS refactoring
  - Estimated duration: 15 min
  - Estimated tokens: 28000
