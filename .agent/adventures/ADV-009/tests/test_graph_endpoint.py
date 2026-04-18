"""test_graph_endpoint.py — HTTP tests for /graph and depends_on endpoints.

TC coverage:
  TC-046  TestGraphShape.test_top_level_keys
  TC-052  TestDependsOn.test_happy
  TC-053  TestDependsOn.test_self_cycle
  TC-054  TestDependsOn.test_cycle
  TC-058  TestImport.test_server_imports_ir
  TC-059  TestGraphShape.test_schema
  TC-060  TestStdlibOnly.test_no_third_party_imports
  TC-061  TestCycleFree.test_self_and_transitive

Stdlib only.
"""
from __future__ import annotations

import ast
import importlib.util
import re
import sys
import unittest
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parents[3]
_SERVER_PATH = _REPO_ROOT / ".agent" / "adventure-console" / "server.py"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Import shared fixtures using the module that lives in the same directory
sys.path.insert(0, str(_TESTS_DIR))
from _fixtures import (  # noqa: E402
    ServerThread,
    TempAdventure,
    http_get,
    http_post_raw,
    http_get_raw,
    load_console_server,
)

_ADV_DIR = _REPO_ROOT / ".agent" / "adventures"


# ---------------------------------------------------------------------------
# TC-058 — static source check: server.py imports adventure_pipeline.tools.ir
# ---------------------------------------------------------------------------

class TestImport(unittest.TestCase):
    """TC-058: server.py references adventure_pipeline.tools.ir."""

    def test_server_imports_ir(self):
        """server.py source contains the adventure_pipeline.tools.ir import."""
        src = _SERVER_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "adventure_pipeline.tools.ir",
            src,
            "server.py must import adventure_pipeline.tools.ir",
        )


# ---------------------------------------------------------------------------
# TC-060 — stdlib-only check: server.py top-level imports
# ---------------------------------------------------------------------------

class TestStdlibOnly(unittest.TestCase):
    """TC-060: server.py top-level imports are stdlib or adventure_pipeline."""

    def test_no_third_party_imports(self):
        """All top-level module imports in server.py are stdlib or adventure_pipeline."""
        src = _SERVER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(_SERVER_PATH))

        # sys.stdlib_module_names is available in Python 3.10+
        stdlib_names: set[str] = sys.stdlib_module_names  # type: ignore[attr-defined]

        allowed_prefixes = {"adventure_pipeline"}

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in stdlib_names and top not in allowed_prefixes:
                        violations.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                top = node.module.split(".")[0]
                # relative imports (level > 0) are fine (module = None or relative)
                if node.level and node.level > 0:
                    continue
                if top not in stdlib_names and top not in allowed_prefixes:
                    violations.append(f"from {node.module} import ...")

        self.assertEqual(
            violations, [],
            f"server.py has non-stdlib/non-adventure_pipeline imports: {violations}",
        )


# ---------------------------------------------------------------------------
# TC-046, TC-059 — GET /api/adventures/ADV-007/graph shape
# ---------------------------------------------------------------------------

@unittest.skipUnless((_ADV_DIR / "ADV-007").exists(), "ADV-007 not found")
class TestGraphShape(unittest.TestCase):
    """Tests for /api/adventures/ADV-007/graph payload shape."""

    @classmethod
    def setUpClass(cls):
        cls._srv = ServerThread(_REPO_ROOT / ".agent")
        cls._srv.__enter__()
        cls.base_url = cls._srv.url

    @classmethod
    def tearDownClass(cls):
        cls._srv.__exit__(None, None, None)

    def test_top_level_keys(self):
        """TC-046: /graph returns 200 JSON with nodes, edges, explanations."""
        data = http_get(self.base_url, "/api/adventures/ADV-007/graph")
        self.assertIsInstance(data, dict)
        for key in ("nodes", "edges", "explanations"):
            self.assertIn(key, data, f"graph payload missing key: {key}")
        self.assertIsInstance(data["nodes"], list)
        self.assertIsInstance(data["edges"], list)
        self.assertIsInstance(data["explanations"], dict)

    def test_schema(self):
        """TC-059: every node has data.id + data.kind; adventure + task node present."""
        data = http_get(self.base_url, "/api/adventures/ADV-007/graph")
        nodes = data["nodes"]
        edges = data["edges"]

        for n in nodes:
            with self.subTest(node=n.get("data", {}).get("id", "?")):
                self.assertIn("data", n)
                self.assertIn("id", n["data"], "node missing data.id")
                self.assertIn("kind", n["data"], "node missing data.kind")

        for e in edges:
            with self.subTest(edge=e.get("data", {}).get("id", "?")):
                self.assertIn("data", e)
                self.assertIn("id", e["data"], "edge missing data.id")
                self.assertIn("source", e["data"], "edge missing data.source")
                self.assertIn("target", e["data"], "edge missing data.target")

        kinds = {n["data"]["kind"] for n in nodes}
        self.assertIn("adventure", kinds, "Expected at least one 'adventure' node")
        self.assertIn("task", kinds, "Expected at least one 'task' node")


