"""Tests for aggregator.py — TC-AG-1, TC-AG-2, TC-AG-3, TC-AG-6."""

import sys
import tempfile
import unittest
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parents[4] / ".agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from telemetry import aggregator  # type: ignore[import]
from telemetry.schema import ROW_HEADER, ROW_SEPARATOR  # type: ignore[import]

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _make_metrics(tmpdir: Path, rows: list[str], *, adventure_id: str = "ADV-099") -> Path:
    """Write a metrics.md with given row strings and return its path."""
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
    return mp


class TestTotalTokensInMatchesRows(unittest.TestCase):
    """TC-AG-1: total_tokens_in frontmatter equals sum of row tokens_in."""

    def test_total_tokens_in_matches_rows(self):
        rows = [
            "| 2fb32edcd1f9 | 2026-04-15T10:30:00Z | coder | ADV099-T001 | opus | 85000 | 28000 | 720 | 12 | 1.6950 | done | high |",
            "| 588cb9f9256f | 2026-04-15T11:00:00Z | planner | ADV099-T002 | sonnet | 20000 | 3500 | 90 | 7 | 0.0705 | ready | high |",
        ]
        with tempfile.TemporaryDirectory() as td:
            mp = _make_metrics(Path(td), rows)
            aggregator.recompute_frontmatter(mp)
            parsed_rows = aggregator.parse_rows(mp)
            expected_tokens_in = sum(r.tokens_in for r in parsed_rows)
            # Re-read the frontmatter to verify.
            text = mp.read_text(encoding="utf-8")
            # Parse frontmatter.
            fm_dict = aggregator._parse_frontmatter(
                text.split("---")[1]
            )
            self.assertEqual(fm_dict["total_tokens_in"], expected_tokens_in)
            self.assertEqual(expected_tokens_in, 105000)


class TestAllFrontmatterTotalsMatchRows(unittest.TestCase):
    """TC-AG-2: All 5 frontmatter fields sum correctly."""

    def test_all_frontmatter_totals_match_rows(self):
        fixture = FIXTURES_DIR / "metrics" / "multi_model.md"
        # Copy to temp dir (read-only fixture, write in temp).
        with tempfile.TemporaryDirectory() as td:
            mp = Path(td) / "metrics.md"
            mp.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
            aggregator.recompute_frontmatter(mp)
            rows = aggregator.parse_rows(mp)
            text = mp.read_text(encoding="utf-8")
            fm_dict = aggregator._parse_frontmatter(text.split("---")[1])

            self.assertEqual(fm_dict["total_tokens_in"], sum(r.tokens_in for r in rows))
            self.assertEqual(fm_dict["total_tokens_out"], sum(r.tokens_out for r in rows))
            self.assertEqual(fm_dict["total_duration"], sum(r.duration_s for r in rows))
            self.assertAlmostEqual(
                float(fm_dict["total_cost"]),
                round(sum(r.cost_usd for r in rows), 4),
                places=4,
            )
            self.assertEqual(fm_dict["agent_runs"], len(rows))


class TestRecomputeIdempotent(unittest.TestCase):
    """TC-AG-3: Byte-identical second run."""

    def test_recompute_idempotent(self):
        fixture = FIXTURES_DIR / "metrics" / "multi_model.md"
        with tempfile.TemporaryDirectory() as td:
            mp = Path(td) / "metrics.md"
            mp.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
            aggregator.recompute_frontmatter(mp)
            content_after_first = mp.read_bytes()
            aggregator.recompute_frontmatter(mp)
            content_after_second = mp.read_bytes()
            self.assertEqual(
                content_after_first,
                content_after_second,
                "recompute_frontmatter is not idempotent: second run produced different bytes",
            )


class TestFormatDurationTableDriven(unittest.TestCase):
    """TC-AG-6: format_duration table-driven (6+ cases)."""

    CASES = [
        (0, "0s"),
        (1, "1s"),
        (95, "95s"),
        (119, "119s"),
        (120, "2min"),
        (60, "1min"),      # 60s < 120 -> "60s" per the rule: < 120 = Xs
        (960, "16min"),
        (3600, "1h"),
        (8100, "2h 15min"),
        (7261, "2h 1min"),
        (150, "2min 30s"),
    ]

    def test_format_duration_table_driven(self):
        # Recompute expected for 60 — format_duration uses < 120 -> "Xs"
        # So 60 -> "60s", not "1min"
        adjusted_cases = []
        for secs, expected in self.CASES:
            if secs == 60:
                expected = "60s"  # 60 < 120 -> raw seconds
            adjusted_cases.append((secs, expected))

        for secs, expected in adjusted_cases:
            with self.subTest(seconds=secs):
                result = aggregator.format_duration(secs)
                self.assertEqual(result, expected, f"format_duration({secs}) = {result!r}, want {expected!r}")


if __name__ == "__main__":
    unittest.main()
