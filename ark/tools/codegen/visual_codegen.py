"""
visual_codegen.py — Code generation for visual .ark artifacts.

Generates from visual .ark specs:
  - {name}.mmd                  — Mermaid markup file (from diagram items)
  - {name}.html                 — Self-contained HTML preview (from preview items)
  - {name}_overlay.json         — Annotation overlay JSON (from annotation items)
  - {name}_review.sh            — Review CLI command script (from visual_review items)
  - catalog_index.html          — Screenshot catalog HTML index (from screenshot items)
  - {name}_config.json          — Render configuration JSON (from render_config items)

Pipeline:  .ark → parse → ArkFile AST → visual_codegen → .mmd / .html / .json / .sh
"""

import json
import os
from pathlib import Path
from typing import Optional, Union


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(obj, key: str, default=None):
    """Get a field from either a dict or a dataclass instance."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default) or default


# ---------------------------------------------------------------------------
# gen_diagram_mmd
# ---------------------------------------------------------------------------

def gen_diagram_mmd(diagram) -> str:
    """
    Generate Mermaid markup from a diagram item.

    Supports diagram_type values: flowchart, sequence, class, state,
    er, gantt, pie, gitgraph (defaults to flowchart if unrecognized).

    Args:
        diagram: A diagram item dict or dataclass with fields:
            name, diagram_type (or type), content, nodes, edges,
            direction, description, title.

    Returns:
        A string containing the Mermaid .mmd source.
    """
    name = _get(diagram, "name", "diagram")
    diagram_type = (
        _get(diagram, "diagram_type")
        or _get(diagram, "type")
        or "flowchart"
    )
    content = _get(diagram, "content") or ""
    nodes = _get(diagram, "nodes") or []
    edges = _get(diagram, "edges") or []
    direction = _get(diagram, "direction") or "TD"
    description = _get(diagram, "description") or ""
    title = _get(diagram, "title") or name

    lines = []

    if description:
        lines.append(f"%% {description}")

    # If raw content is provided, use it directly
    if content.strip():
        lines.append(content.strip())
        return "\n".join(lines)

    # Otherwise generate from structured nodes/edges
    dtype = str(diagram_type).lower()

    if dtype in ("flowchart", "graph", "flow"):
        lines.append(f"flowchart {direction}")
        for node in nodes:
            node_id = _get(node, "id") or _get(node, "name", "node")
            node_label = _get(node, "label") or node_id
            node_shape = _get(node, "shape") or "rect"
            if node_shape in ("circle", "round"):
                lines.append(f"    {node_id}(({node_label}))")
            elif node_shape in ("diamond", "decision"):
                lines.append(f"    {node_id}{{{node_label}}}")
            else:
                lines.append(f"    {node_id}[{node_label}]")
        for edge in edges:
            from_id = _get(edge, "from") or _get(edge, "source", "a")
            to_id = _get(edge, "to") or _get(edge, "target", "b")
            label = _get(edge, "label") or ""
            edge_style = _get(edge, "style") or "arrow"
            if label:
                if edge_style == "dotted":
                    lines.append(f"    {from_id} -.->|{label}| {to_id}")
                else:
                    lines.append(f"    {from_id} -->|{label}| {to_id}")
            else:
                if edge_style == "dotted":
                    lines.append(f"    {from_id} -.-> {to_id}")
                else:
                    lines.append(f"    {from_id} --> {to_id}")

    elif dtype == "sequence":
        lines.append("sequenceDiagram")
        # nodes become participants
        for node in nodes:
            node_id = _get(node, "id") or _get(node, "name", "P")
            node_label = _get(node, "label") or node_id
            lines.append(f"    participant {node_id} as {node_label}")
        for edge in edges:
            from_id = _get(edge, "from") or _get(edge, "source", "A")
            to_id = _get(edge, "to") or _get(edge, "target", "B")
            label = _get(edge, "label") or ""
            lines.append(f"    {from_id}->>{to_id}: {label}")

    elif dtype in ("class", "classDiagram"):
        lines.append("classDiagram")
        for node in nodes:
            node_id = _get(node, "id") or _get(node, "name", "Class")
            fields = _get(node, "fields") or []
            methods = _get(node, "methods") or []
            lines.append(f"    class {node_id} {{")
            for f in fields:
                lines.append(f"        +{f}")
            for m in methods:
                lines.append(f"        +{m}()")
            lines.append("    }")
        for edge in edges:
            from_id = _get(edge, "from") or _get(edge, "source", "A")
            to_id = _get(edge, "to") or _get(edge, "target", "B")
            rel = _get(edge, "relation") or "-->"
            lines.append(f"    {from_id} {rel} {to_id}")

    elif dtype in ("state", "stateDiagram"):
        lines.append("stateDiagram-v2")
        for node in nodes:
            node_id = _get(node, "id") or _get(node, "name", "State")
            node_label = _get(node, "label") or node_id
            if node_id != node_label:
                lines.append(f"    {node_id} : {node_label}")
        for edge in edges:
            from_id = _get(edge, "from") or _get(edge, "source", "[*]")
            to_id = _get(edge, "to") or _get(edge, "target", "[*]")
            label = _get(edge, "label") or ""
            if label:
                lines.append(f"    {from_id} --> {to_id} : {label}")
            else:
                lines.append(f"    {from_id} --> {to_id}")

    else:
        # Generic fallback — emit as flowchart
        lines.append(f"flowchart {direction}")
        lines.append(f"    %% diagram_type: {diagram_type}")
        for node in nodes:
            node_id = _get(node, "id") or _get(node, "name", "node")
            node_label = _get(node, "label") or node_id
            lines.append(f"    {node_id}[{node_label}]")
        for edge in edges:
            from_id = _get(edge, "from") or _get(edge, "source", "a")
            to_id = _get(edge, "to") or _get(edge, "target", "b")
            lines.append(f"    {from_id} --> {to_id}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_preview_html
# ---------------------------------------------------------------------------

def gen_preview_html(preview, render_config=None) -> str:
    """
    Generate a self-contained HTML preview page from a preview item.

    Embeds Mermaid.js via CDN to render diagrams directly in the browser.
    Applies viewport dimensions and theme from render_config if provided.

    Args:
        preview: A preview item dict or dataclass with fields:
            name, title, content, diagram_ref, description,
            width, height, theme, background.
        render_config: Optional render config dict or dataclass with fields:
            viewport_width, viewport_height, theme, background_color.

    Returns:
        A string containing the full self-contained HTML document.
    """
    name = _get(preview, "name", "preview")
    title = _get(preview, "title") or name
    content = _get(preview, "content") or ""
    diagram_ref = _get(preview, "diagram_ref") or _get(preview, "diagram") or ""
    description = _get(preview, "description") or ""

    # Viewport and theme — prefer render_config values, fall back to preview
    viewport_width = None
    viewport_height = None
    theme = None
    background_color = None

    if render_config is not None:
        viewport_width = (
            _get(render_config, "viewport_width")
            or _get(render_config, "width")
        )
        viewport_height = (
            _get(render_config, "viewport_height")
            or _get(render_config, "height")
        )
        theme = _get(render_config, "theme")
        background_color = (
            _get(render_config, "background_color")
            or _get(render_config, "background")
        )

    # Fall back to preview-level settings
    viewport_width = viewport_width or _get(preview, "viewport_width") or _get(preview, "width") or 1280
    viewport_height = viewport_height or _get(preview, "viewport_height") or _get(preview, "height") or 720
    theme = theme or _get(preview, "theme") or "default"
    background_color = background_color or _get(preview, "background") or "#ffffff"

    # Normalise theme for Mermaid
    mermaid_theme = theme if theme in ("default", "dark", "forest", "neutral", "base") else "default"

    # Build body content
    body_sections = []

    if description:
        body_sections.append(f"        <p class=\"description\">{description}</p>")

    if diagram_ref:
        body_sections.append(
            f"        <div class=\"diagram-ref\"><em>Diagram ref: {diagram_ref}</em></div>"
        )

    if content.strip():
        # If content looks like Mermaid source, wrap it
        content_stripped = content.strip()
        mermaid_keywords = (
            "flowchart", "graph", "sequenceDiagram", "classDiagram",
            "stateDiagram", "erDiagram", "gantt", "pie", "gitGraph"
        )
        if any(content_stripped.startswith(kw) for kw in mermaid_keywords):
            body_sections.append(
                f"        <div class=\"mermaid\">\n{content_stripped}\n        </div>"
            )
        else:
            body_sections.append(f"        <div class=\"content\">{content}</div>")
    else:
        body_sections.append(
            "        <div class=\"mermaid\">\n"
            "            flowchart TD\n"
            f"                A[{name}] --> B[No content defined]\n"
            "        </div>"
        )

    body_html = "\n".join(body_sections)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background: {background_color};
            color: #1a1a2e;
            max-width: {viewport_width}px;
            min-height: {viewport_height}px;
            margin: 0 auto;
            padding: 24px;
        }}
        h1 {{
            font-size: 1.5rem;
            margin-bottom: 12px;
            color: #333;
        }}
        .description {{
            color: #555;
            margin-bottom: 16px;
            font-size: 0.95rem;
        }}
        .diagram-ref {{
            color: #888;
            margin-bottom: 12px;
            font-size: 0.85rem;
        }}
        .mermaid {{
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
        }}
        .content {{
            padding: 12px;
            white-space: pre-wrap;
            font-family: monospace;
            background: #f5f5f5;
            border-radius: 4px;
        }}
    </style>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: '{mermaid_theme}' }});
    </script>
</head>
<body>
    <h1>{title}</h1>
{body_html}
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# gen_annotation_json
# ---------------------------------------------------------------------------

def gen_annotation_json(annotation) -> str:
    """
    Generate annotation overlay JSON from an annotation item.

    The overlay format is a JSON object with metadata and a list of
    annotation entries, each with position, label, and style.

    Args:
        annotation: An annotation item dict or dataclass with fields:
            name, target_ref, annotations (list), description, version.

    Returns:
        A string containing the JSON overlay content.
    """
    name = _get(annotation, "name", "annotation")
    target_ref = _get(annotation, "target_ref") or _get(annotation, "target") or ""
    annotations = _get(annotation, "annotations") or []
    description = _get(annotation, "description") or ""
    version = _get(annotation, "version") or "1.0"

    # Normalise annotation entries
    entries = []
    for entry in annotations:
        if isinstance(entry, dict):
            normalized = {
                "id": entry.get("id") or entry.get("name") or f"ann_{len(entries)}",
                "x": entry.get("x") or entry.get("pos_x") or 0,
                "y": entry.get("y") or entry.get("pos_y") or 0,
                "label": entry.get("label") or entry.get("text") or "",
                "type": entry.get("type") or entry.get("style") or "note",
                "color": entry.get("color") or "#ffcc00",
            }
            if "width" in entry:
                normalized["width"] = entry["width"]
            if "height" in entry:
                normalized["height"] = entry["height"]
            entries.append(normalized)
        else:
            # String annotation — treat as a simple label at origin
            entries.append({
                "id": f"ann_{len(entries)}",
                "x": 0,
                "y": 0,
                "label": str(entry),
                "type": "note",
                "color": "#ffcc00",
            })

    overlay = {
        "name": name,
        "version": version,
        "target": target_ref,
        "description": description,
        "annotations": entries,
        "count": len(entries),
    }

    return json.dumps(overlay, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# gen_review_script
# ---------------------------------------------------------------------------

def gen_review_script(visual_review) -> str:
    """
    Generate a review CLI shell script from a visual_review item.

    Produces a shell script that runs `ark visual review` commands for
    each review target specified in the visual_review item.

    Args:
        visual_review: A visual_review item dict or dataclass with fields:
            name, targets (list), reviewer, description, options.

    Returns:
        A string containing the shell script content (#!/bin/sh).
    """
    name = _get(visual_review, "name", "review")
    targets = _get(visual_review, "targets") or []
    reviewer = _get(visual_review, "reviewer") or ""
    description = _get(visual_review, "description") or ""
    options = _get(visual_review, "options") or {}

    lines = ["#!/bin/sh", "# Generated visual review script — do not edit manually"]

    if description:
        lines.append(f"# {description}")

    lines.append(f"# Review: {name}")
    if reviewer:
        lines.append(f"# Reviewer: {reviewer}")

    lines.append("")

    # Build option flags
    option_flags = []
    if isinstance(options, dict):
        for key, val in options.items():
            if isinstance(val, bool):
                if val:
                    option_flags.append(f"--{key}")
            else:
                option_flags.append(f"--{key} {val}")

    flags_str = " ".join(option_flags)

    if targets:
        for target in targets:
            if isinstance(target, dict):
                target_name = target.get("name") or target.get("ref") or str(target)
                target_type = target.get("type") or "diagram"
                lines.append(f"echo 'Reviewing {target_name} ({target_type})...'")
                cmd = f"ark visual review {target_name}"
                if flags_str:
                    cmd += f" {flags_str}"
                lines.append(cmd)
                lines.append("")
            else:
                target_str = str(target)
                lines.append(f"echo 'Reviewing {target_str}...'")
                cmd = f"ark visual review {target_str}"
                if flags_str:
                    cmd += f" {flags_str}"
                lines.append(cmd)
                lines.append("")
    else:
        lines.append(f"echo 'No targets defined for review: {name}'")
        lines.append(f"ark visual review {name}")

    lines.append("echo 'Review complete.'")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# gen_catalog_index
# ---------------------------------------------------------------------------

def gen_catalog_index(screenshots) -> str:
    """
    Generate a static HTML catalog index from a list of screenshot items.

    Produces a grid-layout HTML page with thumbnails and metadata for
    each screenshot in the catalog.

    Args:
        screenshots: A list of screenshot item dicts or dataclasses with fields:
            name, path (or src), title, description, width, height, tags.

    Returns:
        A string containing the full HTML catalog page.
    """
    entries = []
    for shot in screenshots:
        entries.append({
            "name": _get(shot, "name", "screenshot"),
            "path": _get(shot, "path") or _get(shot, "src") or _get(shot, "file") or "",
            "title": _get(shot, "title") or _get(shot, "name", "Screenshot"),
            "description": _get(shot, "description") or "",
            "width": _get(shot, "width") or 320,
            "height": _get(shot, "height") or 200,
            "tags": _get(shot, "tags") or [],
        })

    count = len(entries)

    # Build thumbnail cards
    card_html_parts = []
    for entry in entries:
        tags_html = ""
        if entry["tags"]:
            tags_str = ", ".join(str(t) for t in entry["tags"])
            tags_html = f'<div class="tags">{tags_str}</div>'

        img_src = entry["path"] or "#"
        img_html = (
            f'<img src="{img_src}" alt="{entry["title"]}" '
            f'width="{entry["width"]}" height="{entry["height"]}" '
            f'onerror="this.style.background=\'#ccc\';this.src=\'\'"/>'
            if img_src != "#"
            else f'<div class="placeholder" style="width:{entry["width"]}px;height:{entry["height"]}px;">'
                 f'{entry["name"]}</div>'
        )

        desc_html = f'<p class="desc">{entry["description"]}</p>' if entry["description"] else ""

        card_html_parts.append(f"""    <div class="card">
        {img_html}
        <div class="card-body">
            <h3>{entry["title"]}</h3>
            {desc_html}
            {tags_html}
        </div>
    </div>""")

    cards_html = "\n".join(card_html_parts) if card_html_parts else "    <p>No screenshots in catalog.</p>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Screenshot Catalog</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #f0f2f5;
            color: #1a1a2e;
            padding: 24px;
        }}
        header {{
            margin-bottom: 24px;
        }}
        header h1 {{
            font-size: 1.8rem;
            margin-bottom: 4px;
        }}
        header p {{
            color: #666;
            font-size: 0.9rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: #fff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .card img, .card .placeholder {{
            display: block;
            width: 100%;
            object-fit: cover;
        }}
        .placeholder {{
            background: #dde;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #888;
            font-size: 0.85rem;
        }}
        .card-body {{
            padding: 12px 16px 16px;
        }}
        .card-body h3 {{
            font-size: 1rem;
            margin-bottom: 6px;
        }}
        .desc {{
            font-size: 0.85rem;
            color: #555;
            margin-bottom: 8px;
        }}
        .tags {{
            font-size: 0.75rem;
            color: #888;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Visual Screenshot Catalog</h1>
        <p>{count} screenshot(s) indexed</p>
    </header>
    <div class="grid">
{cards_html}
    </div>
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# gen_render_config_json
# ---------------------------------------------------------------------------

def gen_render_config_json(config) -> str:
    """
    Generate render configuration JSON from a render_config item.

    Produces a JSON object with rendering parameters: viewport, theme,
    background, quality settings, and any custom fields.

    Args:
        config: A render_config item dict or dataclass with fields:
            name, viewport_width, viewport_height, theme, background_color,
            quality, dpi, format, anti_aliasing, description.

    Returns:
        A string containing the JSON configuration content.
    """
    name = _get(config, "name", "render_config")
    description = _get(config, "description") or ""
    viewport_width = _get(config, "viewport_width") or _get(config, "width") or 1280
    viewport_height = _get(config, "viewport_height") or _get(config, "height") or 720
    theme = _get(config, "theme") or "default"
    background_color = _get(config, "background_color") or _get(config, "background") or "#ffffff"
    quality = _get(config, "quality") or "high"
    dpi = _get(config, "dpi") or 96
    fmt = _get(config, "format") or "png"
    anti_aliasing = _get(config, "anti_aliasing")
    if anti_aliasing is None:
        anti_aliasing = True

    output = {
        "name": name,
        "description": description,
        "viewport": {
            "width": viewport_width,
            "height": viewport_height,
        },
        "theme": theme,
        "background_color": background_color,
        "quality": quality,
        "dpi": dpi,
        "format": fmt,
        "anti_aliasing": anti_aliasing,
    }

    # Carry forward any extra fields not already captured
    skip = {
        "name", "description", "viewport_width", "viewport_height",
        "width", "height", "theme", "background_color", "background",
        "quality", "dpi", "format", "anti_aliasing", "kind",
    }
    if isinstance(config, dict):
        for key, val in config.items():
            if key not in skip:
                output[key] = val
    else:
        for attr in dir(config):
            if attr.startswith("_") or attr in skip:
                continue
            try:
                val = getattr(config, attr)
                if not callable(val):
                    output[attr] = val
            except Exception:
                pass

    return json.dumps(output, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# generate — main orchestrator
# ---------------------------------------------------------------------------

def generate(ark_file, out_dir=None) -> dict:
    """
    Generate all visual artifacts from a parsed ArkFile or JSON dict.

    Produces:
      - {name}.mmd                  for each diagram item
      - {name}.html                 for each preview item
      - {name}_overlay.json         for each annotation item
      - {name}_review.sh            for each visual_review item
      - catalog_index.html          if any screenshot items exist
      - {name}_config.json          for each render_config item

    Args:
        ark_file: A parsed ArkFile instance or JSON AST dict.
            When a dict, uses the "items" list with kind-tagged entries.
            When an ArkFile, uses the .items list or domain-specific dicts.
        out_dir: Optional path (str or Path). If provided, files are
            written to disk.

    Returns:
        dict mapping relative filename (str) → file content (str).
        Also includes "files" key (list of filenames) and "count" key (int).
    """
    artifacts = {}

    diagrams = []
    previews = []
    annotations = []
    visual_reviews = []
    screenshots = []
    render_configs = []

    # Collect render_configs first so we can pass to preview gen
    _render_config_map = {}

    if isinstance(ark_file, dict):
        # JSON AST path — iterate items list
        for item in ark_file.get("items", []):
            kind = str(item.get("kind", "")).lower()
            if kind in ("diagram",):
                diagrams.append(item)
            elif kind in ("preview", "visual_preview"):
                previews.append(item)
            elif kind in ("annotation", "visual_annotation"):
                annotations.append(item)
            elif kind in ("visual_review", "review"):
                visual_reviews.append(item)
            elif kind in ("screenshot", "visual_screenshot"):
                screenshots.append(item)
            elif kind in ("render_config", "renderconfig", "render_configuration"):
                render_configs.append(item)
                rc_name = item.get("name", "")
                if rc_name:
                    _render_config_map[rc_name] = item
    else:
        # ArkFile dataclass path — scan .items list
        for item in getattr(ark_file, "items", []):
            item_kind = type(item).__name__.lower()
            if "diagram" in item_kind:
                diagrams.append(item)
            elif "preview" in item_kind:
                previews.append(item)
            elif "annotation" in item_kind:
                annotations.append(item)
            elif "visualreview" in item_kind or "review" in item_kind:
                visual_reviews.append(item)
            elif "screenshot" in item_kind:
                screenshots.append(item)
            elif "renderconfig" in item_kind or "render_config" in item_kind:
                render_configs.append(item)
                rc_name = getattr(item, "name", "")
                if rc_name:
                    _render_config_map[rc_name] = item

        # Also try domain-specific dicts on the ArkFile object
        for d in getattr(ark_file, "diagrams", {}).values():
            if d not in diagrams:
                diagrams.append(d)
        for p in getattr(ark_file, "previews", {}).values():
            if p not in previews:
                previews.append(p)
        for a in getattr(ark_file, "annotations", {}).values():
            if a not in annotations:
                annotations.append(a)
        for vr in getattr(ark_file, "visual_reviews", {}).values():
            if vr not in visual_reviews:
                visual_reviews.append(vr)
        for sc in getattr(ark_file, "screenshots", {}).values():
            if sc not in screenshots:
                screenshots.append(sc)
        for rc in getattr(ark_file, "render_configs", {}).values():
            if rc not in render_configs:
                render_configs.append(rc)
                rc_name = getattr(rc, "name", "") if not isinstance(rc, dict) else rc.get("name", "")
                if rc_name:
                    _render_config_map[rc_name] = rc

    # Generate .mmd for each diagram
    for diagram in diagrams:
        d_name = _get(diagram, "name", "diagram")
        filename = f"{d_name}.mmd"
        artifacts[filename] = gen_diagram_mmd(diagram)

    # Generate .html for each preview (pass matching render_config if referenced)
    for preview in previews:
        p_name = _get(preview, "name", "preview")
        rc_ref = _get(preview, "render_config_ref") or _get(preview, "render_config") or ""
        rc = _render_config_map.get(rc_ref)
        filename = f"{p_name}.html"
        artifacts[filename] = gen_preview_html(preview, rc)

    # Generate annotation overlay JSON for each annotation
    for annotation in annotations:
        a_name = _get(annotation, "name", "annotation")
        filename = f"{a_name}_overlay.json"
        artifacts[filename] = gen_annotation_json(annotation)

    # Generate review scripts
    for vr in visual_reviews:
        vr_name = _get(vr, "name", "review")
        filename = f"{vr_name}_review.sh"
        artifacts[filename] = gen_review_script(vr)

    # Generate catalog index if screenshots exist
    if screenshots:
        artifacts["catalog_index.html"] = gen_catalog_index(screenshots)

    # Generate render config JSON for each render_config
    for rc in render_configs:
        rc_name = _get(rc, "name", "render_config")
        filename = f"{rc_name}_config.json"
        artifacts[filename] = gen_render_config_json(rc)

    # Write to disk if out_dir is provided
    if out_dir is not None:
        out = Path(out_dir)
        for rel_path, content in artifacts.items():
            full_path = out / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

    file_list = list(artifacts.keys())
    return {"files": file_list, "count": len(file_list), **artifacts}


# ---------------------------------------------------------------------------
# Inline smoke-test
# ---------------------------------------------------------------------------

def _smoke_test():
    """Quick self-test using mock dicts (no parser needed)."""

    # --- gen_diagram_mmd: raw content ---
    diagram_raw = {
        "kind": "diagram",
        "name": "arch_overview",
        "diagram_type": "flowchart",
        "content": "flowchart TD\n    A[Client] --> B[Server]\n    B --> C[Database]",
        "description": "Architecture overview",
    }
    mmd = gen_diagram_mmd(diagram_raw)
    assert "flowchart TD" in mmd, f"Missing flowchart in: {mmd}"
    assert "A[Client]" in mmd, f"Missing node in: {mmd}"
    print("gen_diagram_mmd (raw content): PASS")

    # --- gen_diagram_mmd: structured nodes/edges ---
    diagram_struct = {
        "kind": "diagram",
        "name": "flow",
        "diagram_type": "flowchart",
        "direction": "LR",
        "nodes": [
            {"id": "A", "label": "Start"},
            {"id": "B", "label": "Process", "shape": "diamond"},
            {"id": "C", "label": "End"},
        ],
        "edges": [
            {"from": "A", "to": "B", "label": "input"},
            {"from": "B", "to": "C"},
        ],
    }
    mmd2 = gen_diagram_mmd(diagram_struct)
    assert "flowchart LR" in mmd2, f"Missing direction in: {mmd2}"
    assert "A[Start]" in mmd2, f"Missing node A in: {mmd2}"
    assert "B{Process}" in mmd2, f"Missing diamond node in: {mmd2}"
    assert "-->|input|" in mmd2, f"Missing labeled edge in: {mmd2}"
    print("gen_diagram_mmd (structured): PASS")

    # --- gen_preview_html ---
    preview = {
        "kind": "preview",
        "name": "main_preview",
        "title": "Main Preview",
        "content": "flowchart TD\n    X --> Y",
        "description": "Test preview",
    }
    render_cfg = {
        "name": "default_rc",
        "viewport_width": 1920,
        "viewport_height": 1080,
        "theme": "dark",
        "background_color": "#1a1a2e",
    }
    html = gen_preview_html(preview, render_cfg)
    assert "<!DOCTYPE html>" in html, "Missing DOCTYPE"
    assert "Main Preview" in html, "Missing title"
    assert "max-width: 1920px" in html, "Missing viewport width"
    assert "background: #1a1a2e" in html, "Missing background"
    assert "mermaid" in html, "Missing mermaid"
    assert "theme: 'dark'" in html, "Missing theme"
    print("gen_preview_html: PASS")

    # --- gen_annotation_json ---
    annotation = {
        "kind": "annotation",
        "name": "perf_notes",
        "target_ref": "arch_overview",
        "description": "Performance annotations",
        "version": "1.0",
        "annotations": [
            {"id": "a1", "x": 100, "y": 200, "label": "Bottleneck here", "type": "warning", "color": "#ff0000"},
            {"id": "a2", "x": 300, "y": 100, "label": "Optimized path"},
        ],
    }
    ann_json = gen_annotation_json(annotation)
    obj = json.loads(ann_json)
    assert obj["name"] == "perf_notes", f"Wrong name: {obj['name']}"
    assert obj["target"] == "arch_overview", f"Wrong target: {obj['target']}"
    assert obj["count"] == 2, f"Wrong count: {obj['count']}"
    assert obj["annotations"][0]["label"] == "Bottleneck here"
    assert obj["annotations"][0]["color"] == "#ff0000"
    print("gen_annotation_json: PASS")

    # --- gen_review_script ---
    visual_review = {
        "kind": "visual_review",
        "name": "sprint_review",
        "description": "Sprint visual review",
        "reviewer": "QA Team",
        "targets": [
            {"name": "arch_overview", "type": "diagram"},
            {"name": "main_preview", "type": "preview"},
        ],
        "options": {"verbose": True, "output": "html"},
    }
    script = gen_review_script(visual_review)
    assert "#!/bin/sh" in script, "Missing shebang"
    assert "ark visual review arch_overview" in script, "Missing review command"
    assert "--verbose" in script, "Missing verbose flag"
    print("gen_review_script: PASS")

    # --- gen_catalog_index ---
    shots = [
        {"name": "shot1", "path": "screenshots/shot1.png", "title": "Shot 1",
         "description": "First screenshot", "width": 640, "height": 480, "tags": ["ui", "main"]},
        {"name": "shot2", "path": "screenshots/shot2.png", "title": "Shot 2"},
    ]
    catalog = gen_catalog_index(shots)
    assert "<!DOCTYPE html>" in catalog, "Missing DOCTYPE"
    assert "Shot 1" in catalog, "Missing Shot 1 title"
    assert "Shot 2" in catalog, "Missing Shot 2 title"
    assert "2 screenshot(s)" in catalog, "Missing count"
    assert "screenshots/shot1.png" in catalog, "Missing image src"
    assert "ui, main" in catalog, "Missing tags"
    print("gen_catalog_index: PASS")

    # --- gen_render_config_json ---
    rc = {
        "kind": "render_config",
        "name": "hd_config",
        "description": "HD render configuration",
        "viewport_width": 1920,
        "viewport_height": 1080,
        "theme": "dark",
        "background_color": "#000000",
        "quality": "ultra",
        "dpi": 144,
        "format": "png",
        "anti_aliasing": True,
    }
    rc_json = gen_render_config_json(rc)
    rc_obj = json.loads(rc_json)
    assert rc_obj["name"] == "hd_config", f"Wrong name: {rc_obj['name']}"
    assert rc_obj["viewport"]["width"] == 1920, f"Wrong width: {rc_obj['viewport']['width']}"
    assert rc_obj["viewport"]["height"] == 1080, f"Wrong height"
    assert rc_obj["theme"] == "dark", f"Wrong theme"
    assert rc_obj["quality"] == "ultra", f"Wrong quality"
    assert rc_obj["dpi"] == 144, f"Wrong dpi"
    assert rc_obj["anti_aliasing"] is True, "Missing anti_aliasing"
    print("gen_render_config_json: PASS")

    # --- generate (orchestrator) ---
    ast_json = {
        "items": [
            {
                "kind": "diagram",
                "name": "test_diagram",
                "diagram_type": "flowchart",
                "content": "flowchart TD\n    A --> B",
            },
            {
                "kind": "preview",
                "name": "test_preview",
                "title": "Test Preview",
                "content": "flowchart LR\n    X --> Y",
                "render_config_ref": "test_rc",
            },
            {
                "kind": "annotation",
                "name": "test_ann",
                "target_ref": "test_diagram",
                "annotations": [{"id": "x1", "x": 10, "y": 20, "label": "Note"}],
            },
            {
                "kind": "render_config",
                "name": "test_rc",
                "viewport_width": 800,
                "viewport_height": 600,
                "theme": "forest",
            },
        ]
    }
    result = generate(ast_json)
    assert "test_diagram.mmd" in result, f"Missing .mmd file. Keys: {list(result.keys())}"
    assert "test_preview.html" in result, f"Missing .html file. Keys: {list(result.keys())}"
    assert "test_ann_overlay.json" in result, f"Missing overlay.json. Keys: {list(result.keys())}"
    assert "test_rc_config.json" in result, f"Missing _config.json. Keys: {list(result.keys())}"
    assert result["count"] == 4, f"Wrong count: {result['count']}"
    assert len(result["files"]) == 4, f"Wrong files list: {result['files']}"

    # Validate render_config is applied to preview (theme: forest)
    preview_html = result["test_preview.html"]
    assert "theme: 'forest'" in preview_html, f"render_config theme not applied: {preview_html[:500]}"

    # Validate annotation json
    ann = json.loads(result["test_ann_overlay.json"])
    assert ann["annotations"][0]["label"] == "Note"

    print("generate (orchestrator): PASS")
    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    _smoke_test()