# ---------------------------------------------------------------------------
# TC-052, TC-053, TC-054 — POST depends_on mutation tests (TempAdventure)
# ---------------------------------------------------------------------------

class TestDependsOn(unittest.TestCase):
    """Tests for POST /api/adventures/{id}/tasks/{task}/depends_on.

    Creates a synthetic adventure in the REAL .agent/adventures/ directory
    (as ADV-998) so that extract_ir() can find it via its hardcoded root.
    The adventure is cleaned up in tearDownClass.
    """

    ADV_ID = "ADV-998"

    @classmethod
    def setUpClass(cls):
        import shutil
        # Task IDs must match ADV\d{3}-T\d{3}
        cls.t1 = "ADV998-T001"
        cls.t2 = "ADV998-T002"

        # Create synthetic adventure under real adventures dir
        cls.adv_dir = _ADV_DIR / cls.ADV_ID
        if cls.adv_dir.exists():
            shutil.rmtree(str(cls.adv_dir))
        cls.adv_dir.mkdir(parents=True)

        tasks_dir = cls.adv_dir / "tasks"
        tasks_dir.mkdir()

        # manifest.md
        (cls.adv_dir / "manifest.md").write_text(
            f"---\n"
            f"id: {cls.ADV_ID}\n"
            f"title: Temp Test Adventure\n"
            f"state: active\n"
            f"tasks: [{cls.t1}, {cls.t2}]\n"
            f"created: 2026-01-01T00:00:00Z\n"
            f"updated: 2026-01-01T00:00:00Z\n"
            f"---\n\n"
            f"## Concept\n\nSynthetic.\n\n"
            f"## Target Conditions\n\n"
            f"| ID | Description | Source | Design | Plan | Tasks | Proof Method | Proof Command | Status |\n"
            f"|---|---|---|---|---|---|---|---|---|\n"
            f"| TC-001 | First | req | - | - | {cls.t1} | autotest | - | pending |\n",
            encoding="utf-8",
        )

        # adventure.log
        (cls.adv_dir / "adventure.log").write_text(
            '[2026-01-01T00:00:00Z] test | "created"\n',
            encoding="utf-8",
        )

        # task files
        for tid in (cls.t1, cls.t2):
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
                f"## Description\n\nSynthetic.\n\n"
                f"## Log\n\n- [2026-01-01T00:00:00Z] created.\n",
                encoding="utf-8",
            )

        # Boot server against the real .agent dir
        cls._srv = ServerThread(_REPO_ROOT / ".agent")
        cls._srv.__enter__()
        cls.base_url = cls._srv.url

    @classmethod
    def tearDownClass(cls):
        cls._srv.__exit__(None, None, None)
        import shutil
        shutil.rmtree(str(cls.adv_dir), ignore_errors=True)

    def _read_task_deps(self, task_id: str) -> list:
        """Read depends_on from the task file on disk."""
        task_path = self.adv_dir / "tasks" / f"{task_id}.md"
        text = task_path.read_text(encoding="utf-8")
        m = re.search(r"^depends_on:\s*\[([^\]]*)\]", text, re.MULTILINE)
        if not m:
            return []
        inner = m.group(1).strip()
        if not inner:
            return []
        return [s.strip().strip('"').strip("'") for s in inner.split(",") if s.strip()]

    def _reset_task_deps(self, task_id: str, deps: list) -> None:
        """Rewrite depends_on in a task file back to deps."""
        task_path = self.adv_dir / "tasks" / f"{task_id}.md"
        text = task_path.read_text(encoding="utf-8")
        inline_val = "[" + ", ".join(deps) + "]"
        text = re.sub(
            r"^depends_on:.*$",
            f"depends_on: {inline_val}",
            text,
            flags=re.MULTILINE,
        )
        task_path.write_text(text, encoding="utf-8")

    def setUp(self):
        # Reset both tasks to clean depends_on: [] before each test
        self._reset_task_deps(self.t1, [])
        self._reset_task_deps(self.t2, [])

    def test_happy(self):
        """TC-052: POST depends_on happy path — 200, disk updated."""
        path = f"/api/adventures/{self.ADV_ID}/tasks/{self.t1}/depends_on"
        status, body = http_post_raw(self.base_url, path, {"depends_on": self.t2})
        self.assertEqual(status, 200, f"Expected 200, got {status}: {body}")
        self.assertTrue(body.get("ok"), f"Expected ok=True: {body}")
        self.assertIn(self.t2, body.get("depends_on", []))

        # Verify disk state
        disk_deps = self._read_task_deps(self.t1)
        self.assertIn(self.t2, disk_deps, "depends_on not persisted to disk")

    def test_self_cycle(self):
        """TC-053: POST self-cycle returns 400 and task file unchanged."""
        path = f"/api/adventures/{self.ADV_ID}/tasks/{self.t1}/depends_on"
        status, body = http_post_raw(self.base_url, path, {"depends_on": self.t1})
        self.assertEqual(status, 400, f"Expected 400 for self-cycle, got {status}: {body}")
        # File should be unchanged
        disk_deps = self._read_task_deps(self.t1)
        self.assertNotIn(self.t1, disk_deps, "Self-cycle should not have been persisted")

    def test_cycle(self):
        """TC-054: POST transitive cycle returns 400."""
        # Seed: T2 depends on T1
        self._reset_task_deps(self.t2, [self.t1])

        # Now try to add T1 -> T2 which would create T1 -> T2 -> T1
        path = f"/api/adventures/{self.ADV_ID}/tasks/{self.t1}/depends_on"
        status, body = http_post_raw(self.base_url, path, {"depends_on": self.t2})
        self.assertEqual(status, 400, f"Expected 400 for transitive cycle, got {status}: {body}")
        disk_deps = self._read_task_deps(self.t1)
        self.assertNotIn(self.t2, disk_deps, "Cycle-creating dep should not have been persisted")

    def test_unknown_task(self):
        """Unknown task dep returns 400 (invalid id format) or 4xx."""
        path = f"/api/adventures/{self.ADV_ID}/tasks/{self.t1}/depends_on"
        # T999 doesn't exist and also has wrong format for the regex -> 400
        status, body = http_post_raw(self.base_url, path, {"depends_on": "T999"})
        self.assertIn(status, (400, 404),
            f"Expected 400/404 for unknown task, got {status}: {body}")


