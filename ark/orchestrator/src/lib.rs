//! ark-orchestrator — runs an ARK spec through parse → verify → codegen.
//!
//! Library API used by the `ark-orchestrator` binary and by unit tests.

pub use ark_dsl;
pub use ark_codegen;
pub use ark_verify;

use ark_dsl::{ArkFile, Expr, Item, MetaPair};
use anyhow::{Context, Result};
use std::path::{Path, PathBuf};

/// Summary of a full pipeline run over one `.ark` spec.
#[derive(Debug, Clone)]
pub struct PipelineReport {
    pub spec_path: PathBuf,
    pub items_parsed: usize,
    pub entities: usize, // abstraction + class count
    pub islands: usize,
    pub bridges: usize,
    pub registries: usize,
    pub verify_targets: usize,
    pub smt_lines: usize,
    pub rust_lines: usize,
    /// Legacy flat view — every task in canonical (phase, priority, name) order.
    pub registry_order: Vec<RegisteredTask>,
    /// Phase-grouped DAG with bridge edges (Option B).
    pub execution_dag: ExecutionDag,
}

/// One entry pulled out of a `registry { ... }` item.
#[derive(Debug, Clone)]
pub struct RegisteredTask {
    pub name: String,
    pub phase: String,
    pub priority: i64,
}

/// Phase-grouped execution DAG derived from `registry { ... }` + `bridge { ... }` items.
///
/// Phases are ordered by a canonical rank (dev → build → init → runtime → teardown → other).
/// Within a phase, tasks are sorted by `(priority asc, name asc)`.
/// Edges are extracted from top-level `bridge` items.
#[derive(Debug, Clone)]
pub struct ExecutionDag {
    pub phases: Vec<PhaseGroup>,
    pub edges: Vec<BridgeEdge>,
}

/// One phase bucket in the execution DAG.
#[derive(Debug, Clone)]
pub struct PhaseGroup {
    pub phase: String,
    pub tasks: Vec<RegisteredTask>,
}

/// A data-flow edge between two entities, lifted from a `bridge` item.
#[derive(Debug, Clone)]
pub struct BridgeEdge {
    pub name: String,
    pub from_entity: String,
    pub from_port: String,
    pub to_entity: String,
    pub to_port: String,
}

const DEFAULT_PHASE: &str = "unknown";
const DEFAULT_PRIORITY: i64 = 999;

/// Canonical ordering of known phases.
/// Unknown phases sort last (by rank) and then alphabetically.
fn phase_rank(phase: &str) -> u8 {
    match phase {
        "dev" => 0,
        "build" => 1,
        "init" => 2,
        "runtime" => 3,
        "teardown" => 4,
        _ => 5,
    }
}

/// Load and parse a `.ark` file from disk.
pub fn load(spec: &Path) -> Result<ArkFile> {
    let src = std::fs::read_to_string(spec)
        .with_context(|| format!("failed to read spec {}", spec.display()))?;
    ark_dsl::parse_ark_file(&src)
        .with_context(|| format!("failed to parse spec {}", spec.display()))
}

/// Run the full pipeline and produce a report.
pub fn run_pipeline(spec: &Path) -> Result<PipelineReport> {
    let file = load(spec)?;

    let mut entities = 0usize;
    let mut islands = 0usize;
    let mut bridges = 0usize;
    let mut registries = 0usize;
    let mut verify_targets = 0usize;

    for item in &file.items {
        match item {
            Item::Abstraction(_) | Item::Class(_) => entities += 1,
            Item::Island(_) => islands += 1,
            Item::Bridge(_) => bridges += 1,
            Item::Registry(_) => registries += 1,
            Item::Verify(_) => verify_targets += 1,
            Item::Instance(_) => {}
        }
    }

    let smt = ark_verify::to_smtlib(&file);
    let smt_lines = smt.lines().count();

    let rust_src = ark_codegen::gen_rust_file(&file);
    let rust_lines = rust_src.lines().count();

    let execution_dag = build_execution_dag(&file);
    let registry_order: Vec<RegisteredTask> = execution_dag
        .phases
        .iter()
        .flat_map(|g| g.tasks.iter().cloned())
        .collect();

    Ok(PipelineReport {
        spec_path: spec.to_path_buf(),
        items_parsed: file.items.len(),
        entities,
        islands,
        bridges,
        registries,
        verify_targets,
        smt_lines,
        rust_lines,
        registry_order,
        execution_dag,
    })
}

