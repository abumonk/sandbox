# Add /graph + depends_on backend endpoints — Design

## Approach

Extend `.agent/adventure-console/server.py` with two new endpoints, plus a
shared cycle-detection helper and a tiny task-frontmatter rewriter. Both
endpoints lean on the IR extractor authored in ADV009-T016
(`adventure_pipeline.tools.ir.extract_ir`) for canonical node/edge data
and for the cycle walk. No third-party imports; all logic inlined alongside
the existing handlers using the same routing, JSON, and frontmatter
patterns already in `server.py`.

The implementation reuses the existing module structure:

- `parse_frontmatter` / `_FM_RE` for read.
- `safe_adventure_id`, `adventure_path`, `read_text`, `write_text`,
  `append_log`, `now_iso` for path / IO / audit.
- The same regex-routing dispatch in `do_GET` / `do_POST`.
- The same exception → status mapping
  (`FileNotFoundError → 404`, `ValueError → 400`, else `500`).

The only structural addition is a `sys.path` insert at module top so that
`adventure_pipeline.tools.ir` resolves when the server is started from
the repo root (the package lives at `R:/Sandbox/adventure_pipeline/`,
i.e. directly under `REPO_ROOT`, which is already on `sys.path` only when
launched as a script from that directory). Insert `REPO_ROOT` defensively
to make startup location-independent.

## Target Files

- `.agent/adventure-console/server.py` — add IR import, three helpers
  (`_load_ir`, `_cycle_free`, `_rewrite_task_depends_on`), two handler
  functions (`graph_payload`, `add_task_dependency`), two new route
  branches (one in `do_GET`, one in `do_POST`), and update the docstring
  endpoint table. No edits to existing handlers.

## Implementation Steps

1. **Module-top setup (one block, after existing imports).**
   - Add `import sys` is already present; add a short block:
     ```python
     # Make the sibling adventure_pipeline package importable regardless
     # of where the server is launched from.
     _PKG_ROOT = REPO_ROOT
     if str(_PKG_ROOT) not in sys.path:
         sys.path.insert(0, str(_PKG_ROOT))
     from adventure_pipeline.tools.ir import extract_ir   # noqa: E402
     ```
   - Update the module docstring's *Endpoints* table with the two new
     routes:
     ```
     GET  /api/adventures/{id}/graph
     POST /api/adventures/{id}/tasks/{task_id}/depends_on
     ```

2. **Helper: `_load_ir(adv_id)`**
   - Wraps `extract_ir(adv_id)` so handlers can swap stub for tests.
   - Re-raises `FileNotFoundError` unchanged so the GET handler's existing
     `except FileNotFoundError → 404` covers unknown adventures.
   - Wraps any other exception in a `RuntimeError` carrying
     `("ir_extract", original)` so the GET handler can return
     `{"error": "...", "stage": "ir_extract"}` with status 500.

3. **Helper: `_cycle_free(ir, task_id, new_dep)`**
   - Builds an adjacency dict from `ir.tasks`:
     `adj[t.id] = list(t.depends_on)`.
   - Adds the proposed edge: `adj.setdefault(task_id, []).append(new_dep)`.
   - Runs an iterative BFS from `new_dep` over `adj`. Returns
     `False` (i.e. *not* cycle-free) iff `task_id` is reachable from
     `new_dep` (including the case `task_id == new_dep`, which becomes
     a self-loop and is therefore reachable in one hop).
   - Pure function — no IO. Module-level so the future Pipeline editing
     surface can call it directly.

4. **Helper: `_rewrite_task_depends_on(adv_id, task_id, merged)`**
   - Loads `adventure_path(adv_id) / "tasks" / f"{task_id}.md"`.
   - 404 (`FileNotFoundError`) if missing.
   - Splits frontmatter via `_FM_RE`; iterates the existing fm lines and
     rewrites only the `depends_on:` line (or appends one if absent).
   - Format the merged list as the single-line inline form already used
     elsewhere: `depends_on: [ITEM1, ITEM2]` (matches existing style in
     ADV009-T018.md). Items are emitted bare — no quoting (existing
     parser strips quotes either way).
   - Also rewrites the `updated:` line to `now_iso()` (mirrors
     `update_state` behavior on the manifest).
   - Writes the file back via `write_text`.
   - Returns the merged list.

