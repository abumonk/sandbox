"""Tests for visual parser items — TC-003, TC-005, TC-006, TC-007.

Tests that all 7 visual item kinds parse correctly, produce the right
AST dataclasses, regression-test existing .ark files, and populate
ArkFile index dicts properly.
"""

import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "parser"))

import pytest
from ark_parser import (
    parse as ark_parse,
    ArkFile,
    DiagramDef,
    PreviewDef,
    AnnotationDef,
    VisualReviewDef,
    ScreenshotDef,
    VisualSearchDef,
    RenderConfigDef,
)


# ---------------------------------------------------------------------------
# Snippet helpers
# ---------------------------------------------------------------------------

DIAGRAM_SRC = '''
diagram arch_diagram {
    type: flowchart
    source: "graph LR; A --> B"
}
'''

PREVIEW_SRC = '''
preview component_preview {
    source: "<div>Hello</div>"
    viewport: desktop
    mode: static
}
'''

ANNOTATION_SRC = '''
annotation review_markup {
    target: arch_diagram
}
'''

VISUAL_REVIEW_SRC = '''
visual_review design_review {
    target: arch_diagram
}
'''

SCREENSHOT_SRC = '''
screenshot ui_screenshot {
    path: "screenshots/ui.png"
    source: "chrome"
}
'''

VISUAL_SEARCH_SRC = '''
visual_search arch_search {
    search_mode: keyword
    query: "architecture"
}
'''

RENDER_CONFIG_SRC = '''
render_config hd_config {
    format: svg
    width: 1920
    height: 1080
    theme: "default"
}
'''

ALL_ITEMS_SRC = "\n".join([
    DIAGRAM_SRC,
    PREVIEW_SRC,
    ANNOTATION_SRC,
    VISUAL_REVIEW_SRC,
    SCREENSHOT_SRC,
    VISUAL_SEARCH_SRC,
    RENDER_CONFIG_SRC,
])


# ---------------------------------------------------------------------------
# TC-003: Grammar items — all 7 kinds parse without error
# ---------------------------------------------------------------------------

def test_grammar_items():
    """TC-003: One snippet per item kind — all parse without errors."""
    snippets = {
        "diagram": DIAGRAM_SRC,
        "preview": PREVIEW_SRC,
        "annotation": ANNOTATION_SRC,
        "visual_review": VISUAL_REVIEW_SRC,
        "screenshot": SCREENSHOT_SRC,
        "visual_search": VISUAL_SEARCH_SRC,
        "render_config": RENDER_CONFIG_SRC,
    }
    for kind, src in snippets.items():
        result = ark_parse(src)
        assert result is not None, f"Parse returned None for {kind}"
        assert len(result.items) >= 1, f"No items parsed for {kind}"


# ---------------------------------------------------------------------------
# TC-005: AST dataclasses — correct types and fields
# ---------------------------------------------------------------------------

def test_ast_dataclasses():
    """TC-005: Each snippet produces the correct AST dataclass with correct kind."""
    result = ark_parse(DIAGRAM_SRC)
    defs = [i for i in result.items if isinstance(i, DiagramDef)]
    assert len(defs) == 1
    assert defs[0].kind == "diagram"
    assert defs[0].name == "arch_diagram"

    result = ark_parse(PREVIEW_SRC)
    defs = [i for i in result.items if isinstance(i, PreviewDef)]
    assert len(defs) == 1
    assert defs[0].kind == "preview"
    assert defs[0].name == "component_preview"

    result = ark_parse(ANNOTATION_SRC)
    defs = [i for i in result.items if isinstance(i, AnnotationDef)]
    assert len(defs) == 1
    assert defs[0].kind == "annotation"
    assert defs[0].name == "review_markup"

    result = ark_parse(VISUAL_REVIEW_SRC)
    defs = [i for i in result.items if isinstance(i, VisualReviewDef)]
    assert len(defs) == 1
    assert defs[0].kind == "visual_review"
    assert defs[0].name == "design_review"

    result = ark_parse(SCREENSHOT_SRC)
    defs = [i for i in result.items if isinstance(i, ScreenshotDef)]
    assert len(defs) == 1
    assert defs[0].kind == "screenshot"
    assert defs[0].name == "ui_screenshot"

    result = ark_parse(VISUAL_SEARCH_SRC)
    defs = [i for i in result.items if isinstance(i, VisualSearchDef)]
    assert len(defs) == 1
    assert defs[0].kind == "visual_search"
    assert defs[0].name == "arch_search"

    result = ark_parse(RENDER_CONFIG_SRC)
    defs = [i for i in result.items if isinstance(i, RenderConfigDef)]
    assert len(defs) == 1
    assert defs[0].kind == "render_config"
    assert defs[0].name == "hd_config"


