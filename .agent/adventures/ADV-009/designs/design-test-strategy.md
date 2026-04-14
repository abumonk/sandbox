# Test Strategy — Design

## Overview

Defines the automated-test strategy for ADV-009. Unusual constraint: the
deliverable is a browser UI with no build step and no existing test
framework. This design spells out how we verify every TC with
`proof_method: autotest` without adding a frontend bundler, Jest, or
Playwright.

## Target Files

- `.agent/adventures/ADV-009/tests/test-strategy.md` (new — the contract)
- `.agent/adventures/ADV-009/tests/test_server.py` (will be implemented)
- `.agent/adventures/ADV-009/tests/test_ui_smoke.py` (will be implemented)
- `.agent/adventures/ADV-009/tests/test_ui_layout.py` (will be implemented)

## Approach

### Test tiers

**Tier 1 — Python stdlib tests against the server**

- Framework: `unittest` (stdlib; zero install).
- Fixture: a tmp `.agent/adventures/ADV-TEST/` tree populated with a
  synthetic manifest, designs, plans, tasks, reviews.
- Runs `server.py` in-process (import `Handler`, call helpers directly; or
  start `ThreadingHTTPServer` on a random port in a setUp thread).
- Covers every backend TC: TC-026..TC-030 and the existing regression
  surface.

**Tier 2 — Static HTML / JS structural tests**

- Framework: `unittest` + a tiny HTML fetcher that parses `index.html` into
  a soup (use stdlib `html.parser.HTMLParser` or a single-file vendored
  `selectolax`-style regex helper — we'll stick to stdlib).
- Asserts: number of declared tabs, presence of CSS classes, presence of
  specific `data-testid` attributes we add to the UI for hook points.
- Covers structural TCs: TC-004, TC-005, TC-031, TC-032.

**Tier 3 — Headless-browser smoke (single test file)**

- **Only** if Playwright is already available in the environment; the test
  suite opens a `conftest`-style guard that skips the Tier-3 file when
  `playwright` imports fail.
- Launches the server on a random port, drives the UI, asserts visual
  presence.
- Covers behavioral TCs: TC-008, TC-011, TC-013, TC-014, TC-020, TC-024.

If Tier 3 is unavailable, every Tier-3 TC is additionally backed by a
**Tier 2 static assertion** on the markup so `autotest` coverage is never
lost — just weaker.

### Data-testid hooks (added to index.html)

Every interactive / asserted element gets a `data-testid` attribute:
- `tab-overview`, `tab-tasks`, `tab-documents`, `tab-decisions`
- `tc-progress-bar`, `tc-progress-label`
- `next-action-card`, `next-action-button`
- `chip-filter-{all,designs,plans,research,reviews}`
- `task-card-{id}`, `task-card-status-{id}`
- `doc-list-item-{filename}`
- `decisions-card-{state-transitions,permissions,knowledge}`
- `show-details-{context}` for every disclosure.

This is the single contract between Tier 2/3 tests and the UI.

### Run command

From repo root:

```
python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"
```

Tier 3 (when available) is the same command — the Playwright tests live
next to the others and simply skip themselves if the import fails.

### Coverage target

Every TC with `proof_method: autotest` must map to at least one named test
function in the strategy document. No TC is proved by more than one tier
simultaneously unless the primary tier is Tier 3 and a Tier 2 fallback is
required.

## Dependencies

- Every other design (the test strategy asserts their TCs).
- `design-backend-endpoints` (server tests target its additions).

## Target Conditions

- TC-034: `tests/test-strategy.md` exists and maps every TC with
  `proof_method: autotest` to a named test function in a named test file.
- TC-035: All declared test files (`test_server.py`, `test_ui_smoke.py`,
  `test_ui_layout.py`) use stdlib `unittest` as their framework.
- TC-036: The test run command `python -m unittest discover -s
  .agent/adventures/ADV-009/tests -p "test_*.py"` exits 0 after
  implementation.
