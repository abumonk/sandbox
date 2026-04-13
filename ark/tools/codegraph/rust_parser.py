"""Rust source code parser using regex patterns.

Extracts structural elements (functions, structs, enums, impl blocks, methods,
use statements, and call edges) from Rust source files for the code knowledge graph.
"""
from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Top-level function: (pub )? (async )? fn name
_RE_FN = re.compile(
    r"^[ \t]*(pub\s+)?(async\s+)?fn\s+(\w+)",
    re.MULTILINE,
)

# Struct definition: (pub )? struct Name
_RE_STRUCT = re.compile(
    r"^[ \t]*(pub\s+)?struct\s+(\w+)",
    re.MULTILINE,
)

# Enum definition: (pub )? enum Name
_RE_ENUM = re.compile(
    r"^[ \t]*(pub\s+)?enum\s+(\w+)",
    re.MULTILINE,
)

# impl block header — two variants:
#   impl TraitName for TypeName
#   impl TypeName
_RE_IMPL_FOR = re.compile(
    r"^\s*impl(?:<[^>]*>)?\s+\w[\w:<>, ]*\s+for\s+(\w+)",
    re.MULTILINE,
)
_RE_IMPL_PLAIN = re.compile(
    r"^\s*impl(?:<[^>]*>)?\s+(\w+)",
    re.MULTILINE,
)

# use statement (single line)
_RE_USE = re.compile(
    r"^\s*use\s+([^;]+);",
    re.MULTILINE,
)

# A function-call-like token inside bodies: word(
_RE_CALL = re.compile(r"\b(\w+)\s*\(")

# Keywords that look like calls but aren't real function calls
_CALL_KEYWORDS = frozenset({
    "if", "while", "for", "match", "loop", "return",
    "assert", "assert_eq", "assert_ne", "panic", "vec",
    "Some", "Ok", "Err", "Box", "Arc", "Rc",
})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _line_number(source: str, pos: int) -> int:
    """Return 1-based line number for a byte offset in source."""
    return source.count("\n", 0, pos) + 1


def _find_block_end(source: str, brace_start: int) -> int:
    """Given the index of '{' find the matching '}', return its index + 1.

    Returns len(source) if the braces are unbalanced.
    """
    depth = 0
    i = brace_start
    in_string = False
    escape = False
    in_line_comment = False
    in_block_comment = False

    while i < len(source):
        ch = source[i]

        # Handle escape sequences inside strings
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if source[i:i+2] == "*/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if source[i:i+2] == "//":
            in_line_comment = True
            i += 2
            continue

        if source[i:i+2] == "/*":
            in_block_comment = True
            i += 2
            continue

        if ch == '"':
            in_string = True
            i += 1
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1

    return len(source)


def _extract_impl_blocks(source: str) -> list[tuple[str, int, int]]:
    """Return list of (struct_name, block_start, block_end) for impl blocks.

    block_start and block_end are character offsets into source.
    """
    blocks: list[tuple[str, int, int]] = []

    # Collect candidates from both patterns; tag them with struct name
    candidates: list[tuple[int, str]] = []  # (match_end_pos, struct_name)

    for m in _RE_IMPL_FOR.finditer(source):
        candidates.append((m.end(), m.group(1)))

    for m in _RE_IMPL_PLAIN.finditer(source):
        # Make sure this isn't also matched by the FOR pattern at same start
        struct_name = m.group(1)
        candidates.append((m.end(), struct_name))

    # Remove duplicates that resolve to the same position (from overlapping patterns)
    seen_pos: set[int] = set()
    unique: list[tuple[int, str]] = []
    for pos, name in sorted(candidates):
        if pos not in seen_pos:
            unique.append((pos, name))
            seen_pos.add(pos)

    for end_pos, struct_name in unique:
        # Find the '{' that starts this impl block
        brace_idx = source.find("{", end_pos)
        if brace_idx == -1:
            continue
        # Make sure there's no other impl/fn/struct declaration between end_pos and brace_idx
        block_end = _find_block_end(source, brace_idx)
        blocks.append((struct_name, brace_idx, block_end))

    return blocks