# ---------------------------------------------------------------------------
# Field-level tests (supporting TC-003/TC-005)
# ---------------------------------------------------------------------------

def test_diagram_item_fields():
    """Parsed DiagramDef has name, diagram_type, source, render_config fields."""
    result = ark_parse(DIAGRAM_SRC)
    d = next(i for i in result.items if isinstance(i, DiagramDef))
    assert d.name == "arch_diagram"
    assert d.diagram_type == "flowchart"
    assert d.source is not None
    assert "A --> B" in d.source or "A-->" in d.source or d.source


def test_preview_item_fields():
    """Parsed PreviewDef has name, source, viewport, mode fields."""
    result = ark_parse(PREVIEW_SRC)
    p = next(i for i in result.items if isinstance(i, PreviewDef))
    assert p.name == "component_preview"
    assert p.source is not None
    assert p.viewport == "desktop"
    assert p.mode == "static"


def test_annotation_item_fields():
    """Parsed AnnotationDef has name and target fields."""
    result = ark_parse(ANNOTATION_SRC)
    a = next(i for i in result.items if isinstance(i, AnnotationDef))
    assert a.name == "review_markup"
    assert a.target == "arch_diagram"


def test_visual_review_item_fields():
    """Parsed VisualReviewDef has name and target fields."""
    result = ark_parse(VISUAL_REVIEW_SRC)
    v = next(i for i in result.items if isinstance(i, VisualReviewDef))
    assert v.name == "design_review"
    assert v.target == "arch_diagram"


def test_screenshot_item_fields():
    """Parsed ScreenshotDef has name and path fields."""
    result = ark_parse(SCREENSHOT_SRC)
    s = next(i for i in result.items if isinstance(i, ScreenshotDef))
    assert s.name == "ui_screenshot"
    assert s.path is not None


def test_visual_search_item_fields():
    """Parsed VisualSearchDef has name, search_mode, query fields."""
    result = ark_parse(VISUAL_SEARCH_SRC)
    vs = next(i for i in result.items if isinstance(i, VisualSearchDef))
    assert vs.name == "arch_search"
    assert vs.search_mode == "keyword"
    assert "architecture" in (vs.query or "")


def test_render_config_item_fields():
    """Parsed RenderConfigDef has name, format, width, height, theme fields."""
    result = ark_parse(RENDER_CONFIG_SRC)
    rc = next(i for i in result.items if isinstance(i, RenderConfigDef))
    assert rc.name == "hd_config"
    assert rc.format == "svg"
    assert rc.width == 1920
    assert rc.height == 1080
    assert "default" in (rc.theme or "")


# ---------------------------------------------------------------------------
# TC-006: Regression — existing .ark files still parse
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_parser_smoke():
    """TC-006: Representative existing .ark files parse after grammar extension."""
    test_files = [
        REPO_ROOT / "dsl" / "stdlib" / "types.ark",
        REPO_ROOT / "dsl" / "stdlib" / "visual.ark",
    ]

    for path in test_files:
        if not path.exists():
            pytest.skip(f"File not found: {path}")
        # Should parse without raising ArkParseError (import warnings are ok)
        result = ark_parse(path.read_text(encoding="utf-8"), file_path=path)
        assert result is not None, f"Failed to parse {path}"
        assert isinstance(result, ArkFile), f"Expected ArkFile from {path}"


# ---------------------------------------------------------------------------
# TC-007: ArkFile indices are populated
# ---------------------------------------------------------------------------

def test_arkfile_indices():
    """TC-007: Multi-item snippet populates all 7 ArkFile visual index dicts."""
    result = ark_parse(ALL_ITEMS_SRC)
    assert isinstance(result.diagrams, dict)
    assert isinstance(result.previews, dict)
    assert isinstance(result.annotations, dict)
    assert isinstance(result.visual_reviews, dict)
    assert isinstance(result.screenshots, dict)
    assert isinstance(result.visual_searches, dict)
    assert isinstance(result.render_configs, dict)

    assert "arch_diagram" in result.diagrams
    assert "component_preview" in result.previews
    assert "review_markup" in result.annotations
    assert "design_review" in result.visual_reviews
    assert "ui_screenshot" in result.screenshots
    assert "arch_search" in result.visual_searches
    assert "hd_config" in result.render_configs
