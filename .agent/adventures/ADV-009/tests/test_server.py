"""Tests for adventure-console server.py — ADV009-T003 additions.

Run from repo root:
    python -m unittest discover -s .agent/adventures/ADV-009/tests -p "test_*.py"
"""

import ast
import sys
import types
import unittest
from pathlib import Path

# Make server importable without running main()
REPO_ROOT = Path(__file__).resolve().parents[4]  # R:/Sandbox
SERVER_PATH = REPO_ROOT / ".agent" / "adventure-console" / "server.py"

# ---------------------------------------------------------------------------
# Import server module by path so we don't depend on install
# ---------------------------------------------------------------------------

def _import_server():
    import importlib.util
    spec = importlib.util.spec_from_file_location("server", SERVER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


server = _import_server()


# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

def _make_meta(state="active"):
    return {"id": "ADV-009", "title": "Test Adventure", "state": state}


def _make_permissions(status="approved"):
    return {"status": status, "approved": "", "file": "permissions.md"}


def _make_tcs(statuses=("passed", "failed", "pending", "")):
    return [{"id": f"TC-{i:03d}", "description": "", "source": "", "design": "",
             "plan": "", "tasks": "", "proof_method": "", "proof_command": "",
             "status": s} for i, s in enumerate(statuses, start=1)]


# ---------------------------------------------------------------------------
# TC-026: summary block shape
# ---------------------------------------------------------------------------

class TestSummaryBlockShape(unittest.TestCase):
    """TC-026: GET /api/adventures/{id} includes a summary object with all required keys."""

    def test_summary_block_shape(self):
        """get_adventure() for ADV-009 must include all six declared summary keys."""
        try:
            bundle = server.get_adventure("ADV-009")
        except FileNotFoundError:
            self.skipTest("ADV-009 adventure directory not found on disk")

        self.assertIn("summary", bundle, "summary key missing from get_adventure() response")
        summary = bundle["summary"]
        required_keys = {"tc_total", "tc_passed", "tc_failed", "tc_pending",
                         "tasks_by_status", "next_action"}
        missing = required_keys - set(summary.keys())
        self.assertFalse(missing, f"summary missing keys: {missing}")

        # Numeric sanity
        self.assertIsInstance(summary["tc_total"], int)
        self.assertIsInstance(summary["tc_passed"], int)
        self.assertIsInstance(summary["tc_failed"], int)
        self.assertIsInstance(summary["tc_pending"], int)
        self.assertEqual(
            summary["tc_total"],
            summary["tc_passed"] + summary["tc_failed"] + summary["tc_pending"],
            "tc_total must equal sum of passed + failed + pending",
        )
        self.assertIsInstance(summary["tasks_by_status"], dict)

        # next_action sub-keys
        na = summary["next_action"]
        for key in ("kind", "label", "state_hint"):
            self.assertIn(key, na, f"next_action missing key: {key}")


# ---------------------------------------------------------------------------
# TC-029: next_action.kind == "approve_permissions" for review + unapproved
# ---------------------------------------------------------------------------

class TestNextActionReviewUnapprovedPermissions(unittest.TestCase):
    """TC-029: approve_permissions kind when state==review and permissions not approved."""

    def test_next_action_review_unapproved_permissions(self):
        meta = _make_meta(state="review")
        permissions = _make_permissions(status="draft")
        result = server.compute_next_action(meta, permissions, [], [])
        self.assertEqual(result["kind"], "approve_permissions")
        self.assertEqual(result["state_hint"], "review")

    def test_next_action_review_approved_permissions(self):
        meta = _make_meta(state="review")
        permissions = _make_permissions(status="approved")
        result = server.compute_next_action(meta, permissions, [], [])
        self.assertEqual(result["kind"], "open_plan")
        self.assertEqual(result["state_hint"], "review")

    def test_next_action_review_no_permissions(self):
        """No permissions object → treat as unapproved."""
        meta = _make_meta(state="review")
        result = server.compute_next_action(meta, None, [], [])
        self.assertEqual(result["kind"], "approve_permissions")

    def test_next_action_review_missing_status_key(self):
        """permissions dict without status key → treat as unapproved."""
        meta = _make_meta(state="review")
        permissions = {}
        result = server.compute_next_action(meta, permissions, [], [])
        self.assertEqual(result["kind"], "approve_permissions")


# ---------------------------------------------------------------------------
# TC-030 subset: compute_next_action handles every VALID_STATES value + unknown
# ---------------------------------------------------------------------------

class TestNextActionHandlesEveryValidState(unittest.TestCase):
    """compute_next_action must handle every state enum value without raising."""

    ALLOWED_KINDS = {"approve_permissions", "open_plan", "resolve_blocker",
                     "promote_concept", "none"}

    def _assert_valid(self, state, permissions=None):
        meta = _make_meta(state=state)
        result = server.compute_next_action(meta, permissions, [], [])
        self.assertIn(result["kind"], self.ALLOWED_KINDS,
                      f"state={state!r} produced invalid kind {result['kind']!r}")
        self.assertEqual(result["state_hint"], state.lower(),
                         f"state_hint should echo lowercased state for {state!r}")

    def test_blocked(self):
        self._assert_valid("blocked")
        result = server.compute_next_action(_make_meta("blocked"), None, [], [])
        self.assertEqual(result["kind"], "resolve_blocker")

    def test_concept(self):
        self._assert_valid("concept")
        result = server.compute_next_action(_make_meta("concept"), None, [], [])
        self.assertEqual(result["kind"], "promote_concept")

    def test_review_unapproved(self):
        result = server.compute_next_action(
            _make_meta("review"), _make_permissions("draft"), [], [])
        self.assertIn(result["kind"], self.ALLOWED_KINDS)
        self.assertEqual(result["state_hint"], "review")

    def test_planning(self):
        self._assert_valid("planning")
        result = server.compute_next_action(_make_meta("planning"), None, [], [])
        self.assertEqual(result["kind"], "open_plan")

    def test_active(self):
        self._assert_valid("active")
        result = server.compute_next_action(_make_meta("active"), None, [], [])
        self.assertEqual(result["kind"], "open_plan")

    def test_completed(self):
        self._assert_valid("completed")
        result = server.compute_next_action(_make_meta("completed"), None, [], [])
        self.assertEqual(result["kind"], "none")

    def test_cancelled(self):
        self._assert_valid("cancelled")
        result = server.compute_next_action(_make_meta("cancelled"), None, [], [])
        self.assertEqual(result["kind"], "none")

    def test_unknown_fallback(self):
        result = server.compute_next_action(_make_meta("unknown"), None, [], [])
        self.assertIn(result["kind"], self.ALLOWED_KINDS)
        self.assertEqual(result["state_hint"], "unknown")

    def test_all_valid_states_covered(self):
        """All states in VALID_STATES + unknown produce allowed kind values."""
        states = list(server.VALID_STATES) + ["unknown"]
        for state in states:
            with self.subTest(state=state):
                perms = _make_permissions("draft") if state == "review" else None
                result = server.compute_next_action(_make_meta(state), perms, [], [])
                self.assertIn(result["kind"], self.ALLOWED_KINDS)


# ---------------------------------------------------------------------------
# TC-030: server.py remains stdlib-only
# ---------------------------------------------------------------------------

_STDLIB_ALLOWLIST = {
    "__future__", "argparse", "ast", "collections", "contextlib",
    "datetime", "functools", "http", "http.server", "importlib",
    "io", "itertools", "json", "logging", "math", "os", "pathlib",
    "re", "shutil", "socket", "sys", "tempfile", "threading", "time",
    "traceback", "types", "typing", "unittest", "urllib", "urllib.parse",
    "urllib.request", "uuid", "warnings",
}


class TestStdlibOnlyImports(unittest.TestCase):
    """TC-030: server.py top-level imports remain within the stdlib allowlist."""

    def test_stdlib_only_imports(self):
        source = SERVER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(SERVER_PATH))

        non_stdlib = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in _STDLIB_ALLOWLIST:
                        non_stdlib.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    top = node.module.split(".")[0]
                    if top not in _STDLIB_ALLOWLIST:
                        non_stdlib.append(node.module)

        self.assertFalse(
            non_stdlib,
            f"server.py contains non-stdlib imports: {non_stdlib}",
        )


