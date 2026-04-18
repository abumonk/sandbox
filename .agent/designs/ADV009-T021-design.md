# ADV009-T021 — Automated tests for Pipeline tab + IR extractor — Design

## Approach

Extend the ADV-009 test suite with three new stdlib-`unittest` files that
cover every `proof_method: autotest` TC in the TC-039..TC-061 range. The
tests split cleanly along the three surfaces under test:

- **`test_ir.py`** — pure in-process calls into `adventure_pipeline.tools.ir`.
  Covers spec-shape TCs (TC-039..TC-041 via static file parse) and
  round-trip TCs (TC-042..TC-044).
- **`test_graph_endpoint.py`** — boots `server.py` in a ThreadingHTTPServer
  on a random port, drives HTTP via `urllib.request`. Covers the backend
  graph + `depends_on` TCs (TC-046, TC-052..TC-054, TC-058..TC-061).
- **`test_pipeline_tab.py`** — static inspection of `index.html` with
  `html.parser.HTMLParser` + regex. Covers the five Pipeline-tab TCs
  (TC-047..TC-051) and the two client-side edit TCs whose evidence is
  statically inspectable (TC-055, TC-056).

Tests are stdlib-only. They share a small fixture helper module so each
test file stays self-contained but avoids duplicated boot code.

## Target Files

- `.agent/adventures/ADV-009/tests/test_ir.py` — IR extractor tests.
- `.agent/adventures/ADV-009/tests/test_graph_endpoint.py` — HTTP tests
  against `/graph` and `depends_on` POST.
- `.agent/adventures/ADV-009/tests/test_pipeline_tab.py` — static HTML /
  JS inspection of `index.html`.
- `.agent/adventures/ADV-009/tests/_fixtures.py` — small shared helpers
  (path-to-repo-root resolver, synthetic temp-adventure builder,
  in-process server launcher). Not picked up by `test_*.py` discovery.

## TC coverage mapping

Every TC in the task's `target_conditions:` block maps to at least one
named test function. TC-045 and TC-057 are `proof_method: poc` and are
deliberately NOT in scope for this task.

| TC | File | Class.test |
|----|------|-----------|
| TC-039 | test_ir.py | `TestSpecShapes.test_adventure_spec_parses` |
| TC-040 | test_ir.py | `TestSpecShapes.test_processes` |
| TC-041 | test_ir.py | `TestSpecShapes.test_runtime_entities` |
| TC-042 | test_ir.py | `TestRoundTrip.test_adv007` |
| TC-043 | test_ir.py | `TestRoundTrip.test_adv008` |
| TC-044 | test_ir.py | `TestRoundTrip.test_task_ids_match_manifest` |
| TC-046 | test_graph_endpoint.py | `TestGraphShape.test_top_level_keys` |
| TC-047 | test_pipeline_tab.py | `TestCdn.test_cytoscape_script_tag` |
| TC-048 | test_pipeline_tab.py | `TestTabOrder.test_five_tabs_pipeline_fourth` |
| TC-049 | test_pipeline_tab.py | `TestStatusColours.test_stylesheet_entries` |
| TC-050 | test_pipeline_tab.py | `TestNoWebsocket.test_no_ws_or_eventsource` |
| TC-051 | test_pipeline_tab.py | `TestTooltipsFromBackend.test_no_hardcoded_tooltip_strings` |
| TC-052 | test_graph_endpoint.py | `TestDependsOn.test_happy` |
| TC-053 | test_graph_endpoint.py | `TestDependsOn.test_self_cycle` |
| TC-054 | test_graph_endpoint.py | `TestDependsOn.test_cycle` |
| TC-055 | test_pipeline_tab.py | `TestDragOneShot.test_single_post_guard` |
| TC-056 | test_pipeline_tab.py | `TestRollback.test_optimistic_removal_on_4xx` |
| TC-058 | test_graph_endpoint.py | `TestImport.test_server_imports_ir` |
| TC-059 | test_graph_endpoint.py | `TestGraphShape.test_schema` |
| TC-060 | test_graph_endpoint.py | `TestStdlibOnly.test_no_third_party_imports` |
| TC-061 | test_graph_endpoint.py | `TestCycleFree.test_self_and_transitive` |

## Implementation Steps

### 1. `_fixtures.py` (shared helper)

- `repo_root()` — walks up from `__file__` until it finds `.agent/`.
- `ensure_on_syspath()` — inserts `repo_root()` on `sys.path` so
  `adventure_pipeline.tools.ir` and the console's `server` module import
  cleanly from the test runner's CWD.
- `TempAdventure` context manager — copies a minimal fixture adventure
  into `tempfile.mkdtemp()` for the `depends_on` POST tests (never
  mutate real `.agent/adventures/` content). Builds:
  - `manifest.md` with 2 tasks and a TC table.
  - `tasks/T1.md`, `tasks/T2.md` with frontmatter `depends_on: []`.
