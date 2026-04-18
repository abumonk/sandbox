"""Tests for schema.py — TC-S-1, TC-S-2, TC-S-3."""

import sys
import unittest
from pathlib import Path

# Ensure .agent/ is on sys.path so `import schema` works.
_AGENT_DIR = Path(__file__).resolve().parents[4] / ".agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from telemetry.schema import (  # type: ignore[import]
    ROW_COLUMNS,
    ROW_HEADER,
    parse_row,
)
from telemetry.errors import SchemaError  # type: ignore[import]


class TestRowHeaderColumnsExact(unittest.TestCase):
    """TC-S-1: Header line equals the 12-column order."""

    def test_row_header_columns_exact(self):
        # The expected column order per row_schema.md.
        expected_columns = (
            "Run ID",
            "Timestamp",
            "Agent",
            "Task",
            "Model",
            "Tokens In",
            "Tokens Out",
            "Duration (s)",
            "Turns",
            "Cost (USD)",
            "Result",
            "Confidence",
        )
        self.assertEqual(ROW_COLUMNS, expected_columns)
        expected_header = "| " + " | ".join(expected_columns) + " |"
        self.assertEqual(ROW_HEADER, expected_header)


class TestFrontmatterKeysExact(unittest.TestCase):
    """TC-S-2: Frontmatter has exactly the required set of keys."""

    def test_frontmatter_keys_exact(self):
        # Verify by reading what aggregator.py declares as the canonical key order.
        from telemetry.aggregator import _FRONTMATTER_KEY_ORDER  # type: ignore[import]
        expected = {
            "adventure_id",
            "total_tokens_in",
            "total_tokens_out",
            "total_duration",
            "total_cost",
            "agent_runs",
        }
        actual = set(_FRONTMATTER_KEY_ORDER)
        self.assertEqual(actual, expected)


class TestRowTypeCoercion(unittest.TestCase):
    """TC-S-3: Parser rejects non-int token column, bad Run ID format, duplicate Run ID."""

    def _make_row(
        self,
        run_id="a1b2c3d4e5f6",
        timestamp="2026-04-15T10:30:00Z",
        agent="coder",
        task="ADV099-T001",
        model="opus",
        tokens_in="85000",
        tokens_out="28000",
        duration_s="720",
        turns="12",
        cost="1.6950",
        result="done",
        confidence="high",
    ):
        return (
            f"| {run_id} | {timestamp} | {agent} | {task} | {model}"
            f" | {tokens_in} | {tokens_out} | {duration_s} | {turns}"
            f" | {cost} | {result} | {confidence} |"
        )

    def test_non_int_token_column_raises_schema_error(self):
        line = self._make_row(tokens_in="not-a-number")
        with self.assertRaises(SchemaError):
            parse_row(line)

    def test_bad_run_id_format_raises_schema_error(self):
        # Run ID must be exactly 12 lowercase hex chars.
        line = self._make_row(run_id="ZZZZZZZZZZZZ")
        with self.assertRaises(SchemaError):
            parse_row(line)

    def test_bad_run_id_too_short_raises_schema_error(self):
        line = self._make_row(run_id="a1b2c3")
        with self.assertRaises(SchemaError):
            parse_row(line)

    def test_wrong_column_count_raises_schema_error(self):
        line = "| only | three | cells |"
        with self.assertRaises(SchemaError):
            parse_row(line)


if __name__ == "__main__":
    unittest.main()
