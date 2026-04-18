# ADV009-T003: Add AdventureSummary to server.py — Design

## Approach

Extend `get_adventure()` in `.agent/adventure-console/server.py` to attach a
derived `summary` block alongside the existing return dict. Nothing is
persisted to disk — the block is computed on each request from data the
function already loads (tasks, TCs, permissions, manifest state).

Add one new helper `compute_next_action(meta, permissions, tcs, tasks)` that
returns the `next_action` sub-object. The helper is pure, deterministic, and
driven by the adventure `state` enum, with secondary inputs from permissions
status and TC progress.

No new imports. All logic uses stdlib features already imported (`re`, dicts,
list comprehensions).

## Target Files

- `.agent/adventure-console/server.py` — add `compute_next_action()` helper,
  extend `get_adventure()` to compute and attach a `summary` block.

## Reference Shape (from design-backend-endpoints)

```json
"summary": {
  "tc_total": 17,
  "tc_passed": 8,
  "tc_failed": 2,
  "tc_pending": 7,
  "tasks_by_status": {"pending": 4, "in_progress": 2, "passed": 5, "done": 1},
  "next_action": {
    "kind": "approve_permissions",
    "label": "Approve Permissions",
    "state_hint": "review"
  }
}
```

## Implementation Steps

### 1. Add a small constants/helper block above `get_adventure()`

Insert after `_target_conditions()` (around line 178):

```python
# ---------------------------------------------------------------------------
# Summary derivation
# ---------------------------------------------------------------------------

# TC status normalization. Real manifest rows use values like
# "passed", "PASSED", "failed", "pending", or blank. We bucket them into
# three buckets: passed / failed / pending.
_TC_PASSED_TOKENS = {"passed", "pass", "ok", "green", "done"}
_TC_FAILED_TOKENS = {"failed", "fail", "red", "broken"}


def _bucket_tc_status(raw: str) -> str:
    token = (raw or "").strip().lower()
    if token in _TC_PASSED_TOKENS:
        return "passed"
    if token in _TC_FAILED_TOKENS:
        return "failed"
    return "pending"


def compute_next_action(meta: dict,
                        permissions: dict | None,
                        tcs: list[dict],
                        tasks: list[dict]) -> dict:
    """Return a deterministic `next_action` dict driven by adventure state.

    Kinds: "approve_permissions" | "open_plan" | "resolve_blocker"
           | "promote_concept" | "none".
    """
    state = (meta.get("state") or "unknown").strip().lower()

    # Blocked trumps everything: surface the resolver.
    if state == "blocked":
        return {
            "kind": "resolve_blocker",
            "label": "Resolve Blocker",
            "state_hint": "blocked",
        }

    if state == "concept":
        return {
            "kind": "promote_concept",
            "label": "Promote to Planning",
            "state_hint": "concept",
        }

    if state == "review":
        perm_status = (permissions or {}).get("status", "").strip().lower()
        if perm_status != "approved":
            return {
                "kind": "approve_permissions",
                "label": "Approve Permissions",
                "state_hint": "review",
            }
        # Permissions are fine — fall back to opening the plan.
        return {
            "kind": "open_plan",
            "label": "Open Plan",
            "state_hint": "review",
        }

    if state == "planning":
        return {
            "kind": "open_plan",
            "label": "Open Plan",
            "state_hint": "planning",
        }

    if state == "active":
        return {
            "kind": "open_plan",
            "label": "Continue Execution",
            "state_hint": "active",
        }

    # completed, cancelled, unknown — nothing to do from the overview.
    return {
        "kind": "none",
        "label": "",
        "state_hint": state,
    }
```

Notes:
- Every member of `VALID_STATES` (`concept`, `planning`, `review`, `active`,
  `blocked`, `completed`, `cancelled`) plus an `unknown` fallback is handled,
  satisfying AC-2.
- The helper is module-level (not nested) so `test_server.py` can import and
  unit-test it directly.

### 2. Extend `get_adventure()` return dict

Just before the final `return {...}` in `get_adventure()` (around line 262),
compute the summary and add it to the returned dict.

Insert (after the `log_tail` block, before `return`):

```python
    # Summary — derived, not persisted.
    tc_buckets = {"passed": 0, "failed": 0, "pending": 0}
    for tc in tcs:
        tc_buckets[_bucket_tc_status(tc.get("status", ""))] += 1

    tasks_by_status: dict[str, int] = {}
    for t in tasks:
        key = (t.get("status") or "unknown").strip().lower() or "unknown"
        tasks_by_status[key] = tasks_by_status.get(key, 0) + 1

    summary = {
        "tc_total": len(tcs),
        "tc_passed": tc_buckets["passed"],
        "tc_failed": tc_buckets["failed"],
        "tc_pending": tc_buckets["pending"],
        "tasks_by_status": tasks_by_status,
        "next_action": compute_next_action(meta, permissions, tcs, tasks),
    }
```

Then add `"summary": summary,` to the returned dict (after `"log_tail"` or
adjacent to the other top-level keys).

### 3. Leave every other endpoint and helper untouched

- Do not modify `/api/file`, `/state`, `/permissions/approve`,
  `/design/approve`, `/knowledge/apply`, `/log`.
- Do not modify `list_adventures()`.
- Do not add new `import` statements. The helper uses dicts and `.get()` only.

## Testing Strategy

`tests/test-strategy.md` (produced by ADV009-T001) will map TC-026, TC-029,
TC-030 to concrete test functions. The suggested coverage for this task:

**`.agent/adventures/ADV-009/tests/test_server.py` (stdlib unittest):**

1. `test_summary_block_shape` — load a fixture adventure, call
   `get_adventure()`, assert the returned dict has a `summary` key whose
   object contains all of: `tc_total`, `tc_passed`, `tc_failed`,
   `tc_pending`, `tasks_by_status` (dict), `next_action` (dict). Covers
   TC-026.
2. `test_next_action_review_unapproved_permissions` — build synthetic
   `meta = {"state": "review"}`, `permissions = {"status": "draft"}`,
   assert `compute_next_action(...).kind == "approve_permissions"`. Covers
   TC-029.
3. `test_next_action_handles_every_valid_state` — iterate `VALID_STATES`,
   call `compute_next_action({"state": s}, None, [], [])`, assert the
   returned `kind` is in the allowed enum and `state_hint == s`. Covers
   AC-2.
4. `test_stdlib_only_imports` — read `server.py`, assert the set of
   top-level `import` / `from` targets is a subset of the stdlib allowlist
   (`argparse`, `json`, `re`, `sys`, `traceback`, `datetime`,
   `http.server`, `pathlib`, `urllib.parse`, plus `__future__`). Covers
   TC-030.

Run command (per test strategy):

```
python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"
```

## Risks

- **Key-name drift.** The frontend consumes `summary.next_action.kind`. If
  a contributor later renames `kind` → `type`, the overview tab silently
  breaks. Mitigation: lock the shape with `test_summary_block_shape`.
- **Permission status casing.** Existing `permissions.md` files use lower-case
  `approved` but nothing enforces it. The helper lower-cases before
  comparing, so mixed-case values still work.
- **TC status vocabulary.** `_target_conditions()` pulls the raw `status`
  cell from the markdown table; real manifests use `passed` / `PASSED` /
  blank. The `_bucket_tc_status` allowlist is conservative — unrecognized
  tokens fall into `pending`, which is the safe default for an
  action-oriented summary.
- **No new fields persisted.** The summary is recomputed per request. This
  is cheap (one manifest + one permissions.md + N tasks) and matches the
  design contract.
