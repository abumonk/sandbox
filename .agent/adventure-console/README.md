# Adventure Console

A lightweight web UI for browsing and controlling Claudovka `team-pipeline`
adventures living in `.agent/adventures/`.

## Run

From the repo root (`R:/Sandbox`):

```bash
python .agent/adventure-console/server.py
```

The default bind is `http://127.0.0.1:7070`. Override with:

```bash
python .agent/adventure-console/server.py --host 0.0.0.0 --port 8080
```

Open the URL in any modern browser.

## What it does

**Sidebar** — each row shows a colored state badge + ID + title + one-line
subtitle (first sentence of the concept, truncated to ~80 chars). No task
counts, no file counts — those are one click away in the Overview tab.

**Main pane — tabs per adventure:**

| Tab | Purpose |
|-----|---------|
| Overview | Concept synopsis, target-condition progress bar, next-action card |
| Tasks | Grouped-by-status task cards; click to open the full task file |
| Documents | Unified browser for designs / plans / research / reviews with type-filter chips |
| Decisions | Pending approvals, state-transition controls, permissions status, knowledge-suggestion curation |

**State transitions** — controls for transitioning the adventure state
(e.g. `active → blocked / completed / cancelled`) live inside the
**Decisions** tab. Each click hits `POST /api/adventures/{id}/state` which
updates the manifest and appends a line to `adventure.log`.

## How the backend works

`server.py` is a stdlib-only Python HTTP server (no Flask/Django). It walks
`.agent/adventures/ADV-*/manifest.md`, parses YAML frontmatter, and exposes
a small REST-ish API:

| Method | Path | Body | Effect |
|--------|------|------|--------|
| GET | `/api/adventures` | — | Summary list |
| GET | `/api/adventures/{id}` | — | Full bundle |
| GET | `/api/adventures/{id}/documents` | — | Unified list of designs/plans/research/reviews with lightweight metadata |
| GET | `/api/file?path=<rel>` | — | Raw file text (guarded to repo-root) |
| POST | `/api/adventures/{id}/state` | `{new_state}` | Update manifest `state:` + log |
| POST | `/api/adventures/{id}/permissions/approve` | — | Set `permissions.md` `status: approved` + log |
| POST | `/api/adventures/{id}/design/approve` | `{design}` | Append approval note to `adventure.log` |
| POST | `/api/adventures/{id}/knowledge/apply` | `{indices: [int]}` | Write `reviews/knowledge-selection.json` |
| POST | `/api/adventures/{id}/log` | `{message}` | Append free-form log entry |

`GET /api/adventures/{id}` also returns a derived `summary` block with
`tc_total`, `tc_passed`, `tc_failed`, `tc_pending`, `tasks_by_status`, and a
`next_action` hint (`kind`, `label`, `state_hint`). These values are computed
on every request; nothing new is persisted to disk.

## Knowledge extraction

The **Decisions** tab parses the `## 6. Knowledge Extraction Suggestions`
section of `reviews/adventure-report.md` and renders each `### Suggestion N`
block as a checkbox.

Clicking **Record Selection** writes the chosen indices to
`reviews/knowledge-selection.json` — the agent workflow
(`/adventure-review` → `knowledge-extractor`) then applies them.

The console deliberately does *not* directly mutate `.agent/` knowledge
files; that is the extractor agent's job. The console just records the
user's curation intent.

## Safety

- `GET /api/file` resolves the path and refuses anything outside `REPO_ROOT`.
- POST endpoints mutate only a small allow-list of manifest fields and append
  to `adventure.log` — they never delete files.
- No authentication: intended for local use only. Do not expose to the
  network.

## Files

```
.agent/adventure-console/
├── server.py     # stdlib HTTP + API
├── index.html    # single-page UI (vanilla JS + marked.js via CDN)
└── README.md     # this file
```