# ---------------------------------------------------------------------------
# _bucket_tc_status unit tests
# ---------------------------------------------------------------------------

class TestBucketTcStatus(unittest.TestCase):
    """Unit tests for the _bucket_tc_status normalization helper."""

    def test_passed_tokens(self):
        for token in ("passed", "pass", "done", "complete", "completed", "yes",
                      "PASSED", "Done", "YES"):
            with self.subTest(token=token):
                self.assertEqual(server._bucket_tc_status(token), "passed")

    def test_failed_tokens(self):
        for token in ("failed", "fail", "error", "no", "broken",
                      "FAILED", "Error", "NO"):
            with self.subTest(token=token):
                self.assertEqual(server._bucket_tc_status(token), "failed")

    def test_unknown_defaults_to_pending(self):
        for token in ("", "pending", "wip", "tbd", "in_progress", "—"):
            with self.subTest(token=token):
                self.assertEqual(server._bucket_tc_status(token), "pending")



# ---------------------------------------------------------------------------
# TC-027 / TC-028: /api/adventures/{id}/documents endpoint
# ---------------------------------------------------------------------------

class TestDocumentsEndpoint(unittest.TestCase):
    """TC-027 + TC-028: list_documents() returns correct type/wave metadata."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from _fixtures import make_synthetic_adventure, load_console_server
        cls._tmpdir = tempfile.mkdtemp()
        cls._tmp = Path(cls._tmpdir)
        cls._adv_root = make_synthetic_adventure(cls._tmp, "ADV-999")
        # Reload server with patched ADVENTURES_DIR
        cls._srv = load_console_server()
        import unittest.mock as mock
        cls._patch = mock.patch.object(
            cls._srv, "ADVENTURES_DIR", cls._tmp / ".agent" / "adventures"
        )
        cls._patch.start()

    @classmethod
    def tearDownClass(cls):
        cls._patch.stop()
        import shutil
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_types(self):
        """TC-027: every entry has type in {design, plan, research, review}."""
        docs = self._srv.list_documents("ADV-999")
        self.assertIsInstance(docs, list)
        self.assertGreater(len(docs), 0)
        allowed_types = {"design", "plan", "research", "review"}
        for doc in docs:
            self.assertIn(doc.get("type"), allowed_types,
                          f"Unexpected type {doc.get('type')!r} in {doc}")

        # Check we got at least one of each type that we seeded
        types_found = {d["type"] for d in docs}
        self.assertIn("design", types_found)
        self.assertIn("plan", types_found)
        self.assertIn("research", types_found)
        self.assertIn("review", types_found)

    def test_waves(self):
        """TC-028: plan fixture entry reports waves == 2."""
        docs = self._srv.list_documents("ADV-999")
        plan_docs = [d for d in docs if d.get("type") == "plan"]
        self.assertGreater(len(plan_docs), 0, "No plan documents found")
        plan = plan_docs[0]
        self.assertEqual(plan.get("waves"), 2,
                         f"Expected waves=2, got {plan.get('waves')!r}")

    def test_design_one_liner(self):
        """TC-027 (extra): design entry has non-empty one_liner ≤ 120 chars."""
        docs = self._srv.list_documents("ADV-999")
        design_docs = [d for d in docs if d.get("type") == "design"]
        self.assertGreater(len(design_docs), 0, "No design documents found")
        design = design_docs[0]
        one_liner = design.get("one_liner", "")
        self.assertIsInstance(one_liner, str)
        self.assertGreater(len(one_liner), 0, "one_liner should not be empty")
        self.assertLessEqual(len(one_liner), 120,
                             f"one_liner exceeds 120 chars: {one_liner!r}")


# ---------------------------------------------------------------------------
# TC-025: knowledge/apply roundtrip
# ---------------------------------------------------------------------------

class TestKnowledgePayload(unittest.TestCase):
    """TC-025: POST knowledge/apply writes the expected JSON shape."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from _fixtures import make_synthetic_adventure, load_console_server, ServerThread
        cls._tmpdir = Path(tempfile.mkdtemp())
        cls._adv_root = make_synthetic_adventure(cls._tmpdir, "ADV-999")
        cls._srv_thread = ServerThread(cls._tmpdir / ".agent")
        cls._srv_thread.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._srv_thread.__exit__(None, None, None)
        import shutil
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_roundtrip(self):
        """POST knowledge/apply returns JSON with expected keys."""
        from _fixtures import http_post
        payload = {"indices": [1, 3], "actor": "test"}
        result = http_post(self._srv_thread.url,
                           "/api/adventures/ADV-999/knowledge/apply", payload)
        self.assertTrue(result.get("ok"), f"Expected ok=True, got {result!r}")
        self.assertIn("selection", result)
        sel = result["selection"]
        # Check required keys in the selection payload
        for key in ("adventure_id", "selected_indices", "recorded_by", "recorded_at"):
            self.assertIn(key, sel, f"selection missing key: {key}")
        self.assertEqual(sel["adventure_id"], "ADV-999")
        self.assertEqual(sorted(sel["selected_indices"]), [1, 3])


