"""ir.py — Extract an AdventurePipelineIR from a live adventure directory.

Reads a .agent/adventures/ADV-NNN/ directory — manifest frontmatter, the
Target Conditions markdown table, tasks/, designs/, plans/, research/,
reviews/, and permissions.md — and returns a populated AdventurePipelineIR
dataclass whose shape mirrors the Ark entity declarations in
adventure_pipeline/specs/adventure.ark.

Stdlib only: dataclasses, json, pathlib, re, argparse, sys.

CLI:
    python -m adventure_pipeline.tools ADV-NNN
    python -m adventure_pipeline.tools ADV-NNN --adventures-root /some/path
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Repo-relative path resolution
# ---------------------------------------------------------------------------

# adventure_pipeline/tools/ir.py  ->  parents[2] = repo root (R:/Sandbox/)
_PKG_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_ADVENTURES_ROOT = _PKG_ROOT / ".agent" / "adventures"


# ---------------------------------------------------------------------------
# IR dataclasses  (mirror specs/adventure.ark entity shapes)
# ---------------------------------------------------------------------------


@dataclass
class Task:
    id: str
    title: str
    stage: str
    status: str
    assignee: str
    iterations: int
    depends_on: list[str] = field(default_factory=list)
    target_conditions: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    adventure_id: str = ""
    adventure_plan: str = ""
    role: str = ""


@dataclass
class Document:
    """id, kind (design|plan|research|review), path (repo-relative), title."""
    id: str
    kind: str
    path: str
    title: str


@dataclass
class TargetCondition:
    id: str
    description: str
    source: str
    design: str
    plan: str
    tasks: list[str] = field(default_factory=list)
    proof_method: str = ""
    proof_command: str = ""
    status: str = ""


@dataclass
class Decision:
    """Reserved for future use — populated once an adventure emits decisions."""
    kind: str
    label: str
    state_hint: str
    route: str


@dataclass
class Permission:
    category: str   # "shell" | "file" | "mcp" | "external"
    agent: str
    scope: str
    reason: str
    tasks: list[str] = field(default_factory=list)


@dataclass
class Agent:
    name: str
    role: str
    permissions: list[str] = field(default_factory=list)


@dataclass
class Role:
    name: str


@dataclass
class AdventurePipelineIR:
    id: str
    title: str
    state: str
    created: str
    updated: str
    concept: str
    tasks_list: list[str] = field(default_factory=list)   # from manifest frontmatter
    tasks: list[Task] = field(default_factory=list)
    documents: list[Document] = field(default_factory=list)
    tcs: list[TargetCondition] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    permissions: list[Permission] = field(default_factory=list)
    agents: list[Agent] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    log_tail: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Frontmatter parser  (lifted from .agent/adventure-console/server.py)
# ---------------------------------------------------------------------------

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Minimal YAML frontmatter parser (flat scalars + inline lists).

    Behaviour is intentionally identical to server.py::parse_frontmatter to
    avoid parse divergence.
    """
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


# ---------------------------------------------------------------------------
# Target-condition table parser  (mirrors server.py::_target_conditions)
# ---------------------------------------------------------------------------


def _parse_tc_table(body: str) -> list[TargetCondition]:
    """Parse the '## Target Conditions' markdown table from the manifest body."""
    lines = body.splitlines()
    rows: list[TargetCondition] = []
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
            if len(cells) < 2:
                continue
            # tasks column (index 5) may contain comma-separated ids
            raw_tasks = cells[5] if len(cells) > 5 else ""
            task_ids = [t.strip() for t in raw_tasks.split(",") if t.strip()]
            rows.append(TargetCondition(
                id=cells[0] if len(cells) > 0 else "",
                description=cells[1] if len(cells) > 1 else "",
                source=cells[2] if len(cells) > 2 else "",
                design=cells[3] if len(cells) > 3 else "",
                plan=cells[4] if len(cells) > 4 else "",
                tasks=task_ids,
                proof_method=cells[6] if len(cells) > 6 else "",
                proof_command=cells[7] if len(cells) > 7 else "",
                status=cells[8] if len(cells) > 8 else "",
            ))
    return rows


# ---------------------------------------------------------------------------
# Concept extractor
# ---------------------------------------------------------------------------


def _extract_concept(body: str) -> str:
    m = re.search(r"^## Concept\s*\n(.*?)(?=\n## |\Z)", body, re.DOTALL | re.MULTILINE)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# First-heading helper  (for docs without frontmatter)
# ---------------------------------------------------------------------------


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return ""


# ---------------------------------------------------------------------------
# Task loader
# ---------------------------------------------------------------------------


