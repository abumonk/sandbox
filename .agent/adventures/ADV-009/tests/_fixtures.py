"""Shared test fixtures for ADV-009 test suite.

Not a test file (no test_ prefix) — imported by test_server.py,
test_ui_layout.py, test_ui_smoke.py, test_ir.py,
test_graph_endpoint.py, and test_pipeline_tab.py.

Key helpers:
  make_synthetic_adventure(tmpdir, adv_id="ADV-999", ...)
      Builds a minimal .agent/adventures/<adv_id>/ tree in tmpdir.

  TempAdventure(adv_id="ADV-998", ...)
      Context manager: builds a minimal 2-task adventure in a fresh
      tempfile.mkdtemp() directory, exposes .adv_dir and .agent_dir.
      Cleaned up (shutil.rmtree ignore_errors=True) on __exit__.

  ServerThread(adventures_root)
      Context manager: starts ThreadingHTTPServer on a random (port 0) port,
      monkey-patches server.ADVENTURES_DIR / server.AGENT_DIR, exposes
      self.url and self.stop().

  http_get(base_url, path) -> dict | str
  http_post(base_url, path, payload) -> dict
      Thin urllib wrappers.

  http_post_raw(base_url, path, payload) -> (int, dict)
      Like http_post but returns (status_code, parsed_json) without raising.

  load_console_server() -> module
      Imports server.py from the hyphenated adventure-console directory via
      importlib.util.spec_from_file_location so we never need to rename the
      directory or add __init__.py files upstream.

  extract_js_function_body(src, func_name) -> str
      Bracket-balance helper: returns the body of a named JS function.

  ensure_on_syspath() -> None
      Insert REPO_ROOT into sys.path so adventure_pipeline imports cleanly.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import threading
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[4]          # R:/Sandbox
SERVER_PATH = REPO_ROOT / ".agent" / "adventure-console" / "server.py"
INDEX_HTML = REPO_ROOT / ".agent" / "adventure-console" / "index.html"
TESTS_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Server loader
# ---------------------------------------------------------------------------

def load_console_server():
    """Import server.py by file path (hyphen in dir name precludes normal import)."""
    spec = importlib.util.spec_from_file_location("console_server", SERVER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Synthetic adventure tree builder
# ---------------------------------------------------------------------------

def make_synthetic_adventure(
    tmpdir: Path,
    adv_id: str = "ADV-999",
    *,
    state: str = "review",
    permissions_approved: bool = False,
) -> Path:
    """Create a minimal .agent/adventures/<adv_id>/ tree under tmpdir.

    Returns the path to the adventure root (tmpdir/.agent/adventures/<adv_id>).
    """
    adv_root = tmpdir / ".agent" / "adventures" / adv_id
    adv_root.mkdir(parents=True, exist_ok=True)

    # manifest.md
    (adv_root / "manifest.md").write_text(
        f"---\n"
        f"id: {adv_id}\n"
        f"title: Synthetic Test Adventure\n"
        f"state: {state}\n"
        f"tasks: [{adv_id}-T001]\n"
        f"created: 2026-01-01T00:00:00Z\n"
        f"updated: 2026-01-02T00:00:00Z\n"
        f"---\n\n"
        f"## Concept\n\n"
        f"A minimal synthetic adventure used by the test suite.\n\n"
        f"## Target Conditions\n\n"
        f"| ID | Description | Source | Design | Plan | Tasks | Proof Method | Proof Command | Status |\n"
        f"|---|---|---|---|---|---|---|---|---|\n"
        f"| TC-001 | First condition | req | - | - | {adv_id}-T001 | autotest | - | pending |\n"
        f"| TC-002 | Second condition | req | - | - | {adv_id}-T001 | manual | - | passed |\n",
        encoding="utf-8",
    )

    # permissions.md
    perm_status = "approved" if permissions_approved else "draft"
    (adv_root / "permissions.md").write_text(
        f"---\n"
        f"status: {perm_status}\n"
        f"approved: \n"
        f"---\n\n"
        f"# Permissions\n\nMinimal permissions file.\n",
        encoding="utf-8",
    )

    # tasks/
    tasks_dir = adv_root / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    (tasks_dir / f"{adv_id}-T001.md").write_text(
        f"---\n"
        f"id: {adv_id}-T001\n"
        f"title: Sample Task\n"
        f"stage: ready\n"
        f"status: pending\n"
        f"assignee: coder\n"
        f"iterations: 0\n"
        f"depends_on: []\n"
        f"target_conditions: [TC-001]\n"
        f"---\n\n"
        f"## Description\n\nA sample task for fixture purposes.\n\n"
        f"## Acceptance Criteria\n\n- [ ] The task exists.\n\n"
        f"## Log\n\n- [2026-01-01T00:00:00Z] created: Task created.\n",
        encoding="utf-8",
    )

    # designs/
    designs_dir = adv_root / "designs"
    designs_dir.mkdir(exist_ok=True)
    (designs_dir / "design-foo.md").write_text(
        "# Foo Design\n\n"
        "## Overview\n\n"
        "This design decides the foo architecture. It is minimal and synthetic.\n\n"
        "## Details\n\nSome detail content.\n",
        encoding="utf-8",
    )

    # plans/
    plans_dir = adv_root / "plans"
    plans_dir.mkdir(exist_ok=True)
    (plans_dir / "plan-bar.md").write_text(
        "# Bar Plan\n\n"
        "## Wave 1\n\nFirst wave description.\n\n"
        "## Wave 2\n\nSecond wave description.\n\n"
        "## Tasks\n\n"
        "### Task A\n\nFirst task.\n\n"
        "### Task B\n\nSecond task.\n\n"
        "### Task C\n\nThird task.\n",
        encoding="utf-8",
    )

    # research/
    research_dir = adv_root / "research"
    research_dir.mkdir(exist_ok=True)
    (research_dir / "audit.md").write_text(
        "# Audit\n\nMinimal research file.\n",
        encoding="utf-8",
    )

    # reviews/
    reviews_dir = adv_root / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    (reviews_dir / f"{adv_id}-T001-review.md").write_text(
        f"---\n"
        f"task_id: {adv_id}-T001\n"
        f"status: PASSED\n"
        f"build_result: pass\n"
        f"test_result: pass\n"
        f"---\n\n"
        f"# Review: {adv_id}-T001\n\nNo issues found.\n",
        encoding="utf-8",
    )

    # adventure.log
    (adv_root / "adventure.log").write_text(
        "[2026-01-01T00:00:00Z] planner | \"created: synthetic adventure\"\n",
        encoding="utf-8",
    )

    return adv_root


# ---------------------------------------------------------------------------
# ServerThread context manager
# ---------------------------------------------------------------------------

class ServerThread:
    """Start ThreadingHTTPServer on port 0, monkey-patch server module globals.

    Usage::

        with ServerThread(tmp_agent_dir) as srv:
            response = http_get(srv.url, "/api/adventures")

    ``tmp_agent_dir`` is the ``.agent`` directory inside the tmpdir, i.e.
    ``tmpdir / ".agent"``.
    """

    def __init__(self, tmp_agent_dir: Path):
        self._agent_dir = tmp_agent_dir
        self._server = None
        self._thread = None
        self._patches: list = []
        self.url: str = ""

    def __enter__(self) -> "ServerThread":
        import unittest.mock as mock

        # Load a fresh server module (so patches don't leak across tests)
        srv_mod = load_console_server()

        adventures_dir = self._agent_dir / "adventures"
        # REPO_ROOT must also be patched so relative_to() doesn't fail when
        # the tmpdir is outside the real repo root.
        tmp_repo_root = self._agent_dir.parent

        # Patch module-level path globals
        self._patches = [
            mock.patch.object(srv_mod, "ADVENTURES_DIR", adventures_dir),
            mock.patch.object(srv_mod, "AGENT_DIR", self._agent_dir),
            mock.patch.object(srv_mod, "REPO_ROOT", tmp_repo_root),
        ]
        for p in self._patches:
            p.start()

        from http.server import ThreadingHTTPServer
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv_mod.Handler)
        port = httpd.server_address[1]
        self.url = f"http://127.0.0.1:{port}"
        self._server = httpd

        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        self._thread = t
        return self

    def __exit__(self, *_):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        for p in self._patches:
            try:
                p.stop()
            except RuntimeError:
                pass

    def stop(self):
        self.__exit__()


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def http_get(base_url: str, path: str) -> dict | str:
    """GET <base_url><path>. Returns parsed JSON dict or raises."""
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def http_post(base_url: str, path: str, payload: dict) -> dict:
    """POST JSON payload to <base_url><path>. Returns parsed JSON dict."""
    url = base_url.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def http_post_raw(base_url: str, path: str, payload: dict) -> tuple:
    """POST JSON payload to <base_url><path>. Returns (status_code, parsed_json).

    Unlike http_post this never raises on 4xx/5xx — callers check the
    returned status code themselves.
    """
    url = base_url.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except Exception:
            return exc.code, {"error": raw}


def http_get_raw(base_url: str, path: str) -> tuple:
    """GET <base_url><path>. Returns (status_code, parsed_json_or_str).

    Never raises on 4xx/5xx.
    """
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(raw)
        except Exception:
            return exc.code, {"error": raw}


# ---------------------------------------------------------------------------
# ensure_on_syspath
# ---------------------------------------------------------------------------

def ensure_on_syspath() -> None:
    """Insert REPO_ROOT into sys.path so adventure_pipeline imports cleanly."""
    repo = str(REPO_ROOT)
    if repo not in sys.path:
        sys.path.insert(0, repo)


# ---------------------------------------------------------------------------
# TempAdventure context manager (2-task synthetic adventure for mutation tests)
# ---------------------------------------------------------------------------

class TempAdventure:
    """Build a minimal 2-task adventure in a fresh tempdir.

    The adventure ID defaults to ADV-998 so it does not collide with real
    adventures.  Two tasks are created:
        <adv_id>-T001  depends_on: []
        <adv_id>-T002  depends_on: []

    On exit the tmpdir is removed with ignore_errors=True (safe on Windows).

    Attributes:
        tmpdir   — pathlib.Path to the root tempdir
        agent_dir — <tmpdir>/.agent
        adv_dir  — <tmpdir>/.agent/adventures/<adv_id>
        adv_id   — the adventure id string used
    """

    def __init__(self, adv_id: str = "ADV-998"):
        self.adv_id = adv_id
        self.tmpdir: Path | None = None
        self.agent_dir: Path | None = None
        self.adv_dir: Path | None = None

    def __enter__(self) -> "TempAdventure":
        raw = tempfile.mkdtemp(prefix="adv009_test_")
        self.tmpdir = Path(raw)
        self.agent_dir = self.tmpdir / ".agent"
        adv_root = self.agent_dir / "adventures" / self.adv_id
        adv_root.mkdir(parents=True, exist_ok=True)
        self.adv_dir = adv_root

        # Task IDs must match ADV\d{3}-T\d{3} (no hyphen after ADV).
        # Strip the hyphen from the adventure prefix: ADV-998 -> ADV998
        adv_prefix = self.adv_id.replace("-", "")  # "ADV998"
        t1 = adv_prefix + "-T001"
        t2 = adv_prefix + "-T002"

        # manifest.md
        (adv_root / "manifest.md").write_text(
            f"---\n"
            f"id: {self.adv_id}\n"
            f"title: Temp Test Adventure\n"
            f"state: active\n"
            f"tasks: [{t1}, {t2}]\n"
            f"created: 2026-01-01T00:00:00Z\n"
            f"updated: 2026-01-01T00:00:00Z\n"
            f"---\n\n"
            f"## Concept\n\nMinimal synthetic adventure for depends_on tests.\n\n"
            f"## Target Conditions\n\n"
            f"| ID | Description | Source | Design | Plan | Tasks | Proof Method | Proof Command | Status |\n"
            f"|---|---|---|---|---|---|---|---|---|\n"
            f"| TC-001 | First | req | - | - | {t1} | autotest | - | pending |\n",
            encoding="utf-8",
        )

        # tasks/
        tasks_dir = adv_root / "tasks"
        tasks_dir.mkdir(exist_ok=True)

        for tid in (t1, t2):
            (tasks_dir / f"{tid}.md").write_text(
                f"---\n"
                f"id: {tid}\n"
                f"title: Task {tid}\n"
                f"stage: ready\n"
                f"status: pending\n"
                f"assignee: coder\n"
                f"iterations: 0\n"
                f"depends_on: []\n"
                f"target_conditions: [TC-001]\n"
                f"---\n\n"
                f"## Description\n\nSynthetic task for test fixture.\n\n"
                f"## Log\n\n- [2026-01-01T00:00:00Z] created.\n",
                encoding="utf-8",
            )

        # adventure.log
        (adv_root / "adventure.log").write_text(
            f'[2026-01-01T00:00:00Z] test | "created synthetic adventure"\n',
            encoding="utf-8",
        )

        return self

    def __exit__(self, *_):
        if self.tmpdir:
            shutil.rmtree(str(self.tmpdir), ignore_errors=True)


# ---------------------------------------------------------------------------
# extract_js_function_body — bracket-balance helper for static JS inspection
# ---------------------------------------------------------------------------

def extract_js_function_body(src: str, func_name: str) -> str:
    """Return the body text of the first JS function named func_name.

    Searches for ``func_name`` followed by optional whitespace, ``(``, then
    scans forward using brace-counting to find the matching ``}``.  Returns
    the text between the outer ``{`` and ``}`` (exclusive).

    Returns empty string if the function is not found.
    """
    import re
    pattern = re.compile(
        r'\b' + re.escape(func_name) + r'\s*\([^)]*\)\s*\{',
        re.DOTALL,
    )
    m = pattern.search(src)
    if not m:
        return ""
    start = m.end() - 1   # position of the opening '{'
    depth = 0
    for i in range(start, len(src)):
        if src[i] == '{':
            depth += 1
        elif src[i] == '}':
            depth -= 1
            if depth == 0:
                return src[start + 1:i]
    return ""