# ---------------------------------------------------------------------------
# TC-026: GET /api/adventures/{id} summary block (via HTTP)
# ---------------------------------------------------------------------------

class TestSummary(unittest.TestCase):
    """TC-026: summary block present and has correct shape (via HTTP)."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from _fixtures import make_synthetic_adventure, ServerThread
        cls._tmpdir = Path(tempfile.mkdtemp())
        make_synthetic_adventure(cls._tmpdir, "ADV-999")
        cls._srv_thread = ServerThread(cls._tmpdir / ".agent")
        cls._srv_thread.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._srv_thread.__exit__(None, None, None)
        import shutil
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_block_fields(self):
        """summary dict has all required keys and numeric consistency."""
        from _fixtures import http_get
        data = http_get(self._srv_thread.url, "/api/adventures/ADV-999")
        self.assertIn("summary", data)
        s = data["summary"]
        required = {"tc_total", "tc_passed", "tc_failed", "tc_pending",
                    "tasks_by_status", "next_action"}
        missing = required - set(s.keys())
        self.assertFalse(missing, f"summary missing keys: {missing}")
        self.assertEqual(
            s["tc_total"],
            s["tc_passed"] + s["tc_failed"] + s["tc_pending"],
        )
        na = s["next_action"]
        for k in ("kind", "label", "state_hint"):
            self.assertIn(k, na)


# ---------------------------------------------------------------------------
# TC-029: next_action via HTTP (synthetic review + unapproved)
# ---------------------------------------------------------------------------

class TestNextAction(unittest.TestCase):
    """TC-029: next_action.kind == approve_permissions for unapproved review state."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from _fixtures import make_synthetic_adventure, ServerThread
        cls._tmpdir = Path(tempfile.mkdtemp())
        make_synthetic_adventure(cls._tmpdir, "ADV-999",
                                 state="review", permissions_approved=False)
        cls._srv_thread = ServerThread(cls._tmpdir / ".agent")
        cls._srv_thread.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._srv_thread.__exit__(None, None, None)
        import shutil
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_review(self):
        """state=review + unapproved → next_action.kind == approve_permissions."""
        from _fixtures import http_get
        data = http_get(self._srv_thread.url, "/api/adventures/ADV-999")
        na = data["summary"]["next_action"]
        self.assertEqual(na["kind"], "approve_permissions")
        self.assertEqual(na["state_hint"], "review")


