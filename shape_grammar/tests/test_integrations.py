"""test_integrations.py — Tests for shape_grammar.tools.integrations adapters.

Covers:
  - TC-11: Visualizer adapter smoke (non-empty dict with 'ark_data' key).
  - TC-12: Impact adapter returns dict with 'impact' / 'rule_tree_edges' keys.
  - TC-13: Diff adapter returns dict with 'rule_tree_diff' and rule_diff sub-keys.
  - TC-14: All adapters green (umbrella, no exception on cga_tower.ark).
  - Error paths: AdapterError on non-existent .ark file.
  - Garbage subprocess output -> AdapterError with feasibility hint.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from shape_grammar.tools.integrations._errors import AdapterError
from shape_grammar.tools.integrations.diff_adapter import diff
from shape_grammar.tools.integrations.impact_adapter import impact
from shape_grammar.tools.integrations.visualizer_adapter import visualize


# ---------------------------------------------------------------------------
# Path constants (relative to R:/Sandbox working directory)
# ---------------------------------------------------------------------------

_EXAMPLES = Path("shape_grammar/examples")
_CGA_TOWER = _EXAMPLES / "cga_tower.ark"
_L_SYSTEM = _EXAMPLES / "l_system.ark"
_SEMANTIC_FACADE = _EXAMPLES / "semantic_facade.ark"

# Sanity check: confirm the example files are actually there.
# If this assert fires, the test collection itself fails with a clear message.
assert _CGA_TOWER.exists(), f"example not found: {_CGA_TOWER}"
assert _L_SYSTEM.exists(), f"example not found: {_L_SYSTEM}"
assert _SEMANTIC_FACADE.exists(), f"example not found: {_SEMANTIC_FACADE}"


# ---------------------------------------------------------------------------
# TC-11: Visualizer adapter smoke
# ---------------------------------------------------------------------------


def test_visualizer_adapter_smoke() -> None:
    """visualize(cga_tower.ark) returns a non-empty dict with expected keys.

    TC-11: Visualizer adapter produces annotated HTML (via ark graph).
    The output dict must have 'ark_data' and 'sg_annotations' keys.
    """
    result = visualize(_CGA_TOWER)
    assert isinstance(result, dict), f"expected dict, got {type(result)}"
    assert result, "visualize returned an empty dict"
    assert "ark_data" in result, f"missing 'ark_data' key; got {list(result.keys())}"
    assert "sg_annotations" in result, (
        f"missing 'sg_annotations' key; got {list(result.keys())}"
    )


# ---------------------------------------------------------------------------
# TC-12: Impact adapter smoke
# ---------------------------------------------------------------------------


def test_impact_adapter_smoke() -> None:
    """impact(cga_tower.ark, 'Rule') returns a dict with 'rule_tree_edges'.

    TC-12: Impact adapter returns augmented report with rule-tree edges.
    """
    result = impact(_CGA_TOWER, "Rule")
    assert isinstance(result, dict), f"expected dict, got {type(result)}"
    assert "rule_tree_edges" in result, (
        f"missing 'rule_tree_edges' key; got {list(result.keys())}"
    )
    assert isinstance(result["rule_tree_edges"], list), (
        f"'rule_tree_edges' should be a list, got {type(result['rule_tree_edges'])}"
    )


# ---------------------------------------------------------------------------
# TC-13: Diff adapter smoke
# ---------------------------------------------------------------------------


def test_diff_adapter_smoke() -> None:
    """diff(cga_tower.ark, semantic_facade.ark) returns a dict with 'rule_tree_diff'.

    TC-13: Diff adapter returns rule-tree structural diff.
    """
    result = diff(_CGA_TOWER, _SEMANTIC_FACADE)
    assert isinstance(result, dict), f"expected dict, got {type(result)}"
    assert "rule_tree_diff" in result, (
        f"missing 'rule_tree_diff' key; got {list(result.keys())}"
    )
    rtd = result["rule_tree_diff"]
    assert isinstance(rtd, dict), f"rule_tree_diff should be a dict, got {type(rtd)}"
    # The rule_tree_diff must have added/removed/modified sub-keys.
    for key in ("rules_added", "rules_removed", "rules_modified"):
        assert key in rtd, f"rule_tree_diff missing sub-key '{key}'; got {list(rtd.keys())}"


# ---------------------------------------------------------------------------
# TC-14: All adapters green (umbrella)
# ---------------------------------------------------------------------------


def test_all_adapters_green() -> None:
    """All three adapters complete without exception on a single grammar.

    TC-14: Full integration adapter test suite green.
    """
    vis_result = visualize(_CGA_TOWER)
    assert vis_result, "visualize returned empty dict"

    imp_result = impact(_CGA_TOWER)
    assert imp_result, "impact returned empty dict"

    dif_result = diff(_CGA_TOWER, _L_SYSTEM)
    assert dif_result, "diff returned empty dict"


# ---------------------------------------------------------------------------
# Error paths: non-existent file -> AdapterError
# ---------------------------------------------------------------------------


def test_visualizer_adapter_error_path(tmp_path: Path) -> None:
    """visualize() on a non-existent file raises AdapterError."""
    missing = tmp_path / "no_such_file.ark"
    with pytest.raises(AdapterError):
        visualize(missing)


def test_impact_adapter_error_path(tmp_path: Path) -> None:
    """impact() on a non-existent file raises AdapterError."""
    missing = tmp_path / "no_such_file.ark"
    with pytest.raises(AdapterError):
        impact(missing)


def test_diff_adapter_error_path(tmp_path: Path) -> None:
    """diff() with a non-existent first file raises AdapterError."""
    missing = tmp_path / "no_such_file.ark"
    with pytest.raises(AdapterError):
        diff(missing, _CGA_TOWER)


# ---------------------------------------------------------------------------
# Garbage subprocess output -> AdapterError with feasibility hint
# ---------------------------------------------------------------------------


def _make_garbage_run_result() -> MagicMock:
    """Return a mock CompletedProcess whose stdout is pure garbage."""
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout = "this is not HTML and has no const DATA blob"
    mock.stderr = ""
    return mock


def test_visualizer_garbage_output_raises_adapter_error() -> None:
    """When ark graph returns garbage HTML, visualize raises AdapterError with hint."""
    with patch("subprocess.run", return_value=_make_garbage_run_result()):
        # Also patch tempfile so we don't need an actual file write.
        import tempfile
        import builtins

        real_open = builtins.open

        class _FakeTmp:
            name = "fake.html"
            def __enter__(self): return self
            def __exit__(self, *a): pass

        # We need the out_path.read_text to return garbage; patch Path.read_text.
        with patch("shape_grammar.tools.integrations.visualizer_adapter.tempfile") as mock_tf:
            mock_tf.NamedTemporaryFile.return_value = _FakeTmp()
            # Patch Path.read_text and Path.unlink at module level.
            with patch(
                "shape_grammar.tools.integrations.visualizer_adapter.Path.read_text",
                return_value="garbage: no DATA blob here",
            ):
                with patch(
                    "shape_grammar.tools.integrations.visualizer_adapter.Path.unlink",
                    return_value=None,
                ):
                    with pytest.raises(AdapterError) as exc_info:
                        visualize(_CGA_TOWER)
    # The error message must reference the feasibility hint.
    assert "ark-as-host-feasibility.md" in str(exc_info.value), (
        f"AdapterError message missing feasibility hint: {exc_info.value}"
    )


def test_impact_garbage_output_raises_adapter_error() -> None:
    """When ark impact returns content with unexpected format, impact may raise AdapterError.

    impact() raises AdapterError when ark output is absent/has wrong format.
    We simulate a missing 'Impact Analysis:' header.
    """
    # A non-empty string but missing the 'Impact Analysis:' header line.
    garbage = "some content that is not ark impact output"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=garbage,
            stderr="",
        )
        with pytest.raises(AdapterError) as exc_info:
            impact(_CGA_TOWER, "Rule")
    assert "ark-as-host-feasibility.md" in str(exc_info.value), (
        f"AdapterError missing hint: {exc_info.value}"
    )


def test_diff_garbage_output_raises_adapter_error() -> None:
    """When ark diff returns non-JSON output, diff raises AdapterError with hint."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not json at all",
            stderr="",
        )
        with pytest.raises(AdapterError) as exc_info:
            diff(_CGA_TOWER, _SEMANTIC_FACADE)
    assert "ark-as-host-feasibility.md" in str(exc_info.value), (
        f"AdapterError missing hint: {exc_info.value}"
    )


# ---------------------------------------------------------------------------
# Extra: unknown entity -> empty rule_tree_edges (not an error)
# ---------------------------------------------------------------------------


def test_impact_adapter_unknown_entity() -> None:
    """impact() with an entity name not in the grammar returns empty rule_tree_edges."""
    result = impact(_CGA_TOWER, "XyzNonExistentEntity12345")
    assert isinstance(result, dict)
    assert "rule_tree_edges" in result
    # May be empty since the entity doesn't exist in the IR rules.
    assert isinstance(result["rule_tree_edges"], list)
