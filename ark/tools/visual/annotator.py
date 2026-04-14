"""
Image annotation module for the ARK visual communication layer.

Applies annotation elements (rect, arrow, text, blur, segment, highlight,
circle, freehand) to images using Pillow when available, or generates
a JSON overlay descriptor as a fallback.

Pillow (PIL) is an optional dependency. The module works without it by
falling back to render_annotation_json().
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False

# ---------------------------------------------------------------------------
# Supported annotation element types
# ---------------------------------------------------------------------------
SUPPORTED_TYPES = frozenset({
    "rect", "arrow", "text", "blur", "segment",
    "highlight", "circle", "freehand",
})

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_annotations(
    annotation_ast: Dict[str, Any],
    image_path: Optional[str | Path] = None,
    viewport_bounds: Optional[Tuple[int, int]] = None,
) -> Dict[str, Any]:
    """Apply annotation elements from an AST to an image.

    Parameters
    ----------
    annotation_ast:
        An AnnotationDef-like dict (or dataclass converted via __dict__)
        with at minimum an ``elements`` list and optionally a ``target``
        string (image filename hint).
    image_path:
        Path to the base image.  Required when Pillow is available and
        actual rendering is desired; ignored (but accepted) in JSON-only mode.
    viewport_bounds:
        ``(width, height)`` tuple used for bounds validation.  When omitted
        and an image is loaded, the image dimensions are used instead.

    Returns
    -------
    dict
        ``{"elements": list, "warnings": list, "output_path": Path | None}``
    """
    # Normalise AST input — accept dataclass or dict.
    if hasattr(annotation_ast, "__dict__"):
        ast = annotation_ast.__dict__
    else:
        ast = dict(annotation_ast)

    elements: List[Dict[str, Any]] = _extract_elements(ast)
    warnings: List[str] = []
    output_path: Optional[Path] = None

    # Validate bounds if requested.
    if viewport_bounds is not None:
        vw, vh = viewport_bounds
        warnings.extend(validate_bounds(elements, vw, vh))

    if _PILLOW_AVAILABLE and image_path is not None:
        # Full Pillow rendering path.
        img_path = Path(image_path)
        try:
            image = Image.open(img_path).convert("RGBA")
        except (FileNotFoundError, OSError) as exc:
            warnings.append(f"Cannot open image '{img_path}': {exc}")
            # Fall through to JSON overlay below.
            json_result = render_annotation_json(ast)
            return {
                "elements": json_result["elements"],
                "warnings": warnings,
                "output_path": None,
            }

        # Validate against actual image size if no explicit viewport.
        if viewport_bounds is None:
            iw, ih = image.size
            warnings.extend(validate_bounds(elements, iw, ih))

        image = _apply_elements_pillow(image, elements, warnings)

        # Derive output path next to source image.
        out_path = img_path.with_stem(img_path.stem + "_annotated")
        image.save(str(out_path))
        output_path = out_path

    else:
        # JSON overlay fallback (no Pillow or no image supplied).
        if not _PILLOW_AVAILABLE and image_path is not None:
            warnings.append(
                "Pillow is not installed — falling back to JSON overlay descriptor."
            )

    # Build the element list for the return value.
    json_elements = render_annotation_json(ast)["elements"]
    return {
        "elements": json_elements,
        "warnings": warnings,
        "output_path": output_path,
    }


def validate_bounds(
    elements: List[Dict[str, Any]],
    viewport_width: int,
    viewport_height: int,
) -> List[str]:
    """Validate element positions against a viewport.

    For each element that carries positional information the following
    checks are performed::

        x >= 0, y >= 0,
        x + width  <= viewport_width,
        y + height <= viewport_height

    Parameters
    ----------
    elements:
        List of element dicts; each may have ``x``, ``y``, ``width``,
        ``height`` integer fields.
    viewport_width:
        Viewport / image width in pixels.
    viewport_height:
        Viewport / image height in pixels.

    Returns
    -------
    list[str]
        Warning strings for every out-of-bounds element; empty when all
        elements are within the viewport.
    """
    warnings: List[str] = []
    for i, el in enumerate(elements):
        label = el.get("label") or el.get("name") or el.get("type") or f"element[{i}]"
        etype = el.get("type", "unknown")

        x = el.get("x")
        y = el.get("y")
        w = el.get("width")
        h = el.get("height")

        if x is None and y is None:
            continue  # Element has no positional data — skip.

        x = int(x or 0)
        y = int(y or 0)
        w = int(w or 0)
        h = int(h or 0)

        if x < 0:
            warnings.append(
                f"{etype} '{label}': x={x} is negative (out of bounds)."
            )
        if y < 0:
            warnings.append(
                f"{etype} '{label}': y={y} is negative (out of bounds)."
            )
        if x + w > viewport_width:
            warnings.append(
                f"{etype} '{label}': x+width={x + w} exceeds viewport width {viewport_width}."
            )
        if y + h > viewport_height:
            warnings.append(
                f"{etype} '{label}': y+height={y + h} exceeds viewport height {viewport_height}."
            )
    return warnings


def render_annotation_json(annotation_ast: Dict[str, Any]) -> Dict[str, Any]:
    """Convert an annotation AST to a JSON overlay descriptor.

    Each element is normalised to::

        {
            "type":    str,
            "x":       int,
            "y":       int,
            "width":   int,
            "height":  int,
            "label":   str,
            "color":   str,
            "opacity": float,
        }

    Parameters
    ----------
    annotation_ast:
        Annotation definition dict or dataclass.

    Returns
    -------
    dict
        ``{"target": str, "elements": list}``
    """
    if hasattr(annotation_ast, "__dict__"):
        ast = annotation_ast.__dict__
    else:
        ast = dict(annotation_ast)

    target = str(ast.get("target") or ast.get("name") or "")
    raw_elements = _extract_elements(ast)
    normalised = [_normalise_element(el) for el in raw_elements]
    return {"target": target, "elements": normalised}


# ---------------------------------------------------------------------------
# Pillow drawing helpers
# ---------------------------------------------------------------------------

def draw_rect(
    draw: "ImageDraw.ImageDraw",
    position: Dict[str, Any],
    color: str = "#FF0000",
    opacity: float = 1.0,
) -> None:
    """Draw a rectangle annotation on *draw*."""
    x, y, w, h = _pos_xywh(position)
    outline_color = _parse_color_opacity(color, opacity)
    draw.rectangle([x, y, x + w, y + h], outline=outline_color, width=2)


def draw_arrow(
    draw: "ImageDraw.ImageDraw",
    endpoints: Dict[str, Any],
    color: str = "#FF0000",
    width: int = 2,
) -> None:
    """Draw an arrow annotation on *draw*."""
    x1 = int(endpoints.get("x1") or endpoints.get("x", 0))
    y1 = int(endpoints.get("y1") or endpoints.get("y", 0))
    x2 = int(endpoints.get("x2", x1 + 50))
    y2 = int(endpoints.get("y2", y1))

    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    # Arrowhead.
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 10
    left = (
        x2 - arrow_len * math.cos(angle - math.pi / 6),
        y2 - arrow_len * math.sin(angle - math.pi / 6),
    )
    right = (
        x2 - arrow_len * math.cos(angle + math.pi / 6),
        y2 - arrow_len * math.sin(angle + math.pi / 6),
    )
    draw.polygon([(x2, y2), left, right], fill=color)


def draw_text(
    draw: "ImageDraw.ImageDraw",
    position: Dict[str, Any],
    label: str = "",
    color: str = "#FF0000",
    font_size: int = 14,
) -> None:
    """Draw a text annotation on *draw*."""
    x = int(position.get("x", 0))
    y = int(position.get("y", 0))
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()
    draw.text((x, y), label, fill=color, font=font)


def apply_blur(
    image: "Image.Image",
    position: Dict[str, Any],
    radius: int = 5,
) -> "Image.Image":
    """Apply Gaussian blur to a rectangular region of *image*."""
    x, y, w, h = _pos_xywh(position)
    iw, ih = image.size
    # Clamp to image bounds.
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(iw, x + w)
    y2 = min(ih, y + h)
    if x2 <= x1 or y2 <= y1:
        return image
    region = image.crop((x1, y1, x2, y2))
    blurred = region.filter(ImageFilter.GaussianBlur(radius=radius))
    result = image.copy()
    result.paste(blurred, (x1, y1))
    return result


def draw_highlight(
    draw: "ImageDraw.ImageDraw",
    position: Dict[str, Any],
    color: str = "#FFFF00",
    opacity: float = 0.4,
) -> None:
    """Draw a semi-transparent highlight rectangle on *draw*."""
    x, y, w, h = _pos_xywh(position)
    fill_color = _parse_color_opacity(color, opacity)
    draw.rectangle([x, y, x + w, y + h], fill=fill_color)


def draw_circle(
    draw: "ImageDraw.ImageDraw",
    position: Dict[str, Any],
    color: str = "#FF0000",
    opacity: float = 1.0,
) -> None:
    """Draw a circle annotation on *draw*.

    ``position`` may use ``cx``/``cy``/``radius`` (centre + radius) or
    fall back to ``x``/``y``/``width``/``height`` bounding box semantics.
    """
    if "cx" in position or "radius" in position:
        cx = int(position.get("cx", 0))
        cy = int(position.get("cy", 0))
        r = int(position.get("radius", 20))
        bbox = [cx - r, cy - r, cx + r, cy + r]
    else:
        x, y, w, h = _pos_xywh(position)
        bbox = [x, y, x + w, y + h]
    outline_color = _parse_color_opacity(color, opacity)
    draw.ellipse(bbox, outline=outline_color, width=2)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_elements(ast: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pull the element list out of a normalised AST dict."""
    raw = ast.get("elements", [])
    if not isinstance(raw, list):
        return []
    result = []
    for el in raw:
        if isinstance(el, dict):
            result.append(el)
        elif hasattr(el, "__dict__"):
            result.append(el.__dict__)
        elif isinstance(el, str):
            # Bare element name string from the parser (element_stmt).
            result.append({"type": "rect", "name": el, "label": el})
    return result


