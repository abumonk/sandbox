"""Tests for visual.ark schema — TC-001 and TC-002.

Verifies that dsl/stdlib/visual.ark parses without errors and that all
expected enum/struct definitions are present in the ArkFile.
"""

import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "parser"))

import pytest
from ark_parser import parse as ark_parse, ArkFile

VISUAL_ARK = REPO_ROOT / "dsl" / "stdlib" / "visual.ark"


@pytest.fixture(scope="module")
def visual_ark_file():
    """Parse visual.ark once and return the ArkFile."""
    return ark_parse(VISUAL_ARK.read_text(encoding="utf-8"), file_path=VISUAL_ARK)


# ---------------------------------------------------------------------------
# TC-001: visual.ark parses without errors
# ---------------------------------------------------------------------------

def test_visual_ark_parses(visual_ark_file):
    """TC-001: dsl/stdlib/visual.ark parses via ArkParser without raising exceptions."""
    assert visual_ark_file is not None
    assert isinstance(visual_ark_file, ArkFile)
    assert len(visual_ark_file.items) > 0


# ---------------------------------------------------------------------------
# TC-002: All expected types are present
# ---------------------------------------------------------------------------

def _get_enums_and_structs(ark_file):
    """Return (enums_by_name, structs_by_name) dicts from an ArkFile."""
    enums = {}
    structs = {}
    for item in ark_file.items:
        if hasattr(item, "kind"):
            if item.kind == "enum":
                enums[item.name] = item
            elif item.kind == "struct":
                structs[item.name] = item
    return enums, structs


def test_visual_types(visual_ark_file):
    """TC-002: All expected enums and structs are present by name."""
    enums, structs = _get_enums_and_structs(visual_ark_file)

    expected_enums = [
        "DiagramType", "PreviewMode", "AnnotationType", "FeedbackStatus",
        "RenderFormat", "SearchMode", "VisualTag",
    ]
    expected_structs = ["RenderConfig", "ReviewFeedback", "ScreenshotMeta"]

    for name in expected_enums:
        assert name in enums, f"Missing enum: {name}"

    for name in expected_structs:
        assert name in structs, f"Missing struct: {name}"


# ---------------------------------------------------------------------------
# Enum variant tests (supporting TC-002)
# ---------------------------------------------------------------------------

def _variants(enum_item):
    """Return the list of variant name strings from an EnumDef."""
    result = []
    for v in (enum_item.variants if hasattr(enum_item, "variants") else []):
        if isinstance(v, str):
            result.append(v)
        elif isinstance(v, dict):
            result.append(v.get("name", str(v)))
        else:
            result.append(getattr(v, "name", str(v)))
    return result


def test_diagram_type_variants(visual_ark_file):
    """DiagramType has mermaid, flowchart, architecture, sequence variants."""
    enums, _ = _get_enums_and_structs(visual_ark_file)
    assert "DiagramType" in enums
    vs = _variants(enums["DiagramType"])
    for expected in ("mermaid", "flowchart", "architecture", "sequence"):
        assert expected in vs, f"DiagramType missing variant: {expected}"


def test_preview_mode_variants(visual_ark_file):
    """PreviewMode has static, interactive, responsive variants."""
    enums, _ = _get_enums_and_structs(visual_ark_file)
    assert "PreviewMode" in enums
    vs = _variants(enums["PreviewMode"])
    for expected in ("static", "interactive", "responsive"):
        assert expected in vs, f"PreviewMode missing variant: {expected}"


def test_annotation_type_variants(visual_ark_file):
    """AnnotationType has rect, arrow, text, blur, segment variants."""
    enums, _ = _get_enums_and_structs(visual_ark_file)
    assert "AnnotationType" in enums
    vs = _variants(enums["AnnotationType"])
    for expected in ("rect", "arrow", "text", "blur", "segment"):
        assert expected in vs, f"AnnotationType missing variant: {expected}"


def test_feedback_status_variants(visual_ark_file):
    """FeedbackStatus has approved, rejected, pending, annotated variants."""
    enums, _ = _get_enums_and_structs(visual_ark_file)
    assert "FeedbackStatus" in enums
    vs = _variants(enums["FeedbackStatus"])
    for expected in ("approved", "rejected", "pending", "annotated"):
        assert expected in vs, f"FeedbackStatus missing variant: {expected}"


def test_render_format_variants(visual_ark_file):
    """RenderFormat has svg, png, html variants."""
    enums, _ = _get_enums_and_structs(visual_ark_file)
    assert "RenderFormat" in enums
    vs = _variants(enums["RenderFormat"])
    for expected in ("svg", "png", "html"):
        assert expected in vs, f"RenderFormat missing variant: {expected}"


def test_search_mode_variants(visual_ark_file):
    """SearchMode has keyword, tag, semantic variants."""
    enums, _ = _get_enums_and_structs(visual_ark_file)
    assert "SearchMode" in enums
    vs = _variants(enums["SearchMode"])
    for expected in ("keyword", "tag", "semantic"):
        assert expected in vs, f"SearchMode missing variant: {expected}"


def test_visual_tag_variants(visual_ark_file):
    """VisualTag has at least diagram, screenshot, annotation variants."""
    enums, _ = _get_enums_and_structs(visual_ark_file)
    assert "VisualTag" in enums
    vs = _variants(enums["VisualTag"])
    for expected in ("diagram", "screenshot", "annotation"):
        assert expected in vs, f"VisualTag missing variant: {expected}"


# ---------------------------------------------------------------------------
# Struct field tests (supporting TC-002)
# ---------------------------------------------------------------------------

def _field_names(struct_item):
    """Return the list of field name strings from a StructDef."""
    fields = getattr(struct_item, "fields", [])
    result = []
    for f in fields:
        if isinstance(f, str):
            result.append(f)
        elif isinstance(f, dict):
            result.append(f.get("name", ""))
        else:
            result.append(getattr(f, "name", str(f)))
    return result


def test_render_config_struct_fields(visual_ark_file):
    """RenderConfig struct has format, width, height, theme fields."""
    _, structs = _get_enums_and_structs(visual_ark_file)
    assert "RenderConfig" in structs
    fnames = _field_names(structs["RenderConfig"])
    for expected in ("format", "width", "height", "theme"):
        assert expected in fnames, f"RenderConfig missing field: {expected}"


def test_review_feedback_struct_fields(visual_ark_file):
    """ReviewFeedback struct has status, annotations, comments, change_requests fields."""
    _, structs = _get_enums_and_structs(visual_ark_file)
    assert "ReviewFeedback" in structs
    fnames = _field_names(structs["ReviewFeedback"])
    for expected in ("status", "annotations", "comments", "change_requests"):
        assert expected in fnames, f"ReviewFeedback missing field: {expected}"


def test_screenshot_meta_struct_fields(visual_ark_file):
    """ScreenshotMeta struct has path, timestamp, tags fields."""
    _, structs = _get_enums_and_structs(visual_ark_file)
    assert "ScreenshotMeta" in structs
    fnames = _field_names(structs["ScreenshotMeta"])
    for expected in ("path", "timestamp", "tags"):
        assert expected in fnames, f"ScreenshotMeta missing field: {expected}"
