"""
Visual Runner — top-level orchestrator for the ARK visual pipeline.

Reads visual items from a parsed ArkFile (or AST dict) and dispatches to
the appropriate renderers/managers in order:

  1. Diagrams        → mermaid_renderer.render_mermaid()
  2. Previews        → html_previewer.render_preview()
  3. Annotations     → annotator.render_annotation_json()
  4. Screenshots     → screenshot_manager.ScreenshotCatalog
  5. Visual searches → search.search_from_spec()
  6. Visual reviews  → review_loop.run_review()

Entry point:  run_visual_pipeline(ark_file, out_dir) -> dict
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Union

from mermaid_renderer import render_mermaid
from html_previewer import render_preview
from annotator import render_annotation_json
from review_loop import run_review
from screenshot_manager import ScreenshotCatalog, screenshot_from_spec
from search import search_from_spec


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_visual_pipeline(ark_file: Any, out_dir: Union[str, Path]) -> dict:
    """Run the complete visual pipeline on a parsed .ark file.

    Args:
        ark_file: Parsed ArkFile object (from ark_parser) **or** a raw dict
                  with the same attribute structure.  Both dict and dataclass
                  forms are supported — fields are accessed via
                  :func:`_get_attr`.
        out_dir:  Directory where all generated artefacts are written.
                  Sub-directories are created automatically:
                    <out_dir>/diagrams/
                    <out_dir>/previews/
                    <out_dir>/annotations/
                    <out_dir>/screenshots/
                    <out_dir>/searches/
                    <out_dir>/reviews/

    Returns:
        {
            "diagrams":   int,  # number of diagrams processed
            "previews":   int,  # number of previews processed
            "annotations": int, # number of annotations processed
            "screenshots": int, # number of screenshots registered
            "searches":   int,  # number of visual searches executed
            "reviews":    int,  # number of review cycles initiated
            "errors":     list, # list of error strings collected during processing
            "output_dir": str,  # absolute path of out_dir
        }
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Extract all visual items grouped by type ---
    items = extract_visual_items(ark_file)

    # --- Build a render_config lookup dict: name -> config dict ---
    render_configs = resolve_render_configs(items)

    errors: list[str] = []

    # 1. Diagrams
    diagram_results = process_diagrams(
        items.get("diagrams", []),
        render_configs,
        out_dir / "diagrams",
        errors,
    )

    # 2. Previews
    preview_results = process_previews(
        items.get("previews", []),
        render_configs,
        out_dir / "previews",
        errors,
    )

    # 3. Annotations
    annotation_results = process_annotations(
        items.get("annotations", []),
        out_dir / "annotations",
        errors,
    )

    # 4. Screenshots
    screenshot_results = process_screenshots(
        items.get("screenshots", []),
        out_dir / "screenshots",
        errors,
    )

    # 5. Visual searches
    search_results = process_searches(
        items.get("visual_searches", []),
        items,
        out_dir / "searches",
        errors,
    )

    # 6. Visual reviews
    review_results = process_reviews(
        items.get("visual_reviews", []),
        render_configs,
        out_dir / "reviews",
        errors,
    )

    return {
        "diagrams":    len(diagram_results),
        "previews":    len(preview_results),
        "annotations": len(annotation_results),
        "screenshots": len(screenshot_results),
        "searches":    len(search_results),
        "reviews":     len(review_results),
        "errors":      errors,
        "output_dir":  str(out_dir.resolve()),
    }


def extract_visual_items(ark_file: Any) -> dict:
    """Group visual items by type from an ArkFile or equivalent dict.

    Accepts either a parsed ArkFile dataclass or a plain dict.  Returns a
    normalised dict where each key maps to a *list* of item dicts:

        {
            "diagrams":        [dict, ...],
            "previews":        [dict, ...],
            "annotations":     [dict, ...],
            "visual_reviews":  [dict, ...],
            "screenshots":     [dict, ...],
            "visual_searches": [dict, ...],
            "render_configs":  [dict, ...],
        }

    Individual items are normalised so that both dataclass and dict sources
    yield a plain dict with the same keys.
    """
    keys = [
        "diagrams",
        "previews",
        "annotations",
        "visual_reviews",
        "screenshots",
        "visual_searches",
        "render_configs",
    ]

    result: dict = {}
    for key in keys:
        raw = _get_attr(ark_file, key, {})
        # ArkFile stores these as name->def dicts; raw list is also accepted.
        if isinstance(raw, dict):
            items_list = list(raw.values())
        elif isinstance(raw, list):
            items_list = list(raw)
        else:
            items_list = []

        # Normalise each item to a plain dict
        normalised = []
        for item in items_list:
            if isinstance(item, dict):
                normalised.append(item)
            elif hasattr(item, "__dict__"):
                normalised.append(vars(item))
            else:
                normalised.append({"_raw": str(item)})
        result[key] = normalised

    return result