/// Build the phase-grouped execution DAG from a parsed `ArkFile`.
///
/// This is the Option-B orchestrator view: tasks clustered by phase,
/// edges lifted from top-level `bridge { from: ..., to: ... }` items.
pub fn build_execution_dag(file: &ArkFile) -> ExecutionDag {
    use std::collections::BTreeMap;

    // (phase_rank, phase_name) → tasks. BTreeMap keeps canonical order.
    let mut by_phase: BTreeMap<(u8, String), Vec<RegisteredTask>> = BTreeMap::new();

    for item in &file.items {
        if let Item::Registry(reg) = item {
            for entry in &reg.entries {
                let phase = meta_string(&entry.meta, "phase")
                    .unwrap_or_else(|| DEFAULT_PHASE.to_string());
                let priority = meta_int(&entry.meta, "priority").unwrap_or(DEFAULT_PRIORITY);
                let task = RegisteredTask {
                    name: entry.name.clone(),
                    phase: phase.clone(),
                    priority,
                };
                let key = (phase_rank(&phase), phase);
                by_phase.entry(key).or_default().push(task);
            }
        }
    }

    let phases: Vec<PhaseGroup> = by_phase
        .into_iter()
        .map(|((_, phase), mut tasks)| {
            tasks.sort_by(|a, b| a.priority.cmp(&b.priority).then(a.name.cmp(&b.name)));
            PhaseGroup { phase, tasks }
        })
        .collect();

    let mut edges: Vec<BridgeEdge> = Vec::new();
    for item in &file.items {
        if let Item::Bridge(b) = item {
            let (from_entity, from_port) = split_dotted(&b.from);
            let (to_entity, to_port) = split_dotted(&b.to);
            edges.push(BridgeEdge {
                name: b.name.clone(),
                from_entity,
                from_port,
                to_entity,
                to_port,
            });
        }
    }
    edges.sort_by(|a, b| a.name.cmp(&b.name));

    ExecutionDag { phases, edges }
}

/// Split `"Entity.field"` into `("Entity", "field")`.
/// A path with no dot becomes `("whole", "")`.
fn split_dotted(path: &str) -> (String, String) {
    match path.split_once('.') {
        Some((head, tail)) => (head.to_string(), tail.to_string()),
        None => (path.to_string(), String::new()),
    }
}

/// Flatten every `RegistryDef` into a sorted list of tasks.
///
/// This is the legacy flat view; it is derived from `build_execution_dag`
/// so phase ordering is identical (canonical rank, not alphabetical).
/// Unknown `Expr` variants fall back to default phase/priority — never panics.
pub fn build_dag(file: &ArkFile) -> Vec<RegisteredTask> {
    build_execution_dag(file)
        .phases
        .into_iter()
        .flat_map(|g| g.tasks.into_iter())
        .collect()
}

/// Look up a meta key and flatten its value into a displayable string.
fn meta_string(meta: &[MetaPair], key: &str) -> Option<String> {
    for pair in meta {
        if pair.key == key {
            return Some(expr_to_string(&pair.value));
        }
    }
    None
}

/// Look up a meta key and coerce its value to i64, if possible.
fn meta_int(meta: &[MetaPair], key: &str) -> Option<i64> {
    for pair in meta {
        if pair.key == key {
            return expr_to_int(&pair.value);
        }
    }
    None
}

