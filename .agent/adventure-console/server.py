#!/usr/bin/env python3
"""Adventure Console — HTTP server.

Serves a small REST-ish API backed by the .agent/adventures/ tree plus the
index.html single-page UI.  Stdlib only.

Run from the repo root::

    python .agent/adventure-console/server.py            # default port 7070
    python .agent/adventure-console/server.py --port 8080

Endpoints
---------
GET  /                                         -> index.html
GET  /api/adventures                           -> list summary
GET  /api/adventures/{id}                      -> full state bundle
GET  /api/file?path=<relative-path>            -> raw file text
POST /api/adventures/{id}/state                -> body {new_state, actor?}
POST /api/adventures/{id}/permissions/approve  -> body {actor?}
POST /api/adventures/{id}/design/approve       -> body {design: <basename>, actor?}
POST /api/adventures/{id}/knowledge/apply      -> body {indices: [int], actor?}
POST /api/adventures/{id}/log                  -> body {actor, message}

All write endpoints append a line to <adventure>/adventure.log.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs


REPO_ROOT = Path(__file__).resolve().parents[2]      # R:/Sandbox
AGENT_DIR = REPO_ROOT / ".agent"
ADVENTURES_DIR = AGENT_DIR / "adventures"
CONSOLE_DIR = REPO_ROOT / ".agent" / "adventure-console"
INDEX_HTML = CONSOLE_DIR / "index.html"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Minimal YAML frontmatter parser (flat scalars + inline lists)."""
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    meta: dict = {}
    for line in fm_raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            items = [s.strip().strip('"').strip("'") for s in inner.split(",") if s.strip()]
            meta[key] = items
        elif val.lower() in ("true", "false"):
            meta[key] = val.lower() == "true"
        else:
            meta[key] = val.strip('"').strip("'")
    return meta, body


def safe_adventure_id(raw: str) -> str:
    if not re.fullmatch(r"ADV-\d{3}", raw):
        raise ValueError(f"invalid adventure id: {raw!r}")
    return raw


def adventure_path(adv_id: str) -> Path:
    return ADVENTURES_DIR / safe_adventure_id(adv_id)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def append_log(adv_id: str, actor: str, message: str) -> None:
    log_path = adventure_path(adv_id) / "adventure.log"
    line = f'[{now_iso()}] {actor} | "{message}"\n'
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line)


def list_dir(path: Path, suffix: str = ".md") -> list[str]:
    if not path.exists():
        return []
    return sorted(p.name for p in path.iterdir() if p.is_file() and p.name.endswith(suffix))


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------


def list_adventures() -> list[dict]:
    out = []
    if not ADVENTURES_DIR.exists():
        return out
    for entry in sorted(ADVENTURES_DIR.iterdir()):
        if not entry.is_dir() or not entry.name.startswith("ADV-"):
            continue
        manifest = entry / "manifest.md"
        if not manifest.exists():
            continue
        meta, _ = parse_frontmatter(read_text(manifest))
        tasks = meta.get("tasks") or []
        out.append({
            "id": meta.get("id", entry.name),
            "title": meta.get("title", entry.name),
            "state": meta.get("state", "unknown"),
            "created": meta.get("created", ""),
            "updated": meta.get("updated", ""),
            "task_count": len(tasks) if isinstance(tasks, list) else 0,
        })
    return out


def _target_conditions(body: str) -> list[dict]:
    """Parse the '## Target Conditions' markdown table from the manifest body."""
    lines = body.splitlines()
    rows = []
    in_table = False
    header_seen = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Target Conditions"):
            in_table = True
            header_seen = False
            continue
        if in_table and stripped.startswith("## "):
            break
        if in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not header_seen:
                header_seen = True
                continue
            if set("".join(cells)) <= set("-: "):
                continue
            if len(cells) >= 2:
                rows.append({
                    "id": cells[0] if len(cells) > 0 else "",
                    "description": cells[1] if len(cells) > 1 else "",
                    "source": cells[2] if len(cells) > 2 else "",
                    "design": cells[3] if len(cells) > 3 else "",
                    "plan": cells[4] if len(cells) > 4 else "",
                    "tasks": cells[5] if len(cells) > 5 else "",
                    "proof_method": cells[6] if len(cells) > 6 else "",
                    "proof_command": cells[7] if len(cells) > 7 else "",
                    "status": cells[8] if len(cells) > 8 else "",
                })
    return rows


