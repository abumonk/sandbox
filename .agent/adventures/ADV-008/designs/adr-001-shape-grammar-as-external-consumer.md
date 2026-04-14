# ADR-001 — `shape_grammar/` as an External Consumer of Ark

**Status**: Accepted (Checkpoint 1, 2026-04-14)

**Adventure**: ADV-008

## Context

ShapeML is a procedural 3D shape grammar (C++, academic lineage — CGA / CityEngine / Pirkka Aho). The user wants an equivalent hosted on Ark DSL: entities in `.ark`, Z3-verifiable invariants, Python reference evaluator, Rust performant skeleton, integration with Ark's visualizer / impact / diff tools, plus a semantic-rendering research track.

Two architectural paths were considered:

1. **Add `shape_grammar.ark` to Ark's stdlib.** Shape grammar becomes a first-class DSL concern; Ark's parser/verifier/codegen learn about shape rules, operations, scopes.
2. **Sibling package consuming Ark.** `shape_grammar/` lives next to `ark/` in `R:/Sandbox/`; grammars are written in *existing* Ark syntax; `shape_grammar` provides the semantics (evaluator, verifier passes, codegen, runtime) that interpret those islands. Dependency direction `shape_grammar → ark`, strictly one-way.

## Decision

**Adopt path 2.** `shape_grammar/` is a sibling package that consumes Ark as its host language. Ark is not modified. Shape grammars are written as ordinary Ark islands in existing `.ark` syntax.

## Rationale

- **Concern separation**. Ark's identity is a *general-purpose* specification language. Embedding 3D procedural geometry in Ark's stdlib would conflate core and domain, setting a precedent where every new domain inflates the core.
- **Dogfooding Ark-as-host**. This adventure becomes the first real test of whether Ark is expressive enough to host a new domain *without modification*. If we encounter an inexpressible construct, the failure is informative: it triggers a *separate* adventure on Ark extension mechanisms (macros, plugin hooks, IR surface), rather than silently patching core.
- **Blast radius**. A sibling package can be deleted, versioned, or re-homed without touching `ark/`. A stdlib extension cannot.
- **Reviewability**. The `git diff --stat master -- ark/` check (TC-10) is a crisp, machine-verifiable boundary.
- **Precedent for future domains**. The pattern established here — spec island in `.ark` + external semantics package + adapter integrations — is reusable for any future domain (audio, animation, shader DSLs, quest DSL, etc.).

## Consequences

### Positive
- Clean boundary enforceable by CI (`git diff --stat master -- ark/` must be empty).
- Verbosity in shape grammars is accepted as the price of zero-Ark-modification; ergonomic DSL surfaces belong in the runtime / examples / future extension adventures.
- Reusable pattern for future domain packages.
- Ark's stdlib stays focused.

### Negative
- Shape grammars are verbose compared to ShapeML's terse surface syntax (`Window --> extrude | split…`). Contributors writing shape grammars write plain Ark, not a shape-grammar-specific DSL.
- Some integration friction: `shape_grammar` must read Ark's AST from the outside (via the parser as a library or the CLI as subprocess), rather than hook into an internal pipeline.
- Verifier passes must be structured as *post*-Ark-verify analyzers (load Ark's AST, run shape-grammar-specific Z3 obligations) rather than be part of Ark's core verifier loop.

### Neutral
- Tool integration (visualizer, impact, diff) is done through *adapters* in `shape_grammar/tools/integrations/` that read Ark's IR output and emit shape-grammar-annotated views. If a tool genuinely cannot be extended from outside, that is recorded as a findings item — we do not edit the tool.

## Non-Negotiable Constraints

- `shape_grammar/` is the package root. Location: `R:/Sandbox/shape_grammar/`.
- Dependency direction is one-way: `shape_grammar → ark`. `ark/` never imports `shape_grammar`.
- No Lark grammar changes, no new AST node types in Ark, no new verifier passes inside `ark/tools/verify/`, no stdlib entries in `ark/dsl/stdlib/` for shape-grammar concerns.
- CI-equivalent proof: `git diff --stat master -- ark/` must produce empty output at adventure close (TC-10).

## Escape Hatch

If during implementation a genuine Ark extensibility gap is discovered, the correct response is:

1. Stop. Do not patch `ark/`.
2. Log a findings item in `.agent/adventures/ADV-008/research/ark-as-host-feasibility.md`.
3. Either (a) work around it in `shape_grammar/` even at the cost of verbosity, or (b) escalate to a separate Ark-extensibility adventure.

Patching `ark/` mid-adventure is a boundary violation and invalidates TC-10.

## Related Decisions

- Reuses ADV-002's "Reflexive self-indexing" pattern (we use Ark to describe its own consumer).
- Reuses ADV-006's "Separate Domain Modules" pattern — but escalated from `ark/tools/{domain}/` to `{domain}/tools/` at the workspace root.
- Informs future ADRs about layered packages in `R:/Sandbox/`.
