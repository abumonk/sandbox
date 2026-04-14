"""Tests for visual verifier — TC-017, TC-025 through TC-029.

Covers: diagram type validation, review target resolution, annotation bounds (Z3),
render config validation (Z3), and review cycle acyclicity (Z3).
"""

import sys
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "verify"))

import pytest
from visual_verify import (
    check_diagram_types,
    check_review_targets,
    check_annotation_bounds,
    check_render_configs,
    check_review_acyclicity,
    VALID_DIAGRAM_TYPES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _statuses(results):
    return [r["status"] for r in results]


def _has_fail(results):
    return any(r["status"] == "fail" for r in results)


def _all_pass(results):
    return all(r["status"] == "pass" for r in results)


# ============================================================
# TC-025: Diagram type validity
# ============================================================

def test_diagram_type_valid():
    """TC-025: valid type -> pass; invalid type -> fail with message mentioning the type."""
    diagrams_ok = [{"name": "my_diagram", "diagram_type": "mermaid"}]
    results = check_diagram_types(diagrams_ok)
    assert not _has_fail(results), "valid type should not fail"

    diagrams_bad = [{"name": "bad_diagram", "diagram_type": "unknown_type"}]
    results = check_diagram_types(diagrams_bad)
    assert _has_fail(results), "invalid type should fail"
    fail_msgs = [r["message"] for r in results if r["status"] == "fail"]
    assert any("unknown_type" in msg for msg in fail_msgs)


def test_diagram_type_all_valid_variants():
    """Each valid DiagramType variant passes check_diagram_types."""
    for dtype in VALID_DIAGRAM_TYPES:
        diagrams = [{"name": "d", "diagram_type": dtype}]
        results = check_diagram_types(diagrams)
        assert not _has_fail(results), f"Valid type '{dtype}' should not fail"


def test_diagram_type_empty():
    """Empty diagram list produces a pass result."""
    results = check_diagram_types([])
    assert not _has_fail(results)


# ============================================================
# TC-026: Review target resolution
# ============================================================

def test_review_target():
    """TC-026: review targeting existing item -> pass; missing target -> fail."""
    all_names = {"arch_diagram", "component_preview"}

    review_valid = [{"name": "review_a", "target": "arch_diagram"}]
    results = check_review_targets(review_valid, all_names)
    assert _all_pass(results), "valid target should pass"

    review_invalid = [{"name": "review_b", "target": "nonexistent_diagram"}]
    results = check_review_targets(review_invalid, all_names)
    assert _has_fail(results), "missing target should fail"


def test_review_target_preview_valid():
    """visual_review targeting a preview item also passes."""
    all_names = {"component_preview", "arch_diagram"}
    review = [{"name": "review_c", "target": "component_preview"}]
    results = check_review_targets(review, all_names)
    assert _all_pass(results)


# ============================================================
# TC-027: Annotation bounds (Z3)
# ============================================================

def test_annotation_bounds_z3():
    """TC-027: element within bounds -> pass; element exceeding width -> fail."""
    ann_ok = [{
        "name": "ann_ok",
        "elements": [{"type": "rect", "x": 50, "y": 50, "width": 10, "height": 10}],
        "render_config": "rc1",
    }]
    rc = {"rc1": {"width": 100, "height": 100}}
    results = check_annotation_bounds(ann_ok, rc)
    assert not _has_fail(results), "in-bounds element should pass"

    ann_bad = [{
        "name": "ann_bad",
        "elements": [{"type": "rect", "x": 150, "y": 50, "width": 10, "height": 10}],
        "render_config": "rc1",
    }]
    results = check_annotation_bounds(ann_bad, rc)
    assert _has_fail(results), "out-of-bounds element should fail"


def test_annotation_bounds_edge_exactly_at_bound():
    """Element exactly at boundary (x+w == viewport_width) is accepted."""
    ann = [{
        "name": "ann_edge",
        "elements": [{"type": "rect", "x": 0, "y": 0, "width": 100, "height": 100}],
        "render_config": "rc_edge",
    }]
    rc = {"rc_edge": {"width": 100, "height": 100}}
    results = check_annotation_bounds(ann, rc)
    assert not _has_fail(results), "exactly-at-boundary element should pass"


def test_annotation_bounds_no_render_config():
    """Annotation without render_config reference passes (no viewport to check against)."""
    ann = [{
        "name": "ann_free",
        "elements": [{"type": "rect", "x": 50, "y": 50, "width": 10, "height": 10}],
    }]
    results = check_annotation_bounds(ann, {})
    assert not _has_fail(results)


# ============================================================
# TC-028: Render config validity (Z3)
# ============================================================

def test_render_config_z3():
    """TC-028: valid dimensions pass; zero or negative fail."""
    cfg_ok = [{"name": "cfg_ok", "format": "svg", "width": 1920, "height": 1080, "scale": 1.0}]
    results = check_render_configs(cfg_ok)
    assert _all_pass(results), "valid config should pass"

    cfg_zero = [{"name": "cfg_zero", "width": 0, "height": 1080}]
    results = check_render_configs(cfg_zero)
    assert _has_fail(results), "width=0 should fail"

    cfg_neg = [{"name": "cfg_neg", "width": -1, "height": 1080}]
    results = check_render_configs(cfg_neg)
    assert _has_fail(results), "negative width should fail"


def test_render_config_z3_max_dimension():
    """Very large but positive dimensions pass; scale=0 fails."""
    cfg_large = [{"name": "cfg_large", "width": 10000, "height": 8000}]
    results = check_render_configs(cfg_large)
    assert not _has_fail(results), "large positive dimensions should pass"

    cfg_scale_zero = [{"name": "cfg_scale_zero", "width": 1920, "height": 1080, "scale": 0.0}]
    results = check_render_configs(cfg_scale_zero)
    assert _has_fail(results), "scale=0 should fail"


def test_render_config_invalid_format():
    """Invalid format string triggers a fail result."""
    cfg_bad_fmt = [{"name": "cfg_fmt", "width": 800, "height": 600, "format": "bmp"}]
    results = check_render_configs(cfg_bad_fmt)
    assert _has_fail(results)


# ============================================================
# TC-017 / TC-029: Review cycle acyclicity (Z3 ordinals)
# ============================================================

def test_review_acyclicity():
    """TC-017: cyclic review chain -> fail with 'cycle' hint; acyclic -> pass."""
    # Cyclic: A -> B -> A
    cyclic_reviews = [
        {"name": "review_a", "target": "review_b"},
        {"name": "review_b", "target": "review_a"},
    ]
    results = check_review_acyclicity(cyclic_reviews)
    assert _has_fail(results), "cyclic chain should fail"
    fail_msgs = [r["message"] for r in results if r["status"] == "fail"]
    # Message should mention the reviewers involved
    assert any("review_a" in msg or "cycle" in msg.lower() for msg in fail_msgs)


def test_review_acyclic_z3():
    """TC-029: acyclic chain A -> diagram_x -> pass; cyclic A->B->A -> fail."""
    # Acyclic: review_a reviews diagram_x (not another review)
    acyclic_reviews = [
        {"name": "review_a", "target": "diagram_x"},
    ]
    results = check_review_acyclicity(acyclic_reviews)
    assert not _has_fail(results), "acyclic chain should pass"

    # Cyclic: A -> B -> A
    cyclic_reviews = [
        {"name": "rev_x", "target": "rev_y"},
        {"name": "rev_y", "target": "rev_x"},
    ]
    results = check_review_acyclicity(cyclic_reviews)
    assert _has_fail(results), "cyclic chain should fail"


def test_review_acyclic_z3_longer_chain():
    """Chain of 5 acyclic reviews passes; adding a back-edge causes fail."""
    acyclic = [
        {"name": "r1", "target": "r2"},
        {"name": "r2", "target": "r3"},
        {"name": "r3", "target": "r4"},
        {"name": "r4", "target": "r5"},
        {"name": "r5", "target": "diagram_final"},
    ]
    results = check_review_acyclicity(acyclic)
    assert not _has_fail(results), "5-long acyclic chain should pass"

    # Add back-edge r5 -> r1 to form a cycle
    cyclic = acyclic.copy()
    cyclic[-1] = {"name": "r5", "target": "r1"}
    results = check_review_acyclicity(cyclic)
    assert _has_fail(results), "back-edge should cause fail"


def test_review_acyclicity_empty():
    """Empty review list produces a pass result."""
    results = check_review_acyclicity([])
    assert not _has_fail(results)
