"""Tests for visual rendering subsystems — TC-008 through TC-021.

Covers: MermaidRenderer, HtmlPreviewer, Annotator, ReviewLoop,
ScreenshotManager, and VisualSearch.
"""

import json
import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "visual"))

import pytest


# ============================================================
# TC-008 through TC-010: Mermaid Renderer
# ============================================================

from mermaid_renderer import render_mermaid, generate_mermaid_source, MERMAID_KEYWORDS


def test_mermaid_mmd(tmp_path):
    """TC-008: render_mermaid with flowchart spec returns dict with mmd_path ending .mmd."""
    diagram_ast = {
        "name": "arch_diagram",
        "diagram_type": "flowchart",
        "source": "A --> B",
    }
    result = render_mermaid(diagram_ast, {}, tmp_path)
    assert "mmd_path" in result
    mmd_path = result["mmd_path"]
    assert str(mmd_path).endswith(".mmd")
    content = mmd_path.read_text(encoding="utf-8")
    # Should contain flowchart keyword since source doesn't start with one
    assert any(kw in content for kw in ("graph", "flowchart"))


def test_diagram_types(tmp_path):
    """TC-009: render_mermaid succeeds for each DiagramType variant."""
    diagram_types = ["mermaid", "flowchart", "architecture", "sequence",
                     "class_diagram", "state", "er", "gantt"]
    for dtype in diagram_types:
        diagram_ast = {
            "name": f"test_{dtype}",
            "diagram_type": dtype,
            "source": "A --> B",
        }
        result = render_mermaid(diagram_ast, {}, tmp_path)
        assert result is not None, f"render_mermaid failed for type {dtype}"
        assert "mmd_path" in result
        assert result["mmd_path"].exists(), f".mmd file not created for {dtype}"


def test_mermaid_errors(tmp_path):
    """TC-010: render_mermaid with empty source still writes a .mmd file (no source = prefix only)."""
    # The mermaid renderer doesn't raise — it writes the prefix even for empty source
    diagram_ast = {
        "name": "empty_diagram",
        "diagram_type": "flowchart",
        "source": "",
    }
    result = render_mermaid(diagram_ast, {}, tmp_path)
    assert "mmd_path" in result
    # With empty source the content should still be non-empty (just the keyword)
    content = result["mmd_path"].read_text(encoding="utf-8")
    assert len(content.strip()) > 0


def test_generate_mermaid_source_mermaid_type():
    """Type 'mermaid' returns source as-is."""
    src = "graph LR\nA --> B"
    result = generate_mermaid_source("mermaid", src)
    assert result == src


def test_generate_mermaid_source_prefix_added():
    """Non-mermaid type adds the correct prefix."""
    result = generate_mermaid_source("sequence", "A->>B: hello")
    assert result.startswith("sequenceDiagram")


# ============================================================
# TC-011 through TC-012: HTML Previewer
# ============================================================

from html_previewer import render_preview, generate_preview_html, get_viewport_dimensions


def test_html_preview(tmp_path):
    """TC-011: render_preview returns path to a .html file with <!DOCTYPE html>."""
    preview_ast = {
        "name": "component_preview",
        "source": "<div>Hello World</div>",
        "viewport": "desktop",
        "mode": "static",
    }
    result = render_preview(preview_ast, {}, tmp_path)
    assert "html_path" in result
    html_path = result["html_path"]
    assert str(html_path).endswith(".html")
    content = html_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "<div>Hello World</div>" in content


def test_viewports(tmp_path):
    """TC-012: render_preview with different viewport specs embeds width in HTML."""
    # Desktop viewport: 1920x1080
    preview_desktop = {
        "name": "desktop_preview",
        "source": "<p>Desktop</p>",
        "viewport": "desktop",
        "mode": "static",
    }
    result = render_preview(preview_desktop, {}, tmp_path)
    content = result["html_path"].read_text(encoding="utf-8")
    assert "1920" in content

    # Mobile viewport: 375x667
    preview_mobile = {
        "name": "mobile_preview",
        "source": "<p>Mobile</p>",
        "viewport": "mobile",
        "mode": "static",
    }
    result2 = render_preview(preview_mobile, {}, tmp_path)
    content2 = result2["html_path"].read_text(encoding="utf-8")
    assert "375" in content2


