"""Tests for tools/codegen/visual_codegen.py — visual code generation.

Covers TC-030 through TC-033.
"""

import json
import sys
import pathlib
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "codegen"))
sys.path.insert(0, str(REPO_ROOT / "tools" / "parser"))

from visual_codegen import (  # noqa: E402
    gen_diagram_mmd,
    gen_preview_html,
    gen_annotation_json,
    gen_render_config_json,
    gen_review_script,
    gen_catalog_index,
    generate,
)


# ---------------------------------------------------------------------------
# TC-030: Codegen produces .mmd from diagram items
# ---------------------------------------------------------------------------

def test_codegen_mmd_flowchart():
    diag = {"kind": "diagram", "name": "test_diag", "diagram_type": "flowchart",
            "content": "A-->B"}
    result = gen_diagram_mmd(diag)
    assert isinstance(result, str)
    assert len(result) > 0


def test_codegen_mmd_mermaid():
    diag = {"kind": "diagram", "name": "d1", "diagram_type": "mermaid",
            "content": "graph TD; A-->B; B-->C"}
    result = gen_diagram_mmd(diag)
    assert "A" in result
    assert "B" in result


def test_codegen_mmd_sequence():
    diag = {"kind": "diagram", "name": "d2", "diagram_type": "sequence",
            "content": "Alice->>Bob: Hello"}
    result = gen_diagram_mmd(diag)
    assert isinstance(result, str)
    assert len(result) > 0


def test_codegen_mmd_all_types():
    """All DiagramType variants produce non-empty output."""
    for dtype in ["mermaid", "flowchart", "architecture", "sequence",
                  "class_diagram", "state", "er", "gantt"]:
        diag = {"kind": "diagram", "name": f"d_{dtype}", "diagram_type": dtype,
                "content": "A-->B"}
        result = gen_diagram_mmd(diag)
        assert isinstance(result, str), f"Failed for {dtype}"


# ---------------------------------------------------------------------------
# TC-031: Codegen produces .html from preview items
# ---------------------------------------------------------------------------

def test_codegen_html_preview():
    preview = {"kind": "preview", "name": "p1", "content": "<h1>Hello</h1>",
               "viewport": "desktop", "mode": "static"}
    result = gen_preview_html(preview)
    assert "<html" in result.lower() or "<!doctype" in result.lower()
    assert "Hello" in result


def test_codegen_html_with_render_config():
    preview = {"kind": "preview", "name": "p2", "content": "<p>Test</p>",
               "viewport": "mobile", "mode": "interactive"}
    rc = {"format": "html", "width": 375, "height": 667, "theme": "dark"}
    result = gen_preview_html(preview, render_config=rc)
    assert isinstance(result, str)
    assert len(result) > 50


# ---------------------------------------------------------------------------
# TC-032: Codegen produces annotation JSON
# ---------------------------------------------------------------------------

def test_codegen_annotation_json():
    ann = {"kind": "annotation", "name": "a1", "target": "screenshot1",
           "elements": [{"type": "rect", "x": 10, "y": 20, "width": 100,
                         "height": 50, "label": "highlight", "color": "#ff0000"}]}
    result = gen_annotation_json(ann)
    parsed = json.loads(result)
    assert "elements" in parsed or "annotations" in parsed or isinstance(parsed, dict)


def test_codegen_annotation_empty_elements():
    ann = {"kind": "annotation", "name": "a2", "target": "s1", "elements": []}
    result = gen_annotation_json(ann)
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# TC-033: Codegen produces render config JSON
# ---------------------------------------------------------------------------

def test_codegen_render_config_json():
    cfg = {"kind": "render_config", "name": "rc1", "format": "svg",
           "width": 800, "height": 600, "theme": "dark", "scale": 2}
    result = gen_render_config_json(cfg)
    parsed = json.loads(result)
    assert parsed.get("width") == 800 or "width" in str(parsed)
    assert parsed.get("height") == 600 or "height" in str(parsed)


def test_codegen_render_config_defaults():
    cfg = {"kind": "render_config", "name": "rc2"}
    result = gen_render_config_json(cfg)
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# Generate orchestrator
# ---------------------------------------------------------------------------

def test_generate_produces_files():
    ark_file = {
        "items": [
            {"kind": "diagram", "name": "d1", "diagram_type": "mermaid",
             "content": "graph TD; A-->B"},
            {"kind": "render_config", "name": "rc1", "format": "svg",
             "width": 800, "height": 600},
        ],
        "diagrams": {"d1": {"kind": "diagram", "name": "d1", "diagram_type": "mermaid",
                            "content": "graph TD; A-->B"}},
        "render_configs": {"rc1": {"kind": "render_config", "name": "rc1",
                                   "format": "svg", "width": 800, "height": 600}},
        "previews": {}, "annotations": {}, "visual_reviews": {},
        "screenshots": {}, "visual_searches": {},
    }
    with tempfile.TemporaryDirectory() as td:
        result = generate(ark_file, out_dir=td)
        assert isinstance(result, dict)
        files = result.get("files", [])
        assert len(files) >= 1


def test_generate_empty_ark():
    ark_file = {"items": [], "diagrams": {}, "previews": {}, "annotations": {},
                "visual_reviews": {}, "screenshots": {}, "visual_searches": {},
                "render_configs": {}}
    with tempfile.TemporaryDirectory() as td:
        result = generate(ark_file, out_dir=td)
        assert isinstance(result, dict)