# ---------------------------------------------------------------------------
# TC-030: server.py is stdlib-only (via ast walk)
# ---------------------------------------------------------------------------

class TestStdlibOnly(unittest.TestCase):
    """TC-030: server.py imports only stdlib modules."""

    def test_no_third_party(self):
        """Parse server.py with ast; assert all top-level modules in stdlib."""
        source = SERVER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(SERVER_PATH))

        # Build stdlib set from sys.stdlib_module_names (Python 3.10+) or allowlist
        try:
            stdlib_names = sys.stdlib_module_names  # type: ignore[attr-defined]
        except AttributeError:
            # Fallback allowlist for older Python
            stdlib_names = {
                "__future__", "abc", "argparse", "ast", "collections",
                "contextlib", "datetime", "functools", "http", "io",
                "itertools", "json", "logging", "math", "os", "pathlib",
                "re", "shutil", "socket", "sys", "tempfile", "threading",
                "time", "traceback", "types", "typing", "unittest",
                "urllib", "uuid", "warnings",
            }

        non_stdlib: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in stdlib_names:
                        non_stdlib.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    top = node.module.split(".")[0]
                    if top not in stdlib_names:
                        non_stdlib.append(node.module)

        self.assertFalse(
            non_stdlib,
            f"server.py contains non-stdlib imports: {non_stdlib}",
        )


