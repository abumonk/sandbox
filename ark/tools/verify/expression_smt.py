"""
expression_smt.py — Z3 primitive mapping for ARK Expressif primitives.

Provides PRIMITIVE_Z3: a combined dict of all known primitives with metadata:
  - "fn": callable (val, args) -> Z3 expr, or None for opaque
  - "opaque": bool — True means the primitive is modeled as an uninterpreted
    function (regex, temporal, file-io) and produces PASS_OPAQUE, not PASS.

This file is the single source of truth for which primitives the verifier
knows about and how they map to Z3. It merges NATIVE_PRIMITIVES (native Z3
arithmetic/string ops) and OPAQUE_PRIMITIVES (modeled as uninterpreted fns).
"""

from z3 import (
    If, Function, StringSort, RealSort, BoolSort, IntSort,
    Length,
)

from tools.verify.ark_verify import NATIVE_PRIMITIVES, OPAQUE_PRIMITIVES, apply_opaque

# ---------------------------------------------------------------------------
# PRIMITIVE_Z3
# ---------------------------------------------------------------------------
# Each entry has the shape:
#   {
#     "opaque": bool,
#     "fn": callable(val, args) -> Z3 expr | None,
#     "description": str,
#   }

def _make_opaque_fn(name: str):
    """Return a (val, args) -> Z3 expr closure for an opaque primitive."""
    def _fn(val, args):
        return apply_opaque(name, val, args)
    _fn.__name__ = f"opaque_{name.replace('-', '_')}"
    return _fn


PRIMITIVE_Z3: dict = {}

# Native primitives — opaque: False
_native_descriptions = {
    "abs":           "Absolute value: |val|",
    "add":           "Addition: val + arg",
    "sub":           "Subtraction: val - arg",
    "mul":           "Multiplication: val * arg",
    "div":           "Division: val / arg",
    "neg":           "Negation: -val",
    "ceil":          "Ceiling (approximated as identity in Z3 Real)",
    "floor":         "Floor (approximated as identity in Z3 Real)",
    "round-to":      "Round to N decimals (approximated as identity)",
    "pow":           "Power (approximated as identity; Z3 Real has no general pow)",
    "clamp-range":   "Clamp val to [lo, hi]",
    "identity-fn":   "Identity: returns val unchanged",
    "default-float": "Default float: returns val (null handling → identity in SMT)",
    "str-len":       "String length: Length(val) in Z3 string theory",
}
for _name, _fn in NATIVE_PRIMITIVES.items():
    PRIMITIVE_Z3[_name] = {
        "opaque": False,
        "fn": _fn,
        "description": _native_descriptions.get(_name, f"Native Z3 primitive: {_name}"),
    }

# Opaque primitives — opaque: True
_opaque_descriptions = {
    "str-lower":         "Lowercase string (uninterpreted; produces PASS_OPAQUE)",
    "str-upper":         "Uppercase string (uninterpreted; produces PASS_OPAQUE)",
    "str-trim":          "Trim whitespace (uninterpreted; produces PASS_OPAQUE)",
    "str-pad-right":     "Pad string on right (uninterpreted; produces PASS_OPAQUE)",
    "str-pad-left":      "Pad string on left (uninterpreted; produces PASS_OPAQUE)",
    "str-remove-chars":  "Remove characters (uninterpreted; produces PASS_OPAQUE)",
    "str-substring":     "Substring extraction (uninterpreted; produces PASS_OPAQUE)",
    "str-replace":       "String replace (uninterpreted; produces PASS_OPAQUE)",
    "str-starts-with":   "Starts-with check (uninterpreted; produces PASS_OPAQUE)",
    "str-ends-with":     "Ends-with check (uninterpreted; produces PASS_OPAQUE)",
    "str-contains":      "Contains check (uninterpreted; produces PASS_OPAQUE)",
    "str-matches":       "Regex match (uninterpreted; produces PASS_OPAQUE)",
    # Code graph primitives
    "graph-callers":     "All callers of a function (graph query; uninterpreted; PASS_OPAQUE)",
    "graph-call-chain":  "Transitive call chain from entry point (graph query; uninterpreted; PASS_OPAQUE)",
    "graph-dead-code":   "Unreferenced functions (graph query; uninterpreted; PASS_OPAQUE)",
    "graph-complex":     "Functions above complexity threshold (graph query; uninterpreted; PASS_OPAQUE)",
    "graph-subclasses":  "All subclasses of a class (graph query; uninterpreted; PASS_OPAQUE)",
    "graph-importers":   "Modules importing a given module (graph query; uninterpreted; PASS_OPAQUE)",
    "graph-module-deps": "Module dependency graph (graph query; uninterpreted; PASS_OPAQUE)",
    "graph-is-reachable": "Node reachability check (graph predicate; uninterpreted; PASS_OPAQUE)",
    "graph-has-cycles":  "Inheritance cycle check (graph predicate; uninterpreted; PASS_OPAQUE)",
    "graph-is-dead":     "Dead code check for a function (graph predicate; uninterpreted; PASS_OPAQUE)",
}
for _name in OPAQUE_PRIMITIVES:
    PRIMITIVE_Z3[_name] = {
        "opaque": True,
        "fn": _make_opaque_fn(_name),
        "description": _opaque_descriptions.get(_name, f"Opaque primitive: {_name}"),
    }


def is_opaque(primitive_name: str) -> bool:
    """Return True if the named primitive is opaque (produces PASS_OPAQUE)."""
    entry = PRIMITIVE_Z3.get(primitive_name)
    return entry is not None and entry["opaque"]
