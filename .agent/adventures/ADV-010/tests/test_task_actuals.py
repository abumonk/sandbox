"""Tests for task_actuals.py — TC-AG-4, TC-AG-5."""

import sys
import tempfile
import unittest
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parents[4] / ".agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from telemetry import task_actuals, aggregator  # type: ignore[import]
from telemetry.schema import ROW_HEADER, ROW_SEPARATOR  # type: ignore[import]
from telemetry.cost_model import cost_for  # type: ignore[import]

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _make_metrics(tmpdir: Path, rows: list[str], *, adventure_id: str = "ADV-099") -> Path:
    fm = (
        f"---\n"
        f"adventure_id: {adventure_id}\n"
        f"total_tokens_in: 0\n"
        f"total_tokens_out: 0\n"
        f"total_duration: 0\n"
        f"total_cost: 0.0000\n"
        f"agent_runs: 0\n"
        f"---\n"
    )
    table = f"\n## Agent Runs\n\n{ROW_HEADER}\n{ROW_SEPARATOR}\n"
    row_block = "".join(r + "\n" for r in rows)
    mp = tmpdir / "metrics.md"
    mp.write_text(fm + table + row_block, encoding="utf-8")
    aggregator.recompute_frontmatter(mp)
    return mp


def _make_manifest(tmpdir: Path, task_rows: list[dict], *, adventure_id: str = "ADV-099") -> Path:
    header = (
        "| Task | Access Requirements | Skill Set | Est. Duration | Est. Tokens"
        " | Est. Cost | Actual Duration | Actual Tokens | Actual Cost | Variance |"
    )
    sep = (
        "|------|---------------------|-----------|---------------|-------------|"
        "-----------|-----------------|---------------|-------------|----------|"
    )
    data_lines = []
    for row in task_rows:
        task = row.get("task", "ADV099-T001")
        est_tokens = row.get("est_tokens", "--")
        data_lines.append(
            f"| {task} | Read, Write | coding | 20min | {est_tokens}"
            f" | --- | --- | --- | --- | --- |"
        )
    fm = (
        f"---\nid: {adventure_id}\ntitle: Test\nstate: completed\n---\n"
    )
    body = "\n## Evaluations\n\n" + header + "\n" + sep + "\n"
    body += "\n".join(data_lines) + "\n"
    mp = tmpdir / "manifest.md"
    mp.write_text(fm + body, encoding="utf-8")
    return mp


class TestUpdateTaskActualsValues(unittest.TestCase):
    """TC-AG-4: Hand-computed Actual Duration, Tokens, Cost, Variance match."""

    def test_update_task_actuals_values(self):
        # Row for ADV099-T001: opus, 85000 in, 28000 out, 720s, cost=1.6950
        rows = [
            "| 2fb32edcd1f9 | 2026-04-15T10:30:00Z | coder | ADV099-T001 | opus | 85000 | 28000 | 720 | 12 | 1.6950 | done | high |",
        ]
        task_rows = [
            {"task": "ADV099-T001", "est_tokens": "45000"},
            {"task": "ADV099-T002", "est_tokens": "20000"},
        ]
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            _make_metrics(tmpdir, rows)
            manifest_p = _make_manifest(tmpdir, task_rows)

            task_actuals.update(manifest_p, "ADV099-T001")

            content = manifest_p.read_text(encoding="utf-8")
            # Parse the updated row.
            lines = content.split("\n")
            target_line = None
            for line in lines:
                if "| ADV099-T001 |" in line and "coding" in line:
                    target_line = line
                    break
            self.assertIsNotNone(target_line, "ADV099-T001 row not found in manifest")

            parts = [c.strip() for c in target_line.split("|")[1:-1]]
            # Find column indices from header.
            for i, line in enumerate(lines):
                if "| Task |" in line:
                    header_parts = [c.strip() for c in line.split("|")[1:-1]]
                    break
            col = {name: idx for idx, name in enumerate(header_parts)}

            # Hand-computed: 85000+28000=113000 total tokens, 720s = "12min", cost=$1.6950
            actual_duration = parts[col["Actual Duration"]]
            actual_tokens = int(parts[col["Actual Tokens"]])
            actual_cost = parts[col["Actual Cost"]]
            variance = parts[col["Variance"]]

            self.assertEqual(actual_duration, "12min")
            self.assertEqual(actual_tokens, 113000)
            self.assertEqual(actual_cost, "$1.6950")
            # Variance: (113000 - 45000) / 45000 * 100 = +151%
            self.assertEqual(variance, "+151%")


class TestUpdateLeavesOtherRowsByteEqual(unittest.TestCase):
    """TC-AG-5: Only the targeted task row changes; all others are byte-equal."""

    def test_update_leaves_other_rows_byte_equal(self):
        rows = [
            "| 2fb32edcd1f9 | 2026-04-15T10:30:00Z | coder | ADV099-T001 | opus | 85000 | 28000 | 720 | 12 | 1.6950 | done | high |",
            "| 588cb9f9256f | 2026-04-15T11:00:00Z | planner | ADV099-T002 | sonnet | 20000 | 3500 | 90 | 7 | 0.0705 | ready | high |",
        ]
        task_rows = [
            {"task": "ADV099-T001", "est_tokens": "45000"},
            {"task": "ADV099-T002", "est_tokens": "20000"},
        ]
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            _make_metrics(tmpdir, rows)
            manifest_p = _make_manifest(tmpdir, task_rows)

            before = manifest_p.read_text(encoding="utf-8")
            before_lines = before.split("\n")

            task_actuals.update(manifest_p, "ADV099-T001")

            after = manifest_p.read_text(encoding="utf-8")
            after_lines = after.split("\n")

            changed_rows = []
            for i, (b, a) in enumerate(zip(before_lines, after_lines)):
                if b != a:
                    changed_rows.append((i, b, a))

            # Only one row should have changed (the ADV099-T001 row).
            self.assertEqual(
                len(changed_rows), 1,
                f"Expected exactly 1 changed row, got {len(changed_rows)}: {changed_rows}"
            )
            # Verify the changed row is the T001 row.
            _, changed_before, changed_after = changed_rows[0]
            self.assertIn("ADV099-T001", changed_after)
            # T002 row unchanged.
            t002_before = next((l for l in before_lines if "ADV099-T002" in l), None)
            t002_after = next((l for l in after_lines if "ADV099-T002" in l), None)
            self.assertEqual(t002_before, t002_after, "ADV099-T002 row was modified")


if __name__ == "__main__":
    unittest.main()
