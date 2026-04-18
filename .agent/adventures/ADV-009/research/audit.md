# Simplification Audit — Adventure Console v1

**Snapshot date:** 2026-04-16
**Source file:** `.agent/adventure-console/index.html`
**Methodology:** Enumerate every visible element produced by each `renderTab` dispatch branch. Verdicts driven by the 5-second-glance requirement from the manifest concept: anything that cannot be read meaningfully in 5 seconds of opening defaults to `hide-behind-toggle` or `remove`.

---

## Summary

**36 kept * 17 hidden * 13 removed**

(66 rows total)

---

## Catalog

| Element | Current tab | Verdict | Reason | New home (v2) |
|---------|-------------|---------|--------|---------------|
| **SIDEBAR** | | | | |
| "Adventure Console" logo / branding text | sidebar | keep | Anchors app identity; one-glance orientation | Sidebar |
| "Claudovka · team-pipeline" subtitle | sidebar | remove | Team plumbing visible to developers only; not useful to a reader | (removed) |
| Refresh button (↻ Refresh) | sidebar | keep | Users need to reload the list after agent runs; a single control | Sidebar |
| Adventure row — ADV id monospace chip | sidebar | keep | ID is the key pointer used everywhere else | Sidebar |
| Adventure row — state badge | sidebar | keep | State is the first 5-second fact the user needs | Sidebar |
| Adventure row — title | sidebar | keep | Readable name; essential | Sidebar |
| **HEADER** | | | | |
| ADV id monospace label in header | overview | hide-behind-toggle | Redundant once sidebar row is selected; technical noise when already open | Show-details drawer (Overview) |
| Adventure title h1 | overview | keep | Primary label; essential | Overview |
| State pill badge | overview | keep | Core status signal; 5-second-glance | Overview |
| Created timestamp (adv-meta line) | overview | hide-behind-toggle | Rarely relevant to day-to-day reading; clutters meta line | Show-details drawer (Overview) |
| Updated timestamp (adv-meta line) | overview | hide-behind-toggle | Same as created; debug-only for most readers | Show-details drawer (Overview) |
| Tasks count (adv-meta line) | overview | remove | Superseded by Tasks tab count chip and progress bar | (removed) |
| State-transition button row ("Transition →" label + per-state buttons) | overview | remove | Moving to Decisions tab; inline placement conflicts with header clarity | Decisions |
| **TABS BAR** | | | | |
| Designs tab with count suffix | tabs | remove | Folded into Documents tab in v2 | (removed) |
| Plans tab with count suffix | tabs | remove | Folded into Documents tab in v2 | (removed) |
| Tasks tab with count suffix | tabs | keep | Core tab; count suffix kept as quick signal | Tasks |
| Overview tab | tabs | keep | Core tab | Overview |
| Permissions tab | tabs | remove | Folded into Decisions tab in v2 | (removed) |
| Reviews tab with count suffix | tabs | remove | Folded into Documents tab in v2 | (removed) |
| Knowledge tab | tabs | remove | Folded into Decisions tab in v2 | (removed) |
| Research tab with count suffix | tabs | remove | Folded into Documents tab in v2 | (removed) |
| Log tab | tabs | remove | Folded into Show-details drawer; not a primary navigation destination | Show-details drawer (Overview) |
| **OVERVIEW PANE** | | | | |
| "Concept" section heading | overview | keep | Introduces the concept box; helpful label | Overview |
| Concept text box (full raw markdown, scrollable) | overview | hide-behind-toggle | Full markdown blob is too dense for 5-second glance; first 3 lines or a synopsis should show by default | Overview (Show more disclosure) |
| Target Conditions section heading with count | overview | keep | Count gives quick progress signal | Overview |
| TC table — ID column | overview | hide-behind-toggle | ID is a cross-reference code useful in context but noisy at a glance | Overview (Show-details drawer) |
| TC table — Description column | overview | keep | Core content; the actual condition to verify | Overview |
| TC table — Task(s) column | overview | hide-behind-toggle | Useful traceability but secondary to status at a glance | Show-details drawer (Overview) |
| TC table — Proof command column | overview | hide-behind-toggle | Command-line string; debug-only for most readers | Show-details drawer (Overview) |
| TC table — Status badge column | overview | keep | Pass/fail signal; essential for 5-second health check | Overview |
| "Adventure Report" shortcut button (Open report-adventure synthesis) | overview | keep | Useful primary action when a report exists; single button | Overview |
| **TASKS PANE** | | | | |
| Task table — ID column | tasks | keep | Task ID is referenced across the adventure; necessary | Tasks |
| Task table — Title column | tasks | keep | Human-readable description; essential | Tasks |
| Task table — Stage badge | tasks | keep | Stage is a key workflow status | Tasks |
| Task table — Status badge | tasks | keep | Status distinct from stage; essential | Tasks |
| Task table — Assignee column | tasks | hide-behind-toggle | Agent name is technical metadata; not needed for a quick health check | Show-details drawer (Tasks) |
| Task table — Iter (iteration count) column | tasks | hide-behind-toggle | Debug-only; not a primary signal | Show-details drawer (Tasks) |
| Task table — TCs column | tasks | keep | TC linkage is essential for understanding task scope | Tasks |
| Task detail drawer (raw markdown file-view rendered inline) | tasks | hide-behind-toggle | Raw markdown blob replaces structured layout; should render structured components | Tasks (structured detail panel) |
| **DESIGNS PANE** | | | | |
| Designs file list (left panel of split) | designs | keep | Navigation into design docs is valuable | Documents (chip-filtered list) |
| File entry — filename as display label | designs | keep | Human-readable filename; needed for navigation | Documents |
| File entry — Approve button (inline per design row) | designs | keep | Primary action for design workflow | Decisions |
| Designs file view (right panel — rendered markdown) | designs | keep | Rendered doc content is the goal | Documents |
| **PLANS PANE** | | | | |
| Plans file list (left panel of split) | plans | keep | Navigation into plan docs | Documents (chip-filtered list) |
| Plans file view (right panel — rendered markdown) | plans | keep | Rendered doc content | Documents |
| **RESEARCH PANE** | | | | |
| Research file list (left panel of split) | research | keep | Navigation into research docs | Documents (chip-filtered list) |
| Research file view (right panel — rendered markdown) | research | keep | Rendered doc content | Documents |
| **PERMISSIONS PANE** | | | | |
| Permissions status badge | permissions | keep | Approved/pending signal is a 5-second fact | Decisions |
| Permissions "approved by" metadata line | permissions | hide-behind-toggle | Attribution is secondary metadata; useful for audit, not glance | Show-details drawer (Decisions) |
| Permissions Approve button | permissions | keep | Primary action; essential when permissions are pending | Decisions |
| Permissions inline file-view (full markdown) | permissions | hide-behind-toggle | Full permissions doc is too long for default view; render request summary only | Decisions (Show-details disclosure) |
| **REVIEWS PANE** | | | | |
| Adventure-report starred row ("★ adventure-report.md") | reviews | keep | Primary review artifact; the star treatment correctly highlights it | Documents |
| Per-task review row — task_id label | reviews | keep | Task identifier needed for navigation | Documents |
| Per-task review row — status badge | reviews | keep | PASSED/FAILED signal is a core health check | Documents |
| Review file view (right panel — rendered markdown) | reviews | keep | Rendered review content | Documents |
| **KNOWLEDGE PANE** | | | | |
| "Knowledge Extraction — N suggestion(s)" heading | knowledge | remove | Moved to Decisions tab; tab itself removed | Decisions |
| Knowledge instruction meta line | knowledge | remove | Verbose instruction text; collapse into Decisions card label | Decisions |
| Knowledge suggestion items (checkbox + title + meta + content) | knowledge | keep | Primary decision content; checkboxes are the action surface | Decisions |
| Knowledge "Record Selection" button | knowledge | keep | Primary action for knowledge curation | Decisions |
| Knowledge "Select All" button | knowledge | hide-behind-toggle | Bulk convenience; secondary action | Decisions (secondary buttons) |
| Knowledge "None" button | knowledge | hide-behind-toggle | Bulk convenience; secondary action | Decisions (secondary buttons) |
| Knowledge suggestion — kb-meta line (type → target file) | knowledge | hide-behind-toggle | Target file is technical metadata; useful but not glance-critical | Show-details drawer (Decisions) |
| **LOG PANE** | | | | |
| "Adventure Log (tail)" heading | log | remove | Log tab removed; heading goes with it | (removed) |
| Log tail `<pre>` block (raw timestamped lines) | log | hide-behind-toggle | Debug-only; violates 5s-glance when shown by default; accessible via disclosure | Show-details drawer (Overview) |
| **GLOBAL CHROME** | | | | |
| Toast notification banner | global | keep | System feedback is essential for action confirmation | Global (all tabs) |
| Raw file paths under file entries (e.g. `.agent/adventures/ADV-NNN/designs/foo.md`) | global | hide-behind-toggle | File-system paths are developer noise; not meaningful to a reader | Show-details drawer |