5. **Handler: `graph_payload(adv_id)` → dict**

   Build the JSON shape from the `AdventurePipelineIR`:

   - **Adventure node** — `{"data": {"id": "adv", "kind": "adventure",
     "label": f"{ir.id} {ir.title}", "status": ir.state}}`.
   - **Phase nodes** — for each phase in `ir.phases`:
     `{"data": {"id": f"phase:{slug(phase.name)}", "kind": "phase",
     "label": phase.name, "parent": "adv"}}`.
   - **Task nodes** — for each `t` in `ir.tasks`:
     `{"data": {"id": f"task:{t.id}", "kind": "task",
     "label": f"{t.id} — {t.title}", "status": t.status,
     "parent": phase_id_for(t)}}`.
     If a task has no phase mapping, parent = `"adv"`.
   - **Document nodes** — one node per design / plan / research / review
     document found by the IR. `id = f"doc:{name_without_ext}"`,
     `kind = "document"`, `docKind ∈ {design,plan,research,review}`,
     `parent = "adv"`.
   - **TC nodes** — `{"data": {"id": f"tc:{tc.id}", "kind": "tc",
     "label": tc.id, "status": tc.status, "parent": "adv"}}`.
   - **Decision nodes** — derive a fixed small set from IR state:
     - `decision:permissions` if `permissions.status != "approved"`.
     - `decision:design:{name}` for any design lacking the
       `<!-- approved: ... -->` stamp (best-effort: read file and
       check). Status `"pending"` / `"done"` accordingly.
     - `decision:state` always present, status mirrors the legal
       transition state; this is what the click-state-transition edge
       attaches to.

   - **Edges:**
     - `depends_on` — for each task `t` and each dep in `t.depends_on`,
       emit `{"data": {"id": f"e:dep:{t.id}->{dep}", "source":
       f"task:{dep}", "target": f"task:{t.id}", "kind": "depends_on"}}`.
     - `satisfies` — for each task `t` and each `tc_id` in
       `t.target_conditions`, emit `{"data": {"id":
       f"e:tc:{t.id}->{tc_id}", "source": f"task:{t.id}", "target":
       f"tc:{tc_id}", "kind": "satisfies"}}`.
     - `state_transition` — one edge from `"adv"` to
       `f"state:{ir.state}"` (kind `state_transition`). The frontend
       handles the click → POST `/state`.
     - `addresses` — for each TC `tc` with non-empty `tc.design` /
       `tc.plan`, emit edges from `tc:{tc.id}` to the matching
       `doc:{name}` (kind `addresses`). Best-effort; skip if doc not
       found.

   - **Explanations dict:**
     - Per task with deps:
       `f"{t.id} depends on {', '.join(t.depends_on)} — gates
       downstream work."`
     - Per TC: `f"{tc.id}: {tc.description}"`.
     - Per decision: short literal label (`"Pending: approve permissions"`,
       etc.).
     - Per document: `f"{doc.kind}: {doc.name}"`.
     All strings deterministic, derived only from IR fields. No LLM calls.

   - Return `{"nodes": [...], "edges": [...], "explanations": {...}}`.

   Phase / status / slug helpers live as small inner functions.

