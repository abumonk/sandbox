"""Constraint checker for evolved variants.

Validates that evolved content meets safety requirements before acceptance:
- size_limit: variant must not grow beyond threshold relative to original
- semantic_preservation: variant must preserve semantic intent (judge callback)
- caching_compat: variant must preserve the shared prompt prefix (caching)
- test_suite: variant must pass the existing test suite (stub)

Integrates with the optimizer: check_all_constraints() is called after each
mutation. Variants that trigger a 'block' constraint are discarded from the
population. Variants that trigger 'warn' constraints are kept but flagged.
"""
import difflib
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Core result type
# ---------------------------------------------------------------------------

@dataclass
class ConstraintResult:
    """Result of a single constraint check.

    Attributes:
        constraint_name: Human-readable name for the constraint instance.
        constraint_type: Kind of constraint — "size_limit", "semantic_preservation",
                         "caching_compat", or "test_suite".
        passed:          True when the variant satisfies the constraint.
        enforcement:     "block" — discard the variant on failure;
                         "warn"  — keep but flag the variant on failure.
        message:         Human-readable explanation of the outcome.
        details:         Constraint-specific numeric/diagnostic data
                         (e.g. size_ratio, preservation_score, prefix_match).
    """
    constraint_name: str
    constraint_type: str
    passed: bool
    enforcement: str          # "block" or "warn"
    message: str
    details: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Individual constraint checks
# ---------------------------------------------------------------------------

def check_size_limit(
    original_content: str,
    variant_content: str,
    threshold: float = 0.2,
    enforcement: str = "block",
) -> ConstraintResult:
    """Check that the variant does not exceed the allowed size growth.

    Args:
        original_content: Source content before evolution.
        variant_content:  Candidate evolved content.
        threshold:        Maximum allowed fractional growth above original size.
                          0.2 means the variant may be at most 20 % larger.
        enforcement:      "block" or "warn".

    Returns:
        ConstraintResult with passed=True when
        ``len(variant) <= len(original) * (1 + threshold)``.
    """
    original_len = len(original_content)
    variant_len = len(variant_content)
    limit = original_len * (1.0 + threshold)

    passed = variant_len <= limit

    if original_len == 0:
        size_ratio = float("inf") if variant_len > 0 else 1.0
    else:
        size_ratio = variant_len / original_len

    if passed:
        message = (
            f"Size within limit: variant is {variant_len} chars "
            f"({size_ratio:.2%} of original {original_len} chars, "
            f"limit +{threshold:.0%})."
        )
    else:
        message = (
            f"Size limit exceeded: variant is {variant_len} chars "
            f"({size_ratio:.2%} of original {original_len} chars), "
            f"limit is +{threshold:.0%} ({int(limit)} chars)."
        )

    return ConstraintResult(
        constraint_name="size_limit",
        constraint_type="size_limit",
        passed=passed,
        enforcement=enforcement,
        message=message,
        details={
            "original_len": original_len,
            "variant_len": variant_len,
            "size_ratio": size_ratio,
            "threshold": threshold,
            "limit_chars": limit,
        },
    )


def check_semantic_preservation(
    original_content: str,
    variant_content: str,
    threshold: float = 0.8,
    judge_fn: Optional[Callable[[str, str], float]] = None,
    enforcement: str = "block",
) -> ConstraintResult:
    """Check that the variant preserves semantic intent.

    Args:
        original_content: Source content before evolution.
        variant_content:  Candidate evolved content.
        threshold:        Minimum acceptable similarity score (0.0–1.0).
                          Default 0.8.
        judge_fn:         Optional callback ``judge_fn(original, variant) -> float``.
                          Should return a similarity score in [0.0, 1.0].
                          When None, falls back to difflib.SequenceMatcher ratio.
        enforcement:      "block" or "warn".

    Returns:
        ConstraintResult with passed=True when
        ``score >= threshold``.
    """
    if judge_fn is not None:
        score = float(judge_fn(original_content, variant_content))
        method = "judge_fn"
    else:
        score = difflib.SequenceMatcher(
            None, original_content, variant_content
        ).ratio()
        method = "difflib.SequenceMatcher"

    passed = score >= threshold

    if passed:
        message = (
            f"Semantic preservation satisfied: score {score:.3f} >= "
            f"threshold {threshold:.3f} (method: {method})."
        )
    else:
        message = (
            f"Semantic preservation failed: score {score:.3f} < "
            f"threshold {threshold:.3f} (method: {method})."
        )

    return ConstraintResult(
        constraint_name="semantic_preservation",
        constraint_type="semantic_preservation",
        passed=passed,
        enforcement=enforcement,
        message=message,
        details={
            "preservation_score": score,
            "threshold": threshold,
            "method": method,
        },
    )