---

## Open Questions

1. **State-transition buttons (header → Decisions):** Moving them from the header button row to the Decisions tab is the verdict here, but this may feel surprising to users who expect to act from the header. Downstream frontend tasks (T006, T010) should confirm placement: keep a *primary action button* in the header (single most important next action) while full transition menu lives in Decisions.

2. **TC table ID column:** Classified as `hide-behind-toggle` because it is cross-reference noise at a glance. However, the v2 "Show-details" drawer design may prefer to always show the ID alongside the description as it is short. T007 (Overview tab implementation) should resolve this.

3. **Adventure-report shortcut button in Overview:** Rendered only when `a.adventure_report` exists. Verdict is `keep` but its v2 rendering should gracefully degrade when no report exists (currently hidden; v2 might show a "Run /adventure-review" prompt instead).

4. **Knowledge "Select All" / "None" buttons:** Classified `hide-behind-toggle` but they could be primary UX if the list is long. Decisions tab design (T010) should decide whether these appear as secondary buttons by default or only on demand.

5. **Designs Approve button moving to Decisions vs. staying in Documents:** The Approve button is currently inline in the Designs file list. Moving it to Decisions is cleaner architecturally, but it breaks the spatial association between the doc and its action. T009 (Documents tab) and T010 (Decisions tab) should agree on whether Approve lives in the file entry row (Documents) or as a card in Decisions.
