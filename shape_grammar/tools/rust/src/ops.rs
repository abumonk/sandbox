//! ops.rs — Shape-grammar operation primitives trait and stubs.
//!
//! Mirrors `shape_grammar/tools/ops.py`.
//! Each op takes the current `Scope` and a seed, and returns zero or more
//! (child_scope, child_symbol, semantic_label) triples.

use crate::scope::Scope;
use crate::semantic::SemanticLabel;

// ── ScopedShape ───────────────────────────────────────────────────────────────

/// One item produced by an op: the child scope, the symbol (rule name or
/// terminal asset path), and the semantic label to carry forward.
#[derive(Debug, Clone)]
pub struct ScopedShape {
    pub scope: Scope,
    pub symbol: String,
    pub label: SemanticLabel,
}

// ── Op trait ──────────────────────────────────────────────────────────────────

/// An operation primitive in the shape grammar.
///
/// `apply` evaluates the op against `scope` using the deterministic `seed`
/// and returns the list of child work items to enqueue.
pub trait Op {
    fn apply(&self, scope: &Scope, seed: u64, label: &str) -> Vec<ScopedShape>;
}

// ── Concrete op stubs ─────────────────────────────────────────────────────────

/// Extrude op: extends geometry along the scope's normal axis.
pub struct ExtrudeOp {
    pub amount: f64,
}

impl Op for ExtrudeOp {
    fn apply(&self, scope: &Scope, seed: u64, label: &str) -> Vec<ScopedShape> {
        unimplemented!("ExtrudeOp::apply")
    }
}

/// Split op: partitions geometry along a chosen axis into labelled sub-scopes.
pub struct SplitOp {
    pub axis: u8,
    pub ratios: Vec<f64>,
    pub symbols: Vec<String>,
}

impl Op for SplitOp {
    fn apply(&self, scope: &Scope, seed: u64, label: &str) -> Vec<ScopedShape> {
        unimplemented!("SplitOp::apply")
    }
}

/// Component op: selects a face/edge/vertex component of the current scope.
pub struct CompOp {
    pub selector: String,
    pub symbol: String,
}

impl Op for CompOp {
    fn apply(&self, scope: &Scope, seed: u64, label: &str) -> Vec<ScopedShape> {
        unimplemented!("CompOp::apply")
    }
}

/// Scope override op: replaces transform fields without changing the symbol.
pub struct ScopeOp {
    pub translation: Option<[f64; 3]>,
    pub rotation: Option<[f64; 3]>,
    pub scale: Option<[f64; 3]>,
    pub size: Option<[f64; 3]>,
}

impl Op for ScopeOp {
    fn apply(&self, scope: &Scope, seed: u64, label: &str) -> Vec<ScopedShape> {
        unimplemented!("ScopeOp::apply")
    }
}

/// Terminal instance op: marks the current scope as a terminal shape.
pub struct IOp {
    pub asset: String,
}

impl Op for IOp {
    fn apply(&self, scope: &Scope, seed: u64, label: &str) -> Vec<ScopedShape> {
        unimplemented!("IOp::apply")
    }
}

/// Translation op: applies an absolute or relative translation to the scope.
pub struct TOp {
    pub delta: [f64; 3],
}

impl Op for TOp {
    fn apply(&self, scope: &Scope, seed: u64, label: &str) -> Vec<ScopedShape> {
        unimplemented!("TOp::apply")
    }
}

/// Rotation op: applies a rotation (degrees) to the scope.
pub struct ROp {
    pub angles: [f64; 3],
}

impl Op for ROp {
    fn apply(&self, scope: &Scope, seed: u64, label: &str) -> Vec<ScopedShape> {
        unimplemented!("ROp::apply")
    }
}

/// Scale op: applies a scale factor to the scope.
pub struct SOp {
    pub factors: [f64; 3],
}

impl Op for SOp {
    fn apply(&self, scope: &Scope, seed: u64, label: &str) -> Vec<ScopedShape> {
        unimplemented!("SOp::apply")
    }
}
