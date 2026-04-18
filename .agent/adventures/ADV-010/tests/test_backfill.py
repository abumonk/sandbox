"""Tests for tools/backfill.py — TC-BF-1..TC-BF-6."""

import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_AGENT_DIR = _REPO_ROOT / ".agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from telemetry.tools.backfill import (  # type: ignore[import]
    reconstruct_adventure,
    write_metrics_new,
    apply_with_backup,
    discover_adventures,
)
from telemetry import aggregator  # type: ignore[import]
from telemetry.schema import ROW_HEADER, ROW_SEPARATOR  # type: ignore[import]

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _make_task_file(tasks_dir: Path, task_id: str, status: str = "done", updated: str = "2026-04-15T10:00:00Z") -> Path:
    """Create a minimal task file with status and updated frontmatter."""
    tasks_dir.mkdir(parents=True, exist_ok=True)
    content = (
        f"---\n"
        f"id: {task_id}\n"
        f"status: {status}\n"
        f"updated: {updated}\n"
        f"---\n\n## Log\n"
    )
    p = tasks_dir / f"{task_id}.md"
    p.write_text(content, encoding="utf-8")
    return p


def _make_metrics_with_rows(adv_dir: Path, adventure_id: str, rows: list[str]) -> Path:
    """Write a metrics.md with given rows in adv_dir."""
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
    mp = adv_dir / "metrics.md"
    mp.write_text(fm + table + row_block, encoding="utf-8")
    aggregator.recompute_frontmatter(mp)
    return mp


class TestEveryCompletedAdventureHasRuns(unittest.TestCase):
    """TC-BF-1: After backfill, every completed adventure has agent_runs > 0."""

    def test_every_completed_adventure_has_runs(self):
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)

            # Create 2 synthetic adventure directories.
            for adv_id in ["ADV-901", "ADV-902"]:
                adv_dir = tmpdir / adv_id
                adv_dir.mkdir()
                # One done task with an existing row.
                task_id = adv_id.replace("-", "") + "-T001"  # e.g. ADV901-T001
                _make_task_file(adv_dir / "tasks", task_id, status="done")
                _make_metrics_with_rows(
                    adv_dir,
                    adv_id,
                    [
                        f"| a1b2c3d4e5f6 | 2026-04-15T10:00:00Z | coder | {task_id}"
                        f" | opus | 10000 | 5000 | 60 | 3 | 0.2250 | done | medium |"
                    ],
                )

            # Run reconstruct + write for each adventure.
            for adv_id in ["ADV-901", "ADV-902"]:
                adv_dir = tmpdir / adv_id
                rows = reconstruct_adventure(adv_dir, sources=["existing"])
                write_metrics_new(adv_dir, rows)
                apply_with_backup(adv_dir)

                # Verify agent_runs > 0.
                mp = adv_dir / "metrics.md"
                parsed_rows = aggregator.parse_rows(mp)
                self.assertGreater(len(parsed_rows), 0, f"{adv_id}: no rows after backfill")


class TestAdv008RowsPreservedTildesStripped(unittest.TestCase):
    """TC-BF-2: Numeric values preserved; tildes stripped from output."""

    def test_adv008_rows_preserved_tildes_stripped(self):
        fixture = FIXTURES_DIR / "metrics" / "with_tildes.md"
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            adv_dir = tmpdir / "ADV-099"
            adv_dir.mkdir()
            mp = adv_dir / "metrics.md"
            mp.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

            # Reconstruct using existing source only.
            rows = reconstruct_adventure(adv_dir, sources=["existing"])
            self.assertGreater(len(rows), 0, "No rows reconstructed from tilde fixture")

            # Write new metrics.
            write_metrics_new(adv_dir, rows)
            apply_with_backup(adv_dir)

            # Verify no tildes in new metrics.md.
            new_content = mp.read_text(encoding="utf-8")
            self.assertNotIn("~", new_content, "Tilde found in backfilled metrics.md")

            # Verify numeric values are preserved (not zeroed out).
            parsed_rows = aggregator.parse_rows(mp)
            self.assertGreater(len(parsed_rows), 0)
            # Original rows had tokens_in values 45000 and 18000 (tilde-stripped).
            all_tokens_in = [r.tokens_in for r in parsed_rows]
            self.assertTrue(
                any(t > 0 for t in all_tokens_in),
                f"All tokens_in are zero after backfill: {all_tokens_in}"
            )


