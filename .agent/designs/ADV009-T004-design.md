# ADV009-T004: GET /api/adventures/{id}/documents endpoint — Design

## Approach

Add a single new route `GET /api/adventures/{id}/documents` to
`.agent/adventure-console/server.py` that returns a unified JSON array of
`DocumentEntry` records covering designs, plans, research, and reviews for
the given adventure. All parsing is done server-side with stdlib-only
regex + string operations so the frontend never has to re-parse markdown.

Implementation is additive — no existing endpoint or helper is modified.
Parser helpers are module-level functions to keep them unit-testable
without spinning up the HTTP server.

## Target Files

- `.agent/adventure-console/server.py` — add four parser helpers
  (`_design_one_liner`, `_plan_metadata`, `_first_heading`,
  `_review_metadata`), one assembler (`list_documents`), and one routing
  branch inside `do_GET`.

## DocumentEntry shape

Per the design doc, entries share a `type` discriminator and a `file`
basename. Type-specific fields:

- `type: "design"` — `file`, `title`, `one_liner`
- `type: "plan"`   — `file`, `title`, `task_count`, `waves`
- `type: "research"` — `file`, `title`
- `type: "review"` — `file`, `task_id`, `status`, `build_result?`,
  `test_result?`

Ordering: designs, then plans, then research, then reviews; inside each
group sorted by filename (matches `list_dir` semantics already used by
`get_adventure`).

## Implementation Steps

1. **Helper `_first_heading(text: str) -> str`** — return the text of
   the first `^# ` (H1) line, stripped of the leading `# ` and trimmed.
   Returns `""` if absent. Used for research + as a fallback title for
   designs/plans.

2. **Helper `_design_one_liner(text: str) -> str`** — locate the
   `## Overview` section with a regex analogous to the existing concept
   matcher (`^## Overview\s*\n(.*?)(?=\n## |\Z)`, `DOTALL | MULTILINE`).
   From that block take the first non-empty, non-heading line, split on
   the first `. ` / `.\n` / end-of-string, return the first sentence
   trimmed and truncated to 120 chars (append `…` if truncation
   occurred). Returns `""` when no Overview section is present.

3. **Helper `_plan_metadata(text: str) -> tuple[int, int]`** — return
   `(task_count, waves)`:
   - `task_count` = number of lines matching `^### ` that appear after
     the first `^## Tasks` heading (scan line-by-line, set a flag when
     `## Tasks` is seen, count `### ` lines until the next `## `).
   - `waves` = count of lines matching `^## Wave ` OR `^## Phase `
     across the whole document (case-sensitive, per design doc).

4. **Helper `_review_metadata(text: str) -> dict`** — reuse
   `parse_frontmatter` and surface `task_id`, `status`, `build_result`,
   `test_result` (falling back to `""`). This mirrors the inline logic
   already present in `get_adventure` so the documents endpoint gives
   identical review metadata.

5. **Assembler `list_documents(adv_id: str) -> list[dict]`**:
   - Resolve `root = adventure_path(adv_id)` (raises on bad id); raise
     `FileNotFoundError` if root is missing (matches `get_adventure`).
   - Iterate `root / "designs"` via `list_dir`; for each, read text,
     emit `{type: "design", file, title: _first_heading or stem,
     one_liner: _design_one_liner}`.
   - Iterate `root / "plans"`; emit `{type: "plan", file, title,
     task_count, waves}` from `_plan_metadata`.
   - Iterate `root / "research"`; emit `{type: "research", file,
     title}`.
   - Iterate `root / "reviews"` (skip non-`.md`, skip
     `adventure-report.md` to stay consistent with the existing split);
     emit `{type: "review", file, **_review_metadata(text)}`.
   - Return the concatenated list.

6. **Route in `do_GET`** — directly after the existing
   `/api/adventures/{id}` match, add:
   ```python
   m = re.fullmatch(r"/api/adventures/(ADV-\d{3})/documents", path)
   if m:
       self._send_json(200, list_documents(m.group(1)))
       return
   ```
   The existing `FileNotFoundError` / generic exception handlers already
   translate missing adventures to 404 / 500, so no extra error handling
   is needed.

7. **Stdlib discipline** — only `re`, `pathlib`, existing helpers. No
   new imports. Validated by `grep -E '^import |^from ' server.py`
   diffing against the pre-change set (covered by TC-030).

## Testing Strategy

Per the Wave-A test strategy (ADV009-T001), verification lives in
`.agent/adventures/ADV-009/tests/test_server.py` using stdlib
`unittest`. This task introduces the endpoint; the test file itself is
out of scope here but the handler is designed to make the following
assertions trivial:

- **TC-027**: fixture adventure contains one file in each of
  designs/plans/research/reviews → endpoint returns 4 entries with the
  correct `type` values.
- **TC-028**: plan fixture with `## Wave 1` and `## Wave 2` headings →
  matching entry has `waves == 2`.
- **One-liner extraction**: design fixture with
  `## Overview\nFirst sentence. Second.` → entry has
  `one_liner == "First sentence"`; long-Overview fixture (>120 chars
  without a period) truncates to 120 chars + ellipsis.
- **TC-030**: static check — assert `server.py` has no new top-level
  imports beyond the pre-existing set.

Manual smoke: with the server running,
`curl http://127.0.0.1:7070/api/adventures/ADV-009/documents` should
return a JSON array.

## Risks

- **Overview-section variance**: some designs may have an `## Overview`
  that opens with a code block or a heading line. The helper skips
  leading empty/heading lines so the one-liner falls back to `""`
  instead of returning markdown syntax.
- **Sentence-splitting on abbreviations** (`e.g.`, `i.e.`): the
  ≤120-char cap guards against runaway length; a trailing abbreviation
  period is an acceptable cosmetic edge case for v1.
- **Ordering stability**: `list_dir` sorts by filename, so the endpoint
  is deterministic across runs — important for snapshot-style tests.
- **`adventure-report.md` double counting**: explicitly skipped in the
  reviews loop to avoid a “review” entry with no `task_id`.
