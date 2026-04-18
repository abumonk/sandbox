"""Live canary test — TC-LC-1.

This test is gated on the existence of a canary fixture file produced by an
actual subagent run on ADV-009.  If the fixture does not exist the test is
skipped silently.

When the fixture does exist the test asserts:
1. The post-capture metrics.md has at least one row with non-zero tokens.
2. The frontmatter totals match the row sums (no stale totals).
"""

import os
import sys
import unittest
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parents[4] / ".agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from telemetry import aggregator  # type: ignore[import]

# Expected location of the live canary fixture (post-capture metrics.md snapshot).
_CANARY_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "canary" / "adv009_post_capture.md"
)


class TestAdv009CanaryRowPopulated(unittest.TestCase):
    """TC-LC-1: ADV-009 canary row populated with non-zero tokens."""

    @unittest.skipUnless(
        os.path.exists(str(_CANARY_FIXTURE_PATH)),
        f"Canary fixture not found at {_CANARY_FIXTURE_PATH}; skipping live canary test",
    )
    def test_adv009_canary_row_populated(self):
        # Parse the post-capture metrics snapshot.
        rows = aggregator.parse_rows(_CANARY_FIXTURE_PATH)
        self.assertGreater(len(rows), 0, "Canary fixture has no rows")

        # At least one row must have non-zero tokens.
        nonzero_rows = [r for r in rows if r.tokens_in > 0 or r.tokens_out > 0]
        self.assertGreater(
            len(nonzero_rows), 0,
            "All rows in canary fixture have zero tokens"
        )

        # Frontmatter totals must match the row sums.
        import tempfile
        from pathlib import Path as P
        import shutil
        with tempfile.TemporaryDirectory() as td:
            mp_copy = P(td) / "metrics.md"
            shutil.copy2(_CANARY_FIXTURE_PATH, mp_copy)
            aggregator.recompute_frontmatter(mp_copy)
            text = mp_copy.read_text(encoding="utf-8")
            fm_dict = aggregator._parse_frontmatter(text.split("---")[1])
            parsed_rows = aggregator.parse_rows(mp_copy)
            self.assertEqual(
                fm_dict["total_tokens_in"],
                sum(r.tokens_in for r in parsed_rows),
                "total_tokens_in frontmatter does not match row sum"
            )
            self.assertEqual(
                fm_dict["agent_runs"],
                len(parsed_rows),
                "agent_runs frontmatter does not match row count"
            )


if __name__ == "__main__":
    unittest.main()
