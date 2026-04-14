"""ir.py — Extract a shape-grammar IR from an Ark-parsed AST.

Consumes `.ark` island source files that declare shape-grammar entities
using **vanilla Ark syntax** (see `shape_grammar/specs/shape_grammar.ark`).
Produces a `ShapeGrammarIR` dataclass that is the canonical input for every
downstream shape_grammar consumer (evaluator, verifier passes, adapters).

Two parse modes:
  1. **Library import (preferred)**: imports `ark_parser.parse` after
     prepending `ark/tools/parser/` to `sys.path`. Returns a fully resolved
     `ArkFile` dataclass, then serialized to JSON via `to_json`.
  2. **Subprocess fallback**: runs `python ark/ark.py parse <file>` and
     captures stdout. Used when the library path fails (import error,
     different Ark layout, CI sandbox restrictions).

Error paths follow `schemas/processes.md` § IR extraction:
  - AST missing `ShapeGrammar` island -> IRError("no ShapeGrammar island found")
  - Rule missing `operations` field   -> IRError("rule {id} has no operations")
  - max_depth not a positive Int      -> IRError("max_depth must be positive Int")

CLI:
  python -m shape_grammar.tools.ir <file.ark>
      -> prints a populated IR JSON to stdout.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

# --------------------------------------------------------------------
# Locate the Ark repo root (a sibling of shape_grammar/) so we can
# reach ark/tools/parser/ and ark/ark.py without hard-coding paths.
# --------------------------------------------------------------------

_PKG_ROOT = Path(__file__).resolve().parent.parent.parent   # R:/Sandbox/
ARK_ROOT = _PKG_ROOT / "ark"
ARK_PARSER_DIR = ARK_ROOT / "tools" / "parser"
ARK_CLI = ARK_ROOT / "ark.py"


# --------------------------------------------------------------------
# Error + dataclasses
# --------------------------------------------------------------------


class IRError(RuntimeError):
    """Raised when the shape-grammar IR cannot be extracted from the AST."""


@dataclass
class IRRange:
    """Captured [min..max] range constraint from Ark's `Int [a .. b]` syntax."""

    min: Optional[float] = None
    max: Optional[float] = None


@dataclass
class IRField:
    """One $data field on an entity (class/abstraction/island)."""

    name: str
    type: str
    default: Any = None
    range: Optional[IRRange] = None
    enum_values: list[str] = field(default_factory=list)


@dataclass
class IRInvariant:
    """An `invariant: expr` statement captured verbatim from the AST."""

    expr: dict[str, Any]


@dataclass
class IREntity:
    """A generic shape-grammar entity lifted from an Ark AST node."""

    name: str
    kind: str                                    # "abstraction" | "class" | "island"
    fields: list[IRField] = field(default_factory=list)
    invariants: list[IRInvariant] = field(default_factory=list)
    parent: Optional[str] = None                 # for `class X : Y`
    contains: list[str] = field(default_factory=list)   # for island { contains: [T] }


@dataclass
class IRRule:
    """A grammar rule lifted from an instance grammar (future: T15 examples).

    Placeholder shape — populated once example grammars exist. The base
    spec file only declares `class Rule` structurally; concrete Rule
    instances with id/lhs/ops lists come from the example grammars.
    """

    id: str
    lhs: str
    is_terminal: bool = False
    operations: list[str] = field(default_factory=list)
    label: Optional[str] = None


@dataclass
class IRSemanticLabel:
    """One `class SemanticLabel` instance (name + tags + inherits flag)."""

    name: str
    tags: list[str] = field(default_factory=list)
    inherits: bool = True


@dataclass
class ShapeGrammarIR:
    """Canonical shape-grammar intermediate representation.

    Produced by `extract_ir`. Every downstream consumer (evaluator,
    verifier passes, adapters) reads from this shape and nothing else.
    """

    source_file: str
    entities: list[IREntity] = field(default_factory=list)
    island_name: Optional[str] = None
    max_depth: Any = None                        # int | IRRange | None
    seed: Any = None                             # int | IRRange | None
    axiom: Optional[str] = None
    rules: list[IRRule] = field(default_factory=list)
    semantic_labels: list[IRSemanticLabel] = field(default_factory=list)
    provenance: dict[str, str] = field(default_factory=dict)


# --------------------------------------------------------------------
# Parsing — library-first, subprocess fallback
# --------------------------------------------------------------------


def _parse_via_library(source: str, file_path: Path) -> dict:
    """Parse using `ark_parser.parse` + `to_json`. Returns AST JSON dict."""
    if str(ARK_PARSER_DIR) not in sys.path:
        sys.path.insert(0, str(ARK_PARSER_DIR))
    try:
        from ark_parser import parse, to_json  # type: ignore
    except ImportError as exc:                   # pragma: no cover
        raise IRError(f"library import failed: {exc}")
    try:
        ark_file = parse(source, file_path=str(file_path))
    except Exception as exc:
        raise IRError(f"parse error: {exc}")
    return json.loads(to_json(ark_file))


