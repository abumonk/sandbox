use clap::Parser;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "ark-orchestrator", about = "Run an ARK spec through parse->verify->codegen")]
struct Args {
    /// Path to the .ark spec (usually specs/root.ark)
    spec: PathBuf,
    /// Print the SMT-LIB text to stdout
    #[arg(long)]
    emit_smt: bool,
    /// Print the generated Rust source to stdout
    #[arg(long)]
    emit_rust: bool,
}

fn main() -> anyhow::Result<()> {
    let args = Args::parse();
    let report = ark_orchestrator::run_pipeline(&args.spec)?;
    println!("spec:     {}", report.spec_path.display());
    println!("items:    {}", report.items_parsed);
    println!("entities: {}", report.entities);
    println!("islands:  {}", report.islands);
    println!("bridges:  {}", report.bridges);
    println!(
        "verify:   {} targets, {} SMT lines",
        report.verify_targets, report.smt_lines
    );
    println!("codegen:  {} Rust lines", report.rust_lines);
    println!("Execution DAG:");
    for group in &report.execution_dag.phases {
        println!("  phase [{}] ({} tasks):", group.phase, group.tasks.len());
        for t in &group.tasks {
            println!("    priority {:>3} — {}", t.priority, t.name);
        }
    }
    if !report.execution_dag.edges.is_empty() {
        println!("Bridges ({}):", report.execution_dag.edges.len());
        for e in &report.execution_dag.edges {
            let from = if e.from_port.is_empty() {
                e.from_entity.clone()
            } else {
                format!("{}.{}", e.from_entity, e.from_port)
            };
            let to = if e.to_port.is_empty() {
                e.to_entity.clone()
            } else {
                format!("{}.{}", e.to_entity, e.to_port)
            };
            println!("  {}: {} → {}", e.name, from, to);
        }
    }
    if args.emit_smt {
        let file = ark_orchestrator::load(&args.spec)?;
        println!("\n; === SMT ===\n{}", ark_verify::to_smtlib(&file));
    }
    if args.emit_rust {
        let file = ark_orchestrator::load(&args.spec)?;
        println!("\n// === RUST ===\n{}", ark_codegen::gen_rust_file(&file));
    }
    Ok(())
}
