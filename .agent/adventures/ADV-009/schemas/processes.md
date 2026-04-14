# Processes — ADV-009

## Processes

### Render v2 console page
1. Browser GETs `/` → server sends `index.html`.
2. On load, `App.refreshList()` calls `/api/adventures` and populates the
   sidebar (unchanged from v1).
3. User clicks an adventure row → `App.open(id)` fetches
   `/api/adventures/{id}` and renders header + four tabs.
4. Tab dispatcher invokes one of `renderOverview`, `renderTasks`,
   `renderDocuments`, `renderDecisions`.

Error paths:
- Fetch failure → toast with error + sidebar-level empty state.
- Missing `summary` block (old server build) → fall back to client-side
  TC aggregation.

### Render Documents tab
1. First open: call `/api/adventures/{id}/documents` (cached per adventure).
2. Render chip bar (All / Designs / Plans / Research / Reviews).
3. Render unified list filtered by active chip (default: All).
4. Row click → fetch raw file via `/api/file?path=...` and dispatch to the
   type-specific renderer.

Error paths:
- New endpoint 404 (legacy server) → fall back to concatenating
  `a.designs/plans/research/reviews` arrays.

### Compute next action (server)
1. If `adventure.state == "review"` and permissions unapproved →
   `approve_permissions`.
2. If `adventure.state == "planning"` → `open_plan`.
3. If `adventure.state == "blocked"` → `resolve_blocker`.
4. If `adventure.state == "concept"` → `promote_concept`.
5. If `adventure.state == "active"` → `open_tasks`.
6. If `adventure.state == "completed"` → `read_report`.
7. Else `none`.

Error paths: if the permissions file is malformed, fall back to `open_plan`
for the `review` state and log a server-side warning.

### Approve permissions from Decisions card
1. User clicks "Approve Permissions" in Decisions card.
2. Frontend POSTs `/api/adventures/{id}/permissions/approve`.
3. Server flips frontmatter `status: approved`, appends log line.
4. Frontend refetches `/api/adventures/{id}` and re-renders.

Error paths: existing error-toast flow from v1 (unchanged).

### Run v2 test suite
1. `python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"`
2. Tier-1 tests import helpers from `.agent/adventure-console/server.py`
   or spin a threading server on a random port.
3. Tier-2 tests read `index.html` from disk and parse with stdlib.
4. Tier-3 tests import `playwright.sync_api`; on ImportError the whole
   module is skipped.
5. Exit code 0 iff all non-skipped tests pass.
