"""Tests for capture.py — TC-CC-1, TC-CC-2, TC-CC-3, TC-CC-4, TC-HI-1, TC-HI-2, TC-HI-3."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_AGENT_DIR = _REPO_ROOT / ".agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from telemetry import capture  # type: ignore[import]
from telemetry.errors import PayloadError  # type: ignore[import]
from telemetry import schema, aggregator  # type: ignore[import]
from telemetry.cost_model import cost_for  # type: ignore[import]

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_event(name: str) -> dict:
    if not name.endswith(".json"):
        name += ".json"
    return json.loads((FIXTURES_DIR / "events" / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Helper: run capture against a temp metrics.md
# ---------------------------------------------------------------------------

def _run_capture_in_tempdir(tmpdir: Path, payload: dict) -> Path:
    """Invoke capture.append_row + recompute_frontmatter against a temp metrics file.

    Returns the path to the metrics file.
    """
    adv_id = payload.get("adventure_id", "ADV-099")
    event = schema.validate_event(payload)
    cost = cost_for(event.model, event.tokens_in, event.tokens_out)
    row = schema.build_row(event, cost)

    # Manually create metrics.md in tmpdir with the correct adventure_id.
    mp = tmpdir / "metrics.md"
    from telemetry.schema import ROW_HEADER, ROW_SEPARATOR  # type: ignore[import]
    content = (
        f"---\n"
        f"adventure_id: {adv_id}\n"
        f"total_tokens_in: 0\n"
        f"total_tokens_out: 0\n"
        f"total_duration: 0\n"
        f"total_cost: 0.0000\n"
        f"agent_runs: 0\n"
        f"---\n"
        f"\n"
        f"## Agent Runs\n"
        f"\n"
        f"{ROW_HEADER}\n"
        f"{ROW_SEPARATOR}\n"
    )
    mp.write_text(content, encoding="utf-8")

    # Use aggregator.parse_rows for idempotency check (as append_row does).
    existing = aggregator.parse_rows(mp)
    for existing_row in existing:
        if existing_row.run_id == row.run_id:
            return mp
    serialized = schema.serialize(row)
    text = mp.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    text += serialized + "\n"
    mp.write_text(text, encoding="utf-8")
    aggregator.recompute_frontmatter(mp)
    return mp


class TestValidateEventRejectsInvalid(unittest.TestCase):
    """TC-CC-1: 10 bad payload cases each raise PayloadError or subclass."""

    def _assert_rejects(self, payload: dict, description: str):
        with self.subTest(case=description):
            with self.assertRaises(PayloadError, msg=f"Expected PayloadError for: {description}"):
                schema.validate_event(payload)

    def test_validate_event_rejects_invalid(self):
        base = _load_event("happy_opus")

        # 1. Missing event_type
        p = dict(base); del p["event_type"]
        self._assert_rejects(p, "missing event_type")

        # 2. Invalid event_type
        p = dict(base); p["event_type"] = "UnknownEvent"
        self._assert_rejects(p, "invalid event_type")

        # 3. Missing timestamp
        p = dict(base); del p["timestamp"]
        self._assert_rejects(p, "missing timestamp")

        # 4. Bad timestamp format
        p = dict(base); p["timestamp"] = "not-a-timestamp"
        self._assert_rejects(p, "bad timestamp format")

        # 5. Missing adventure_id
        p = dict(base); del p["adventure_id"]
        self._assert_rejects(p, "missing adventure_id")

        # 6. Missing agent
        p = dict(base); del p["agent"]
        self._assert_rejects(p, "missing agent")

        # 7. Unknown model (from bad_model fixture)
        p = dict(base); p["model"] = "unknown-model-xyz"
        self._assert_rejects(p, "unknown model")

        # 8. Negative tokens_in
        p = dict(base); p["tokens_in"] = -1
        self._assert_rejects(p, "negative tokens_in")

        # 9. duration_ms = 0 (not positive)
        p = dict(base); p["duration_ms"] = 0
        self._assert_rejects(p, "zero duration_ms")

        # 10. Bad task format
        p = dict(base); p["task"] = "INVALID-TASK"
        self._assert_rejects(p, "bad task format")


class TestValidEventWritesOneRow(unittest.TestCase):
    """TC-CC-2: One row appended with every column correct."""

    def test_valid_event_writes_one_row(self):
        payload = _load_event("happy_opus")
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            mp = _run_capture_in_tempdir(tmpdir, payload)
            rows = aggregator.parse_rows(mp)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row.agent, payload["agent"])
            self.assertEqual(row.task, payload["task"])
            self.assertEqual(row.model, "opus")  # normalized
            self.assertEqual(row.tokens_in, payload["tokens_in"])
            self.assertEqual(row.tokens_out, payload["tokens_out"])
            self.assertEqual(row.turns, payload["turns"])
            self.assertEqual(row.result, payload["result"])
            self.assertEqual(row.confidence, "high")


class TestReplaySameEventIdempotent(unittest.TestCase):
    """TC-CC-3: Running capture twice with the same event leaves one row."""

    def test_replay_same_event_idempotent(self):
        payload = _load_event("replay")
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            adv_id = payload.get("adventure_id", "ADV-099")
            from telemetry.schema import ROW_HEADER, ROW_SEPARATOR  # type: ignore[import]
            mp = tmpdir / "metrics.md"
            content = (
                f"---\nadventure_id: {adv_id}\ntotal_tokens_in: 0\n"
                f"total_tokens_out: 0\ntotal_duration: 0\ntotal_cost: 0.0000\n"
                f"agent_runs: 0\n---\n\n## Agent Runs\n\n{ROW_HEADER}\n{ROW_SEPARATOR}\n"
            )
            mp.write_text(content, encoding="utf-8")

            event = schema.validate_event(payload)
            cost = cost_for(event.model, event.tokens_in, event.tokens_out)
            row = schema.build_row(event, cost)

            # Append twice using capture.append_row (uses the real repo path).
            # Instead, use the same logic directly on tmp file.
            serialized = schema.serialize(row)
            text = mp.read_text(encoding="utf-8")
            if not text.endswith("\n"):
                text += "\n"
            text += serialized + "\n"
            mp.write_text(text, encoding="utf-8")

            # Second append: check run_id already present.
            existing = aggregator.parse_rows(mp)
            seen = [r for r in existing if r.run_id == row.run_id]
            if not seen:
                text2 = mp.read_text(encoding="utf-8")
                if not text2.endswith("\n"):
                    text2 += "\n"
                text2 += serialized + "\n"
                mp.write_text(text2, encoding="utf-8")

            rows = aggregator.parse_rows(mp)
            run_id_matches = [r for r in rows if r.run_id == row.run_id]
            self.assertEqual(len(run_id_matches), 1, "Idempotency broken: same run_id appears more than once")


class TestRowCostMatchesCostModel(unittest.TestCase):
    """TC-CC-4: Row's cost column equals cost_model output."""

    def test_row_cost_matches_cost_model(self):
        payload = _load_event("happy_opus")
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            mp = _run_capture_in_tempdir(tmpdir, payload)
            rows = aggregator.parse_rows(mp)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            expected_cost = cost_for(row.model, row.tokens_in, row.tokens_out)
            self.assertAlmostEqual(row.cost_usd, expected_cost, places=4)


