# ADV009-T012 — Implement automated tests for ADV-009 (server + ui-layout + ui-smoke)

## Approach

Implement the three test files declared in `design-test-strategy.md` using
only Python stdlib `unittest`. Tier 1 (`test_server.py`) exercises the
HTTP server and helper functions in-process. Tier 2 (`test_ui_layout.py`)
parses `.agent/adventure-console/index.html` statically with
`html.parser.HTMLParser`. Tier 3 (`test_ui_smoke.py`) gates on a runtime
`import playwright` and skips the entire module cleanly when absent.

The full discover command must exit 0:

```
python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"
```

Test class / method names are pre-bound by the manifest's `Proof Command`
column (TC-004..TC-033 etc.), so this design is mostly a faithful map
from manifest commands to file structure.

## Target Files

- `.agent/adventures/ADV-009/tests/__init__.py` — empty marker so
  `unittest discover` treats the dir as a package (needed because the
  `Proof Command` column references dotted paths like
  `.agent.adventures.ADV-009.tests.test_server.TestSummary`).
- `.agent/adventures/ADV-009/tests/_fixtures.py` — synthetic adventure
  tree builder + ServerThread context manager (shared helpers).
- `.agent/adventures/ADV-009/tests/test_server.py` — Tier 1 backend
  tests.
- `.agent/adventures/ADV-009/tests/test_ui_layout.py` — Tier 2 static
  HTML/CSS tests.
- `.agent/adventures/ADV-009/tests/test_ui_smoke.py` — Tier 3 Playwright
  smoke tests (skipped if Playwright not importable).

## Implementation Steps

### 1. Package + fixtures
1. Write empty `__init__.py` and ensure all sibling `.agent/...`
   directories along the dotted path also have `__init__.py` IF the
   manifest's dotted-path proof commands are intended to be runnable
   directly. NOTE: manifest commands like
   `python -m unittest .agent.adventures.ADV-009.tests.test_server.TestSummary`
   are illustrative; the binding acceptance criterion (TC-036) only
   requires the discover command to exit 0. The coder should add only
   the `tests/__init__.py` marker — not bless `.agent/`,
   `.agent/adventures/`, etc. as Python packages (would risk import
   side-effects across the repo).
2. Implement `_fixtures.py` with:
   - `make_synthetic_adventure(tmpdir, adv_id="ADV-TEST", *, state="review", permissions_approved=False)` —
     creates a tmp `<tmpdir>/.agent/adventures/<adv_id>/` tree with:
     - `manifest.md` with frontmatter `id`, `title`, `state`, `tasks: [<adv>-T001]`
     - `permissions.md` with status line
     - `tasks/<adv>-T001.md` (status pending)
     - `designs/design-foo.md` with `## Overview` paragraph
     - `plans/plan-bar.md` containing `## Wave 1` and `## Wave 2` headings
       and 3 `### ` task headings under `## Tasks`
     - `research/audit.md` (`# Title`)
     - `reviews/<adv>-T001-review.md` with frontmatter `status: PASSED`
     - `adventure.log` (single created line)
   - `ServerThread(adventures_root)` — starts `ThreadingHTTPServer` on
     port 0 with the `Handler` class from `server.py`, monkey-patches
     `server.ADVENTURES_DIR` and `server.AGENT_DIR` to point at the
     tmp tree, exposes `self.url` and `self.stop()`. Patch via
     `unittest.mock.patch.object` inside `__enter__`.
   - `http_get(url, path)` and `http_post(url, path, payload)` thin
     stdlib wrappers (`urllib.request`).

### 2. `test_server.py` (Tier 1)

Class layout maps directly to manifest `Proof Command` strings:

