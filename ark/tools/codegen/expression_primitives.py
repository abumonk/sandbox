"""
expression_primitives.py — Primitive operator → target-language mapping.

Each entry in EXPR_PRIMITIVES describes a primitive operator referenced in
``chain:`` bodies of stdlib expression / predicate declarations
(dsl/stdlib/expression.ark, dsl/stdlib/predicate.ark).

Entry shape
-----------
{
    "rust":  <Rust snippet>,   # Method call (.foo()) or binary op (+ {0}) or fn call
    "kind":  <"method"|"binary"|"fn"|"predicate">,
    "arity": <int>,            # Number of *extra* arguments (0 = unary/no-arg)
}

``arity`` counts only the *extra* arguments beyond the receiver / first operand.
  arity=0  → primitive takes no extra args (e.g. .abs(), .to_lowercase())
  arity=1  → one extra arg   (e.g. + {0},  .powf({0}))
  arity=2  → two extra args  (e.g. .clamp({0}, {1}))

Argument placeholders use Python str.format notation: {0}, {1}, …

Codegen task (design 05) consumes this map.
"""

EXPR_PRIMITIVES: dict = {
    # ------------------------------------------------------------------
    # Numeric — arity-0 (receiver-only)
    # ------------------------------------------------------------------
    "abs": {
        "rust": ".abs()",
        "kind": "method",
        "arity": 0,
    },
    "ceil": {
        "rust": ".ceil()",
        "kind": "method",
        "arity": 0,
    },
    "floor": {
        "rust": ".floor()",
        "kind": "method",
        "arity": 0,
    },
    "neg": {
        "rust": "-{self}",
        "kind": "unary",
        "arity": 0,
    },

    # ------------------------------------------------------------------
    # Numeric — arity-1 (one extra argument)
    # ------------------------------------------------------------------
    "add": {
        "rust": " + {0}",
        "kind": "binary",
        "arity": 1,
    },
    "sub": {
        "rust": " - {0}",
        "kind": "binary",
        "arity": 1,
    },
    "mul": {
        "rust": " * {0}",
        "kind": "binary",
        "arity": 1,
    },
    "div": {
        "rust": " / {0}",
        "kind": "binary",
        "arity": 1,
    },
    "pow": {
        "rust": ".powf({0})",
        "kind": "method",
        "arity": 1,
    },
    "round-to": {
        # round to N decimal digits: multiply, round, divide
        "rust": "{{ let _s = 10_f32.powi({0}); ({recv} * _s).round() / _s }}",
        "kind": "fn",
        "arity": 1,
    },

    # ------------------------------------------------------------------
    # Numeric — arity-2
    # ------------------------------------------------------------------
    "clamp-range": {
        "rust": ".clamp({0}, {1})",
        "kind": "method",
        "arity": 2,
    },

    # ------------------------------------------------------------------
    # Null-handling — arity-0
    # ------------------------------------------------------------------
    "null-to-zero": {
        "rust": ".unwrap_or(0.0)",
        "kind": "method",
        "arity": 0,
    },
    "neutral": {
        # Identity: returns the value unchanged.
        "rust": "",
        "kind": "identity",
        "arity": 0,
    },

    # ------------------------------------------------------------------
    # Null-handling — arity-1
    # ------------------------------------------------------------------
    "null-to-value": {
        "rust": ".unwrap_or({0})",
        "kind": "method",
        "arity": 1,
    },

    # ------------------------------------------------------------------
    # Text — arity-0
    # ------------------------------------------------------------------
    "str-lower": {
        "rust": ".to_lowercase()",
        "kind": "method",
        "arity": 0,
    },
    "str-upper": {
        "rust": ".to_uppercase()",
        "kind": "method",
        "arity": 0,
    },
    "str-trim": {
        "rust": ".trim()",
        "kind": "method",
        "arity": 0,
    },
    "str-len": {
        "rust": ".len() as i32",
        "kind": "method",
        "arity": 0,
    },
    "str-is-empty": {
        "rust": ".is_empty()",
        "kind": "predicate",
        "arity": 0,
    },

    # ------------------------------------------------------------------
    # Text — arity-1
    # ------------------------------------------------------------------
    "str-remove-chars": {
        "rust": ".replace(|c: char| {0}.contains(c), \"\")",
        "kind": "method",
        "arity": 1,
    },
    "str-starts-with": {
        "rust": ".starts_with({0})",
        "kind": "predicate",
        "arity": 1,
    },
    "str-ends-with": {
        "rust": ".ends_with({0})",
        "kind": "predicate",
        "arity": 1,
    },
    "str-contains": {
        "rust": ".contains({0})",
        "kind": "predicate",
        "arity": 1,
    },
    "str-matches": {
        # Requires the `regex` crate at call-site.
        "rust": "regex::Regex::new({0}).map_or(false, |re| re.is_match({recv}))",
        "kind": "fn",
        "arity": 1,
    },

    # ------------------------------------------------------------------
    # Text — arity-2
    # ------------------------------------------------------------------
    "str-pad-right": {
        "rust": "{{ let mut _s = {recv}.to_owned(); while _s.chars().count() < {0} as usize {{ _s.push_str({1}); }} _s }}",
        "kind": "fn",
        "arity": 2,
    },
    "str-pad-left": {
        "rust": "{{ let mut _s = {recv}.to_owned(); while _s.chars().count() < {0} as usize {{ _s = format!(\"{{}}{{}}\", {1}, _s); }} _s }}",
        "kind": "fn",
        "arity": 2,
    },
    "str-replace": {
        "rust": ".replace({0}, {1})",
        "kind": "method",
        "arity": 2,
    },

    # ------------------------------------------------------------------
    # Text — arity-2 (str-substring uses start + len)
    # ------------------------------------------------------------------
    "str-substring": {
        "rust": ".chars().skip({0} as usize).take({1} as usize).collect::<String>()",
        "kind": "method",
        "arity": 2,
    },

    # ------------------------------------------------------------------
    # Null / missing — predicate, arity-0
    # ------------------------------------------------------------------
    "is-null-float": {
        # Represented as f32::NAN in Rust — use is_nan().
        "rust": ".is_nan()",
        "kind": "predicate",
        "arity": 0,
    },

    # ------------------------------------------------------------------
    # Graph queries — opaque, arity varies
    # ------------------------------------------------------------------
    "graph-callers": {
        "rust": "graph.callers({0})",
        "kind": "fn",
        "arity": 1,
    },
    "graph-call-chain": {
        "rust": "graph.call_chain({0})",
        "kind": "fn",
        "arity": 1,
    },
    "graph-dead-code": {
        "rust": ".dead_code()",
        "kind": "method",
        "arity": 0,
    },
    "graph-complex": {
        "rust": ".complex_functions({0})",
        "kind": "method",
        "arity": 1,
    },
    "graph-subclasses": {
        "rust": ".subclasses({0})",
        "kind": "method",
        "arity": 1,
    },
    "graph-importers": {
        "rust": ".importers({0})",
        "kind": "method",
        "arity": 1,
    },
    "graph-module-deps": {
        "rust": ".module_deps({0})",
        "kind": "method",
        "arity": 1,
    },
    "graph-is-reachable": {
        "rust": ".is_reachable({0}, {1})",
        "kind": "predicate",
        "arity": 2,
    },
    "graph-has-cycles": {
        "rust": ".has_cycles()",
        "kind": "predicate",
        "arity": 0,
    },
    "graph-is-dead": {
        "rust": ".is_dead({0})",
        "kind": "predicate",
        "arity": 1,
    },
}