fn expr_to_string(expr: &Expr) -> String {
    match expr {
        Expr::Ident(s) => s.clone(),
        Expr::StringLit(s) => s.clone(),
        Expr::Number(n) => {
            if n.fract() == 0.0 && n.is_finite() {
                format!("{}", *n as i64)
            } else {
                format!("{}", n)
            }
        }
        Expr::Bool(b) => b.to_string(),
        Expr::DottedPath(parts) => parts.join("."),
        // Anything else: fall through to default sentinel — never panic.
        _ => DEFAULT_PHASE.to_string(),
    }
}

fn expr_to_int(expr: &Expr) -> Option<i64> {
    match expr {
        Expr::Number(n) if n.is_finite() => Some(*n as i64),
        Expr::Ident(s) | Expr::StringLit(s) => s.parse::<i64>().ok(),
        _ => None,
    }
}

// ============================================================
// Tests
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;
    use ark_dsl::{BridgeDef, RegistryDef, RegistryEntry};

    fn mk_meta(key: &str, value: Expr) -> MetaPair {
        MetaPair {
            key: key.to_string(),
            value,
        }
    }

    #[test]
    fn builds_dag_from_registry() {
        let reg = RegistryDef {
            name: "Backlog".into(),
            entries: vec![
                RegistryEntry {
                    name: "task_a".into(),
                    meta: vec![
                        mk_meta("phase", Expr::Ident("runtime".into())),
                        mk_meta("priority", Expr::Number(5.0)),
                    ],
                },
                RegistryEntry {
                    name: "task_b".into(),
                    meta: vec![
                        mk_meta("phase", Expr::Ident("runtime".into())),
                        mk_meta("priority", Expr::Number(2.0)),
                    ],
                },
            ],
        };
        let file = ArkFile {
            imports: vec![],
            items: vec![Item::Registry(reg)],
            ..Default::default()
        };
        let dag = build_dag(&file);
        assert_eq!(dag.len(), 2);
        // sorted: same phase, so priority ascending
        assert_eq!(dag[0].name, "task_b");
        assert_eq!(dag[0].priority, 2);
        assert_eq!(dag[0].phase, "runtime");
        assert_eq!(dag[1].name, "task_a");
        assert_eq!(dag[1].priority, 5);
    }

    #[test]
    fn build_dag_defaults_on_unknown_expr() {
        // ForAll is not handled by expr_to_string/int — must fall back.
        let weird_phase = Expr::ForAll {
            ty: "X".into(),
            var: "x".into(),
            condition: None,
            body: vec![],
        };
        let reg = RegistryDef {
            name: "R".into(),
            entries: vec![RegistryEntry {
                name: "weird".into(),
                meta: vec![
                    mk_meta("phase", weird_phase),
                    mk_meta("priority", Expr::Bool(true)),
                ],
            }],
        };
        let file = ArkFile {
            imports: vec![],
            items: vec![Item::Registry(reg)],
            ..Default::default()
        };
        let dag = build_dag(&file);
        assert_eq!(dag.len(), 1);
        assert_eq!(dag[0].phase, DEFAULT_PHASE);
        assert_eq!(dag[0].priority, DEFAULT_PRIORITY);
    }

    #[test]
    fn execution_dag_groups_by_phase_canonical_order() {
        // Mix phases deliberately out of order; runtime must come after dev.
        let reg = RegistryDef {
            name: "Sys".into(),
            entries: vec![
                RegistryEntry {
                    name: "rt_a".into(),
                    meta: vec![
                        mk_meta("phase", Expr::Ident("runtime".into())),
                        mk_meta("priority", Expr::Number(10.0)),
                    ],
                },
                RegistryEntry {
                    name: "dev_tool".into(),
                    meta: vec![
                        mk_meta("phase", Expr::Ident("dev".into())),
                        mk_meta("priority", Expr::Number(0.0)),
                    ],
                },
                RegistryEntry {
                    name: "rt_b".into(),
                    meta: vec![
                        mk_meta("phase", Expr::Ident("runtime".into())),
                        mk_meta("priority", Expr::Number(5.0)),
                    ],
                },
            ],
        };
        let file = ArkFile {
            imports: vec![],
            items: vec![Item::Registry(reg)],
            ..Default::default()
        };
        let dag = build_execution_dag(&file);
        assert_eq!(dag.phases.len(), 2);
        // dev before runtime by canonical rank
        assert_eq!(dag.phases[0].phase, "dev");
        assert_eq!(dag.phases[0].tasks.len(), 1);
        assert_eq!(dag.phases[0].tasks[0].name, "dev_tool");
        assert_eq!(dag.phases[1].phase, "runtime");
        // within phase: priority ascending
        assert_eq!(dag.phases[1].tasks[0].name, "rt_b");
        assert_eq!(dag.phases[1].tasks[0].priority, 5);
        assert_eq!(dag.phases[1].tasks[1].name, "rt_a");
        assert_eq!(dag.phases[1].tasks[1].priority, 10);
        assert!(dag.edges.is_empty());
    }

    #[test]
    fn execution_dag_lifts_bridge_edges() {
        let bridge_a = BridgeDef {
            name: "FeedA".into(),
            from: "Producer.out_val".into(),
            to: "Consumer.in_val".into(),
            contract: None,
        };
        let bridge_b = BridgeDef {
            name: "Bare".into(),
            from: "LonelyEntity".into(), // no dot — port becomes ""
            to: "Other.slot".into(),
            contract: None,
        };
        let file = ArkFile {
            imports: vec![],
            items: vec![Item::Bridge(bridge_a), Item::Bridge(bridge_b)],
            ..Default::default()
        };
        let dag = build_execution_dag(&file);
        assert_eq!(dag.edges.len(), 2);
        // Sorted by name: Bare < FeedA
        assert_eq!(dag.edges[0].name, "Bare");
        assert_eq!(dag.edges[0].from_entity, "LonelyEntity");
        assert_eq!(dag.edges[0].from_port, "");
        assert_eq!(dag.edges[0].to_entity, "Other");
        assert_eq!(dag.edges[0].to_port, "slot");
        assert_eq!(dag.edges[1].name, "FeedA");
        assert_eq!(dag.edges[1].from_entity, "Producer");
        assert_eq!(dag.edges[1].from_port, "out_val");
        assert_eq!(dag.edges[1].to_entity, "Consumer");
        assert_eq!(dag.edges[1].to_port, "in_val");
    }

    #[test]
    fn phase_rank_orders_known_phases() {
        assert!(phase_rank("dev") < phase_rank("build"));
        assert!(phase_rank("build") < phase_rank("init"));
        assert!(phase_rank("init") < phase_rank("runtime"));
        assert!(phase_rank("runtime") < phase_rank("teardown"));
        assert!(phase_rank("teardown") < phase_rank("unknown"));
        assert!(phase_rank("nonexistent") == phase_rank("unknown"));
    }

    #[test]
    fn run_pipeline_on_real_spec() {
        let report = run_pipeline(Path::new("../specs/meta/backlog.ark"))
            .expect("pipeline should succeed on backlog.ark");
        assert!(
            report.items_parsed > 20,
            "expected >20 items, got {}",
            report.items_parsed
        );
        assert!(
            report.entities > 10,
            "expected >10 entities, got {}",
            report.entities
        );
        assert!(report.registries >= 1, "expected at least 1 registry");
        assert!(report.islands >= 1, "expected at least 1 island");
        assert!(report.smt_lines > 0);
        assert!(report.rust_lines > 0);
        assert!(
            !report.execution_dag.phases.is_empty(),
            "execution DAG should have at least one phase"
        );
        // Flattened registry_order must match the sum of phase tasks.
        let flat: usize = report
            .execution_dag
            .phases
            .iter()
            .map(|p| p.tasks.len())
            .sum();
        assert_eq!(flat, report.registry_order.len());
    }
}
