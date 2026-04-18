"""Validates TC-016 — validation-coverage arithmetic.

The validation-coverage.md file produced by T009 lists every source TC from
ADV-001..008 with a verdict column whose value is one of
COVERED-BY / RETIRED-BY / DEFERRED-TO. This unittest parses the file and
asserts the count identity.
"""

import pathlib
import re
import unittest

COVERAGE = pathlib.Path(
    ".agent/adventures/ADV-011/research/validation-coverage.md"
)

VERDICTS = ("COVERED-BY", "RETIRED-BY", "DEFERRED-TO")


class TestCoverageArithmetic(unittest.TestCase):
    """TC-016: covered + retired + deferred == total_source_TCs."""

    def setUp(self):
        self.assertTrue(
            COVERAGE.exists(),
            f"Missing {COVERAGE} — T009 must produce it before T011 runs.",
        )
        self.text = COVERAGE.read_text(encoding="utf-8")

    def _count_rows_by_verdict(self):
        counts = {v: 0 for v in VERDICTS}
        total = 0
        for line in self.text.splitlines():
            if not (line.startswith("| TC-") or line.startswith("| ADV-")):
                continue
            total += 1
            for v in VERDICTS:
                if v in line:
                    counts[v] += 1
                    break
        return total, counts

    def test_each_tc_has_exactly_one_verdict(self):
        """Every TC row must match exactly one of the three verdicts."""
        total, counts = self._count_rows_by_verdict()
        self.assertGreater(total, 0, "No TC rows found in validation-coverage.md")
        self.assertEqual(
            sum(counts.values()),
            total,
            f"Some rows have 0 or >1 verdicts. counts={counts}, total={total}",
        )

    def test_arithmetic_holds(self):
        """TC-016: covered + retired + deferred == total."""
        total, counts = self._count_rows_by_verdict()
        self.assertEqual(
            counts["COVERED-BY"] + counts["RETIRED-BY"] + counts["DEFERRED-TO"],
            total,
        )


if __name__ == "__main__":
    unittest.main()
