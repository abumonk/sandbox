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

**Sidebar** — lists every `ADV-###` under `.agent/adventures/` with a colored
state badge.

**Main pane — tabs per adventure:**

| Tab | Purpose |
|-----|---------|
| Overview | Concept, target-conditions table, state-transition buttons |
| Designs | Browse + render `designs/*.md`; per-file **Approve** button |
| Plans | Browse + render `plans/*.md` |
| Tasks | Sortable task list; click a row to read the full task file |
| Permissions | Show `permissions.md`; **Approve Permissions** button toggles status |
| Reviews | Task-level reviews + the synthesis `adventure-report.md` |
| Knowledge | Parses Section 6 of the adventure report — check suggestions, click **Record Selection** to save `knowledge-selection.json` |
| Research | `research/*.md` browser |
| Log | Tail of `adventure.log` |

**State transitions** — the header shows the buttons valid for the current
state (e.g. `active → blocked / completed / cancelled`). Each click hits
`POST /api/adventures/{id}/state` which updates the manifest and appends a
line to `adventure.log`.

## How the backend works

`server.py` is a stdlib-only Python HTTP server (no Flask/Django). It walks
`.agent/adventures/ADV-*/manifest.md`, parses YAML frontmatter, and exposes
a small REST-ish API:

| Method | Path | Body | Effect |
|--------|------|------|--------|
| GET | `/api/adventures` | — | Summary list |
| GET | `/api/adventures/{id}` | — | Full bundle |
| GET | `/api/file?path=<rel>` | — | Raw file text (guarded to repo-root) |
| POST | `/api/adventures/{id}/state` | `{new_state}` | Update manifest `state:` + log |
| POST | `/api/adventures/{id}/permissions/approve` | — | Set `permissions.md` `status: approved` + log |
| POST | `/api/adventures/{id}/design/approve` | `{design}` | Append approval note to `adventure.log` |
| POST | `/api/adventures/{id}/knowledge/apply` | `{indices: [int]}` | Write `reviews/knowledge-selection.json` |
| POST | `/api/adventures/{id}/log` | `{message}` | Append free-form log entry |

## Knowledge extraction

The **Knowledge** tab parses the `## 6. Knowledge Extraction Suggestions`
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