def test_get_viewport_dimensions():
    """get_viewport_dimensions returns correct sizes for named viewports."""
    w, h = get_viewport_dimensions("desktop")
    assert w == 1920 and h == 1080

    w, h = get_viewport_dimensions("mobile")
    assert w == 375 and h == 667

    w, h = get_viewport_dimensions("tablet")
    assert w == 768 and h == 1024


def test_html_preview_interactive_mode(tmp_path):
    """Interactive mode embeds JS in the HTML."""
    preview_ast = {
        "name": "interactive_preview",
        "source": "<button>Click me</button>",
        "viewport": "desktop",
        "mode": "interactive",
    }
    result = render_preview(preview_ast, {}, tmp_path)
    content = result["html_path"].read_text(encoding="utf-8")
    assert "<script>" in content


# ============================================================
# TC-013 through TC-014: Annotator
# ============================================================

from annotator import apply_annotations, validate_bounds, render_annotation_json


def test_annotator():
    """TC-013: apply_annotations returns elements list and no crash for standard types."""
    annotation_ast = {
        "name": "test_annotation",
        "target": "some_image.png",
        "elements": [
            {"type": "rect", "x": 10, "y": 10, "width": 50, "height": 50, "label": "box"},
            {"type": "text", "x": 20, "y": 20, "label": "note"},
        ],
    }
    result = apply_annotations(annotation_ast)
    assert "elements" in result
    assert "warnings" in result
    assert len(result["elements"]) >= 2


def test_bounds():
    """TC-014: validate_bounds returns warnings for out-of-bounds elements."""
    elements_in = [{"type": "rect", "x": 10, "y": 10, "width": 20, "height": 20}]
    warnings_in = validate_bounds(elements_in, viewport_width=100, viewport_height=100)
    assert len(warnings_in) == 0

    elements_out = [{"type": "rect", "x": 150, "y": 10, "width": 20, "height": 20}]
    warnings_out = validate_bounds(elements_out, viewport_width=100, viewport_height=100)
    assert len(warnings_out) > 0


def test_render_annotation_json():
    """render_annotation_json produces a dict with target and elements."""
    annotation_ast = {
        "name": "my_annotation",
        "target": "diagram.png",
        "elements": [
            {"type": "rect", "x": 0, "y": 0, "width": 30, "height": 30},
            {"type": "arrow", "x": 5, "y": 5, "width": 40, "height": 0},
        ],
    }
    result = render_annotation_json(annotation_ast)
    assert "target" in result
    assert "elements" in result
    assert len(result["elements"]) == 2


# ============================================================
# TC-015 through TC-016: Review Loop
# ============================================================

from review_loop import (
    create_review_manifest,
    parse_feedback,
    run_review,
    FeedbackStatus,
)


def test_review_manifest(tmp_path):
    """TC-015: run_review returns dict with review_id, manifest_path, status, feedback."""
    target_ast = {"name": "arch_diagram", "type": "diagram"}
    rendered_file = tmp_path / "arch_diagram.mmd"
    rendered_file.write_text("flowchart TD\nA-->B", encoding="utf-8")

    def stub_render(ast, out_dir):
        return rendered_file

    result = run_review(target_ast, stub_render, tmp_path)

    assert "review_id" in result
    assert "manifest_path" in result
    assert "status" in result
    assert "feedback" in result
    assert result["status"] in ("pending", "approved", "rejected", "annotated",
                                "changes_requested")


def test_feedback_parse():
    """TC-016: parse_feedback correctly maps status strings to validated values."""
    for status in ("approved", "rejected", "pending", "annotated"):
        result = parse_feedback({"status": status})
        assert result["status"] == status

    annotated = parse_feedback({
        "status": "annotated",
        "annotations": [{"type": "rect"}],
    })
    assert annotated["status"] == "annotated"
    assert len(annotated["annotations"]) == 1

    with pytest.raises(ValueError):
        parse_feedback({"status": "unknown_status_xyz"})