def _load_task(path: Path) -> Task:
    text = path.read_text(encoding="utf-8")
    m, _ = parse_frontmatter(text)
    raw_iter = m.get("iterations", "0")
    try:
        iterations = int(str(raw_iter))
    except (ValueError, TypeError):
        iterations = 0
    assignee = m.get("assignee", "")
    return Task(
        id=m.get("id", path.stem),
        title=m.get("title", ""),
        stage=m.get("stage", ""),
        status=m.get("status", ""),
        assignee=assignee,
        iterations=iterations,
        depends_on=m.get("depends_on") or [],
        target_conditions=m.get("target_conditions") or [],
        files=m.get("files") or [],
        tags=m.get("tags") or [],
        adventure_id=m.get("adventure_id", ""),
        adventure_plan=m.get("adventure_plan", ""),
        role=m.get("role", assignee),
    )


# ---------------------------------------------------------------------------
# Document loader
# ---------------------------------------------------------------------------

_SUBDIR_TO_KIND = {
    "designs": "design",
    "plans": "plan",
    "research": "research",
    "reviews": "review",
}


def _load_document(path: Path, kind: str, repo_root: Path) -> Document:
    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    doc_id = meta.get("id", path.stem)
    title = meta.get("title", "") or _first_heading(text) or path.stem
    rel_path = str(path.relative_to(repo_root)).replace("\\", "/")
    return Document(id=doc_id, kind=kind, path=rel_path, title=title)


# ---------------------------------------------------------------------------
# Permissions table walker
# ---------------------------------------------------------------------------