def _normalise_element(el: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise an element dict to the canonical JSON overlay format."""
    etype = str(el.get("type") or el.get("kind") or "rect")
    if etype not in SUPPORTED_TYPES:
        etype = "rect"

    label = str(el.get("label") or el.get("name") or "")
    color = str(el.get("color") or "#FF0000")
    opacity = float(el.get("opacity") if el.get("opacity") is not None else 1.0)

    # Position fields — support both cx/cy/radius and x/y/w/h.
    if "cx" in el or "radius" in el:
        cx = int(el.get("cx", 0))
        cy = int(el.get("cy", 0))
        r = int(el.get("radius", 20))
        x, y, w, h = cx - r, cy - r, r * 2, r * 2
    else:
        x = int(el.get("x") or 0)
        y = int(el.get("y") or 0)
        w = int(el.get("width") or el.get("w") or 0)
        h = int(el.get("height") or el.get("h") or 0)

    return {
        "type": etype,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "label": label,
        "color": color,
        "opacity": opacity,
    }


def _pos_xywh(position: Dict[str, Any]) -> Tuple[int, int, int, int]:
    """Extract (x, y, width, height) from a position dict."""
    x = int(position.get("x", 0))
    y = int(position.get("y", 0))
    w = int(position.get("width") or position.get("w") or 0)
    h = int(position.get("height") or position.get("h") or 0)
    return x, y, w, h


def _parse_color_opacity(color: str, opacity: float) -> Tuple[int, int, int, int]:
    """Convert a ``#RRGGBB`` hex color + opacity float to an RGBA tuple."""
    color = color.lstrip("#")
    if len(color) == 6:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
    else:
        r, g, b = 255, 0, 0
    a = max(0, min(255, int(opacity * 255)))
    return (r, g, b, a)


def _apply_elements_pillow(
    image: "Image.Image",
    elements: List[Dict[str, Any]],
    warnings: List[str],
) -> "Image.Image":
    """Apply all annotation elements to *image* using Pillow.

    Elements are processed in order (painter's algorithm).
    """
    # Work on a copy with an alpha channel.
    composite = image.copy()

    for el in elements:
        el = _normalise_element(el)
        etype = el["type"]
        position = {k: el[k] for k in ("x", "y", "width", "height")}
        color = el["color"]
        opacity = el["opacity"]
        label = el["label"]

        try:
            if etype == "blur":
                composite = apply_blur(composite, position)
            elif etype in ("rect", "segment"):
                overlay = Image.new("RGBA", composite.size, (0, 0, 0, 0))
                d = ImageDraw.Draw(overlay)
                draw_rect(d, position, color=color, opacity=opacity)
                composite = Image.alpha_composite(composite, overlay)
            elif etype == "highlight":
                overlay = Image.new("RGBA", composite.size, (0, 0, 0, 0))
                d = ImageDraw.Draw(overlay)
                draw_highlight(d, position, color=color, opacity=opacity)
                composite = Image.alpha_composite(composite, overlay)
            elif etype == "circle":
                overlay = Image.new("RGBA", composite.size, (0, 0, 0, 0))
                d = ImageDraw.Draw(overlay)
                draw_circle(d, position, color=color, opacity=opacity)
                composite = Image.alpha_composite(composite, overlay)
            elif etype == "arrow":
                # Arrow uses x/y as start; x+width/y+height as end.
                endpoints = {
                    "x1": el["x"],
                    "y1": el["y"],
                    "x2": el["x"] + el["width"],
                    "y2": el["y"] + el["height"],
                }
                overlay = Image.new("RGBA", composite.size, (0, 0, 0, 0))
                d = ImageDraw.Draw(overlay)
                draw_arrow(d, endpoints, color=color)
                composite = Image.alpha_composite(composite, overlay)
            elif etype == "text":
                overlay = Image.new("RGBA", composite.size, (0, 0, 0, 0))
                d = ImageDraw.Draw(overlay)
                draw_text(d, position, label=label, color=color)
                composite = Image.alpha_composite(composite, overlay)
            elif etype == "freehand":
                # Freehand: treat as a simple rectangle outline placeholder.
                overlay = Image.new("RGBA", composite.size, (0, 0, 0, 0))
                d = ImageDraw.Draw(overlay)
                draw_rect(d, position, color=color, opacity=opacity)
                composite = Image.alpha_composite(composite, overlay)
            # "blur" was already handled above; unknown types are skipped silently.
        except Exception as exc:  # noqa: BLE001 — don't crash on a single bad element
            warnings.append(f"Failed to render '{etype}' element '{label}': {exc}")

    return composite
