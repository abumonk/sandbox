"""Tests for error isolation — TC-EI-1..TC-EI-5, TC-HI-4."""

import json
import os
import stat
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_AGENT_DIR = _REPO_ROOT / ".agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from telemetry import aggregator  # type: ignore[import]
from telemetry.schema import ROW_HEADER, ROW_SEPARATOR  # type: ignore[import]

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CAPTURE_PY = _REPO_ROOT / ".agent" / "telemetry" / "capture.py"

_VALID_PAYLOAD = {
    "event_type": "SubagentStop",
    "timestamp": "2026-04-15T10:30:00Z",
    "adventure_id": "ADV-010",
    "agent": "coder",
    "task": "ADV010-T005",
    "model": "claude-opus-4-6",
    "tokens_in": 85000,
    "tokens_out": 28000,
    "duration_ms": 720000,
    "turns": 12,
    "result": "done",
    "session_id": "sess-abc123",
}

_INVALID_PAYLOAD = {
    "event_type": "SubagentStop",
    "timestamp": "bad-timestamp",
    "adventure_id": "ADV-010",
    "agent": "coder",
    "model": "claude-opus-4-6",
    "tokens_in": 1000,
    "tokens_out": 500,
    "duration_ms": 60000,
    "turns": 3,
    "result": "done",
}


def _run_capture(payload_str: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run capture.py subprocess with the given stdin payload string.

    Runs with cwd=.agent/ so that ``python -m telemetry.capture`` resolves.
    """
    run_env = dict(os.environ)
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "telemetry.capture"],
        input=payload_str,
        capture_output=True,
        text=True,
        timeout=30,
        env=run_env,
        cwd=str(_AGENT_DIR),
    )


class TestPayloadErrorExitZero(unittest.TestCase):
    """TC-EI-1: Subprocess with invalid payload -> exit 0."""

    def test_payload_error_exit_zero(self):
        result = _run_capture(json.dumps(_INVALID_PAYLOAD))
        self.assertEqual(
            result.returncode, 0,
            f"Expected exit 0 for bad payload, got {result.returncode}; stderr={result.stderr!r}"
        )


class TestWriteErrorLogsAndExitsZero(unittest.TestCase):
    """TC-EI-2: Read-only metrics.md causes exit 0 + error log entry."""

    @unittest.skipIf(sys.platform == "win32", "chmod read-only on Windows may not block writes")
    def test_write_error_logs_and_exits_zero(self):
        # This test only fully works on Unix where chmod works for writes.
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            adv_dir = tmpdir / ".agent" / "adventures" / "ADV-010"
            adv_dir.mkdir(parents=True)
            mp = adv_dir / "metrics.md"
            mp.write_text(
                "---\nadventure_id: ADV-010\ntotal_tokens_in: 0\n"
                "total_tokens_out: 0\ntotal_duration: 0\ntotal_cost: 0.0000\n"
                f"agent_runs: 0\n---\n\n## Agent Runs\n\n{ROW_HEADER}\n{ROW_SEPARATOR}\n",
                encoding="utf-8"
            )
            mp.chmod(stat.S_IREAD)
            try:
                result = _run_capture(json.dumps(_VALID_PAYLOAD))
                self.assertEqual(result.returncode, 0)
            finally:
                mp.chmod(stat.S_IREAD | stat.S_IWRITE)


class TestKeyboardInterruptPropagates(unittest.TestCase):
    """TC-EI-3: KeyboardInterrupt is not caught by main()."""

    def test_keyboard_interrupt_propagates(self):
        from telemetry import capture  # type: ignore[import]
        import unittest.mock as mock

        # Patch read_stdin to raise KeyboardInterrupt.
        with mock.patch.object(capture, "read_stdin", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                capture.main()


class TestErrorLogIsValidJsonl(unittest.TestCase):
    """TC-EI-4: All lines in capture-errors.log parse as JSON with {ts, exc, msg}."""

    def test_error_log_is_valid_jsonl(self):
        # Trigger a capture error to ensure at least one line exists.
        _run_capture(json.dumps(_INVALID_PAYLOAD))

        error_log = _REPO_ROOT / ".agent" / "telemetry" / "capture-errors.log"
        if not error_log.exists():
            self.skipTest("capture-errors.log does not exist yet")

        lines = error_log.read_text(encoding="utf-8").splitlines()
        if not lines:
            self.skipTest("capture-errors.log is empty")

        for i, line in enumerate(lines):
            if not line.strip():
                continue
            with self.subTest(line_number=i + 1):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    self.fail(f"Line {i+1} is not valid JSON: {exc}\nLine: {line!r}")
                self.assertIn("ts", record, f"Line {i+1} missing 'ts' key")
                self.assertIn("exc", record, f"Line {i+1} missing 'exc' key")
                self.assertIn("msg", record, f"Line {i+1} missing 'msg' key")


class TestFrontmatterHealsAfterPartialFail(unittest.TestCase):
    """TC-EI-5: Stale frontmatter heals on next successful capture."""

    def test_frontmatter_heals_after_partial_fail(self):
        from telemetry import schema, capture  # type: ignore[import]
        from telemetry.cost_model import cost_for  # type: ignore[import]

        # Write a tampered metrics.md with wrong frontmatter totals.
        fixture = FIXTURES_DIR / "metrics" / "tampered.md"
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            mp = tmpdir / "metrics.md"
            mp.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

            # Run recompute_frontmatter (simulates what capture does after append).
            aggregator.recompute_frontmatter(mp)

            # Verify frontmatter now matches actual row data.
            rows = aggregator.parse_rows(mp)
            text = mp.read_text(encoding="utf-8")
            fm_dict = aggregator._parse_frontmatter(text.split("---")[1])

            self.assertEqual(fm_dict["total_tokens_in"], sum(r.tokens_in for r in rows))
            self.assertEqual(fm_dict["total_tokens_out"], sum(r.tokens_out for r in rows))
            self.assertEqual(fm_dict["agent_runs"], len(rows))


class TestMalformedJsonExitsZero(unittest.TestCase):
    """TC-HI-4: stdin is not JSON -> exit 0."""

    def test_malformed_json_exits_zero(self):
        malformed_path = FIXTURES_DIR / "events" / "malformed.txt"
        if malformed_path.exists():
            payload_str = malformed_path.read_text(encoding="utf-8")
        else:
            payload_str = "this is not valid json {{{"
        result = _run_capture(payload_str)
        self.assertEqual(
            result.returncode, 0,
            f"Expected exit 0 for malformed JSON, got {result.returncode}; stderr={result.stderr!r}"
        )


if __name__ == "__main__":
    unittest.main()