def check_caching_compat(
    original_content: str,
    variant_content: str,
    prefix_length: int = 100,
    enforcement: str = "warn",
) -> ConstraintResult:
    """Check that the shared prompt prefix is preserved (caching compatibility).

    Prompt caching requires that the first ``prefix_length`` characters of the
    variant exactly match the original, so the cached KV block remains valid.

    Args:
        original_content: Source content before evolution.
        variant_content:  Candidate evolved content.
        prefix_length:    Number of leading characters that must be identical.
        enforcement:      "block" or "warn".

    Returns:
        ConstraintResult with passed=True when the first ``prefix_length``
        characters of the variant equal the first ``prefix_length`` characters
        of the original.
    """
    original_prefix = original_content[:prefix_length]
    variant_prefix = variant_content[:prefix_length]
    passed = original_prefix == variant_prefix

    if passed:
        actual_len = min(len(original_content), len(variant_content), prefix_length)
        message = (
            f"Caching compatibility satisfied: first {actual_len} chars "
            "are unchanged."
        )
    else:
        # Find first differing position for a helpful message
        mismatch_pos = next(
            (i for i, (a, b) in enumerate(zip(original_prefix, variant_prefix)) if a != b),
            min(len(original_prefix), len(variant_prefix)),
        )
        message = (
            f"Caching compatibility failed: prefix diverges at position "
            f"{mismatch_pos} (checked first {prefix_length} chars)."
        )

    return ConstraintResult(
        constraint_name="caching_compat",
        constraint_type="caching_compat",
        passed=passed,
        enforcement=enforcement,
        message=message,
        details={
            "prefix_length": prefix_length,
            "prefix_match": passed,
            "mismatch_position": None if passed else (
                next(
                    (i for i, (a, b) in enumerate(zip(original_prefix, variant_prefix)) if a != b),
                    min(len(original_prefix), len(variant_prefix)),
                )
            ),
        },
    )


def check_test_suite(
    variant_content: str,
    test_command: Optional[str] = None,
    enforcement: str = "block",
) -> ConstraintResult:
    """Check that the variant passes the existing test suite.

    Note: Full test execution requires shell access and a populated filesystem.
    In the current implementation this is a stub that always returns passed=True
    with a note that the check is not implemented. When ``test_command`` is
    None the stub behaviour is identical.

    Args:
        variant_content: Candidate evolved content (unused in stub).
        test_command:    Shell command used to run the test suite (e.g.
                         ``"pytest tests/"``). Passed for API completeness.
        enforcement:     "block" or "warn".

    Returns:
        ConstraintResult with passed=True and a message noting the stub status.
    """
    # Stub: test_suite check not implemented
    message = "test_suite check not implemented — skipped (stub returns pass)."
    if test_command:
        message = (
            f"test_suite check not implemented — would run: {test_command!r}. "
            "Stub returns pass."
        )

    return ConstraintResult(
        constraint_name="test_suite",
        constraint_type="test_suite",
        passed=True,
        enforcement=enforcement,
        message=message,
        details={
            "test_command": test_command,
            "stub": True,
        },
    )


# ---------------------------------------------------------------------------
# Aggregate helpers
# ---------------------------------------------------------------------------

def check_all_constraints(
    original_content: str,
    variant_content: str,
    constraints_list: list[dict],
    judge_fn: Optional[Callable[[str, str], float]] = None,
) -> list[ConstraintResult]:
    """Run all applicable constraints and return their results.

    Each entry in ``constraints_list`` is a dict with at least a ``"type"``
    key. Recognised keys per type:

    * ``"size_limit"``
      - ``threshold`` (float, default 0.2)
      - ``enforcement`` ("block"|"warn", default "block")

    * ``"semantic_preservation"``
      - ``threshold`` (float, default 0.8)
      - ``enforcement`` ("block"|"warn", default "block")

    * ``"caching_compat"``
      - ``prefix_length`` (int, default 100)
      - ``enforcement`` ("block"|"warn", default "warn")

    * ``"test_suite"``
      - ``test_command`` (str|None, default None)
      - ``enforcement`` ("block"|"warn", default "block")

    Unknown constraint types are skipped with a warning result.

    Args:
        original_content: Source content before evolution.
        variant_content:  Candidate evolved content.
        constraints_list: List of constraint specification dicts.
        judge_fn:         Optional semantic judge callback passed through to
                          ``check_semantic_preservation``.

    Returns:
        List of ConstraintResult, one per entry in ``constraints_list``.
    """
    results: list[ConstraintResult] = []

    for spec in constraints_list:
        constraint_type = spec.get("type", "")
        enforcement = spec.get("enforcement", "block")

        if constraint_type == "size_limit":
            threshold = float(spec.get("threshold", 0.2))
            result = check_size_limit(
                original_content,
                variant_content,
                threshold=threshold,
                enforcement=enforcement,
            )

        elif constraint_type == "semantic_preservation":
            threshold = float(spec.get("threshold", 0.8))
            result = check_semantic_preservation(
                original_content,
                variant_content,
                threshold=threshold,
                judge_fn=judge_fn,
                enforcement=enforcement,
            )

        elif constraint_type == "caching_compat":
            prefix_length = int(spec.get("prefix_length", 100))
            # Default enforcement for caching is "warn" (non-fatal)
            enforcement = spec.get("enforcement", "warn")
            result = check_caching_compat(
                original_content,
                variant_content,
                prefix_length=prefix_length,
                enforcement=enforcement,
            )

        elif constraint_type == "test_suite":
            test_command = spec.get("test_command", None)
            result = check_test_suite(
                variant_content,
                test_command=test_command,
                enforcement=enforcement,
            )

        else:
            # Unknown constraint type — produce a passing warn result
            result = ConstraintResult(
                constraint_name=constraint_type or "unknown",
                constraint_type=constraint_type or "unknown",
                passed=True,
                enforcement="warn",
                message=f"Unknown constraint type {constraint_type!r} — skipped.",
                details={"spec": spec},
            )

        results.append(result)

    return results


def should_block(results: list[ConstraintResult]) -> bool:
    """Return True if any block-enforcement constraint failed.

    A variant should be discarded from the evolution population when at least
    one result has ``enforcement="block"`` AND ``passed=False``.

    Args:
        results: List of ConstraintResult as returned by check_all_constraints.

    Returns:
        True when the variant must be blocked; False otherwise.
    """
    return any(
        not result.passed and result.enforcement == "block"
        for result in results
    )
