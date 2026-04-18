"""Fixture-based unit tests for the four backfill reconstructors.

Runs against the real ADV-008 adventure data already committed in the repo.
Each test class exercises one reconstructor module and validates the
acceptance criteria documented in ADV010-T011.

Usage::

    cd R:/Sandbox
    python -m pytest .agent/adventures/ADV-010/tests/test_reconstructors.py -v
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Allow importing from .agent/telemetry without installing as a package.
_AGENT_DIR = Path(__file__).parent.parent.parent.parent  # R:/Sandbox/.agent
sys.path.insert(0, str(_AGENT_DIR))

import pytest

from telemetry.tools.reconstructors import (
    Candidate,
    parse_existing_rows,
    parse_log,
    git_windows_for_adventure,
    parse_task_logs,
)

# Paths to ADV-008 fixture data (real committed files).
_ADV008 = _AGENT_DIR / "adventures" / "ADV-008"
_METRICS_MD = _ADV008 / "metrics.md"
_ADVENTURE_LOG = _ADV008 / "adventure.log"
_TASKS_DIR = _ADV008 / "tasks"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_tilde(value: object) -> bool:
    """Return True if *value*'s string representation contains a ``~``."""
    return "~" in str(value)


# ---------------------------------------------------------------------------
# Test: existing_rows
# ---------------------------------------------------------------------------

class TestExistingRowsParse:
    """Tests for ``existing_rows.parse()``."""

    @pytest.fixture(scope="class")
    def candidates(self) -> list[Candidate]:
        assert _METRICS_MD.exists(), f"Fixture not found: {_METRICS_MD}"
        return parse_existing_rows(_METRICS_MD)

    def test_returns_candidates(self, candidates: list[Candidate]):
        """Should return at least one candidate."""
        assert len(candidates) > 0

    def test_expected_row_count(self, candidates: list[Candidate]):
        """ADV-008/metrics.md has 35 data rows (accept 34-36 to handle edits)."""
        assert 34 <= len(candidates) <= 36, (
            f"Expected 34-36 candidates, got {len(candidates)}"
        )

    def test_no_tilde_in_numeric_fields(self, candidates: list[Candidate]):
        """Tilde prefixes must be stripped from all numeric fields."""
        for c in candidates:
            assert not _has_tilde(c.tokens_in), f"~ in tokens_in: {c}"
            assert not _has_tilde(c.tokens_out), f"~ in tokens_out: {c}"
            assert not _has_tilde(c.duration_s), f"~ in duration_s: {c}"
            assert not _has_tilde(c.turns), f"~ in turns: {c}"

    def test_tokens_are_integers(self, candidates: list[Candidate]):
        """Tokens In and Tokens Out must be Python ints."""
        for c in candidates:
            assert isinstance(c.tokens_in, int), f"tokens_in not int: {c}"
            assert isinstance(c.tokens_out, int), f"tokens_out not int: {c}"

    def test_duration_is_integer_seconds(self, candidates: list[Candidate]):
        """Duration must be an integer number of seconds."""
        for c in candidates:
            assert isinstance(c.duration_s, int), f"duration_s not int: {c}"
            assert c.duration_s >= 0, f"duration_s negative: {c}"

    def test_duration_conversion_4min(self, candidates: list[Candidate]):
        """A row with duration '4min' should parse to 240 seconds."""
        four_min_rows = [c for c in candidates if c.duration_s == 240]
        assert len(four_min_rows) >= 1, "Expected at least one row with duration=240s (4min)"

    def test_duration_conversion_95s(self, candidates: list[Candidate]):
        """A row with duration '95s' should parse to 95 seconds."""
        ninety_five_s_rows = [c for c in candidates if c.duration_s == 95]
        assert len(ninety_five_s_rows) >= 1, "Expected at least one row with duration=95s"

    def test_all_confidence_medium(self, candidates: list[Candidate]):
        """All candidates must have confidence='medium'."""
        bad = [c for c in candidates if c.confidence != "medium"]
        assert not bad, f"Candidates with wrong confidence: {bad}"

    def test_all_source_existing(self, candidates: list[Candidate]):
        """All candidates must have source='existing'."""
        bad = [c for c in candidates if c.source != "existing"]
        assert not bad, f"Candidates with wrong source: {bad}"

    def test_missing_file_returns_empty(self):
        """parse() on a non-existent path should return an empty list."""
        result = parse_existing_rows(Path("/nonexistent/metrics.md"))
        assert result == []

    def test_candidate_is_frozen_dataclass(self, candidates: list[Candidate]):
        """Candidates should be immutable (frozen dataclass)."""
        c = candidates[0]
        with pytest.raises((AttributeError, TypeError)):
            c.agent = "tampered"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Test: log_parser
# ---------------------------------------------------------------------------