class TestBackfillIdempotent(unittest.TestCase):
    """TC-BF-3: Byte-identical second run."""

    def test_backfill_idempotent(self):
        fixture = FIXTURES_DIR / "metrics" / "multi_model.md"
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            adv_dir = tmpdir / "ADV-099"
            adv_dir.mkdir()
            mp = adv_dir / "metrics.md"
            mp.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

            # First run.
            rows1 = reconstruct_adventure(adv_dir, sources=["existing"])
            write_metrics_new(adv_dir, rows1)
            apply_with_backup(adv_dir)
            content1 = mp.read_bytes()

            # Second run.
            rows2 = reconstruct_adventure(adv_dir, sources=["existing"])
            write_metrics_new(adv_dir, rows2)
            apply_with_backup(adv_dir)
            content2 = mp.read_bytes()

            self.assertEqual(content1, content2, "Backfill is not idempotent: second run differs")


class TestBackfillRowsNeverHighConfidence(unittest.TestCase):
    """TC-BF-4: No row has confidence == "high" after backfill."""

    def test_backfill_rows_never_high_confidence(self):
        fixture = FIXTURES_DIR / "metrics" / "multi_model.md"
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            adv_dir = tmpdir / "ADV-099"
            adv_dir.mkdir()
            mp = adv_dir / "metrics.md"
            mp.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

            rows = reconstruct_adventure(adv_dir, sources=["existing"])
            write_metrics_new(adv_dir, rows)
            apply_with_backup(adv_dir)

            parsed_rows = aggregator.parse_rows(mp)
            for row in parsed_rows:
                self.assertNotEqual(
                    row.confidence, "high",
                    f"Backfill emitted a row with confidence='high': task={row.task}"
                )


class TestUnreconstructableRowEmitted(unittest.TestCase):
    """TC-BF-5: Task with no sources -> result=unrecoverable row."""

    def test_unreconstructable_row_emitted(self):
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            adv_dir = tmpdir / "ADV-999"
            adv_dir.mkdir()

            # One done task file, but no candidates from any source.
            _make_task_file(adv_dir / "tasks", "ADV999-T001", status="done")

            # Empty metrics.md.
            _make_metrics_with_rows(adv_dir, "ADV-999", [])

            rows = reconstruct_adventure(adv_dir, sources=["existing"])
            write_metrics_new(adv_dir, rows)
            apply_with_backup(adv_dir)

            parsed_rows = aggregator.parse_rows(adv_dir / "metrics.md")
            unrecoverable = [r for r in parsed_rows if r.result == "unrecoverable"]
            self.assertGreater(
                len(unrecoverable), 0,
                f"Expected at least one unrecoverable row, got: {[r.result for r in parsed_rows]}"
            )


class TestNoApplyDoesNotModifyOriginal(unittest.TestCase):
    """TC-BF-6: Running without apply leaves original metrics.md untouched."""

    def test_no_apply_does_not_modify_original(self):
        fixture = FIXTURES_DIR / "metrics" / "single_row.md"
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            adv_dir = tmpdir / "ADV-099"
            adv_dir.mkdir()
            mp = adv_dir / "metrics.md"
            original_content = fixture.read_text(encoding="utf-8")
            mp.write_text(original_content, encoding="utf-8")

            # Reconstruct and write .new but do NOT apply.
            rows = reconstruct_adventure(adv_dir, sources=["existing"])
            write_metrics_new(adv_dir, rows)
            # Do NOT call apply_with_backup.

            # Original should be identical (normalise line endings for cross-platform).
            current = mp.read_text(encoding="utf-8").replace("\r\n", "\n")
            original_norm = original_content.replace("\r\n", "\n")
            self.assertEqual(
                current,
                original_norm,
                "metrics.md was modified without --apply"
            )
            # .new file should exist.
            new_path = adv_dir / "metrics.md.new"
            self.assertTrue(new_path.exists(), "metrics.md.new was not created")


if __name__ == "__main__":
    unittest.main()
