//! evaluator.rs — Shape-grammar evaluator trait and Terminal type.
//!
//! Mirrors `shape_grammar/tools/evaluator.py`:
//!   - `Terminal` is a fully-resolved shape with its scope, symbol tag,
//!     and semantic label.
//!   - `Evaluator` walks an IR, dispatches ops, and returns all terminals.

use crate::scope::Scope;
use crate::semantic::SemanticLabel;

// ── Terminal ──────────────────────────────────────────────────────────────────

/// A fully-resolved, non-terminal-expanding shape produced by evaluation.
#[derive(Debug, Clone)]
pub struct Terminal {
    /// The scope (transform + attrs) at the point the terminal was produced.
    pub scope: Scope,
    /// Symbol tag (asset path, geometry type, or rule name that bottomed out).
    pub tag: String,
    /// Semantic label propagated to this terminal.
    pub label: SemanticLabel,
}

// ── Evaluator trait ───────────────────────────────────────────────────────────

/// Reference-evaluator interface.
///
/// `evaluate` walks the shape-grammar IR starting from its axiom, dispatches
/// operations through `ops.rs`, maintains a scope stack, and collects all
/// terminal shapes.  The `seed` parameter makes the evaluation deterministic.
pub trait Evaluator {
    /// Evaluate the grammar and return all terminal shapes.
    fn evaluate(&self, seed: u64) -> Vec<Terminal>;
}

// ── StubEvaluator — minimal concrete type to exercise the trait ───────────────

/// Stub evaluator that satisfies the trait but does no real work.
pub struct StubEvaluator;

impl Evaluator for StubEvaluator {
    fn evaluate(&self, seed: u64) -> Vec<Terminal> {
        unimplemented!("StubEvaluator::evaluate")
    }
}