- `ServerProcess` — starts `server.py`'s `ThreadingHTTPServer` on
  `('127.0.0.1', 0)` in a daemon thread, exposes `.base_url`, joins on
  `__exit__`. Uses the same pattern already established in T012's
  `test_server.py`.

### 2. `test_ir.py`

**`TestSpecShapes`** — opens the three `.ark` files directly with
`pathlib.Path.read_text()` and runs targeted regex checks. We do NOT
depend on the Ark parser being runnable in-process; the parse cleanliness
is a separate POC test owned by TC-039's `proof_command`. Here we assert
declarations exist:

- `test_adventure_spec_parses` — reads `adventure_pipeline/specs/adventure.ark`,
  asserts regex finds `abstraction Adventure`, `class Phase`, `abstraction Task`,
  `enum State`, `enum Status`, `enum ProofMethod`.
- `test_processes` — reads `pipeline.ark`, asserts regex finds
  `process AdventureStateMachine`, `process TaskLifecycle`,
  `process ReviewPipeline`.
- `test_runtime_entities` — reads `entities.ark`, asserts regex finds
  `class RunningAgent`, `class ActiveTask`, `class PendingDecision`,
  `class KnowledgeSuggestion`, `class ReviewArtifact`.

**`TestRoundTrip`** — calls `extract_ir("ADV-007")` and
`extract_ir("ADV-008")` (these live adventures exist on disk).

- `test_adv007` — asserts returned dataclass has non-empty `tasks`,
  `documents`, `tcs`, `permissions`. Spot-checks: `tasks` contains a
  task whose `id` starts with `ADV007-T`; at least one `Design`-kind
  document; `tcs` list non-empty.
- `test_adv008` — mirror of the above for ADV-008.
- `test_task_ids_match_manifest` — parses the `tasks:` frontmatter array
  from `ADV-007/manifest.md` by regex; asserts
  `set(ir_task_ids) == set(manifest_task_ids)` (covers TC-044 no-orphans
  and no-missing).