# ---------------------------------------------------------------------------
# TC-034 / TC-035: test-strategy.md cross-checks
# ---------------------------------------------------------------------------

_STRATEGY_PATH = REPO_ROOT / ".agent" / "adventures" / "ADV-009" / "tests" / "test-strategy.md"
_STRATEGY_SKIP = not _STRATEGY_PATH.exists()
_STRATEGY_SKIP_REASON = "test-strategy.md not found (ADV009-T001 may not have run yet)"


@unittest.skipIf(_STRATEGY_SKIP, _STRATEGY_SKIP_REASON)
class TestStrategyDoc(unittest.TestCase):
    """TC-034 + TC-035: test-strategy.md exists and is coherent."""

    @classmethod
    def setUpClass(cls):
        cls.strategy_text = _STRATEGY_PATH.read_text(encoding="utf-8")

    def test_tc_mapping(self):
        """TC-034: every autotest TC from manifest appears in test-strategy.md."""
        manifest_path = REPO_ROOT / ".agent" / "adventures" / "ADV-009" / "manifest.md"
        if not manifest_path.exists():
            self.skipTest("manifest.md not found")

        import re
        manifest_text = manifest_path.read_text(encoding="utf-8")

        # Find autotest TCs in manifest body (rows where proof_method col == autotest)
        # Table rows look like: | TC-NNN | desc | ... | autotest | ... |
        autotest_tcs: list[str] = []
        in_table = False
        header_seen = False
        for line in manifest_text.splitlines():
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
                if len(cells) >= 7:
                    tc_id = cells[0]
                    proof_method = cells[6] if len(cells) > 6 else ""
                    if proof_method.strip().lower() == "autotest" and re.match(r"TC-\d+", tc_id):
                        autotest_tcs.append(tc_id)

        if not autotest_tcs:
            self.skipTest("No autotest TCs found in manifest (table may not be parsed)")

        missing = [tc for tc in autotest_tcs
                   if tc not in self.strategy_text]
        self.assertFalse(
            missing,
            f"These autotest TCs from manifest are missing from test-strategy.md: {missing}",
        )

    def test_framework(self):
        """TC-035: test files import unittest; no other test framework found."""
        test_files = [
            REPO_ROOT / ".agent" / "adventures" / "ADV-009" / "tests" / "test_server.py",
            REPO_ROOT / ".agent" / "adventures" / "ADV-009" / "tests" / "test_ui_layout.py",
            REPO_ROOT / ".agent" / "adventures" / "ADV-009" / "tests" / "test_ui_smoke.py",
        ]
        forbidden = {"pytest", "nose", "hypothesis", "doctest"}

        for tf in test_files:
            if not tf.exists():
                continue
            source = tf.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(tf))
            self.assertIn(
                "unittest",
                source,
                f"{tf.name} does not import unittest",
            )
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        self.assertNotIn(
                            top, forbidden,
                            f"{tf.name} imports forbidden framework: {top}",
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.level == 0 and node.module:
                        top = node.module.split(".")[0]
                        self.assertNotIn(
                            top, forbidden,
                            f"{tf.name} imports forbidden framework: {top}",
                        )


if __name__ == "__main__":
    unittest.main()