def _walk_table_under_heading(body: str, heading: str) -> list[list[str]]:
    """Return a list of cell-lists for the markdown table under `heading`.

    Stops at the next `### ` or `## ` heading or blank-line sequence that
    is not part of a table.  Skips the header and separator rows.
    """
    lines = body.splitlines()
    rows: list[list[str]] = []
    in_section = False
    header_seen = False
    for line in lines:
        stripped = line.strip()
        if stripped == heading or stripped.startswith(heading + " "):
            in_section = True
            header_seen = False
            continue
        if in_section:
            if stripped.startswith("### ") or stripped.startswith("## "):
                break
            if not stripped:
                # allow one blank line between heading and table
                continue
            if stripped.startswith("|"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if not header_seen:
                    header_seen = True
                    continue
                if set("".join(cells)) <= set("-: "):
                    continue
                rows.append(cells)
    return rows


def _load_permissions(path: Path) -> list[Permission]:
    """Parse the four permission sections from permissions.md."""
    text = path.read_text(encoding="utf-8")
    permissions: list[Permission] = []

    # --- Shell Access ---
    # columns: # | Agent | Stage | Command | Reason | Tasks
    for cells in _walk_table_under_heading(text, "### Shell Access"):
        if len(cells) < 5:
            continue
        # leading cell is row number or '-' placeholder
        if cells[0] == "-":
            continue
        agent = cells[1] if len(cells) > 1 else ""
        # stage at index 2 (ignored in IR, absorbed into category)
        scope = cells[3] if len(cells) > 3 else ""
        reason = cells[4] if len(cells) > 4 else ""
        raw_tasks = cells[5] if len(cells) > 5 else ""
        task_ids = [t.strip() for t in raw_tasks.split(",") if t.strip()]
        permissions.append(Permission(
            category="shell",
            agent=agent,
            scope=scope,
            reason=reason,
            tasks=task_ids,
        ))

    # --- File Access ---
    # columns: # | Agent | Stage | Scope | Mode | Reason | Tasks
    for cells in _walk_table_under_heading(text, "### File Access"):
        if len(cells) < 5:
            continue
        if cells[0] == "-":
            continue
        agent = cells[1] if len(cells) > 1 else ""
        scope_base = cells[3] if len(cells) > 3 else ""
        mode = cells[4] if len(cells) > 4 else ""
        scope = f"{scope_base} ({mode})" if mode else scope_base
        reason = cells[5] if len(cells) > 5 else ""
        raw_tasks = cells[6] if len(cells) > 6 else ""
        task_ids = [t.strip() for t in raw_tasks.split(",") if t.strip()]
        permissions.append(Permission(
            category="file",
            agent=agent,
            scope=scope,
            reason=reason,
            tasks=task_ids,
        ))

    # --- MCP Tools ---
    # columns: # | Agent | Stage | Tool | Reason | Tasks
    for cells in _walk_table_under_heading(text, "### MCP Tools"):
        if len(cells) < 3:
            continue
        if cells[0] == "-":
            continue
        agent = cells[1] if len(cells) > 1 else ""
        scope = cells[3] if len(cells) > 3 else ""
        reason = cells[4] if len(cells) > 4 else ""
        raw_tasks = cells[5] if len(cells) > 5 else ""
        task_ids = [t.strip() for t in raw_tasks.split(",") if t.strip()]
        permissions.append(Permission(
            category="mcp",
            agent=agent,
            scope=scope,
            reason=reason,
            tasks=task_ids,
        ))

    # --- External Access ---
    # columns: # | Agent | Stage | Type | Target | Reason | Tasks
    for cells in _walk_table_under_heading(text, "### External Access"):
        if len(cells) < 4:
            continue
        if cells[0] == "-":
            continue
        agent = cells[1] if len(cells) > 1 else ""
        access_type = cells[3] if len(cells) > 3 else ""
        target = cells[4] if len(cells) > 4 else ""
        scope = f"{access_type} {target}".strip() if target else access_type
        reason = cells[5] if len(cells) > 5 else ""
        raw_tasks = cells[6] if len(cells) > 6 else ""
        task_ids = [t.strip() for t in raw_tasks.split(",") if t.strip()]
        permissions.append(Permission(
            category="external",
            agent=agent,
            scope=scope,
            reason=reason,
            tasks=task_ids,
        ))

    return permissions


# ---------------------------------------------------------------------------
# Main assembler
# ---------------------------------------------------------------------------


def extract_ir(
    adv_id_or_path: str,
    adventures_root: Optional[str] = None,
) -> AdventurePipelineIR:
    """Read a live adventure directory and return a populated AdventurePipelineIR.

    Args:
        adv_id_or_path: An adventure ID (e.g. "ADV-007") or a filesystem path
                        to the adventure directory.
        adventures_root: Optional override for the adventures root directory.
                         Defaults to <repo_root>/.agent/adventures.

    Returns:
        Populated AdventurePipelineIR.

    Raises:
        FileNotFoundError: If the adventure directory or manifest.md is missing.
    """
    repo_root = _PKG_ROOT

    # Resolve adventure directory
    if re.fullmatch(r"ADV-\d{3,}", adv_id_or_path):
        root_dir = Path(adventures_root) if adventures_root else _DEFAULT_ADVENTURES_ROOT
        adv_dir = root_dir / adv_id_or_path
    else:
        adv_dir = Path(adv_id_or_path)

    if not adv_dir.exists():
        raise FileNotFoundError(f"adventure directory not found: {adv_dir}")

    manifest_path = adv_dir / "manifest.md"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.md not found in {adv_dir}")

    manifest_text = manifest_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(manifest_text)

    concept = _extract_concept(body)
    tasks_list: list[str] = meta.get("tasks") or []

    # ---- Tasks ----
    tasks: list[Task] = []
    tasks_dir = adv_dir / "tasks"
    if tasks_dir.exists():
        for tf in sorted(tasks_dir.glob("ADV*-T*.md")):
            try:
                tasks.append(_load_task(tf))
            except Exception:
                # malformed task file — skip gracefully
                pass

    # ---- Documents ----
    documents: list[Document] = []
    for subdir, kind in _SUBDIR_TO_KIND.items():
        doc_dir = adv_dir / subdir
        if not doc_dir.exists():
            continue
        for fpath in sorted(doc_dir.glob("*.md")):
            try:
                documents.append(_load_document(fpath, kind, repo_root))
            except Exception:
                pass

    # ---- Target Conditions ----
    tcs = _parse_tc_table(body)

    # ---- Permissions ----
    permissions_path = adv_dir / "permissions.md"
    permissions: list[Permission] = []
    if permissions_path.exists():
        try:
            permissions = _load_permissions(permissions_path)
        except Exception:
            pass

    # ---- Decisions (reserved — empty for ADV-007/008) ----
    decisions: list[Decision] = []

    # ---- Agents — derived from permission entries ----
    seen_agents: dict[str, set[str]] = {}
    for p in permissions:
        if p.agent and p.agent not in seen_agents:
            seen_agents[p.agent] = set()
        if p.agent:
            seen_agents[p.agent].add(p.scope)

    agents: list[Agent] = [
        Agent(name=name, role=name, permissions=sorted(scopes))
        for name, scopes in sorted(seen_agents.items())
    ]

    # ---- Roles — derived from task assignee fields ----
    role_names: set[str] = set()
    for task in tasks:
        if task.assignee:
            role_names.add(task.assignee)
    roles: list[Role] = [Role(name=r) for r in sorted(role_names)]

    # ---- Log tail ----
    log_path = adv_dir / "adventure.log"
    log_tail: list[str] = []
    if log_path.exists():
        log_tail = log_path.read_text(encoding="utf-8").splitlines()[-40:]

    return AdventurePipelineIR(
        id=meta.get("id", adv_dir.name),
        title=meta.get("title", ""),
        state=meta.get("state", "unknown"),
        created=meta.get("created", ""),
        updated=meta.get("updated", ""),
        concept=concept,
        tasks_list=tasks_list,
        tasks=tasks,
        documents=documents,
        tcs=tcs,
        decisions=decisions,
        permissions=permissions,
        agents=agents,
        roles=roles,
        log_tail=log_tail,
    )


# ---------------------------------------------------------------------------
# JSON serialiser
# ---------------------------------------------------------------------------


def to_json(ir: AdventurePipelineIR) -> str:
    """Serialise an AdventurePipelineIR to a JSON string."""
    return json.dumps(asdict(ir), indent=2, sort_keys=False, default=str)