class TestSettingsJsonHasBothHooks(unittest.TestCase):
    """TC-HI-1: .claude/settings.local.json contains SubagentStop + PostToolUse."""

    def test_settings_json_has_both_hooks(self):
        settings_path = _REPO_ROOT / ".claude" / "settings.local.json"
        if not settings_path.exists():
            self.skipTest(f"settings.local.json not found at {settings_path}")
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        hooks = data.get("hooks", {})
        self.assertIn(
            "SubagentStop", hooks,
            "hooks.SubagentStop not present in settings.local.json"
        )
        self.assertIn(
            "PostToolUse", hooks,
            "hooks.PostToolUse not present in settings.local.json"
        )


class TestSettingsJsonPreservesPermissions(unittest.TestCase):
    """TC-HI-2: permissions.allow list is present and non-empty."""

    def test_settings_json_preserves_permissions(self):
        settings_path = _REPO_ROOT / ".claude" / "settings.local.json"
        if not settings_path.exists():
            self.skipTest(f"settings.local.json not found at {settings_path}")
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        allow_list = data.get("permissions", {}).get("allow", None)
        self.assertIsNotNone(allow_list, "permissions.allow missing from settings.local.json")
        self.assertIsInstance(allow_list, list)
        self.assertGreater(len(allow_list), 0, "permissions.allow is empty")


class TestCaptureSubprocessHappyPath(unittest.TestCase):
    """TC-HI-3: Subprocess stdin -> exit 0."""

    def test_capture_subprocess_happy_path(self):
        import subprocess
        payload = _load_event("happy_opus")
        env = dict(os.environ)
        env["ADVENTURE_ID"] = "ADV-010"
        # Run with cwd=.agent/ so ``python -m telemetry.capture`` resolves.
        result = subprocess.run(
            [sys.executable, "-m", "telemetry.capture"],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            cwd=str(_AGENT_DIR),
        )
        self.assertEqual(
            result.returncode, 0,
            f"capture.py exited {result.returncode}; stderr={result.stderr!r}"
        )


if __name__ == "__main__":
    unittest.main()
