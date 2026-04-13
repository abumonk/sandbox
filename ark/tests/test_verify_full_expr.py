"""Tests for full-expression #process body translation (VerifyFullExprTask).

The verifier used to read only `pre:` and `post:` from each process — body
assignments (x' = expr) were silently ignored. After this task, body
assignments become Z3 equality facts used by both the invariant
preservation check AND a new post-obligation check.

Scope covered by these tests:
  1. Body assignments translate into equality constraints.
  2. @in port fields are registered as typed Z3 vars.
  3. The new post-obligation check passes when body actually entails post.
  4. The new post-obligation check FAILS and reports a counterexample
     when body does not entail post.
  5. Unhandled body statements (conditional/for_all) are skipped gracefully
     — no crash, verification still runs.
"""

from ark_verify import check_invariants_hold


def _entity(parse_src, source: str) -> dict:
    """Parse one class and return its AST dict."""
    ast = parse_src(source)
    for item in ast["items"]:
        if item.get("kind") == "class":
            return item
    raise AssertionError("no class in source")


def _checks_by_prefix(results: list, prefix: str) -> list:
    return [r for r in results if r["check"].startswith(prefix)]


def test_body_assignment_is_translated_and_invariant_holds(parse_src):
    """`speed' = speed + 1` plus pre `speed >= 0` implies `speed >= 0`
    still holds (current-state inv) — the body assignment must not
    introduce spurious counterexamples."""
    src = """
    class Counter {
      $data speed: Float = 0.0
      @in{ tick: Float }
      #process[strategy: code]{
        pre: speed >= 0
        speed' = speed + 1
        post: speed' >= 1
      }
      invariant: speed >= 0
    }
    """
    ent = _entity(parse_src, src)
    results = check_invariants_hold(ent)
    invs = _checks_by_prefix(results, "invariant_holds_")
    assert invs, "expected at least one invariant check"
    assert all(r["status"] == "PASS" for r in invs), \
        f"invariant should hold: {invs}"


def test_in_port_field_usable_in_body(parse_src):
    """@in fields must be registered as typed Z3 vars so body expressions
    referring to them don't blow up or silently become free Real vars."""
    src = """
    class Accum {
      $data total: Float = 0.0
      @in{ delta: Float }
      #process[strategy: code]{
        pre: total >= 0
        pre: delta >= 0
        total' = total + delta
        post: total' >= 0
      }
      invariant: total >= 0
    }
    """
    ent = _entity(parse_src, src)
    results = check_invariants_hold(ent)
    # Post-obligation for the body: pre ∧ (total' = total + delta) ⇒ total' >= 0
    post_checks = _checks_by_prefix(results, "post_implied_by_body_")
    assert post_checks, "expected a post-obligation check"
    assert post_checks[0]["status"] == "PASS", \
        f"post should follow from body: {post_checks[0]}"


def test_post_obligation_pass_when_body_entails_post(parse_src):
    """Clean case: pre: x >= 0, body: x' = x + 5, post: x' >= 5."""
    src = """
    class Good {
      $data x: Float = 0.0
      #process[strategy: code]{
        pre: x >= 0
        x' = x + 5
        post: x' >= 5
      }
    }
    """
    ent = _entity(parse_src, src)
    results = check_invariants_hold(ent)
    post_checks = _checks_by_prefix(results, "post_implied_by_body_")
    assert len(post_checks) == 1
    assert post_checks[0]["status"] == "PASS"


def test_post_obligation_fail_when_body_violates_post(parse_src):
    """Bad spec: pre: x >= 0, body: x' = x - 10, post: x' >= 0.
    Counterexample exists (x = 0 → x' = -10)."""
    src = """
    class Bad {
      $data x: Float = 0.0
      #process[strategy: code]{
        pre: x >= 0
        x' = x - 10
        post: x' >= 0
      }
    }
    """
    ent = _entity(parse_src, src)
    results = check_invariants_hold(ent)
    post_checks = _checks_by_prefix(results, "post_implied_by_body_")
    assert len(post_checks) == 1
    assert post_checks[0]["status"] == "FAIL", \
        f"expected FAIL, got {post_checks[0]}"
    # Counterexample should reference x_next
    assert "x_next" in post_checks[0]["detail"] or "x " in post_checks[0]["detail"]


def test_conditional_body_statement_skipped_gracefully(parse_src):
    """Unhandled body statements (condition/for_all) must not crash the
    verifier — they're silently dropped, and the process still gets its
    invariant/post checks on the parts we DO understand."""
    src = """
    class WithCond {
      $data n: Int [0..10] = 0
      #process[strategy: code]{
        pre: n >= 0
        n' = n + 1
        condition n > 5:
          n' = 0
        post: n' >= 0
      }
      invariant: n >= 0
    }
    """
    ent = _entity(parse_src, src)
    # Must not raise — that is the main assertion here.
    results = check_invariants_hold(ent)
    # The handled body piece (n' = n + 1) should still satisfy the post.
    post_checks = _checks_by_prefix(results, "post_implied_by_body_")
    assert post_checks, "expected at least one post check"
