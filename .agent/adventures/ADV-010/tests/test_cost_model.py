"""Tests for cost_model.py — TC-CM-1, TC-CM-2, TC-CM-3, TC-CM-4."""

import sys
import unittest
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parents[4] / ".agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from telemetry.cost_model import (  # type: ignore[import]
    cost_for,
    normalize_model,
    load_rates,
)
from telemetry.errors import UnknownModelError  # type: ignore[import]


class TestCostForOpusKnownFixture(unittest.TestCase):
    """TC-CM-1: cost_for("opus", 85000, 28000) equals hand-computed value."""

    def test_cost_for_opus_known_fixture(self):
        # Rate for opus is 0.015 per 1k tokens.
        # (85000 + 28000) / 1000 * 0.015 = 113 * 0.015 = 1.6950
        result = cost_for("opus", 85000, 28000)
        self.assertAlmostEqual(result, 1.6950, places=4)


class TestUnknownModelRaises(unittest.TestCase):
    """TC-CM-2: UnknownModelError raised for unrecognised model IDs."""

    def test_unknown_model_raises(self):
        with self.assertRaises(UnknownModelError):
            cost_for("unknown-model-xyz", 1, 1)

    def test_empty_string_model_raises(self):
        with self.assertRaises(UnknownModelError):
            cost_for("", 1, 1)


class TestNormalizeModelAliases(unittest.TestCase):
    """TC-CM-3: Table-driven over 6+ aliases."""

    ALIAS_TABLE = [
        ("claude-opus-4-6", "opus"),
        ("claude-sonnet-4", "sonnet"),
        ("sonnet-4", "sonnet"),
        ("claude-haiku-3", "haiku"),
        ("haiku-3", "haiku"),
        ("opus", "opus"),
        ("sonnet", "sonnet"),
        ("haiku", "haiku"),
        ("claude-opus", "opus"),
        ("claude-sonnet", "sonnet"),
    ]

    def test_normalize_model_aliases(self):
        for alias, expected in self.ALIAS_TABLE:
            with self.subTest(alias=alias):
                result = normalize_model(alias)
                self.assertEqual(result, expected, f"normalize_model({alias!r}) = {result!r}, want {expected!r}")


class TestLoadRatesFromConfigMd(unittest.TestCase):
    """TC-CM-4: Parses current .agent/config.md into exact expected dict."""

    def test_load_rates_from_config_md(self):
        rates = load_rates()
        expected = {"opus": 0.015, "sonnet": 0.003, "haiku": 0.001}
        self.assertEqual(rates, expected)


if __name__ == "__main__":
    unittest.main()