**`TestIrEntityShape`** (additional, not mapped to a TC but required by
the task description "entity shape, enum serialization, orphan-id
detection"): checks `asdict(ir)` is JSON-serializable via `json.dumps`
and that all enum-valued fields serialize to their string name.

### 3. `test_graph_endpoint.py`

All tests use `ServerProcess` fixture. Server is launched once per
`TestCase` class via `setUpClass`, bound to a real on-disk adventure
(ADV-007) for read-only tests and to the `TempAdventure` for mutation
tests.

**`TestImport`**
- `test_server_imports_ir` — opens `.agent/adventure-console/server.py`,
  asserts the string `from adventure_pipeline.tools.ir import extract_ir`
  (or equivalent import form `adventure_pipeline.tools.ir`) appears in
  the source. Covers TC-058 statically.

**`TestStdlibOnly`**
- `test_no_third_party_imports` — parses `server.py` with `ast.parse`,
  walks all `Import`/`ImportFrom` nodes, asserts every top-level module
  is either in `sys.stdlib_module_names` (Python 3.10+) or is
  `adventure_pipeline` (our own sibling package). Covers TC-060.

**`TestGraphShape`**
- `test_top_level_keys` — GETs `/api/adventures/ADV-007/graph`, asserts
  HTTP 200, JSON has keys `nodes`, `edges`, `explanations`; `nodes` and
  `edges` are lists, `explanations` is a dict. Covers TC-046.
- `test_schema` — stronger shape check: every node has `data.id` and
  `data.kind`; every edge has `data.id`, `data.source`, `data.target`.
  At least one node of kind `adventure`, one of `task`. Covers TC-059.

**`TestDependsOn`** (uses `TempAdventure` with two tasks T1, T2)
- `test_happy` — POSTs `{"depends_on": "T2"}` to
  `/api/adventures/{adv}/tasks/T1/depends_on`; asserts 200; response body
  contains merged list including `T2`; re-reads `T1.md` on disk and
  asserts frontmatter `depends_on:` now contains `T2`. Covers TC-052.
- `test_self_cycle` — POSTs `{"depends_on": "T1"}` to T1; asserts 400
  and T1's file is unchanged. Covers TC-053.
- `test_cycle` — seeds T2 with `depends_on: [T1]`, then POSTs T2 as a
  dep of T1; asserts 400. Covers TC-054.
- `test_unknown_task` — additional coverage per task description: POSTs
  `{"depends_on": "T999"}`; asserts 400.

**`TestCycleFree`**
- `test_self_and_transitive` — imports `_cycle_free` (or the
  equivalently named helper) directly from the `server` module, builds a
  tiny in-memory IR stub with 3 tasks forming a chain, asserts the
  helper rejects self-cycles and transitive cycles while accepting safe
  additions. Covers TC-061.

### 4. `test_pipeline_tab.py`

Reads `.agent/adventure-console/index.html` once per module via
`setUpModule`, caches as `HTML`. Uses `html.parser.HTMLParser` for
DOM-shape checks and raw string/regex checks for script and stylesheet
concerns.

**`TestCdn`**
- `test_cytoscape_script_tag` — walks parsed `<script>` tags; asserts at
  least one has a `src` matching `r"https?://[^"']*cytoscape[^"']*\.js"`.
  Additionally asserts no local `./vendor/cytoscape` reference. Covers
  TC-047.

**`TestTabOrder`**
- `test_five_tabs_pipeline_fourth` — locates the tab bar (by the
  `data-testid="tab-*"` hooks introduced by T006), asserts five buttons,
  order `[Overview, Tasks, Documents, Pipeline, Decisions]`. Covers
  TC-048.

**`TestStatusColours`**
- `test_stylesheet_entries` — finds cytoscape style block (either inside
  the inline `<script>` defining cytoscape `style: [...]` or a CSS block
  keyed by node `kind`/`status` data attributes). Asserts the four
  expected kind/status pairs each appear at least once:
  `task` + `--accent`, `tc` + `--muted`/`--ok`/`--danger`, `decision` +
  `--warn`, `document` + `--ink`. Regex-based. Covers TC-049.

**`TestNoWebsocket`**
- `test_no_ws_or_eventsource` — greps `index.html` for
  `r"\bWebSocket\b"`, `r"\bEventSource\b"`, `r"wss?://"`. Asserts zero
  matches. Additionally opens `.agent/adventure-console/server.py` and
  asserts the same. Covers TC-050.

**`TestTooltipsFromBackend`**
- `test_no_hardcoded_tooltip_strings` — locates the `renderPipeline`
  function body by regex (`function renderPipeline\s*\([^)]*\)\s*\{ ...
  \}` — use a bracket-balancing helper in `_fixtures.py`). Asserts no
  string literal inside contains tooltip-like content: specifically, no
  literal string matching
  `r"['\"](depends on|satisfies|gate|approve|review)[^'\"]*['\"]"` in
  the function body. Must see one or more references to
  `explanations\[` or `explanations.`. Covers TC-051.

**`TestDragOneShot`**
- `test_single_post_guard` — greps the JS source for the drag handler
  (locate by `cy.on('ehcomplete'` or the drag-end event identifier used
  by T020). Asserts the handler wires a 500 ms debounce guard (via a
  `disabled` flag set and cleared) OR a visible `setTimeout(...500)`
  acting as the double-submit guard. Since this is a static test, we
  assert the **pattern is present**, not the runtime behaviour. Covers
  TC-055 statically; qa-tester owns the runtime check in a follow-up
  POC.

**`TestRollback`**
- `test_optimistic_removal_on_4xx` — greps the `depends_on` POST
  handler in the JS source, asserts the error path calls `cy.remove(` or
  equivalent on a 4xx branch. Covers TC-056 statically.

### 5. Test discovery + run command

Add no `__init__.py`; `unittest discover` works without one when the
pattern matches. From the repo root:

```
python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"
```

Must exit 0 once T015–T020 are complete. While T021 is in isolation
(tests authored before T015–T020 land), tests will fail naturally — the
acceptance criterion ties to the final stacked state.

## Testing Strategy

- Run `python -m unittest discover -s .agent/adventures/ADV-009/tests -p
  "test_*.py"` from repo root; expect exit 0.
- Spot-check each test file independently:
  `python -m unittest .agent.adventures.ADV-009.tests.test_ir`, etc.
- Verify every TC from TC-039..TC-061 (minus TC-045, TC-057 which are
  POC) has a `test_` function in the mapping table above.
- Check that no test file imports anything outside `sys.stdlib_module_names`
  and `adventure_pipeline.*`. Concretely: `grep -RE "^import |^from "
  .agent/adventures/ADV-009/tests/test_*.py` — review output manually.

## Risks

- **Ordering with T018–T020**: Tests are authored assuming the graph
  endpoints + Pipeline tab markup are already in place. If T021 runs
  before T018–T020, all three files will fail. Mitigation: T021's
  `depends_on` already lists T018–T020. The runner must honour the
  dependency graph.
- **Static regex for `renderPipeline` detection** (TC-051, TC-055, TC-056):
  Depends on the function name `renderPipeline` actually being used. If
  T019/T020 inline the logic differently, assertions miss. Mitigation:
  the designs explicitly name `renderPipeline(adv)` and the plan copies
  that signature, so the contract is set.
- **Ark file parse via regex, not the real Ark parser** (TC-039): We
  check for declarations by string match, not grammar conformance. The
  manifest-declared `proof_command` for TC-039 uses `python ark/ark.py
  parse ...` directly; our `test_adventure_spec_parses` is a *coverage
  helper*, not a substitute. Acceptable because TC-039 is covered
  end-to-end by the proof_command and the discover run remains
  stdlib-only.
- **`TempAdventure` contamination**: If test cleanup fails on Windows
  file locks, leftover `tempfile` dirs accumulate. Mitigation: wrap
  teardown in `shutil.rmtree(..., ignore_errors=True)` and rely on
  `tempfile.mkdtemp` auto-cleanup on reboot.
- **`sys.stdlib_module_names`** requires Python 3.10+. The project
  config already specifies Python 3.12 (see manifest §Environment).