| Class.method | TC | Asserts |
|---|---|---|
| `TestSummary.test_block_fields` | TC-026 | `summary` dict has keys `tc_total`, `tc_passed`, `tc_failed`, `tc_pending`, `tasks_by_status`, `next_action`. |
| `TestNextAction.test_review` | TC-029 | synthetic adventure with `state=review`, unapproved permissions → `summary.next_action.kind == "approve_permissions"`. |
| `TestStdlibOnly.test_no_third_party` | TC-030 | parse `server.py` with `ast`, walk all `Import` / `ImportFrom`, assert every top-level module is in `sys.stdlib_module_names`. |
| `TestDocumentsEndpoint.test_types` | TC-027 | response array contains exactly one entry per fixture file with correct `type` ∈ {design, plan, research, review}. |
| `TestDocumentsEndpoint.test_waves` | TC-028 | the plan fixture entry reports `waves == 2`. |
| `TestDocumentsEndpoint.test_design_one_liner` | TC-027 (extra) | design entry has non-empty `one_liner` ≤ 120 chars. |
| `TestKnowledgePayload.test_roundtrip` | TC-025 | `POST .../knowledge/apply` writes the same JSON shape as the v1 baseline (compare against a small inline reference dict). |
| `TestStrategyDoc.test_tc_mapping` | TC-034 | parse `tests/test-strategy.md`, assert every `proof_method: autotest` TC ID from `manifest.md` appears in the strategy doc. |
| `TestStrategyDoc.test_framework` | TC-035 | grep all three test files for `import unittest`; assert no other test framework imports. |

Module-level guard: if `tests/test-strategy.md` does not yet exist
(ADV009-T001 not done), `TestStrategyDoc` should `unittest.skip(...)`
the entire class so the discover run still exits 0 — this preserves
TC-036 even if T001 lags behind.

### 3. `test_ui_layout.py` (Tier 2)

Use `html.parser.HTMLParser` subclass `TagSoup` that records
`(tag, attrs_dict, text_until_next_tag)` tuples. Add helpers:
`find_by_testid(soup, tid)`, `count_by_class(soup, cls)`,
`has_link_to(soup, href_substr)`.

| Class.method | TC | Asserts |
|---|---|---|
| `TestAuditPresence.test_min_rows` | TC-001 | parse `research/audit.md`; ≥ 30 rows in markdown table. (Reads file, not HTML.) |
| `TestAuditVerdicts.test_verdict_set` | TC-002 | every audit row's verdict cell ∈ {keep, hide-behind-toggle, remove}. |
| `TestAuditCoverage.test_branches` | TC-003 | union of audit "Element" column covers every legacy tab name. |
| `TestTabBar.test_four_tabs` | TC-004 | exactly four elements with `data-testid` matching `tab-(overview|tasks|documents|decisions)`. (When Pipeline tab lands per addendum, this will need a follow-up; for ADV009-T012 scope, accept four.) |
| `TestTabBar.test_no_legacy_tabs` | TC-005 | no element text equals one of `Log`, `Knowledge`, `Permissions`, `Designs`, `Plans`, `Research`, `Reviews` at the tab-bar role level. |
| `TestHeader.test_components` | TC-006 | header contains `data-testid="tc-progress-bar"`, `data-testid="next-action-button"`, a state pill (`.pill.state`), title, ID. |
| `TestTasksTab.test_buckets` | TC-008 | template/section markup has bucket containers for each status; container hidden via `hidden` attr or `display:none` when empty. (Tests static template, not runtime data.) |
| `TestTasksTab.test_card_shape` | TC-009 | task card template includes `data-testid="task-card-status-{id}"` placeholder, depends-on slot, TC-checklist slot; no `data-testid="task-card-path"` or `assignee` slot. |
| `TestDocumentsTab.test_chips` | TC-013 | exactly five chip filter elements with `data-testid="chip-filter-(all|designs|plans|research|reviews)"`. |
| `TestOverview.test_progress_bar` | TC-018 | overview section contains `data-testid="tc-progress-bar"` and no `<table>` for TC progress. |
| `TestDecisions.test_three_cards` | TC-022 | decisions tab includes `decisions-card-state-transitions`, `decisions-card-permissions`, `decisions-card-knowledge`. |
| `TestVisualSystem.test_classes` | TC-031 | inline `<style>` (or referenced CSS file) defines all of `.card`, `.pill`, `.progress`, `.chip-bar`, `.chip`, `.stack`, `.disclosure`. |
| `TestVisualSystem.test_no_external` | TC-032 | only one external `<script>` (marked.js) and one external CSS (none expected). Asserts no `<link rel="stylesheet" href="http...">`. |
| `TestVisualSystem.test_card_usage` | TC-033 | every section identified by `data-testid="next-action-card"`, `decisions-card-*`, `task-card-*` has class containing `card`. |

