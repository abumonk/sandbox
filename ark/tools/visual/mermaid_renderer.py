"""
Mermaid Renderer
Renders diagram items from the ARK AST to .mmd (Mermaid markup) files.
Optionally invokes the mmdc CLI to produce SVG/PNG output.

Pipeline:  DiagramDef (AST) → generate_mermaid_source() → .mmd file
           → mmdc (if available) → .svg / .png
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# ============================================================
# DIAGRAM TYPE PREFIXES
# ============================================================

# Maps diagram_type → Mermaid keyword prefix (with trailing newline)
DIAGRAM_PREFIXES: dict[str, str] = {
    "flowchart":      "flowchart TD\n",
    "sequence":       "sequenceDiagram\n",
    "architecture":   "graph LR\n",
    "class_diagram":  "classDiagram\n",
    "state":          "stateDiagram-v2\n",
    "er":             "erDiagram\n",
    "gantt":          "gantt\n",
}

# Known Mermaid opening keywords used for validation
MERMAID_KEYWORDS = [
    "graph",
    "flowchart",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "gantt",
]

# Supported render output formats
DEFAULT_FORMAT = "svg"


# ============================================================
# PUBLIC API
# ============================================================

def render_mermaid(diagram_ast: dict, render_config: dict, out_dir: Path) -> dict:
    """Render a diagram item to .mmd and optionally .svg/.png.

    Args:
        diagram_ast: Parsed diagram item from AST (DiagramDef serialized as dict,
                     or a DiagramDef dataclass instance with .diagram_type/.source/.name).
        render_config: Render configuration dict.
                       Supported keys:
                         "format"  — "svg" | "png" (default: "svg")
                         "theme"   — "default" | "dark" | "forest" | "neutral"
        out_dir: Directory where output files are written.

    Returns:
        {
            "mmd_path":    Path to the generated .mmd file (always present),
            "output_path": Path to SVG/PNG (or None if mmdc not available),
            "format":      The output format string ("svg" or "png"),
        }
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Extract fields from AST (supports both dict and dataclass) ---
    if isinstance(diagram_ast, dict):
        name = diagram_ast.get("name") or "diagram"
        diagram_type = diagram_ast.get("diagram_type") or "mermaid"
        source = diagram_ast.get("source") or ""
    else:
        name = getattr(diagram_ast, "name", None) or "diagram"
        diagram_type = getattr(diagram_ast, "diagram_type", None) or "mermaid"
        source = getattr(diagram_ast, "source", None) or ""

    fmt = render_config.get("format", DEFAULT_FORMAT).lower()
    theme = render_config.get("theme", "default")

    # --- Generate .mmd content ---
    mmd_content = generate_mermaid_source(diagram_type, source)

    # --- Write .mmd file ---
    safe_name = _safe_filename(name)
    mmd_path = out_dir / f"{safe_name}.mmd"
    mmd_path.write_text(mmd_content, encoding="utf-8")

    # --- Optionally invoke mmdc CLI ---
    output_path: Optional[Path] = None
    mmdc = shutil.which("mmdc")
    if mmdc:
        output_path = out_dir / f"{safe_name}.{fmt}"
        config_path: Optional[Path] = None
        try:
            # Build mmdc config JSON for theme
            mermaid_cfg = {"theme": theme}
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as cfg_file:
                json.dump(mermaid_cfg, cfg_file)
                config_path = Path(cfg_file.name)

            cmd = [
                mmdc,
                "--input", str(mmd_path),
                "--output", str(output_path),
                "--configFile", str(config_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                # mmdc failed — clear output_path so callers know it's unavailable
                output_path = None
        except Exception:
            output_path = None
        finally:
            if config_path and config_path.exists():
                try:
                    config_path.unlink()
                except OSError:
                    pass

    return {
        "mmd_path": mmd_path,
        "output_path": output_path,
        "format": fmt,
    }


def generate_mermaid_source(diagram_type: str, source: str) -> str:
    """Generate valid Mermaid markup from a diagram type and source content.

    For type "mermaid": source is returned as-is (already Mermaid markup).
    For all other recognised types: the appropriate keyword prefix is prepended
    unless the source already starts with that (or any) Mermaid keyword.

    Args:
        diagram_type: One of "mermaid", "flowchart", "sequence", "architecture",
                      "class_diagram", "state", "er", "gantt".
        source: Raw source text from the diagram item.

    Returns:
        Complete Mermaid source string ready to be written to a .mmd file.
    """
    source = source.strip() if source else ""

    if diagram_type == "mermaid":
        # Already Mermaid markup — return as-is
        return source

    prefix = DIAGRAM_PREFIXES.get(diagram_type)
    if prefix is None:
        # Unknown type: fall back to graph LR
        prefix = "graph LR\n"

    # Check if source already starts with a Mermaid keyword so we don't double-wrap
    if _starts_with_mermaid_keyword(source):
        return source

    if source:
        return prefix + source
    return prefix.rstrip("\n")


def validate_mermaid_syntax(mmd_content: str) -> list[str]:
    """Basic syntax validation of Mermaid markup.

    Checks:
    - File starts with a recognised Mermaid diagram keyword
    - Brackets and braces are balanced

    Args:
        mmd_content: The full text of a .mmd file.

    Returns:
        List of error strings. Empty list means no errors detected.
    """
    errors: list[str] = []
    content = mmd_content.strip()

    if not content:
        errors.append("Empty Mermaid content: no diagram keyword found")
        return errors

    # --- Check for recognised opening keyword ---
    if not _starts_with_mermaid_keyword(content):
        keyword_list = ", ".join(MERMAID_KEYWORDS)
        errors.append(
            f"Missing diagram type declaration. "
            f"Expected one of: {keyword_list}"
        )

    # --- Bracket / brace matching ---
    bracket_errors = _check_brackets(content)
    errors.extend(bracket_errors)

    return errors


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _safe_filename(name: str) -> str:
    """Convert an ARK item name to a safe filesystem filename."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


def _starts_with_mermaid_keyword(source: str) -> bool:
    """Return True if source begins with a known Mermaid diagram keyword."""
    first_line = source.split("\n", 1)[0].strip()
    for kw in MERMAID_KEYWORDS:
        if first_line.startswith(kw):
            return True
    return False


def _check_brackets(content: str) -> list[str]:
    """Check that brackets and braces are balanced. Returns list of error strings."""
    errors: list[str] = []
    stack: list[tuple[str, int]] = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    closing = set(pairs.values())

    in_string = False
    string_char = ""

    for line_no, line in enumerate(content.splitlines(), start=1):
        for col, ch in enumerate(line, start=1):
            # Minimal string detection (single/double quotes) to skip content
            if not in_string and ch in ('"', "'"):
                in_string = True
                string_char = ch
                continue
            if in_string:
                if ch == string_char:
                    in_string = False
                continue

            if ch in pairs:
                stack.append((ch, line_no))
            elif ch in closing:
                if not stack:
                    errors.append(
                        f"Line {line_no}, col {col}: unexpected closing '{ch}'"
                    )
                else:
                    open_ch, open_line = stack.pop()
                    expected = pairs[open_ch]
                    if ch != expected:
                        errors.append(
                            f"Line {line_no}, col {col}: mismatched bracket "
                            f"'{ch}' — opened with '{open_ch}' on line {open_line}"
                        )

    for open_ch, open_line in stack:
        errors.append(
            f"Line {open_line}: unclosed '{open_ch}'"
        )

    return errors