class TestLogParserParse:
    """Tests for ``log_parser.parse()``."""

    @pytest.fixture(scope="class")
    def candidates(self) -> list[Candidate]:
        assert _ADVENTURE_LOG.exists(), f"Fixture not found: {_ADVENTURE_LOG}"
        return parse_log(_ADVENTURE_LOG)

    def test_returns_candidates(self, candidates: list[Candidate]):
        """Should return at least one candidate."""
        assert len(candidates) > 0

    def test_at_least_19_spawn_events(self, candidates: list[Candidate]):
        """ADV-008 has ≥19 spawn events — expect at least 19 candidates."""
        assert len(candidates) >= 19, (
            f"Expected >= 19 candidates, got {len(candidates)}"
        )

    def test_all_source_log(self, candidates: list[Candidate]):
        assert all(c.source == "log" for c in candidates)

    def test_all_confidence_low(self, candidates: list[Candidate]):
        assert all(c.confidence == "low" for c in candidates)

    def test_each_candidate_has_task_or_agent(self, candidates: list[Candidate]):
        """Every candidate should have a non-empty task or agent field."""
        for c in candidates:
            assert c.task or c.agent, f"Candidate has neither task nor agent: {c}"

    def test_paired_candidates_have_nonneg_duration(self, candidates: list[Candidate]):
        """Candidates with result='complete' should have duration_s >= 0."""
        completed = [c for c in candidates if c.result == "complete"]
        for c in completed:
            assert c.duration_s >= 0, f"Negative duration on completed: {c}"

    def test_missing_file_returns_empty(self):
        result = parse_log(Path("/nonexistent/adventure.log"))
        assert result == []


# ---------------------------------------------------------------------------
# Test: git_windows
# ---------------------------------------------------------------------------

class TestGitWindowsForAdventure:
    """Tests for ``git_windows.for_adventure()``."""

    @pytest.fixture(scope="class")
    def candidates(self) -> list[Candidate]:
        return git_windows_for_adventure("ADV-008")

    def test_returns_candidates(self, candidates: list[Candidate]):
        """Should return a non-empty list for ADV-008."""
        assert len(candidates) > 0

    def test_all_source_git(self, candidates: list[Candidate]):
        assert all(c.source == "git" for c in candidates)

    def test_all_confidence_low(self, candidates: list[Candidate]):
        assert all(c.confidence == "low" for c in candidates)

    def test_duration_nonneg(self, candidates: list[Candidate]):
        """All per-task windows must have non-negative duration."""
        for c in candidates:
            assert c.duration_s >= 0, f"Negative duration: {c}"

    def test_task_ids_match_adv008_pattern(self, candidates: list[Candidate]):
        """Task IDs should match ADV008-T\\d+ pattern."""
        pattern = re.compile(r"ADV008-T\d+", re.IGNORECASE)
        for c in candidates:
            assert pattern.match(c.task), f"Unexpected task ID: {c.task!r}"

    def test_timestamps_are_iso_format(self, candidates: list[Candidate]):
        """Timestamps should be non-empty ISO-8601 strings."""
        for c in candidates:
            assert c.timestamp, f"Empty timestamp: {c}"
            # Basic format check: starts with YYYY-
            assert re.match(r"^\d{4}-", c.timestamp), (
                f"Invalid timestamp format: {c.timestamp!r}"
            )


# ---------------------------------------------------------------------------
# Test: task_logs
# ---------------------------------------------------------------------------

class TestTaskLogsParse:
    """Tests for ``task_logs.parse()``."""

    @pytest.fixture(scope="class")
    def candidates(self) -> list[Candidate]:
        assert _TASKS_DIR.exists(), f"Fixture not found: {_TASKS_DIR}"
        return parse_task_logs(_TASKS_DIR)

    def test_returns_candidates(self, candidates: list[Candidate]):
        """Should return at least one candidate for ADV-008 tasks."""
        assert len(candidates) > 0

    def test_all_source_task_log(self, candidates: list[Candidate]):
        assert all(c.source == "task_log" for c in candidates)

    def test_all_confidence_low(self, candidates: list[Candidate]):
        assert all(c.confidence == "low" for c in candidates)

    def test_task_ids_match_adv008_pattern(self, candidates: list[Candidate]):
        """Each task ID should match ADV008-T\\d+."""
        pattern = re.compile(r"ADV008-T\d+")
        for c in candidates:
            assert pattern.match(c.task), f"Unexpected task ID: {c.task!r}"

    def test_duration_is_int_nonneg(self, candidates: list[Candidate]):
        """Duration should be a non-negative integer."""
        for c in candidates:
            assert isinstance(c.duration_s, int)
            assert c.duration_s >= 0, f"Negative duration: {c}"

    def test_duration_computed_from_log_timestamps(self, candidates: list[Candidate]):
        """At least one task should have duration_s > 0 (has multiple log entries)."""
        positive_dur = [c for c in candidates if c.duration_s > 0]
        assert len(positive_dur) > 0, "Expected at least one candidate with duration_s > 0"

    def test_missing_dir_returns_empty(self):
        result = parse_task_logs(Path("/nonexistent/tasks"))
        assert result == []