def resolve_render_configs(items: dict) -> dict:
    """Build a name→config dict from the render_config items list.

    Each render_config item is expected to have at least a ``name`` field.
    The resulting dict maps config name → plain dict of config values.

    Args:
        items: The grouped-items dict returned by :func:`extract_visual_items`.

    Returns:
        dict mapping config name (str) → config dict.
    """
    configs: dict[str, dict] = {}
    for cfg in items.get("render_configs", []):
        name = cfg.get("name") or cfg.get("id") or ""
        if name:
            configs[name] = cfg
    return configs


def process_diagrams(
    diagrams: list,
    render_configs: dict,
    out_dir: Path,
    errors: list,
) -> list[dict]:
    """Render each diagram item using :func:`render_mermaid`.

    Args:
        diagrams:       List of diagram item dicts.
        render_configs: Resolved config lookup from :func:`resolve_render_configs`.
        out_dir:        Output directory for .mmd / .svg / .png files.
        errors:         Mutable list to which error strings are appended.

    Returns:
        List of result dicts from ``render_mermaid``, one per diagram.
    """
    results: list[dict] = []
    out_dir = Path(out_dir)

    for diagram in diagrams:
        try:
            config_name = diagram.get("render_config") or ""
            render_config = render_configs.get(config_name, {}) if config_name else {}
            result = render_mermaid(diagram, render_config, out_dir)
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            name = diagram.get("name", "<unnamed>")
            errors.append(f"diagram '{name}': {exc}")

    return results


def process_previews(
    previews: list,
    render_configs: dict,
    out_dir: Path,
    errors: list,
) -> list[dict]:
    """Render each preview item using :func:`render_preview`.

    Args:
        previews:       List of preview item dicts.
        render_configs: Resolved config lookup from :func:`resolve_render_configs`.
        out_dir:        Output directory for HTML files.
        errors:         Mutable list to which error strings are appended.

    Returns:
        List of result dicts from ``render_preview``, one per preview.
    """
    results: list[dict] = []
    out_dir = Path(out_dir)

    for preview in previews:
        try:
            config_name = preview.get("render_config") or ""
            render_config = render_configs.get(config_name, {}) if config_name else {}
            result = render_preview(preview, render_config, out_dir)
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            name = preview.get("name", "<unnamed>")
            errors.append(f"preview '{name}': {exc}")

    return results


def process_annotations(
    annotations: list,
    out_dir: Path,
    errors: list,
) -> list[dict]:
    """Process each annotation item using :func:`render_annotation_json`.

    Args:
        annotations: List of annotation item dicts.
        out_dir:     Output directory (reserved for future file output).
        errors:      Mutable list to which error strings are appended.

    Returns:
        List of result dicts from ``render_annotation_json``, one per annotation.
    """
    results: list[dict] = []

    for annotation in annotations:
        try:
            result = render_annotation_json(annotation)
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            name = annotation.get("name", "<unnamed>")
            errors.append(f"annotation '{name}': {exc}")

    return results


def process_screenshots(
    screenshots: list,
    out_dir: Path,
    errors: list,
) -> list[dict]:
    """Register each screenshot item into a :class:`ScreenshotCatalog`.

    Args:
        screenshots: List of screenshot item dicts.
        out_dir:     Directory where the catalog JSON file is written.
        errors:      Mutable list to which error strings are appended.

    Returns:
        List of registration result dicts, one per screenshot.
    """
    results: list[dict] = []
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    catalog_path = out_dir / "screenshot_catalog.json"
    catalog = ScreenshotCatalog(catalog_path)

    for screenshot in screenshots:
        try:
            entry = screenshot_from_spec(screenshot)
            catalog.register(entry)
            name = entry._name()
            results.append({"name": name, "path": entry.path, "registered": True})
        except Exception as exc:  # noqa: BLE001
            name = screenshot.get("name", "<unnamed>")
            errors.append(f"screenshot '{name}': {exc}")

    if results:
        try:
            catalog.save()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"screenshot catalog save failed: {exc}")

    return results


