"""conftest.py — Shared pytest fixtures for shape_grammar tests.

All fixtures are auto-injected by pytest via conftest discovery.
Tests should use these fixtures rather than hard-coding paths so that
if the spec layout changes, only this file needs updating.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path constants (relative to the R:/Sandbox working directory)
# ---------------------------------------------------------------------------

_SPECS_DIR = Path("shape_grammar/specs")
_FIXTURES_DIR = Path("shape_grammar/tests/fixtures")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def spec_paths() -> dict[str, Path]:
    """Return a mapping from spec island name to its .ark file path.

    Covers the three canonical spec islands authored in T04-T06:
      - shape_grammar  : core entities (Shape, Rule, Scope, Terminal, ShapeGrammar)
      - operations     : operation primitives (ExtrudeOp, SplitOp, ...)
      - semantic       : semantic layer (SemanticLabel, Provenance)
    """
    return {
        "shape_grammar": _SPECS_DIR / "shape_grammar.ark",
        "operations": _SPECS_DIR / "operations.ark",
        "semantic": _SPECS_DIR / "semantic.ark",
    }


@pytest.fixture(
    params=["shape_grammar", "operations", "semantic"],
    ids=["shape_grammar.ark", "operations.ark", "semantic.ark"],
)
def spec_path(request, spec_paths) -> Path:
    """Parametrized fixture: yields one spec .ark path per test run."""
    return spec_paths[request.param]


@pytest.fixture
def canonical_ir():
    """Return a ShapeGrammarIR extracted from shape_grammar.ark.

    shape_grammar.ark is the primary structural spec; it declares the
    ShapeGrammar island with max_depth, seed, and axiom fields, making
    it the most useful baseline for structural assertions.
    """
    from shape_grammar.tools.ir import extract_ir
    return extract_ir(_SPECS_DIR / "shape_grammar.ark")


@pytest.fixture
def rng_seed() -> int:
    """Pinned RNG seed. All determinism tests use this fixture."""
    return 42


@pytest.fixture
def unbounded_fixture_path() -> Path:
    """Return the path to the deliberate counterexample for TC-04d."""
    return _FIXTURES_DIR / "unbounded.ark"