def _parse_via_subprocess(file_path: Path) -> dict:
    """Parse using the `ark.py parse` CLI. Returns AST JSON dict."""
    if not ARK_CLI.exists():
        raise IRError(f"ark CLI not found at {ARK_CLI}")
    result = subprocess.run(
        [sys.executable, str(ARK_CLI), "parse", str(file_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise IRError(
            f"ark parse exit={result.returncode}; stderr: {result.stderr[:500]}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IRError(f"ark parse stdout is not valid JSON: {exc}")


def parse_ark(file_path: str | Path) -> dict:
    """Parse an .ark file; library path first, subprocess fallback."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise IRError(f"file not found: {file_path}")
    source = file_path.read_text(encoding="utf-8")
    try:
        return _parse_via_library(source, file_path)
    except IRError:
        return _parse_via_subprocess(file_path)


# --------------------------------------------------------------------
# AST traversal -> IR
# --------------------------------------------------------------------


def _find_entities(ast: dict) -> list[dict]:
    """Return the list of top-level entity dicts (class/abstraction/island).

    Ark's ArkFile serializes as:
      {"kind": "ark_file", "entities": [...], ...}
    where each entity dict carries a `kind` discriminator. Exact shape
    depends on Ark's to_json output; the field walker below is resilient
    to either a flat `entities` list or nested `items`.
    """
    if isinstance(ast, dict):
        if "entities" in ast and isinstance(ast["entities"], list):
            return ast["entities"]
        if "items" in ast and isinstance(ast["items"], list):
            return [it for it in ast["items"] if isinstance(it, dict)]
    return []


def _ark_literal(node: Any) -> Any:
    """Unwrap an Ark AST literal node {"expr": "number"|"string"|"bool", "value": X}."""
    if isinstance(node, dict) and "expr" in node and "value" in node:
        return node.get("value")
    return node


def _extract_range(field_dict: Any) -> Optional[IRRange]:
    """Extract [min..max] from a data-field's sibling `constraint` key."""
    if not isinstance(field_dict, dict):
        return None
    ct = field_dict.get("constraint")
    if isinstance(ct, dict) and ct.get("constraint") == "range":
        return IRRange(min=_ark_literal(ct.get("min")), max=_ark_literal(ct.get("max")))
    return None


def _extract_enum(field_dict: Any) -> list[str]:
    """Extract inline-enum values from a data-field's sibling `constraint` key."""
    if not isinstance(field_dict, dict):
        return []
    ct = field_dict.get("constraint")
    if isinstance(ct, dict) and ct.get("constraint") == "enum":
        vals = ct.get("values") or ct.get("members") or []
        return [str(_ark_literal(v)) for v in vals]
    return []


def _extract_type_str(type_node: Any) -> str:
    """Render an Ark type AST node as a human-readable string."""
    if isinstance(type_node, dict):
        if type_node.get("type") == "named":
            return str(type_node.get("name", "?"))
        if type_node.get("type") == "array":
            inner = type_node.get("element") or type_node.get("inner") or {}
            return f"[{_extract_type_str(inner)}]"
        if "name" in type_node:
            return str(type_node["name"])
    return str(type_node) if type_node is not None else "?"


def _extract_fields(entity: dict) -> list[IRField]:
    """Extract `$data` fields from an entity dict."""
    out: list[IRField] = []
    for candidate in entity.get("data_fields", []) or entity.get("fields", []) or []:
        if not isinstance(candidate, dict):
            continue
        out.append(
            IRField(
                name=candidate.get("name", "?"),
                type=_extract_type_str(candidate.get("type")),
                default=_ark_literal(candidate.get("default")),
                range=_extract_range(candidate),
                enum_values=_extract_enum(candidate),
            )
        )
    return out


def _extract_invariants(entity: dict) -> list[IRInvariant]:
    """Extract `invariant:` expressions from an entity dict."""
    out: list[IRInvariant] = []
    for inv in entity.get("invariants", []) or []:
        if isinstance(inv, dict):
            out.append(IRInvariant(expr=inv))
        else:
            out.append(IRInvariant(expr={"raw": str(inv)}))
    return out


def _entity_kind(raw: dict) -> Optional[str]:
    """Normalise an entity's kind string to one of class/abstraction/island."""
    k = raw.get("kind") or raw.get("entity_kind") or ""
    k = k.lower()
    if "abstract" in k:
        return "abstraction"
    if "island" in k:
        return "island"
    if "class" in k:
        return "class"
    return None


def _extract_entity(raw: dict) -> Optional[IREntity]:
    """Lift a raw Ark-AST entity dict into an IREntity."""
    kind = _entity_kind(raw)
    if kind is None:
        return None
    name = raw.get("name")
    if not name:
        return None
    # Ark uses `inherits` for `class X : Y` supertype reference.
    parent = raw.get("parent") or raw.get("supertype") or raw.get("inherits")
    if isinstance(parent, list):
        parent = parent[0] if parent else None
    contains_raw = raw.get("contains") or []
    contains: list[str] = []
    for c in contains_raw:
        if isinstance(c, str):
            contains.append(c)
        elif isinstance(c, dict):
            contains.append(c.get("name") or c.get("type") or str(c))
    return IREntity(
        name=name,
        kind=kind,
        fields=_extract_fields(raw),
        invariants=_extract_invariants(raw),
        parent=parent,
        contains=contains,
    )


def _find_island(entities: list[IREntity]) -> Optional[IREntity]:
    """Locate the first `island` entity. None if no island is present."""
    for e in entities:
        if e.kind == "island":
            return e
    return None


def _island_scalar(entity: IREntity, field_name: str) -> Any:
    """Return a concrete default value for a named field if the spec sets one;
    otherwise return the captured range (Int [a..b]), or None."""
    for f in entity.fields:
        if f.name == field_name:
            if f.default is not None:
                return f.default
            if f.range is not None:
                return asdict(f.range)
            return None
    return None


# --------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------


def extract_ir(file_path: str | Path) -> ShapeGrammarIR:
    """Parse an .ark file and return a populated ShapeGrammarIR.

    Raises IRError on any AST shape it cannot interpret.
    """
    file_path = Path(file_path)
    ast = parse_ark(file_path)
    raw_entities = _find_entities(ast)
    entities = [e for e in (_extract_entity(r) for r in raw_entities) if e is not None]

    ir = ShapeGrammarIR(source_file=str(file_path), entities=entities)

    island = _find_island(entities)
    if island is None:
        # Not fatal when parsing operation/semantic sub-specs that do not
        # contain an island; only fatal if the caller asks for full grammar
        # instance extraction. Here we just return entities and let the caller
        # decide. The documented error path is triggered by require_island=True.
        return ir

    ir.island_name = island.name
    ir.max_depth = _island_scalar(island, "max_depth")
    ir.seed = _island_scalar(island, "seed")
    ir.axiom = _island_scalar(island, "axiom")

    # Instance rules / semantic labels live in example grammars (T15).
    # The structural class declarations are visible in `entities` above.

    return ir


def require_populated(ir: ShapeGrammarIR) -> ShapeGrammarIR:
    """Raise IRError if the IR is empty (no entities found at all)."""
    if not ir.entities:
        raise IRError("no ShapeGrammar island found")
    # Structural sanity: if an island is present, its max_depth must describe
    # a positive Int (either a concrete int > 0, or a range with min > 0).
    if ir.island_name is not None and ir.max_depth is not None:
        md = ir.max_depth
        if isinstance(md, int) and md <= 0:
            raise IRError("max_depth must be positive Int")
        if isinstance(md, dict):
            lo = md.get("min")
            if isinstance(lo, (int, float)) and lo <= 0:
                raise IRError("max_depth must be positive Int")
    return ir


def require_island(ir: ShapeGrammarIR) -> ShapeGrammarIR:
    """Raise IRError if the extracted IR contains no `island` entity.

    Matches the documented error path in schemas/processes.md § IR extraction:
    "AST missing ShapeGrammar island -> IRError(\"no ShapeGrammar island found\")".
    """
    if ir.island_name is None:
        raise IRError("no ShapeGrammar island found")
    return ir


def validate_rules(ir: ShapeGrammarIR) -> ShapeGrammarIR:
    """Raise IRError if any extracted Rule has no operations attached.

    Matches the documented error path in schemas/processes.md § IR extraction:
    "Rule missing operations field -> IRError(\"rule {id} has no operations\")".

    Operates on `ir.rules` (instance-level rules populated from example
    grammars in T15). Rule-class structural declarations in the base spec
    are not checked — they are type definitions, not grammar instances.
    """
    for rule in ir.rules:
        if not rule.operations:
            raise IRError(f"rule {rule.id} has no operations")
    return ir


def to_json_dict(ir: ShapeGrammarIR) -> dict:
    """Serialize the IR into a plain JSON-ready dict."""
    return asdict(ir)


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------


def _cli_main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m shape_grammar.tools.ir <file.ark>", file=sys.stderr)
        return 2
    try:
        ir = require_populated(extract_ir(argv[1]))
    except IRError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(to_json_dict(ir), indent=2, default=str))
    return 0


if __name__ == "__main__":                       # pragma: no cover
    sys.exit(_cli_main(sys.argv))
