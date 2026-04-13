"""End-to-end pipeline tests that invoke ark.py as a subprocess.

Verifies that:
- parse command exits 0 for test_expression.ark
- codegen --target rust --stdout produces correct output for test_expression.ark
- codegen --target cpp raises non-zero exit (NotImplementedError)
- parse command exits 0 for expressif_examples.ark
"""

import subprocess
import sys
import pytest
from pathlib import Path

_ARK_ROOT = Path(__file__).resolve().parent.parent
_ARK_PY = _ARK_ROOT / "ark.py"


def _run_ark(*args, check=False):
    """Run ark.py with args, return CompletedProcess."""
    result = subprocess.run(
        [sys.executable, str(_ARK_PY)] + list(args),
        capture_output=True, text=True, cwd=str(_ARK_ROOT)
    )
    return result


# ---------------------------------------------------------------------------
# 1. test_parse_test_expression
# ---------------------------------------------------------------------------

def test_parse_test_expression():
    """python ark.py parse specs/test_expression.ark exits 0."""
    result = _run_ark("parse", "specs/test_expression.ark")
    assert result.returncode == 0, (
        f"Expected exit 0, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# 2. test_codegen_test_expression
# ---------------------------------------------------------------------------

def test_codegen_test_expression():
    """Codegen --target rust --stdout contains normalize-name or normalize_name."""
    result = _run_ark("codegen", "specs/test_expression.ark", "--target", "rust", "--stdout")
    assert result.returncode == 0, (
        f"Expected exit 0, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    output = result.stdout
    assert ("pub fn normalize_name" in output or "normalize-name" in output), (
        f"Expected 'pub fn normalize_name' or 'normalize-name' in output.\n"
        f"stdout: {output}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# 3. test_codegen_produces_player_struct
# ---------------------------------------------------------------------------

def test_codegen_produces_player_struct():
    """Codegen --target rust --stdout contains struct Player."""
    result = _run_ark("codegen", "specs/test_expression.ark", "--target", "rust", "--stdout")
    assert result.returncode == 0, (
        f"Expected exit 0, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    output = result.stdout
    assert "struct Player" in output, (
        f"Expected 'struct Player' in output.\n"
        f"stdout: {output}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# 4. test_codegen_predicate_bool
# ---------------------------------------------------------------------------

def test_codegen_predicate_bool():
    """Codegen --target rust --stdout contains -> bool (from is-valid-name predicate)."""
    result = _run_ark("codegen", "specs/test_expression.ark", "--target", "rust", "--stdout")
    assert result.returncode == 0, (
        f"Expected exit 0, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    output = result.stdout
    assert "-> bool" in output, (
        f"Expected '-> bool' in output.\n"
        f"stdout: {output}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# 5. test_parse_expressif_examples
# ---------------------------------------------------------------------------

def test_parse_expressif_examples():
    """python ark.py parse specs/examples/expressif_examples.ark exits 0."""
    result = _run_ark("parse", "specs/examples/expressif_examples.ark")
    assert result.returncode == 0, (
        f"Expected exit 0, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# 6. test_cpp_codegen_raises_on_expression
# ---------------------------------------------------------------------------

def test_cpp_codegen_raises_on_expression():
    """Codegen --target cpp on test_expression.ark exits non-zero (NotImplementedError)."""
    result = _run_ark("codegen", "specs/test_expression.ark", "--target", "cpp")
    assert result.returncode != 0, (
        f"Expected non-zero exit for cpp codegen on expression spec, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