def process_searches(
    visual_searches: list,
    items: dict,
    out_dir: Path,
    errors: list,
) -> list[dict]:
    """Execute each visual search item using :func:`search_from_spec`.

    The catalog used for searching is built from the screenshot items
    already present in *items*.

    Args:
        visual_searches: List of visual_search item dicts.
        items:           The grouped-items dict (used to build a catalog from
                         screenshot items for searching).
        out_dir:         Output directory (reserved for future result files).
        errors:          Mutable list to which error strings are appended.

    Returns:
        List of dicts, each containing ``{"name": str, "results": list}``
        for one search item.
    """
    results: list[dict] = []

    # Build a minimal catalog from screenshot items for searching.
    screenshots = items.get("screenshots", [])
    catalog: dict[str, Any] = {
        "version": 1,
        "screenshots": {
            (s.get("name") or s.get("path") or str(i)): s
            for i, s in enumerate(screenshots)
        },
    }

    for search in visual_searches:
        try:
            search_results = search_from_spec(search, catalog)
            name = search.get("name", "<unnamed>")
            results.append({
                "name": name,
                "results": [
                    {
                        "path": r.path,
                        "score": r.score,
                        "tags": r.tags,
                        "matched_terms": r.matched_terms,
                    }
                    for r in search_results
                ],
            })
        except Exception as exc:  # noqa: BLE001
            name = search.get("name", "<unnamed>")
            errors.append(f"visual_search '{name}': {exc}")

    return results


def process_reviews(
    visual_reviews: list,
    render_configs: dict,
    out_dir: Path,
    errors: list,
) -> list[dict]:
    """Initiate a review cycle for each visual_review item via :func:`run_review`.

    The render function used is a no-op that returns a placeholder path when
    no previously-rendered artefact is available.  Callers that need a real
    render-then-review flow should call :func:`review_loop.run_review` directly
    with a proper ``render_fn``.

    Args:
        visual_reviews: List of visual_review item dicts.
        render_configs: Resolved config lookup (not currently used but kept for
                        future render-before-review integration).
        out_dir:        Directory for manifest and feedback JSON files.
        errors:         Mutable list to which error strings are appended.

    Returns:
        List of result dicts from ``run_review``, one per review item.
    """
    results: list[dict] = []
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for review in visual_reviews:
        try:
            # Provide a simple pass-through render_fn that writes a placeholder
            # if the target artifact does not already exist on disk.
            def _noop_render(target_ast, _out_dir, _review=review):
                target = _get_attr(target_ast, "target") or _get_attr(target_ast, "name") or "artifact"
                placeholder = Path(_out_dir) / f"{target}.placeholder"
                placeholder.parent.mkdir(parents=True, exist_ok=True)
                if not placeholder.exists():
                    placeholder.write_text(f"[placeholder for review: {target}]", encoding="utf-8")
                return placeholder

            result = run_review(review, _noop_render, out_dir)
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            name = review.get("name", "<unnamed>")
            errors.append(f"visual_review '{name}': {exc}")

    return results


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------


def visual_runner_from_spec(ark_file: Any) -> dict:
    """Convenience wrapper: run the full pipeline writing to a temp directory.

    Creates a temporary directory, runs :func:`run_visual_pipeline`, and
    returns the result dict.  Useful for quick one-shot invocations where
    the caller does not care about the output location.

    Args:
        ark_file: Parsed ArkFile or equivalent dict.

    Returns:
        Same dict as :func:`run_visual_pipeline`.
    """
    with tempfile.TemporaryDirectory(prefix="ark_visual_") as tmp:
        return run_visual_pipeline(ark_file, Path(tmp))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Retrieve *key* from either a dict or an object attribute."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)
