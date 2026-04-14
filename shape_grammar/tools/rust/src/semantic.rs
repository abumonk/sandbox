//! semantic.rs — Semantic label propagation stubs.
//!
//! Mirrors `shape_grammar/tools/semantic.py`.
//! `SemanticLabel` annotates every node in the derivation tree with a label,
//! a tag set, and an inheritance flag.  The `Semantic` trait expresses the
//! propagation interface (child inherits parent's label unless overridden).

// ── SemanticLabel ────────────────────────────────────────────────────────────

/// Annotation attached to every shape node in the derivation tree.
#[derive(Debug, Clone)]
pub struct SemanticLabel {
    /// Human-readable label name (e.g. "wall", "window", "load_bearing").
    pub name: String,
    /// Classifier tags (e.g. ["structural", "facade"]).
    pub tags: Vec<String>,
    /// When `true`, child nodes inherit this label unless they override it.
    pub inherits: bool,
}

impl SemanticLabel {
    /// Construct an unlabelled root sentinel.
    pub fn unlabelled() -> Self {
        SemanticLabel {
            name: String::from("__unlabelled__"),
            tags: Vec::new(),
            inherits: true,
        }
    }
}

impl Default for SemanticLabel {
    fn default() -> Self {
        Self::unlabelled()
    }
}

// ── Semantic trait ────────────────────────────────────────────────────────────

/// Label propagation interface.
pub trait Semantic {
    /// Propagate this label to a child context.
    ///
    /// If `override_label` is `Some`, use it; otherwise inherit `self`.
    fn propagate(&self, override_label: Option<SemanticLabel>) -> SemanticLabel;

    /// Return `true` if this label should be inherited by child nodes.
    fn is_inheritable(&self) -> bool;
}

// ── DefaultSemantic — stub implementation ─────────────────────────────────────

/// Stub implementation of `Semantic` on `SemanticLabel`.
impl Semantic for SemanticLabel {
    fn propagate(&self, override_label: Option<SemanticLabel>) -> SemanticLabel {
        unimplemented!("SemanticLabel::propagate")
    }

    fn is_inheritable(&self) -> bool {
        unimplemented!("SemanticLabel::is_inheritable")
    }
}