def get_adventure(adv_id: str) -> dict:
    root = adventure_path(adv_id)
    if not root.exists():
        raise FileNotFoundError(f"adventure {adv_id} not found")

    manifest_text = read_text(root / "manifest.md")
    meta, body = parse_frontmatter(manifest_text)

    # Concept section
    concept = ""
    concept_match = re.search(r"^## Concept\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL | re.MULTILINE)
    if concept_match:
        concept = concept_match.group(1).strip()

    tcs = _target_conditions(body)

    # Tasks
    task_files = sorted((root / "tasks").glob("ADV*-T*.md")) if (root / "tasks").exists() else []
    tasks = []
    for tf in task_files:
        tmeta, _ = parse_frontmatter(read_text(tf))
        tasks.append({
            "id": tmeta.get("id", tf.stem),
            "title": tmeta.get("title", ""),
            "stage": tmeta.get("stage", ""),
            "status": tmeta.get("status", ""),
            "assignee": tmeta.get("assignee", ""),
            "iterations": tmeta.get("iterations", "0"),
            "depends_on": tmeta.get("depends_on") or [],
            "target_conditions": tmeta.get("target_conditions") or [],
            "file": str(tf.relative_to(REPO_ROOT)).replace("\\", "/"),
        })

    # Designs / plans / schemas / roles / tests
    designs = list_dir(root / "designs")
    plans = list_dir(root / "plans")
    schemas = list_dir(root / "schemas")
    roles = list_dir(root / "roles")
    tests = list_dir(root / "tests")
    research = list_dir(root / "research")

    # Reviews
    reviews = []
    reviews_dir = root / "reviews"
    if reviews_dir.exists():
        for rf in sorted(reviews_dir.iterdir()):
            if not rf.is_file() or not rf.name.endswith(".md"):
                continue
            rmeta, _ = parse_frontmatter(read_text(rf))
            reviews.append({
                "file": rf.name,
                "task_id": rmeta.get("task_id", rf.stem.replace("-review", "")),
                "status": rmeta.get("status", ""),
                "build_result": rmeta.get("build_result", ""),
                "test_result": rmeta.get("test_result", ""),
            })

    # Permissions
    permissions_file = root / "permissions.md"
    permissions = None
    if permissions_file.exists():
        pmeta, _ = parse_frontmatter(read_text(permissions_file))
        permissions = {
            "status": pmeta.get("status", "draft"),
            "approved": pmeta.get("approved", ""),
            "file": str(permissions_file.relative_to(REPO_ROOT)).replace("\\", "/"),
        }

    # Adventure report (post-review)
    adventure_report = None
    report_path = reviews_dir / "adventure-report.md" if reviews_dir.exists() else None
    if report_path and report_path.exists():
        adventure_report = {
            "file": str(report_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        }

    # Log tail
    log_path = root / "adventure.log"
    log_tail = []
    if log_path.exists():
        log_tail = read_text(log_path).splitlines()[-40:]

    return {
        "id": meta.get("id", adv_id),
        "title": meta.get("title", ""),
        "state": meta.get("state", "unknown"),
        "created": meta.get("created", ""),
        "updated": meta.get("updated", ""),
        "tasks_list": meta.get("tasks") or [],
        "concept": concept,
        "target_conditions": tcs,
        "tasks": tasks,
        "designs": designs,
        "plans": plans,
        "schemas": schemas,
        "roles": roles,
        "tests": tests,
        "research": research,
        "reviews": reviews,
        "permissions": permissions,
        "adventure_report": adventure_report,
        "log_tail": log_tail,
    }


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


VALID_STATES = {"concept", "planning", "review", "active", "blocked", "completed", "cancelled"}


def update_state(adv_id: str, new_state: str, actor: str) -> dict:
    if new_state not in VALID_STATES:
        raise ValueError(f"invalid state: {new_state}")
    manifest_path = adventure_path(adv_id) / "manifest.md"
    text = read_text(manifest_path)
    meta, body = parse_frontmatter(text)
    old_state = meta.get("state", "unknown")
    if old_state == new_state:
        return {"ok": True, "old_state": old_state, "new_state": new_state, "noop": True}

    # Reconstruct the frontmatter preserving order
    new_fm_lines = []
    fm_match = _FM_RE.match(text)
    fm_raw = fm_match.group(1) if fm_match else ""
    for line in fm_raw.splitlines():
        if line.lstrip().startswith("state:"):
            new_fm_lines.append(f"state: {new_state}")
        elif line.lstrip().startswith("updated:"):
            new_fm_lines.append(f"updated: {now_iso()}")
        else:
            new_fm_lines.append(line)
    # Ensure updated present
    if not any(l.lstrip().startswith("updated:") for l in new_fm_lines):
        new_fm_lines.append(f"updated: {now_iso()}")
    new_text = "---\n" + "\n".join(new_fm_lines) + "\n---\n" + body
    write_text(manifest_path, new_text)
    append_log(adv_id, actor or "console", f"state: {old_state} -> {new_state}")
    return {"ok": True, "old_state": old_state, "new_state": new_state}


def approve_permissions(adv_id: str, actor: str) -> dict:
    perm_path = adventure_path(adv_id) / "permissions.md"
    if not perm_path.exists():
        raise FileNotFoundError("permissions.md not found")
    text = read_text(perm_path)
    fm_match = _FM_RE.match(text)
    if not fm_match:
        raise ValueError("permissions.md has no frontmatter")
    fm_raw = fm_match.group(1)
    body = fm_match.group(2)
    new_fm_lines = []
    saw_status = False
    saw_approved = False
    for line in fm_raw.splitlines():
        if line.lstrip().startswith("status:"):
            new_fm_lines.append("status: approved")
            saw_status = True
        elif line.lstrip().startswith("approved:"):
            new_fm_lines.append(f"approved: {now_iso()}")
            saw_approved = True
        else:
            new_fm_lines.append(line)
    if not saw_status:
        new_fm_lines.append("status: approved")
    if not saw_approved:
        new_fm_lines.append(f"approved: {now_iso()}")
    write_text(perm_path, "---\n" + "\n".join(new_fm_lines) + "\n---\n" + body)
    append_log(adv_id, actor or "console", "permissions approved via console")
    return {"ok": True}


def approve_design(adv_id: str, design: str, actor: str) -> dict:
    design_path = adventure_path(adv_id) / "designs" / design
    if not design_path.exists():
        raise FileNotFoundError(f"design {design!r} not found")
    # Append approval stamp as a HTML-comment line (idempotent)
    text = read_text(design_path)
    stamp = f"<!-- approved: {actor or 'console'} @ {now_iso()} -->"
    if stamp.split(" @ ")[0] in text:
        return {"ok": True, "noop": True}
    if text.endswith("\n"):
        text += stamp + "\n"
    else:
        text += "\n" + stamp + "\n"
    write_text(design_path, text)
    append_log(adv_id, actor or "console", f"design approved: {design}")
    return {"ok": True}


def record_knowledge_selection(adv_id: str, indices: list[int], actor: str) -> dict:
    """Record selection in a decisions json for later manual pickup."""
    decisions_path = adventure_path(adv_id) / "reviews" / "knowledge-selection.json"
    payload = {
        "adventure_id": adv_id,
        "selected_indices": sorted(set(int(i) for i in indices)),
        "recorded_by": actor or "console",
        "recorded_at": now_iso(),
        "note": "To apply: /team-pipeline:adventure-review (or invoke knowledge-extractor with these indices).",
    }
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(decisions_path, json.dumps(payload, indent=2))
    append_log(adv_id, actor or "console",
               f"knowledge selection recorded: indices={payload['selected_indices']}")
    return {"ok": True, "selection": payload}


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):    # quiet default access log
        sys.stderr.write("[" + self.log_date_time_string() + "] " + (format % args) + "\n")

    # -- helpers ------------------------------------------------------------

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: int, text: str, content_type: str = "text/plain; charset=utf-8") -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        if not raw.strip():
            return {}
        return json.loads(raw)

    # -- routing ------------------------------------------------------------

    def do_GET(self) -> None:                  # noqa: N802
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if path in ("/", "/index.html"):
                self._send_text(200, read_text(INDEX_HTML), "text/html; charset=utf-8")
                return

            if path == "/api/adventures":
                self._send_json(200, list_adventures())
                return

            m = re.fullmatch(r"/api/adventures/(ADV-\d{3})", path)
            if m:
                self._send_json(200, get_adventure(m.group(1)))
                return

            if path == "/api/file":
                rel = (query.get("path", [""]) or [""])[0]
                safe = (REPO_ROOT / rel).resolve()
                if REPO_ROOT.resolve() not in safe.parents and safe != REPO_ROOT.resolve():
                    self._send_json(400, {"error": "path outside repo"})
                    return
                if not safe.exists() or not safe.is_file():
                    self._send_json(404, {"error": f"not found: {rel}"})
                    return
                self._send_text(200, safe.read_text(encoding="utf-8", errors="replace"))
                return

            self._send_json(404, {"error": f"no route: {path}"})
        except FileNotFoundError as e:
            self._send_json(404, {"error": str(e)})
        except Exception as e:                 # noqa: BLE001
            traceback.print_exc()
            self._send_json(500, {"error": str(e), "trace": traceback.format_exc()})

    def do_POST(self) -> None:                 # noqa: N802
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            body = self._read_json_body()
            actor = body.get("actor") or "console"

            m = re.fullmatch(r"/api/adventures/(ADV-\d{3})/state", path)
            if m:
                self._send_json(200, update_state(m.group(1), body.get("new_state", ""), actor))
                return

            m = re.fullmatch(r"/api/adventures/(ADV-\d{3})/permissions/approve", path)
            if m:
                self._send_json(200, approve_permissions(m.group(1), actor))
                return

            m = re.fullmatch(r"/api/adventures/(ADV-\d{3})/design/approve", path)
            if m:
                self._send_json(200, approve_design(m.group(1), body.get("design", ""), actor))
                return

            m = re.fullmatch(r"/api/adventures/(ADV-\d{3})/knowledge/apply", path)
            if m:
                self._send_json(200, record_knowledge_selection(m.group(1), body.get("indices", []), actor))
                return

            m = re.fullmatch(r"/api/adventures/(ADV-\d{3})/log", path)
            if m:
                append_log(m.group(1), actor, body.get("message", ""))
                self._send_json(200, {"ok": True})
                return

            self._send_json(404, {"error": f"no route: {path}"})
        except FileNotFoundError as e:
            self._send_json(404, {"error": str(e)})
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
        except Exception as e:                 # noqa: BLE001
            traceback.print_exc()
            self._send_json(500, {"error": str(e), "trace": traceback.format_exc()})


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7070)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    if not INDEX_HTML.exists():
        print(f"ERROR: {INDEX_HTML} not found", file=sys.stderr)
        return 1

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Adventure Console running at {url}  (Ctrl-C to stop)")
    print(f"  REPO_ROOT       = {REPO_ROOT}")
    print(f"  ADVENTURES_DIR  = {ADVENTURES_DIR}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
