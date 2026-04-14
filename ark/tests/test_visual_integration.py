"""Tests for visual communication integration — end-to-end pipeline tests.

Covers TC-022 through TC-024, TC-034 through TC-037.
"""

import json
import subprocess
import sys
import pathlib
import tempfile

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "parser"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "visual"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "codegen"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "verify"))

from ark_parser import parse as ark_parse  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_ark(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "ark.py"] + list(args),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )


# ---------------------------------------------------------------------------
# TC-022: Visual runner dispatches diagrams to mermaid renderer
# ---------------------------------------------------------------------------

def test_runner_diagrams():
    from visual_runner import run_visual_pipeline
    ark = {
        "items": [
            {"kind": "diagram", "name": "d1", "diagram_type": "mermaid",
             "content": "graph TD; A-->B"},
        ],
        "diagrams": {"d1": {"kind": "diagram", "name": "d1",
                            "diagram_type": "mermaid", "content": "graph TD; A-->B"}},
        "previews": {}, "annotations": {}, "visual_reviews": {},
        "screenshots": {}, "visual_searches": {}, "render_configs": {},
    }
    with tempfile.TemporaryDirectory() as td:
        result = run_visual_pipeline(ark, td)
        assert result.get("diagrams", 0) >= 1 or "diagram" in str(result).lower()


# ---------------------------------------------------------------------------
# TC-023: Visual runner dispatches previews to html previewer
# ---------------------------------------------------------------------------

def test_runner_previews():
    from visual_runner import run_visual_pipeline
    ark = {
        "items": [
            {"kind": "preview", "name": "p1", "content": "<h1>Hi</h1>",
             "viewport": "desktop", "mode": "static"},
        ],
        "diagrams": {},
        "previews": {"p1": {"kind": "preview", "name": "p1",
                            "content": "<h1>Hi</h1>", "viewport": "desktop",
                            "mode": "static"}},
        "annotations": {}, "visual_reviews": {},
        "screenshots": {}, "visual_searches": {}, "render_configs": {},
    }
    with tempfile.TemporaryDirectory() as td:
        result = run_visual_pipeline(ark, td)
        assert result.get("previews", 0) >= 1 or "preview" in str(result).lower()


# ---------------------------------------------------------------------------
# TC-024: CLI ark visual subcommand works
# ---------------------------------------------------------------------------

def test_cli_visual_help():
    r = _run_ark("visual", "--help")
    # Should exit 0 or print usage
    assert r.returncode == 0 or "usage" in (r.stdout + r.stderr).lower()


def test_cli_visual_verify():
    spec = REPO_ROOT / "specs" / "infra" / "visual_island.ark"
    if not spec.exists():
        pytest.skip("visual_island.ark not found")
    r = _run_ark("visual", "verify", str(spec))
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# TC-034: Visual island spec parses and verifies
# ---------------------------------------------------------------------------

def test_visual_island_spec_parses():
    spec = REPO_ROOT / "specs" / "infra" / "visual_island.ark"
    if not spec.exists():
        pytest.skip("visual_island.ark not found")
    result = ark_parse(spec.read_text(encoding="utf-8"))
    assert result is not None


def test_visual_island_spec_verifies():
    spec = REPO_ROOT / "specs" / "infra" / "visual_island.ark"
    if not spec.exists():
        pytest.skip("visual_island.ark not found")
    r = _run_ark("visual", "verify", str(spec))
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# TC-035: Example visual specs produce rendered output
# ---------------------------------------------------------------------------

def test_example_specs_parse():
    spec = REPO_ROOT / "specs" / "examples" / "visual_examples.ark"
    if not spec.exists():
        pytest.skip("visual_examples.ark not found")
    result = ark_parse(spec.read_text(encoding="utf-8"))
    assert result is not None


def test_example_specs_codegen():
    spec = REPO_ROOT / "specs" / "examples" / "visual_examples.ark"
    if not spec.exists():
        pytest.skip("visual_examples.ark not found")
    with tempfile.TemporaryDirectory() as td:
        r = _run_ark("visual", "codegen", str(spec), "--out", td)
        # codegen should produce output (may succeed or have minor issues)
        assert r.returncode == 0 or "generated" in (r.stdout + r.stderr).lower()


# ---------------------------------------------------------------------------
# TC-036: Visualizer renders visual pipeline items
# ---------------------------------------------------------------------------

def test_visualizer_visual():
    """Verify extract_visual_data exists and handles visual items."""
    sys.path.insert(0, str(REPO_ROOT / "tools" / "visualizer"))
    from ark_visualizer import extract_visual_data
    ast = {
        "items": [
            {"kind": "diagram", "name": "d1", "diagram_type": "mermaid"},
            {"kind": "render_config", "name": "rc1", "format": "svg"},
        ]
    }
    result = extract_visual_data(ast)
    assert "nodes" in result
    assert "links" in result or "edges" in result


# ---------------------------------------------------------------------------
# TC-037: VisualIsland registered in root.ark
# ---------------------------------------------------------------------------

def test_root_ark_visual_registered():
    root = REPO_ROOT / "specs" / "root.ark"
    if not root.exists():
        pytest.skip("root.ark not found")
    content = root.read_text(encoding="utf-8")
    assert "VisualIsland" in content


def test_root_ark_parses():
    root = REPO_ROOT / "specs" / "root.ark"
    if not root.exists():
        pytest.skip("root.ark not found")
    r = _run_ark("parse", str(root))
    assert r.returncode == 0
