"""HTML Previewer — renders preview items to self-contained HTML files.

Supports viewport configuration (mobile/tablet/desktop/custom),
static/interactive/responsive modes, and light/dark theme settings.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union


# ---------------------------------------------------------------------------
# Viewport size registry
# ---------------------------------------------------------------------------

VIEWPORT_SIZES: dict[str, tuple[int, int]] = {
    "mobile": (375, 667),
    "tablet": (768, 1024),
    "desktop": (1920, 1080),
    "custom": (800, 600),
}


def get_viewport_dimensions(viewport: str) -> tuple[int, int]:
    """Return (width, height) in pixels for a named viewport.

    Args:
        viewport: One of "mobile", "tablet", "desktop", or "custom".
                  Unknown values fall back to the "custom" dimensions.

    Returns:
        A (width, height) tuple.
    """
    return VIEWPORT_SIZES.get(viewport, VIEWPORT_SIZES["custom"])


# ---------------------------------------------------------------------------
# CSS theme helpers
# ---------------------------------------------------------------------------

_LIGHT_THEME_VARS = """
    --bg-color: #ffffff;
    --text-color: #1a1a1a;
    --link-color: #0066cc;
    --border-color: #e0e0e0;
    --accent-color: #005fcc;
    --surface-color: #f5f5f5;
"""

_DARK_THEME_VARS = """
    --bg-color: #1e1e1e;
    --text-color: #e8e8e8;
    --link-color: #5ea5ff;
    --border-color: #3a3a3a;
    --accent-color: #7cb9ff;
    --surface-color: #2a2a2a;
"""

_BASE_CSS = """
    *, *::before, *::after { box-sizing: border-box; }
    body {
        margin: 0;
        padding: 16px;
        background-color: var(--bg-color);
        color: var(--text-color);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI',
                     Roboto, Helvetica, Arial, sans-serif;
        font-size: 16px;
        line-height: 1.5;
    }
    a { color: var(--link-color); }
    img { max-width: 100%; height: auto; }
"""

_RESPONSIVE_CSS = """
    @media (max-width: 600px) {
        body { padding: 8px; font-size: 14px; }
    }
    @media (min-width: 601px) and (max-width: 1024px) {
        body { padding: 12px; }
    }
    @media (min-width: 1025px) {
        body { max-width: 1200px; margin: 0 auto; }
    }
"""

_INTERACTIVE_JS = """
(function () {
    'use strict';

    function handleClick(event) {
        var el = event.target;
        el.style.outline = '2px solid var(--accent-color)';
        setTimeout(function () { el.style.outline = ''; }, 600);
    }

    function handleMouseover(event) {
        var el = event.target;
        if (el !== document.body) {
            el.setAttribute('data-hovered', 'true');
        }
    }

    function handleMouseout(event) {
        event.target.removeAttribute('data-hovered');
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.body.addEventListener('click', handleClick);
        document.body.addEventListener('mouseover', handleMouseover);
        document.body.addEventListener('mouseout', handleMouseout);
    });
}());
"""


# ---------------------------------------------------------------------------
# HTML template generator
# ---------------------------------------------------------------------------

def generate_preview_html(
    source: str,
    viewport: str,
    mode: str,
    theme: str,
) -> str:
    """Build a self-contained HTML document for the given preview parameters.

    Args:
        source:   Raw HTML content to embed as the page body.
        viewport: Viewport name ("mobile", "tablet", "desktop", "custom").
        mode:     Rendering mode — "static", "interactive", or "responsive".
        theme:    Color theme — "light" or "dark".

    Returns:
        A complete, self-contained HTML string.
    """
    width, height = get_viewport_dimensions(viewport)

    # Choose CSS variable block
    theme_vars = _DARK_THEME_VARS if theme == "dark" else _LIGHT_THEME_VARS

    # Responsive extras
    responsive_css = _RESPONSIVE_CSS if mode == "responsive" else ""

    # Interactive JS block
    js_block = ""
    if mode == "interactive":
        js_block = f"<script>{_INTERACTIVE_JS}</script>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width={width}, initial-scale=1.0">
    <meta name="generator" content="ark-html-previewer">
    <title>Preview — {viewport} / {mode}</title>
    <style>
        :root {{{theme_vars}}}
        {_BASE_CSS}
        {responsive_css}
    </style>
</head>
<body>
{source}
</body>
{js_block}
</html>"""
    return html


# ---------------------------------------------------------------------------
# Public rendering entry point
# ---------------------------------------------------------------------------

def render_preview(
    preview_ast: dict,
    render_config: dict,
    out_dir: Union[str, Path],
) -> dict:
    """Render a parsed preview item to a self-contained HTML file.

    Args:
        preview_ast:   A dict (or PreviewDef-like object) containing at least:
                         - ``source`` (str): raw HTML content to embed.
                         - ``viewport`` (str | None): viewport name.
                         - ``mode`` (str | None): rendering mode.
                         - ``name`` (str | None): used to derive the filename.
        render_config: A dict with optional keys:
                         - ``theme`` (str): "light" (default) or "dark".
                         - ``output_name`` (str): override the output filename.
        out_dir:       Directory where the HTML file is written. Created if it
                       does not exist.

    Returns:
        A dict with keys:
            ``html_path`` (Path): absolute path to the written file.
            ``viewport``  (str):  effective viewport name used.
            ``mode``      (str):  effective rendering mode used.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Extract fields from preview_ast (dict or dataclass) ---
    def _get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    source: str = _get(preview_ast, "source") or ""
    viewport: str = _get(preview_ast, "viewport") or "desktop"
    mode: str = _get(preview_ast, "mode") or "static"
    name: str = _get(preview_ast, "name") or ""

    # Normalise mode/viewport to lower-case
    viewport = viewport.lower()
    mode = mode.lower()

    # Theme from render_config
    theme: str = (render_config.get("theme") or "light").lower()

    # Derive output filename
    if render_config.get("output_name"):
        filename = render_config["output_name"]
        if not filename.endswith(".html"):
            filename += ".html"
    elif name:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        filename = f"{safe_name}.html"
    else:
        # Fallback: hash of source content
        digest = hashlib.sha1(source.encode()).hexdigest()[:8]
        filename = f"preview_{digest}.html"

    html_content = generate_preview_html(source, viewport, mode, theme)

    html_path = out_dir / filename
    html_path.write_text(html_content, encoding="utf-8")

    return {
        "html_path": html_path,
        "viewport": viewport,
        "mode": mode,
    }
