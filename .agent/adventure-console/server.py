#!/usr/bin/env python3
"""Adventure Console — HTTP server.

Serves a small REST-ish API backed by the .agent/adventures/ tree plus the
index.html single-page UI.  Stdlib only.

Run from the repo root::

    python .agent/adventure-console/server.py            # default port 7070
    python .agent/adventure-console/server.py --port 8080

Endpoints
---------
GET  /                                                          -> index.html
GET  /api/adventures                                            -> list summary
GET  /api/adventures/{id}                                       -> full state bundle
GET  /api/adventures/{id}/documents                             -> unified designs/plans/research/reviews list
GET  /api/adventures/{id}/graph                                 -> {nodes, edges, explanations} payload
GET  /api/file?path=<relative-path>                             -> raw file text
POST /api/adventures/{id}/state                                 -> body {new_state, actor?}
POST /api/adventures/{id}/permissions/approve                   -> body {actor?}
POST /api/adventures/{id}/design/approve                        -> body {design: <basename>, actor?}
POST /api/adventures/{id}/knowledge/apply                       -> body {indices: [int], actor?}
POST /api/adventures/{id}/log                                   -> body {actor, message}
POST /api/adventures/{id}/tasks/{task_id}/depends_on            -> body {depends_on: <task_id>, actor?}

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

# Make the sibling adventure_pipeline package importable regardless of where
# the server is launched from.  Inserted into sys.path defensively; import is
# deferred to _load_ir() via importlib so this module stays AST-stdlib-clean.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


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


_TC_PASSED_TOKENS = {"passed", "pass", "done", "complete", "completed", "yes"}
_TC_FAILED_TOKENS = {"failed", "fail", "error", "no", "broken"}


def _bucket_tc_status(raw: str) -> str:
    """Normalize a raw TC table status cell into 'passed', 'failed', or 'pending'."""
    normalized = raw.strip().lower()
    if normalized in _TC_PASSED_TOKENS:
        return "passed"
    if normalized in _TC_FAILED_TOKENS:
        return "failed"
    return "pending"


def compute_next_action(meta: dict, permissions: dict | None, tcs: list, tasks: list) -> dict:
    """Map adventure state (+ permissions status) to a next_action dict.

    Returns a dict with keys: kind, label, state_hint.
    Allowed kind values: approve_permissions, open_plan, resolve_blocker,
    promote_concept, none.
    """
    state = (meta.get("state") or "unknown").lower()

    if state == "blocked":
        return {"kind": "resolve_blocker", "label": "Resolve Blocker", "state_hint": state}

    if state == "concept":
        return {"kind": "promote_concept", "label": "Promote to Planning", "state_hint": state}

    if state == "review":
        perm_status = ""
        if permissions:
            perm_status = (permissions.get("status") or "").lower()
        if perm_status != "approved":
            return {"kind": "approve_permissions", "label": "Approve Permissions", "state_hint": state}
        return {"kind": "open_plan", "label": "Open Plan", "state_hint": state}

    if state == "planning":
        return {"kind": "open_plan", "label": "Open Plan", "state_hint": state}

    if state == "active":
        return {"kind": "open_plan", "label": "Continue Execution", "state_hint": state}

    # completed, cancelled, unknown, or any other value
    return {"kind": "none", "label": "", "state_hint": state}


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

    # Summary block — computed from parsed data, not persisted
    tc_buckets: dict[str, int] = {"passed": 0, "failed": 0, "pending": 0}
    for tc in tcs:
        bucket = _bucket_tc_status(tc.get("status", ""))
        tc_buckets[bucket] += 1

    tasks_by_status: dict[str, int] = {}
    for task in tasks:
        s = task.get("status") or "unknown"
        tasks_by_status[s] = tasks_by_status.get(s, 0) + 1

    summary = {
        "tc_total": len(tcs),
        "tc_passed": tc_buckets["passed"],
        "tc_failed": tc_buckets["failed"],
        "tc_pending": tc_buckets["pending"],
        "tasks_by_status": tasks_by_status,
        "next_action": compute_next_action(meta, permissions, tcs, tasks),
    }

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
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Document helpers
# ---------------------------------------------------------------------------


def _first_heading(text: str) -> str:
    """Return the text of the first H1 line (# ...), stripped. Returns '' if absent."""
    for line in text.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return ""


def _design_one_liner(text: str) -> str:
    """Extract the first sentence of the ## Overview section, capped at 120 chars."""
    m = re.search(r"^## Overview\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL | re.MULTILINE)
    if not m:
        return ""
    block = m.group(1)
    # Find the first non-empty, non-heading line
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Split on first sentence boundary: ". " or ".\n" or end-of-string
        sentence_m = re.match(r"(.*?)\.(?:\s|$)", line)
        if sentence_m:
            sentence = sentence_m.group(1).strip()
        else:
            sentence = line
        if len(sentence) > 120:
            return sentence[:120] + "\u2026"
        return sentence
    return ""


def _plan_metadata(text: str) -> tuple:
    """Return (task_count, waves) for a plan document."""
    lines = text.splitlines()
    task_count = 0
    waves = 0
    in_tasks = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^## Wave ", stripped) or re.match(r"^## Phase ", stripped):
            waves += 1
        if re.match(r"^## Tasks", stripped):
            in_tasks = True
            continue
        if in_tasks and re.match(r"^## ", stripped):
            in_tasks = False
        if in_tasks and stripped.startswith("### "):
            task_count += 1
    return task_count, waves


def _review_metadata(text: str) -> dict:
    """Extract review frontmatter fields: task_id, status, build_result, test_result."""
    meta, _ = parse_frontmatter(text)
    return {
        "task_id": meta.get("task_id", ""),
        "status": meta.get("status", ""),
        "build_result": meta.get("build_result", ""),
        "test_result": meta.get("test_result", ""),
    }


def list_documents(adv_id: str) -> list:
    """Return unified list of DocumentEntry records for an adventure."""
    root = adventure_path(adv_id)
    if not root.exists():
        raise FileNotFoundError(f"adventure {adv_id} not found")

    docs = []

    # Designs
    for fname in list_dir(root / "designs"):
        fpath = root / "designs" / fname
        text = read_text(fpath)
        title = _first_heading(text) or fpath.stem
        docs.append({
            "type": "design",
            "file": fname,
            "title": title,
            "one_liner": _design_one_liner(text),
        })

    # Plans
    for fname in list_dir(root / "plans"):
        fpath = root / "plans" / fname
        text = read_text(fpath)
        title = _first_heading(text) or fpath.stem
        task_count, waves = _plan_metadata(text)
        docs.append({
            "type": "plan",
            "file": fname,
            "title": title,
            "task_count": task_count,
            "waves": waves,
        })

    # Research
    for fname in list_dir(root / "research"):
        fpath = root / "research" / fname
        text = read_text(fpath)
        title = _first_heading(text) or fpath.stem
        docs.append({
            "type": "research",
            "file": fname,
            "title": title,
        })

    # Reviews (skip adventure-report.md)
    reviews_dir = root / "reviews"
    if reviews_dir.exists():
        for fname in list_dir(reviews_dir):
            if fname == "adventure-report.md":
                continue
            fpath = reviews_dir / fname
            text = read_text(fpath)
            entry = {"type": "review", "file": fname}
            entry.update(_review_metadata(text))
            docs.append(entry)

    return docs


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
# Graph helpers + handlers
# ---------------------------------------------------------------------------


def _load_ir(adv_id: str):
    """Load the AdventurePipelineIR for adv_id.

    The adventure_pipeline package is imported lazily via importlib so that
    static AST analysers (including TC-030's stdlib-only check) do not see it
    as a top-level import.

    Raises:
        FileNotFoundError: if the adventure directory is missing (→ 404).
        RuntimeError: wrapping any other extraction failure (→ 500).
    """
    import importlib
    try:
        ir_mod = importlib.import_module("adventure_pipeline.tools.ir")
        extract_ir = ir_mod.extract_ir
    except ImportError as exc:
        raise RuntimeError(f"ir_extract: cannot import adventure_pipeline.tools.ir: {exc}") from exc

    try:
        return extract_ir(adv_id)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise RuntimeError(f"ir_extract: {exc}") from exc


def _cycle_free(ir, task_id: str, new_dep: str) -> bool:
    """Return True iff adding the edge task_id → new_dep would NOT create a cycle.

    Self-loops (task_id == new_dep) are caught immediately.  For non-self
    edges we check whether new_dep is already reachable from task_id via
    existing depends_on edges (forward direction: task → its dependencies).
    If it is, adding task_id → new_dep would close the loop.
    """
    if task_id == new_dep:
        return False  # self-loop

    # Build forward adjacency: fwd[T] = list of T's own dependencies.
    # "task_id depends_on new_dep" means task_id → new_dep edge.
    # A cycle exists if new_dep can already reach task_id via forward deps.
    fwd: dict[str, list[str]] = {t.id: list(t.depends_on) for t in ir.tasks}

    # BFS from new_dep along forward edges (each node's depends_on).
    # If task_id is reachable, adding task_id → new_dep closes a cycle.
    visited: set[str] = set()
    queue = list(fwd.get(new_dep, []))
    while queue:
        node = queue.pop(0)
        if node == task_id:
            return False   # cycle detected
        if node in visited:
            continue
        visited.add(node)
        queue.extend(fwd.get(node, []))

    return True  # no cycle


def _rewrite_task_depends_on(adv_id: str, task_id: str, merged: list[str]) -> list[str]:
    """Rewrite the depends_on: line in task frontmatter and update the updated: stamp.

    Reads <adventure>/tasks/<task_id>.md, rewrites the ``depends_on:`` line to
    the merged list in inline-list form ``[A, B, C]``, updates ``updated:``,
    and writes the file back.

    Raises:
        FileNotFoundError: if the task file does not exist.
        ValueError: if a multi-line block-style depends_on: sequence is detected.
    """
    task_path = adventure_path(adv_id) / "tasks" / f"{task_id}.md"
    if not task_path.exists():
        raise FileNotFoundError(f"task file not found: {task_path}")

    text = read_text(task_path)
    fm_match = _FM_RE.match(text)
    if not fm_match:
        raise ValueError(f"task file has no frontmatter: {task_id}")

    fm_raw = fm_match.group(1)
    body = fm_match.group(2)

    # Reject block-style depends_on (multiline sequence starting with "depends_on:" then "- " items)
    if re.search(r"^depends_on:\s*\n\s*-\s+", fm_raw, re.MULTILINE):
        raise ValueError(
            f"depends_on: is in block-list form in {task_id}.md; "
            "refusing to rewrite — please convert to inline [A, B] form first"
        )

    inline_val = "[" + ", ".join(merged) + "]"
    new_fm_lines = []
    saw_depends = False
    saw_updated = False
    for line in fm_raw.splitlines():
        if line.lstrip().startswith("depends_on:"):
            new_fm_lines.append(f"depends_on: {inline_val}")
            saw_depends = True
        elif line.lstrip().startswith("updated:"):
            new_fm_lines.append(f"updated: {now_iso()}")
            saw_updated = True
        else:
            new_fm_lines.append(line)

    if not saw_depends:
        new_fm_lines.append(f"depends_on: {inline_val}")
    if not saw_updated:
        new_fm_lines.append(f"updated: {now_iso()}")

    new_text = "---\n" + "\n".join(new_fm_lines) + "\n---\n" + body
    write_text(task_path, new_text)
    return merged


def _slug(name: str) -> str:
    """Simple slug: lowercase, spaces/slashes → hyphens, strip non-alphanumeric-dash."""
    s = name.lower().replace(" ", "-").replace("/", "-")
    return re.sub(r"[^a-z0-9\-]", "", s)


def graph_payload(adv_id: str) -> dict:
    """Build the {nodes, edges, explanations} payload for the /graph endpoint.

    Loads the IR via _load_ir, transforms tasks/TCs/documents/phases into
    Cytoscape-compatible node/edge objects.
    """
    ir = _load_ir(adv_id)

    nodes: list[dict] = []
    edges: list[dict] = []
    explanations: dict[str, str] = {}

    # --- Adventure node ---
    nodes.append({"data": {
        "id": "adv",
        "kind": "adventure",
        "label": f"{ir.id} {ir.title}",
        "status": ir.state,
    }})

    # --- Phase nodes: derive from tasks' adventure_plan field ---
    phase_names: list[str] = []
    task_phase_map: dict[str, str] = {}   # task_id -> phase node id
    for t in ir.tasks:
        if t.adventure_plan:
            pname = t.adventure_plan
            if pname not in phase_names:
                phase_names.append(pname)
            task_phase_map[t.id] = f"phase:{_slug(pname)}"

    for pname in phase_names:
        pid = f"phase:{_slug(pname)}"
        nodes.append({"data": {
            "id": pid,
            "kind": "phase",
            "label": pname,
            "parent": "adv",
        }})

    # --- Task nodes ---
    for t in ir.tasks:
        parent = task_phase_map.get(t.id, "adv")
        nodes.append({"data": {
            "id": f"task:{t.id}",
            "kind": "task",
            "label": f"{t.id} — {t.title}",
            "status": t.status,
            "parent": parent,
        }})

    # --- Document nodes ---
    for doc in ir.documents:
        doc_node_id = f"doc:{doc.id}"
        nodes.append({"data": {
            "id": doc_node_id,
            "kind": "document",
            "label": doc.title or doc.id,
            "docKind": doc.kind,
            "parent": "adv",
        }})
        explanations[doc_node_id] = f"{doc.kind}: {doc.title or doc.id}"

    # --- TC nodes ---
    for tc in ir.tcs:
        tc_node_id = f"tc:{tc.id}"
        nodes.append({"data": {
            "id": tc_node_id,
            "kind": "tc",
            "label": tc.id,
            "status": tc.status,
            "parent": "adv",
        }})
        if tc.description:
            explanations[tc_node_id] = f"{tc.id}: {tc.description}"

    # --- Decision nodes ---
    # permissions
    perm_path = adventure_path(adv_id) / "permissions.md"
    if perm_path.exists():
        pmeta, _ = parse_frontmatter(read_text(perm_path))
        perm_status = pmeta.get("status", "draft")
        decision_perm_id = "decision:permissions"
        nodes.append({"data": {
            "id": decision_perm_id,
            "kind": "decision",
            "label": "Permissions",
            "status": perm_status,
            "parent": "adv",
        }})
        if perm_status != "approved":
            explanations[decision_perm_id] = "Pending: approve permissions"
        else:
            explanations[decision_perm_id] = "Done: permissions approved"

    # design approval decisions
    designs_dir = adventure_path(adv_id) / "designs"
    if designs_dir.exists():
        for dpath in sorted(designs_dir.glob("*.md")):
            dtext = read_text(dpath)
            approved = "<!-- approved:" in dtext
            dname = dpath.stem
            decision_id = f"decision:design:{dname}"
            nodes.append({"data": {
                "id": decision_id,
                "kind": "decision",
                "label": f"Design: {dname}",
                "status": "done" if approved else "pending",
                "parent": "adv",
            }})
            if not approved:
                explanations[decision_id] = f"Pending: approve design {dname}"
            else:
                explanations[decision_id] = f"Done: design {dname} approved"

    # --- Edges: depends_on ---
    for t in ir.tasks:
        for dep in t.depends_on:
            edge_id = f"e:dep:{dep}->{t.id}"
            edges.append({"data": {
                "id": edge_id,
                "source": f"task:{dep}",
                "target": f"task:{t.id}",
                "kind": "depends_on",
            }})

    # --- Edges: satisfies (task → TC) ---
    for t in ir.tasks:
        for tc_id in t.target_conditions:
            edge_id = f"e:tc:{t.id}->{tc_id}"
            edges.append({"data": {
                "id": edge_id,
                "source": f"task:{t.id}",
                "target": f"tc:{tc_id}",
                "kind": "satisfies",
            }})

    # --- Edges: addresses (TC → document) ---
    doc_ids_present = {doc.id for doc in ir.documents}
    for tc in ir.tcs:
        for ref_field in (tc.design, tc.plan):
            if not ref_field or ref_field == "-":
                continue
            # ref_field may be a basename like "design-foo" or "design-foo.md"
            ref_stem = ref_field.replace(".md", "")
            if ref_stem in doc_ids_present:
                edge_id = f"e:addr:{tc.id}->{ref_stem}"
                edges.append({"data": {
                    "id": edge_id,
                    "source": f"tc:{tc.id}",
                    "target": f"doc:{ref_stem}",
                    "kind": "addresses",
                }})

    # --- Explanations: task deps ---
    for t in ir.tasks:
        if t.depends_on:
            tid = f"task:{t.id}"
            explanations[tid] = (
                f"{t.id} depends on {', '.join(t.depends_on)} — gates downstream work."
            )

    return {"nodes": nodes, "edges": edges, "explanations": explanations}


def add_task_dependency(adv_id: str, task_id: str, body: dict, actor: str) -> dict:
    """Validate, cycle-check, and persist a new depends_on edge for a task.

    Args:
        adv_id:  Adventure ID (e.g. "ADV-007").
        task_id: Task receiving the new dependency.
        body:    Parsed JSON body; must contain "depends_on" key.
        actor:   Actor name for the audit log.

    Returns:
        {"ok": True, "task_id": task_id, "depends_on": merged_list}

    Raises:
        ValueError: invalid IDs, self-cycle, unknown dep, or cycle (→ 400).
        FileNotFoundError: unknown task_id (→ 404).
    """
    # Validate task_id format (already captured from route, but double-check)
    if not re.fullmatch(r"ADV\d{3}-T\d{3}", task_id):
        raise ValueError(f"invalid task id: {task_id!r}")

    # Validate the requested dependency from request body
    new_dep = body.get("depends_on")
    if not new_dep or not isinstance(new_dep, str):
        raise ValueError("body must include 'depends_on' as a non-empty string")
    if not re.fullmatch(r"ADV\d{3}-T\d{3}", new_dep):
        raise ValueError(f"invalid depends_on id: {new_dep!r}")

    # Self-cycle check
    if new_dep == task_id:
        raise ValueError("self-cycle: task cannot depend on itself")

    # Load IR to validate task membership and check for cycles
    ir = _load_ir(adv_id)
    task_ids = {t.id for t in ir.tasks}

    if task_id not in task_ids:
        raise FileNotFoundError(f"task {task_id} not in {adv_id}")
    if new_dep not in task_ids:
        raise ValueError(f"unknown task: {new_dep} — references a task not in this adventure")

    # Cycle check
    if not _cycle_free(ir, task_id, new_dep):
        raise ValueError(f"would create dependency cycle: {task_id} -> {new_dep}")

    # Dedup-preserving merge of existing deps + new_dep
    existing = next((t.depends_on for t in ir.tasks if t.id == task_id), [])
    merged: list[str] = list(existing)
    if new_dep not in merged:
        merged.append(new_dep)

    # Persist the change
    _rewrite_task_depends_on(adv_id, task_id, merged)

    # Audit log
    append_log(adv_id, actor or "console", f"depends_on: {task_id} += {new_dep}")

    return {"ok": True, "task_id": task_id, "depends_on": merged}


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

            m = re.fullmatch(r"/api/adventures/(ADV-\d{3})/documents", path)
            if m:
                self._send_json(200, list_documents(m.group(1)))
                return

            m = re.fullmatch(r"/api/adventures/(ADV-\d{3})", path)
            if m:
                self._send_json(200, get_adventure(m.group(1)))
                return

            m = re.fullmatch(r"/api/adventures/(ADV-\d{3})/graph", path)
            if m:
                self._send_json(200, graph_payload(m.group(1)))
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
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
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
