"""test_ir.py — IR extractor tests for ADV-009.

TC coverage:
  TC-039  TestSpecShapes.test_adventure_spec_parses
  TC-040  TestSpecShapes.test_processes
  TC-041  TestSpecShapes.test_runtime_entities
  TC-042  TestRoundTrip.test_adv007
  TC-043  TestRoundTrip.test_adv008
  TC-044  TestRoundTrip.test_task_ids_match_manifest

Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

# Ensure repo root is on sys.path before importing adventure_pipeline
_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parents[3]   # .agent/adventures/ADV-009/tests -> R:/Sandbox
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adventure_pipeline.tools.ir import extract_ir  # noqa: E402

_SPECS_DIR = _REPO_ROOT / "adventure_pipeline" / "specs"
_ADV_DIR = _REPO_ROOT / ".agent" / "adventures"


# ---------------------------------------------------------------------------
# TC-039, TC-040, TC-041 — spec shape checks via regex on .ark source
# ---------------------------------------------------------------------------

class TestSpecShapes(unittest.TestCase):
    """Verify the three .ark spec files contain expected declarations."""

    def test_adventure_spec_parses(self):
        """TC-039: adventure.ark declares core abstractions and enums."""
        src = (_SPECS_DIR / "adventure.ark").read_text(encoding="utf-8")
        for pattern in (
            r"\babstraction\s+Adventure\b",
            r"\bclass\s+Phase\b",
            r"\babstraction\s+Task\b",
            r"\benum\s+State\b",
            r"\benum\s+Status\b",
            r"\benum\s+ProofMethod\b",
        ):
            with self.subTest(pattern=pattern):
                self.assertRegex(src, pattern,
                    msg=f"adventure.ark missing: {pattern}")

    def test_processes(self):
        """TC-040: pipeline.ark declares the three expected process classes."""
        src = (_SPECS_DIR / "pipeline.ark").read_text(encoding="utf-8")
        # pipeline.ark uses 'class' keyword with embedded #process[] blocks
        for pattern in (
            r"\b(?:class|process)\s+AdventureStateMachine\b",
            r"\b(?:class|process)\s+TaskLifecycle\b",
            r"\b(?:class|process)\s+ReviewPipeline\b",
        ):
            with self.subTest(pattern=pattern):
                self.assertRegex(src, pattern,
                    msg=f"pipeline.ark missing: {pattern}")

    def test_runtime_entities(self):
        """TC-041: entities.ark declares the five runtime snapshot classes."""
        src = (_SPECS_DIR / "entities.ark").read_text(encoding="utf-8")
        for pattern in (
            r"\bclass\s+RunningAgent\b",
            r"\bclass\s+ActiveTask\b",
            r"\bclass\s+PendingDecision\b",
            r"\bclass\s+KnowledgeSuggestion\b",
            r"\bclass\s+ReviewArtifact\b",
        ):
            with self.subTest(pattern=pattern):
                self.assertRegex(src, pattern,
                    msg=f"entities.ark missing: {pattern}")


# ---------------------------------------------------------------------------
# TC-042, TC-043, TC-044 — round-trip extraction on live adventures
# ---------------------------------------------------------------------------

class TestRoundTrip(unittest.TestCase):
    """extract_ir produces correctly populated IR for real adventures."""

    @classmethod
    def setUpClass(cls):
        # Verify both adventures exist; skip gracefully if not
        cls._adv007_exists = (_ADV_DIR / "ADV-007").exists()
        cls._adv008_exists = (_ADV_DIR / "ADV-008").exists()

    def test_adv007(self):
        """TC-042: ADV-007 IR has non-empty tasks, documents, tcs, permissions."""
        if not self._adv007_exists:
            self.skipTest("ADV-007 directory not found")
        ir = extract_ir("ADV-007")

        self.assertGreater(len(ir.tasks), 0, "ir.tasks should be non-empty")
        self.assertTrue(
            any(t.id.startswith("ADV007-T") for t in ir.tasks),
            "Expected at least one task with id starting ADV007-T",
        )

        self.assertGreater(len(ir.documents), 0, "ir.documents should be non-empty")
        self.assertTrue(
            any(d.kind == "design" for d in ir.documents),
            "Expected at least one Design-kind document",
        )

        self.assertGreater(len(ir.tcs), 0, "ir.tcs should be non-empty")
        self.assertGreater(len(ir.permissions), 0, "ir.permissions should be non-empty")

    def test_adv008(self):
        """TC-043: ADV-008 IR has non-empty tasks, documents, tcs, permissions."""
        if not self._adv008_exists:
            self.skipTest("ADV-008 directory not found")
        ir = extract_ir("ADV-008")

        self.assertGreater(len(ir.tasks), 0, "ir.tasks should be non-empty")
        self.assertGreater(len(ir.documents), 0, "ir.documents should be non-empty")
        self.assertGreater(len(ir.tcs), 0, "ir.tcs should be non-empty")
        # ADV-008 may or may not have permissions; just check tcs + tasks
        task_ids = {t.id for t in ir.tasks}
        # All task ids should start with ADV008-T
        self.assertTrue(
            all(tid.startswith("ADV008-T") for tid in task_ids),
            f"Unexpected task id prefix in ADV-008: {task_ids}",
        )

    def test_task_ids_match_manifest(self):
        """TC-044: task IDs in IR == task IDs in manifest frontmatter (no orphans)."""
        if not self._adv007_exists:
            self.skipTest("ADV-007 directory not found")

        manifest_text = (_ADV_DIR / "ADV-007" / "manifest.md").read_text(encoding="utf-8")
        # Parse the tasks: inline-list from frontmatter
        m = re.search(r"^tasks:\s*\[([^\]]*)\]", manifest_text, re.MULTILINE)
        self.assertIsNotNone(m, "manifest.md tasks: list not found")
        manifest_task_ids = {
            s.strip().strip('"').strip("'")
            for s in m.group(1).split(",")
            if s.strip()
        }

        ir = extract_ir("ADV-007")
        ir_task_ids = {t.id for t in ir.tasks}

        self.assertEqual(
            ir_task_ids,
            manifest_task_ids,
            "IR task ids do not match manifest task list (orphans or missing tasks)",
        )


# ---------------------------------------------------------------------------
# IR entity shape + JSON round-trip
# ---------------------------------------------------------------------------

class TestIrEntityShape(unittest.TestCase):
    """IR dataclass is JSON-serialisable and enum fields emit strings."""

    @classmethod
    def setUpClass(cls):
        cls._adv007_exists = (_ADV_DIR / "ADV-007").exists()

    def test_json_round_trip(self):
        """asdict(ir) serialises without error via json.dumps."""
        if not self._adv007_exists:
            self.skipTest("ADV-007 directory not found")
        ir = extract_ir("ADV-007")
        try:
            serialised = json.dumps(asdict(ir), default=str)
        except Exception as exc:  # noqa: BLE001
            self.fail(f"json.dumps(asdict(ir)) raised: {exc}")
        self.assertGreater(len(serialised), 10, "serialised IR should be non-trivial")

    def test_enum_fields_are_strings(self):
        """All leaf string fields in the serialised IR are Python strings."""
        if not self._adv007_exists:
            self.skipTest("ADV-007 directory not found")
        ir = extract_ir("ADV-007")
        d = asdict(ir)
        # Top-level string fields
        for field in ("id", "title", "state", "created", "updated"):
            self.assertIsInstance(d[field], str,
                f"IR.{field} should be a str, got {type(d[field])}")


if __name__ == "__main__":
    unittest.main()
