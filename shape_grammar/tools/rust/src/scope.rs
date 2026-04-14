//! scope.rs — Scope struct and ScopeStack trait.
//!
//! Mirrors `shape_grammar/tools/scope.py`:
//!   - `Scope` carries transform state (translation, rotation, scale, size)
//!     plus a string attribute bag inherited down the derivation tree.
//!   - `ScopeStack` is a LIFO stack supporting push/pop/top/get.

use crate::Vec3;
use std::collections::HashMap;

// ── Scope ────────────────────────────────────────────────────────────────────

/// Transform + attribute bundle for one level of the derivation tree.
#[derive(Debug, Clone)]
pub struct Scope {
    pub translation: Vec3,
    pub rotation: Vec3,
    pub scale: Vec3,
    pub size: Vec3,
    pub attrs: HashMap<String, String>,
}

impl Scope {
    /// Construct the canonical identity scope.
    pub fn identity() -> Self {
        Scope {
            translation: [0.0, 0.0, 0.0],
            rotation: [0.0, 0.0, 0.0],
            scale: [1.0, 1.0, 1.0],
            size: [0.0, 0.0, 0.0],
            attrs: HashMap::new(),
        }
    }

    /// Return a new Scope with `override_attrs` layered on top of this scope's attrs.
    pub fn push_attrs(&self, override_attrs: HashMap<String, String>) -> Self {
        let mut new_attrs = self.attrs.clone();
        for (k, v) in override_attrs {
            new_attrs.insert(k, v);
        }
        Scope {
            attrs: new_attrs,
            ..self.clone()
        }
    }

    /// Return the value of the named attribute, or `None`.
    pub fn get_attr(&self, name: &str) -> Option<&str> {
        self.attrs.get(name).map(|s| s.as_str())
    }

    /// Return true if the attribute is defined in this scope.
    pub fn has_attr(&self, name: &str) -> bool {
        self.attrs.contains_key(name)
    }
}

impl Default for Scope {
    fn default() -> Self {
        Self::identity()
    }
}

// ── ScopeStack trait ─────────────────────────────────────────────────────────

/// LIFO stack of `Scope` frames representing the dynamic-scope chain.
pub trait ScopeStack {
    /// Push a new scope onto the top of the stack.
    fn push(&mut self, scope: Scope);

    /// Pop and return the top scope, or `None` if the stack is empty.
    fn pop(&mut self) -> Option<Scope>;

    /// Return a reference to the top scope without removing it.
    fn top(&self) -> Option<&Scope>;

    /// Walk the stack top-to-bottom and return the first value for `name`,
    /// or `None` if the attribute is not defined anywhere in the chain.
    fn get(&self, name: &str) -> Option<&str>;

    /// Return the current stack depth.
    fn depth(&self) -> usize;
}

// ── VecScopeStack — default concrete implementation ──────────────────────────

/// A `Vec`-backed `ScopeStack` implementation.
pub struct VecScopeStack {
    frames: Vec<Scope>,
}

impl VecScopeStack {
    pub fn new() -> Self {
        VecScopeStack { frames: Vec::new() }
    }
}

impl Default for VecScopeStack {
    fn default() -> Self {
        Self::new()
    }
}

impl ScopeStack for VecScopeStack {
    fn push(&mut self, scope: Scope) {
        unimplemented!("VecScopeStack::push")
    }

    fn pop(&mut self) -> Option<Scope> {
        unimplemented!("VecScopeStack::pop")
    }

    fn top(&self) -> Option<&Scope> {
        unimplemented!("VecScopeStack::top")
    }

    fn get(&self, name: &str) -> Option<&str> {
        unimplemented!("VecScopeStack::get")
    }

    fn depth(&self) -> usize {
        unimplemented!("VecScopeStack::depth")
    }
}