# ---------------------------------------------------------------------------
# TC-061 — direct import of _cycle_free helper
# ---------------------------------------------------------------------------

class TestCycleFree(unittest.TestCase):
    """TC-061: _cycle_free helper correctly detects self-cycles and transitive cycles."""

    @classmethod
    def setUpClass(cls):
        # Load server module by file path and extract _cycle_free as a plain function
        spec = importlib.util.spec_from_file_location("console_server_cf", _SERVER_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Bind as a plain callable (not a method on cls)
        cls._cf = staticmethod(mod._cycle_free)

    def _make_ir(self, deps: dict) -> object:
        """Build a minimal IR-like stub with tasks having depends_on lists.

        deps: {task_id: [dep_ids...]}
        """
        class _Task:
            def __init__(self, id_, depends_on):
                self.id = id_
                self.depends_on = depends_on

        class _IR:
            def __init__(self, tasks):
                self.tasks = tasks

        tasks = [_Task(tid, d) for tid, d in deps.items()]
        return _IR(tasks)

    def test_self_and_transitive(self):
        """_cycle_free rejects self-cycles and transitive cycles; accepts safe edges."""
        cf = self._cf

        # Self-loop: A -> A
        ir1 = self._make_ir({"A": [], "B": []})
        self.assertFalse(cf(ir1, "A", "A"), "self-loop must be rejected")

        # Safe edge: D depends_on A (no path from A back to D)
        # fwd: A->[], B->[A], C->[B], D->[]
        ir2 = self._make_ir({"A": [], "B": ["A"], "C": ["B"], "D": []})
        self.assertTrue(cf(ir2, "D", "A"), "D->A should be safe (no cycle)")

        # Direct cycle: B depends_on A already. Adding A depends_on B.
        # fwd: A->[], B->[A]. BFS from new_dep=B: B's deps=[A], find A==task_id → cycle
        ir3 = self._make_ir({"A": [], "B": ["A"]})
        self.assertFalse(cf(ir3, "A", "B"), "A->B with B->A existing is a direct cycle")

        # Transitive cycle: B depends_on A, C depends_on B. Adding A depends_on C.
        # fwd: A->[], B->[A], C->[B]. BFS from new_dep=C: C->[B]->[A], find A==task_id → cycle
        ir4 = self._make_ir({"A": [], "B": ["A"], "C": ["B"]})
        self.assertFalse(cf(ir4, "A", "C"), "A->C with C->B->A existing is a transitive cycle")


if __name__ == "__main__":
    unittest.main()
