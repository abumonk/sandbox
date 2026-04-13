"""Tests for BMC temporal verification (TemporalBMCTask).

MVP scope recap:
  - Only `□φ` (box / globally) is supported.
  - K-step unrolling over $data transitions from the first #process.
  - Background range constraints + initial defaults + frame axioms.
  - PASS_BOUNDED(K) when no bad state found within K steps.
  - FAIL with failing-step index when a counterexample exists.
  - Other temporal operators (◇, ○, U) report UNKNOWN.

These tests use the real parser (via the `parse_src` fixture) so the
temporal operator symbols go through the full grammar → AST path.
"""

from ark_verify import verify_temporal, BMC_DEFAULT_BOUND


def _items(parse_src, source: str) -> list:
    return parse_src(source)["items"]


def test_box_property_holds_passes_bounded(parse_src):
    """Counter increments; `□(x >= 0)` must hold across K steps."""
    src = """
    class SafeCounter {
      $data x: Int = 0
      @in{ tick: Float }
      #process[strategy: code]{
        pre: x >= 0
        x' = x + 1
      }
      temporal: □(x >= 0)
    }
    """
    results = verify_temporal(_items(parse_src, src))
    assert len(results) == 1
    r = results[0]
    assert r["status"] == "PASS_BOUNDED", f"expected PASS_BOUNDED, got {r}"
    assert f"K{BMC_DEFAULT_BOUND}" in r["check"]


def test_box_property_fails_with_counterexample(parse_src):
    """Counter decrements from 0; `□(x >= 0)` fails at step 1."""
    src = """
    class BadCounter {
      $data x: Int = 0
      @in{ tick: Float }
      #process[strategy: code]{
        x' = x - 1
      }
      temporal: □(x >= 0)
    }
    """
    results = verify_temporal(_items(parse_src, src))
    assert len(results) == 1
    r = results[0]
    assert r["status"] == "FAIL", f"expected FAIL, got {r}"
    # The failing step should be reported and the counterexample should
    # mention x at some step-suffixed name.
    assert "step" in r["detail"]
    assert "x_s" in r["detail"]


def test_unsupported_temporal_operator_is_unknown(parse_src):
    """`◇φ` (eventually) is out of MVP scope — must return UNKNOWN, not crash."""
    src = """
    class Eventual {
      $data x: Int = 0
      #process[strategy: code]{
        x' = x + 1
      }
      temporal: ◇(x == 5)
    }
    """
    results = verify_temporal(_items(parse_src, src))
    assert len(results) == 1
    r = results[0]
    assert r["status"] == "UNKNOWN"
    assert "not yet supported" in r["detail"]
    assert "◇" in r["detail"]


def test_entity_without_temporal_produces_no_results(parse_src):
    """Classes with no `temporal:` block contribute nothing to the BMC pass."""
    src = """
    class Quiet {
      $data x: Int = 0
      #process[strategy: code]{
        x' = x + 1
      }
      invariant: x >= 0
    }
    """
    results = verify_temporal(_items(parse_src, src))
    assert results == []


def test_box_with_custom_bound(parse_src):
    """A shorter bound still exercises the same pipeline and reports K in the name."""
    src = """
    class Tiny {
      $data x: Int = 0
      #process[strategy: code]{
        x' = x + 1
      }
      temporal: □(x >= 0)
    }
    """
    results = verify_temporal(_items(parse_src, src), bound=3)
    assert len(results) == 1
    r = results[0]
    assert r["status"] == "PASS_BOUNDED"
    assert "K3" in r["check"]