def test_create_review_manifest_fields(tmp_path):
    """create_review_manifest writes a JSON file with expected keys."""
    target_ast = {"name": "preview_item", "type": "preview"}
    rendered_file = tmp_path / "preview_item.html"
    rendered_file.write_text("<!DOCTYPE html>", encoding="utf-8")

    manifest = create_review_manifest(target_ast, rendered_file, tmp_path)
    assert "review_id" in manifest
    assert "target_name" in manifest
    assert "rendered_path" in manifest
    assert "feedback_path" in manifest
    assert manifest["target_name"] == "preview_item"


# ============================================================
# TC-018 through TC-019: Screenshot Manager
# ============================================================

from screenshot_manager import (
    ScreenshotCatalog,
    ScreenshotEntry,
    screenshot_from_spec,
    register_screenshot,
    load_catalog,
)


def test_screenshot_register(tmp_path):
    """TC-018: ScreenshotCatalog.register adds entry; get() returns it with path/tags."""
    catalog = ScreenshotCatalog()
    entry = ScreenshotEntry(
        path="screenshots/arch.png",
        tags=["diagram", "mermaid"],
        description="Architecture diagram",
    )
    catalog.register(entry)

    result = catalog.get("arch")  # keyed by stem
    assert result is not None
    assert result.path == "screenshots/arch.png"
    assert "diagram" in result.tags
    assert "mermaid" in result.tags


def test_catalog_roundtrip(tmp_path):
    """TC-019: catalog persists to disk and reloads correctly."""
    catalog_path = tmp_path / "catalog.json"
    catalog1 = ScreenshotCatalog(catalog_path)
    entry = ScreenshotEntry(
        path="screenshots/ui.png",
        tags=["screenshot", "ui"],
        description="UI screenshot",
    )
    catalog1.register(entry)
    catalog1.save()

    # Load fresh instance from the same path
    catalog2 = ScreenshotCatalog(catalog_path)
    result = catalog2.get("ui")
    assert result is not None
    assert result.path == "screenshots/ui.png"
    assert "ui" in result.tags


def test_screenshot_from_spec():
    """screenshot_from_spec builds a ScreenshotEntry from a dict."""
    spec = {
        "path": "screenshots/game.png",
        "tags": ["game", "screenshot"],
        "description": "Game screenshot",
        "source": "selenium",
    }
    entry = screenshot_from_spec(spec)
    assert entry.path == "screenshots/game.png"
    assert "game" in entry.tags
    assert entry.description == "Game screenshot"


# ============================================================
# TC-020 through TC-021: Search
# ============================================================

from search import VisualSearch, keyword_search, tag_search


CATALOG = {
    "screenshots": {
        "arch1": {
            "path": "arch1.png",
            "tags": ["architecture", "diagram"],
            "description": "Architecture overview diagram",
        },
        "ui1": {
            "path": "ui1.png",
            "tags": ["ui", "screenshot"],
            "description": "User interface screenshot",
        },
        "mermaid1": {
            "path": "mermaid1.png",
            "tags": ["mermaid", "diagram"],
            "description": "Mermaid flowchart",
        },
    }
}


def test_keyword_search():
    """TC-020: VisualSearch.search with keyword mode returns matching entries."""
    results = VisualSearch.search(query="architecture", mode="keyword", catalog=CATALOG)
    paths = [r.path for r in results]
    assert "arch1.png" in paths
    # ui1.png does not mention architecture
    assert "ui1.png" not in paths


def test_tag_search():
    """TC-021: VisualSearch.search with tag mode returns only entries with ALL specified tags."""
    results = VisualSearch.search(
        mode="tag",
        tags=["mermaid", "diagram"],
        catalog=CATALOG,
    )
    paths = [r.path for r in results]
    assert "mermaid1.png" in paths
    # arch1 has diagram but not mermaid
    assert "arch1.png" not in paths
    # ui1 has neither
    assert "ui1.png" not in paths


def test_keyword_search_no_match():
    """keyword_search returns empty list when nothing matches."""
    entries = list(CATALOG["screenshots"].values())
    results = keyword_search(entries, "xyzzy_nonexistent_token")
    assert len(results) == 0


def test_tag_search_partial_not_returned():
    """tag_search excludes entries with only partial tag match."""
    entries = list(CATALOG["screenshots"].values())
    results = tag_search(entries, ["diagram", "ui"])
    paths = [r.path for r in results]
    # No entry has BOTH diagram AND ui
    assert len(paths) == 0