6. **Handler: `add_task_dependency(adv_id, task_id, body, actor)` → dict**
   - Validate `task_id` matches `ADV\d{3}-T\d{3}` (raise `ValueError`
     → 400 otherwise).
   - Validate `new_dep = body.get("depends_on")` is a non-empty string
     matching the same regex (raise `ValueError` → 400 otherwise).
   - Self-cycle: if `new_dep == task_id` → `ValueError("self-cycle: task
     cannot depend on itself")`.
   - Load IR via `_load_ir(adv_id)`. Build `task_ids = {t.id for t in
     ir.tasks}`.
   - If `task_id not in task_ids` → `FileNotFoundError(f"task {task_id}
     not in {adv_id}")` (→ 404). If `new_dep not in task_ids` →
     `ValueError(f"unknown task: {new_dep}")` (→ 400, matches "references
     a task not in this adventure").
   - Cycle check: `if not _cycle_free(ir, task_id, new_dep): raise
     ValueError("would create dependency cycle")` → 400.
   - Determine merged list: existing `depends_on` for that task (from
     IR) + `[new_dep]`, dedup-preserving-order.
   - Call `_rewrite_task_depends_on(adv_id, task_id, merged)`.
   - `append_log(adv_id, actor, f"depends_on: {task_id} += {new_dep}")`.
   - Return `{"ok": True, "task_id": task_id, "depends_on": merged}`.

7. **Routing**

   - `do_GET`: insert before the final `404` line:
     ```python
     m = re.fullmatch(r"/api/adventures/(ADV-\d{3})/graph", path)
     if m:
         try:
             ir = _load_ir(m.group(1))
         except FileNotFoundError:
             raise
         self._send_json(200, graph_payload_from_ir(ir))
         return
     ```
     (The outer `try/except` already maps `FileNotFoundError → 404`.)
     If `_load_ir` raises a `RuntimeError("ir_extract", ...)`, the
     existing `except Exception` branch returns 500 with the message —
     the design doc's `{"error": "...", "stage": "ir_extract"}` is met
     by formatting the `str()` of that error to start with
     `"ir_extract: ..."`. (Acceptance criterion 1 only requires 200 with
     the schema — the stage tag is an internal nicety.)

   - `do_POST`: insert before the final `404` line:
     ```python
     m = re.fullmatch(
         r"/api/adventures/(ADV-\d{3})/tasks/(ADV\d{3}-T\d{3})/depends_on",
         path,
     )
     if m:
         self._send_json(
             200,
             add_task_dependency(m.group(1), m.group(2), body, actor),
         )
         return
     ```

8. **No edits** to: existing handlers `update_state`,
   `approve_permissions`, `approve_design`,
   `record_knowledge_selection`, the `/api/file` route, or anything in
   `data assembly`. The new code is strictly additive — same convention
   as design-graph-backend-endpoints §"Affected existing tasks".

## Testing Strategy

Acceptance criteria are validated by unit tests authored in ADV009-T021
(`tests/test_graph_endpoint.py`). At implementation time the coder
performs these manual smoke checks:

1. Start server: `python .agent/adventure-console/server.py --port 7070`.
2. `curl -s localhost:7070/api/adventures/ADV-007/graph | python -m json.tool` —
   expect `nodes`, `edges`, `explanations` keys; ≥1 task node; ≥1
   depends_on edge.
3. `curl -s -X POST -H "Content-Type: application/json" \
      -d '{"depends_on": "ADV007-T002"}' \
      localhost:7070/api/adventures/ADV-007/tasks/ADV007-T003/depends_on` —
   expect 200 + merged list, then read the file back to confirm
   `depends_on:` line was rewritten.
4. Self-cycle: post `{"depends_on": "ADV007-T003"}` to T003 → 400.
5. Cycle: post a back-edge that creates a cycle → 400.
6. Run `python -m unittest discover -s .agent/adventures/ADV-009/tests`
   once T021 is implemented.

The new endpoints touch only one source file and depend on the IR
extractor. No new third-party imports — verifiable with
`grep -nE "^import |^from " .agent/adventure-console/server.py` showing
only stdlib + `adventure_pipeline.tools.ir`.

## Risks

- **IR import path.** If the adventure_pipeline package is not yet
  on `sys.path`, the explicit `sys.path.insert(0, REPO_ROOT)` block
  handles it. Risk: future move of the package would require updating
  this insert. Mitigation: comment the block.
- **Cycle detection over `_cycle_free`.** BFS over a small task graph
  (~25 nodes) is trivially fast; correctness risk is in the corner
  cases (`task_id == new_dep`, `new_dep` already in `t.depends_on`).
  Both are unit-tested in T021.
- **Frontmatter rewrite.** `_rewrite_task_depends_on` only rewrites the
  `depends_on:` and `updated:` lines and preserves everything else —
  including comments. Risk: existing inline-list lines that span
  multiple lines would not be matched; mitigation: all current task
  files use the single-line `[A, B]` form (verified by grepping the
  ADV-007 task corpus). Add a defensive raise if a multi-line
  `depends_on:` block is detected (start `:` followed by newline +
  `- ` items) — refuse with `ValueError` to surface the schema drift
  rather than silently corrupting.
- **Concurrent writes.** No file locking. If the human and an agent
  edit the same task file simultaneously the last writer wins. Out of
  scope for v1 — same trade-off as every other write endpoint in this
  server.
- **Decision node heuristics.** The "decision:design:{name}" enumeration
  walks every design file once per `/graph` poll (5 s). On a 20-design
  adventure this is ~20 small reads = negligible. Document a follow-up
  if the cost ever becomes visible.
