"""
Tests for evolution constraint checker — TC-018 through TC-022.

Tests that constraint_checker.py correctly enforces size limits,
semantic preservation, caching compatibility, and that should_block
returns the right answer.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_EVOLUTION_DIR = REPO_ROOT / "tools" / "evolution"
if str(_EVOLUTION_DIR) not in sys.path:
    sys.path.insert(0, str(_EVOLUTION_DIR))

from constraint_checker import (  # noqa: E402
    check_size_limit,
    check_semantic_preservation,
    check_caching_compat,
    check_all_constraints,
    should_block,
    ConstraintResult,
)


# ============================================================
# TC-018: Size limit blocks variants exceeding threshold
# ============================================================

def test_size_block():
    """TC-018: check_size_limit returns passed=False, enforcement='block' when 25% larger."""
    original = "a" * 100  # 100 chars
    # 25% larger (exceeds 20% threshold)
    variant = "a" * 125

    result = check_size_limit(original, variant, threshold=0.20, enforcement="block")

    assert isinstance(result, ConstraintResult)
    assert result.passed is False
    assert result.enforcement == "block"
    assert "exceeded" in result.message.lower() or "limit" in result.message.lower()


def test_size_block_details():
    """Size limit result includes numeric details."""
    original = "x" * 100
    variant = "x" * 130  # 30% larger
    result = check_size_limit(original, variant, threshold=0.20)
    assert "original_len" in result.details
    assert "variant_len" in result.details
    assert "size_ratio" in result.details
    assert result.details["original_len"] == 100
    assert result.details["variant_len"] == 130


# ============================================================
# TC-019: Size limit passes variants within threshold
# ============================================================

def test_size_pass():
    """TC-019: check_size_limit returns passed=True when variant is 10% larger."""
    original = "a" * 100  # 100 chars
    variant = "a" * 110   # 10% larger (within 20% threshold)

    result = check_size_limit(original, variant, threshold=0.20)

    assert result.passed is True
    assert "within" in result.message.lower() or "size" in result.message.lower()


def test_size_exact_limit():
    """Size limit passes when variant is exactly at the threshold."""
    original = "a" * 100
    variant = "a" * 120  # exactly 20% larger
    result = check_size_limit(original, variant, threshold=0.20)
    assert result.passed is True


def test_size_smaller_always_passes():
    """Smaller variant always passes size limit check."""
    original = "a" * 200
    variant = "a" * 150  # smaller
    result = check_size_limit(original, variant, threshold=0.20)
    assert result.passed is True


def test_size_warn_enforcement():
    """check_size_limit with enforcement='warn' still returns enforcement='warn' on fail."""
    original = "a" * 100
    variant = "a" * 150  # 50% larger — fails
    result = check_size_limit(original, variant, threshold=0.20, enforcement="warn")
    assert result.passed is False
    assert result.enforcement == "warn"


# ============================================================
# TC-020: Semantic preservation uses judge callback
# ============================================================

def test_semantic():
    """TC-020: check_semantic_preservation uses judge_fn; passes at >=0.8, fails at <0.8."""
    original = "This is the original skill description with detailed instructions."
    variant_pass = "This is the improved skill description with detailed instructions."
    variant_fail = "Completely different text that has no relation to original."

    # Score 0.9 — passes
    def judge_pass(orig, var):
        return 0.9

    result_pass = check_semantic_preservation(original, variant_pass,
                                               threshold=0.8, judge_fn=judge_pass)
    assert result_pass.passed is True

    # Score 0.6 — fails
    def judge_fail(orig, var):
        return 0.6

    result_fail = check_semantic_preservation(original, variant_fail,
                                               threshold=0.8, judge_fn=judge_fail)
    assert result_fail.passed is False


def test_semantic_no_judge_uses_difflib():
    """check_semantic_preservation without judge_fn uses difflib ratio."""
    # Identical content should have very high similarity
    content = "The quick brown fox jumps over the lazy dog." * 5
    result = check_semantic_preservation(content, content, threshold=0.8)
    assert result.passed is True
    assert result.details["method"] == "difflib.SequenceMatcher"


def test_semantic_judge_called_with_correct_args():
    """judge_fn receives (original, variant) as positional args."""
    received = []

    def tracking_judge(orig, var):
        received.append((orig, var))
        return 0.9

    original = "original text"
    variant = "variant text"
    check_semantic_preservation(original, variant, judge_fn=tracking_judge)

    assert len(received) == 1
    assert received[0] == (original, variant)


# ============================================================
# TC-021: Caching compatibility checks prefix
# ============================================================

def test_caching():
    """TC-021: caching_compat passes when prefix matches, fails when prefix diverges."""
    # Create content where first 100 chars are identical
    shared_prefix = "A" * 100
    suffix_a = "suffix_original_more_content"
    suffix_b = "suffix_variant_more_content"
    original = shared_prefix + suffix_a
    variant_pass = shared_prefix + suffix_b

    result_pass = check_caching_compat(original, variant_pass, prefix_length=100)
    assert result_pass.passed is True

    # Create content where prefix diverges at position 50
    original2 = "A" * 50 + "B" * 100
    variant_fail = "A" * 49 + "X" + "B" * 100  # diverges at char 49
    result_fail = check_caching_compat(original2, variant_fail, prefix_length=100)
    assert result_fail.passed is False


def test_caching_default_enforcement_warn():
    """check_caching_compat defaults to enforcement='warn'."""
    original = "prefix" + "x" * 100
    variant = "PREFIX" + "x" * 100  # different prefix
    result = check_caching_compat(original, variant, prefix_length=6)
    assert result.passed is False
    assert result.enforcement == "warn"


def test_caching_identical_content_passes():
    """Identical original and variant always pass caching compat check."""
    content = "Same content " * 20
    result = check_caching_compat(content, content, prefix_length=100)
    assert result.passed is True


def test_caching_mismatch_position_in_details():
    """Failed caching check includes mismatch_position in details."""
    original = "AAABBB" + "x" * 100
    variant = "AAAXBB" + "x" * 100  # diverges at position 3
    result = check_caching_compat(original, variant, prefix_length=10)
    assert result.passed is False
    assert result.details.get("mismatch_position") is not None


# ============================================================
# TC-022: should_block returns correct answer
# ============================================================

def test_should_block():
    """TC-022: should_block returns True only for block-enforcement failures."""
    # All passing — should NOT block
    all_pass = [
        ConstraintResult("c1", "size_limit", True, "block", "ok"),
        ConstraintResult("c2", "semantic", True, "warn", "ok"),
    ]
    assert should_block(all_pass) is False

    # One warn failure — should NOT block
    warn_fail = [
        ConstraintResult("c1", "size_limit", True, "block", "ok"),
        ConstraintResult("c2", "semantic", False, "warn", "failed"),
    ]
    assert should_block(warn_fail) is False

    # One block failure — SHOULD block
    block_fail = [
        ConstraintResult("c1", "size_limit", False, "block", "exceeded"),
        ConstraintResult("c2", "semantic", True, "warn", "ok"),
    ]
    assert should_block(block_fail) is True


def test_should_block_empty_results():
    """should_block with empty list returns False."""
    assert should_block([]) is False


def test_warn_constraint_not_blocking():
    """A failing warn-level constraint does not cause should_block to return True."""
    results = [
        ConstraintResult("caching", "caching_compat", False, "warn", "prefix diverged"),
    ]
    assert should_block(results) is False


# ============================================================
# Additional: check_all_constraints
# ============================================================

def test_check_all_constraints():
    """check_all_constraints runs all applicable checks and returns results list."""
    original = "A" * 100
    variant = "A" * 115  # 15% larger — within threshold

    constraints_list = [
        {"type": "size_limit", "threshold": 0.2, "enforcement": "block"},
        {"type": "caching_compat", "prefix_length": 50},
    ]
    results = check_all_constraints(original, variant, constraints_list)
    assert len(results) == 2
    assert all(isinstance(r, ConstraintResult) for r in results)
    # size_limit should pass (15% < 20%)
    size_result = next(r for r in results if r.constraint_type == "size_limit")
    assert size_result.passed is True


def test_check_all_constraints_semantic():
    """check_all_constraints with semantic_preservation uses judge_fn."""
    original = "content"
    variant = "content"

    def always_high(orig, var):
        return 0.95

    constraints_list = [
        {"type": "semantic_preservation", "threshold": 0.8, "enforcement": "block"},
    ]
    results = check_all_constraints(original, variant, constraints_list,
                                    judge_fn=always_high)
    assert len(results) == 1
    assert results[0].passed is True