### 4. `test_ui_smoke.py` (Tier 3)

Top of file:

```python
import unittest

try:
    from playwright.sync_api import sync_playwright
    PW_AVAILABLE = True
except Exception:
    PW_AVAILABLE = False


@unittest.skipUnless(PW_AVAILABLE, "Playwright not installed")
class TestTaskDetail(unittest.TestCase): ...
```

Spin up `ServerThread` in `setUpClass` (against the synthetic fixture)
and a Chromium browser. Page object: navigate to `http://localhost:{port}/`,
wait for `data-testid="tab-overview"`.

| Class.method | TC | Behaviour asserted |
|---|---|---|
| `TestTaskDetail.test_structured` | TC-010 | click first task card, detail panel has separate elements for Description and Acceptance Criteria (not one `.markdown-blob`). |
| `TestTaskDetail.test_disclosure` | TC-011 | frontmatter pre tag has `hidden`; click `data-testid="show-details-task"` → no longer hidden. |
| `TestDocuments.test_chip_filter` | TC-014 | click `chip-filter-designs`; intercept network — no XHR fired in the click handler window (use `page.on("request")` counter). |
| `TestDocuments.test_design_header` | TC-015 | open a design doc; first rendered line begins with "What this design decides:". |
| `TestDocuments.test_plan_waves` | TC-016 | open the plan fixture; DOM has two `.wave-group` (or `data-testid="plan-wave-1"` / `plan-wave-2`). |
| `TestDocuments.test_review_strip` | TC-017 | open the review fixture; element with `data-testid="review-status-badge"` text is `PASSED`. |
| `TestOverview.test_next_action` | TC-020 | the overview's `next-action-card` text matches the backend `summary.next_action.label` (fetched via `page.evaluate('fetch(...).then(...)')`). |
| `TestDecisions.test_state_post` | TC-024 | click state-transition button; `page.on("request")` confirms a POST to `/api/adventures/<id>/state`. |

Each `setUpClass` must call `playwright.chromium.launch(headless=True)`
and `tearDownClass` must close it; failures during `setUpClass` should
raise `unittest.SkipTest` (so missing browser binary still leaves the
discover command at exit 0).

### 5. Discover wiring

After files exist, run from repo root:

```
python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"
```

If the manifest's dotted-path proof commands are also expected to run
literally, the coder may additionally `touch __init__.py` for each
parent directory. Recommend deferring that to a follow-up — the
discover command is the binding acceptance criterion.

## Testing Strategy

Self-testing of the test suite happens at three points:

1. **Manifest cross-check**: `TestStrategyDoc.test_tc_mapping` proves
   coverage of every `autotest` TC.
2. **Discover exit code**: TC-036 — must be 0 on a machine with no
   Playwright (Tier-3 skipped) AND on one with Playwright.
3. **Pre-merge dry run**: the coder runs the discover command twice —
   once with `PYTHONPATH` cleared, once after `pip install playwright`
   (if available locally) — to confirm both branches.

## Risks

- **Implementation coupling**: Tier 2 tests fully depend on the UI
  rewrite tasks (T005..T011) landing the exact `data-testid` strings
  enumerated in `design-test-strategy.md` § "Data-testid hooks". Coder
  should ground-truth each ID against the actual `index.html` after
  T011; if any ID differs, update the test rather than the markup
  (the design doc is the contract).
- **Pipeline tab addendum**: TC-004 currently asserts "exactly four
  tabs". Once ADV009-T019 ships the Pipeline tab, this will become
  five. Documented as a known follow-up; out of scope for T012.
- **Server import side-effects**: importing `server.py` triggers
  `argparse` only inside `if __name__ == "__main__":`, so
  `from .agent.adventure-console.server import Handler` is safe — but
  the directory name contains a hyphen, so we must use `importlib`:
  `spec = importlib.util.spec_from_file_location("console_server",
  CONSOLE_DIR / "server.py")`. Document this in `_fixtures.py`.
- **Fixture isolation**: each test class must build a fresh tmpdir to
  avoid cross-test mutation from POST endpoints.
- **TestStrategyDoc skip**: skipping when `test-strategy.md` is absent
  is intentional but should emit a clear skip reason so reviewers
  notice ADV009-T001 is still pending.