def _positions_inside_impls(impl_blocks: list[tuple[str, int, int]]) -> dict[int, str]:
    """Build a mapping from character offset to struct_name for all impl block regions.

    This is used to determine whether a matched function falls inside an impl.
    """
    # We store (start, end, struct_name) tuples
    return impl_blocks  # type: ignore[return-value]  # used directly


def _in_impl(pos: int, impl_blocks: list[tuple[str, int, int]]) -> str | None:
    """Return the struct_name if pos is inside any impl block, else None."""
    for struct_name, start, end in impl_blocks:
        if start < pos < end:
            return struct_name
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_rust_source(source: str, module_name: str) -> tuple[list[dict], list[dict]]:
    """Parse Rust source code and return (nodes, edges).

    Parameters
    ----------
    source:
        Raw Rust source text.
    module_name:
        The logical module name (used as prefix for fully-qualified names and
        as the ``module`` field in every node/edge).

    Returns
    -------
    nodes:
        List of dicts, each with keys ``name``, ``type``, ``module``, ``line``.
    edges:
        List of dicts, each with keys ``source``, ``target``, ``kind``,
        ``module``, ``line``.
    """
    nodes: list[dict] = []
    edges: list[dict] = []

    # ------------------------------------------------------------------ #
    # 1. Collect impl blocks so we can classify functions as methods       #
    # ------------------------------------------------------------------ #
    impl_blocks = _extract_impl_blocks(source)

    # ------------------------------------------------------------------ #
    # 2. Structs                                                           #
    # ------------------------------------------------------------------ #
    for m in _RE_STRUCT.finditer(source):
        name = m.group(2)
        fqn = f"{module_name}::{name}"
        line = _line_number(source, m.start())
        nodes.append({"name": fqn, "type": "class", "module": module_name, "line": line})

    # ------------------------------------------------------------------ #
    # 3. Enums                                                             #
    # ------------------------------------------------------------------ #
    for m in _RE_ENUM.finditer(source):
        name = m.group(2)
        fqn = f"{module_name}::{name}"
        line = _line_number(source, m.start())
        nodes.append({"name": fqn, "type": "class", "module": module_name, "line": line})

    # ------------------------------------------------------------------ #
    # 4. Functions and methods                                             #
    # ------------------------------------------------------------------ #
    fn_nodes: list[dict] = []

    for m in _RE_FN.finditer(source):
        fn_name = m.group(3)
        pos = m.start()
        line = _line_number(source, pos)

        struct_owner = _in_impl(pos, impl_blocks)
        if struct_owner:
            fqn = f"{module_name}::{struct_owner}::{fn_name}"
            node = {"name": fqn, "type": "method", "module": module_name, "line": line}
        else:
            fqn = f"{module_name}::{fn_name}"
            node = {"name": fqn, "type": "function", "module": module_name, "line": line}

        nodes.append(node)
        fn_nodes.append(node)

        # Determine the body of this function for call extraction
        brace_idx = source.find("{", m.end())
        if brace_idx != -1:
            body_end = _find_block_end(source, brace_idx)
            body = source[brace_idx:body_end]
            for call_m in _RE_CALL.finditer(body):
                callee = call_m.group(1)
                if callee in _CALL_KEYWORDS:
                    continue
                if callee == fn_name:
                    continue  # trivial self-recursion still allowed, but often noise
                call_line = line + body[:call_m.start()].count("\n")
                edges.append({
                    "source": fqn,
                    "target": callee,
                    "kind": "calls",
                    "module": module_name,
                    "line": call_line,
                })

    # ------------------------------------------------------------------ #
    # 5. Use statements → imports edges                                    #
    # ------------------------------------------------------------------ #
    for m in _RE_USE.finditer(source):
        path_raw = m.group(1).strip()
        line = _line_number(source, m.start())
        edges.append({
            "source": module_name,
            "target": path_raw,
            "kind": "imports",
            "module": module_name,
            "line": line,
        })

    return nodes, edges


def parse_rust_file(path: Path) -> tuple[list[dict], list[dict]]:
    """Parse a .rs file, return (nodes, edges).

    The module name is derived from the file stem (e.g. ``lib`` for ``lib.rs``).
    """
    source = path.read_text(encoding="utf-8", errors="replace")
    module_name = path.stem
    return parse_rust_source(source, module_name)
