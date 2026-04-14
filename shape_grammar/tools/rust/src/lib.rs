//! shape_grammar — Rust skeleton for the shape-grammar evaluator.
//!
//! This crate mirrors the public API of the Python reference implementation
//! under `shape_grammar/tools/`.  All trait methods are stubs only;
//! `cargo check` passes but no functional implementation is present.

#![allow(dead_code, unused_imports, unused_variables)]

pub mod evaluator;
pub mod ops;
pub mod scope;
pub mod semantic;

// ── Shared primitive types ──────────────────────────────────────────────────

/// 3-component vector (x, y, z) of 64-bit floats.
pub type Vec3 = [f64; 3];

/// Deterministic RNG seed.
pub type Seed = u64;

// ── Root error type ─────────────────────────────────────────────────────────

/// Top-level error enum for the shape_grammar crate.
#[derive(Debug)]
pub enum Error {
    /// A requested scope attribute was not defined.
    UndefinedAttribute(String),
    /// Maximum derivation depth exceeded.
    MaxDepthExceeded,
    /// An operation was applied in an invalid context.
    InvalidOp(String),
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Error::UndefinedAttribute(name) => write!(f, "undefined attribute: {name}"),
            Error::MaxDepthExceeded => write!(f, "max derivation depth exceeded"),
            Error::InvalidOp(msg) => write!(f, "invalid op: {msg}"),
        }
    }
}

impl std::error::Error for Error {}
