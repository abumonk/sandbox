//! pest Pairs → AST conversion.
//!
//! Every `*_from_pair` function takes a pest `Pair<Rule>` matching exactly
//! the rule named in the function, and walks its inner pairs into the AST
//! types defined in `lib.rs`.

use crate::{
    ArkFile, ArkParser, BridgeDef, CheckDef, Constraint, ContractDef, DataField, EntityDef, Expr,
    ExpressionDef, ImportPath, InPort, InstanceDef, IslandDef, Item, MetaPair, OutPort,
    PipeStage, PredicateDef, ProcessRule, RefKind, RegistryDef, RegistryEntry, Rule, Statement,
    TypeExpr, TypedField, VerifyDef,
};
use anyhow::{anyhow, Result};
use pest::iterators::Pair;
use pest::Parser;

/// Entry point — parse a full .ark source string into an `ArkFile` AST.
pub fn parse(input: &str) -> Result<ArkFile> {
    let mut pairs = ArkParser::parse(Rule::file, input)
        .map_err(|e| anyhow!("parse error: {e}"))?;
    let file_pair = pairs
        .next()
        .ok_or_else(|| anyhow!("empty parse result"))?;
    let mut file = file_from_pair(file_pair)?;
    build_indices(&mut file);
    Ok(file)
}

/// Populate `classes_index`, `instances_index`, and `island_classes_index`
/// from `file.items`. Pure-additive — `items` is not mutated.
///
/// Duplicate top-level class names are last-wins (the index points at the
/// most recent declaration); orphan instances (class not declared) still
/// land in `instances_index`.
pub(crate) fn build_indices(file: &mut ArkFile) {
    file.classes_index.clear();
    file.instances_index.clear();
    file.island_classes_index.clear();
    file.expression_index.clear();
    file.predicate_index.clear();

    for (idx, item) in file.items.iter().enumerate() {
        match item {
            Item::Class(def) => {
                file.classes_index.insert(def.name.clone(), idx);
            }
            Item::Instance(inst) => {
                file.instances_index
                    .entry(inst.class_name.clone())
                    .or_default()
                    .push(idx);
            }
            Item::Island(isl) => {
                let mut nested: std::collections::BTreeMap<String, usize> =
                    std::collections::BTreeMap::new();
                for (nested_idx, cls) in isl.classes.iter().enumerate() {
                    nested.insert(cls.name.clone(), nested_idx);
                }
                if !nested.is_empty() {
                    file.island_classes_index.insert(isl.name.clone(), nested);
                }
            }
            Item::Expression(def) => {
                file.expression_index.insert(def.name.clone(), idx);
            }
            Item::Predicate(def) => {
                file.predicate_index.insert(def.name.clone(), idx);
            }
            _ => {}
        }
    }
}

fn file_from_pair(pair: Pair<Rule>) -> Result<ArkFile> {
    let mut imports = Vec::new();
    let mut items = Vec::new();

    for inner in pair.into_inner() {
        match inner.as_rule() {
            Rule::import_stmt => imports.push(import_from_pair(inner)?),
            Rule::abstraction_def => {
                items.push(Item::Abstraction(entity_from_pair(inner)?));
            }
            Rule::class_def => {
                items.push(Item::Class(entity_from_pair(inner)?));
            }
            Rule::instance_def => {
                items.push(Item::Instance(instance_from_pair(inner)?));
            }
            Rule::island_def => {
                items.push(Item::Island(island_from_pair(inner)?));
            }
            Rule::bridge_def => {
                items.push(Item::Bridge(bridge_from_pair(inner)?));
            }
            Rule::registry_def => {
                items.push(Item::Registry(registry_from_pair(inner)?));
            }
            Rule::verify_def => {
                items.push(Item::Verify(verify_from_pair(inner)?));
            }
            Rule::expression_def => {
                items.push(Item::Expression(expression_def_from_pair(inner)?));
            }
            Rule::predicate_def => {
                items.push(Item::Predicate(predicate_def_from_pair(inner)?));
            }
            Rule::EOI => {}
            other => return Err(anyhow!("unexpected top-level rule: {:?}", other)),
        }
    }

    Ok(ArkFile {
        imports,
        items,
        ..Default::default()
    })
}

// ============================================================
// IMPORTS
// ============================================================

fn import_from_pair(pair: Pair<Rule>) -> Result<ImportPath> {
    // import_stmt = { "import" ~ dotted_path }
    let dotted = pair
        .into_inner()
        .next()
        .ok_or_else(|| anyhow!("import missing dotted_path"))?;
    Ok(ImportPath(dotted_path_segments(dotted)))
}

fn dotted_path_segments(pair: Pair<Rule>) -> Vec<String> {
    // dotted_path / dotted_path_or_ident are compound atomic;
    // their inner pairs are the ident atoms.
    pair.into_inner()
        .filter(|p| p.as_rule() == Rule::ident)
        .map(|p| p.as_str().to_string())
        .collect::<Vec<_>>()
        .into_iter()
        .map(|s| s)
        .collect()
}

// ============================================================
// ENTITIES (abstraction / class)
// ============================================================

fn entity_from_pair(pair: Pair<Rule>) -> Result<EntityDef> {
    // abstraction_def/class_def = { kw ~ ident ~ inherits? ~ "{" ~ entity_body ~ "}" }
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("entity missing name"))?
        .as_str()
        .to_string();

    let mut inherits = Vec::new();
    let mut body_pair: Option<Pair<Rule>> = None;

    for p in inner {
        match p.as_rule() {
            Rule::inherits => inherits = ident_list_from_inherits(p),
            Rule::entity_body => body_pair = Some(p),
            _ => {}
        }
    }

    let mut entity = EntityDef {
        name,
        inherits,
        data_fields: Vec::new(),
        in_ports: Vec::new(),
        out_ports: Vec::new(),
        processes: Vec::new(),
        invariants: Vec::new(),
        temporals: Vec::new(),
        description: None,
    };

    if let Some(body) = body_pair {
        for member in body.into_inner() {
            apply_entity_member(&mut entity, member)?;
        }
    }

    Ok(entity)
}

fn apply_entity_member(entity: &mut EntityDef, pair: Pair<Rule>) -> Result<()> {
    match pair.as_rule() {
        Rule::in_port => entity.in_ports.push(in_port_from_pair(pair)?),
        Rule::out_port => entity.out_ports.push(out_port_from_pair(pair)?),
        Rule::process_rule => entity.processes.push(process_from_pair(pair)?),
        Rule::data_field => entity.data_fields.push(data_field_from_pair(pair)?),
        Rule::invariant_stmt => entity.invariants.push(expr_from_inner(pair)?),
        Rule::temporal_stmt => entity.temporals.push(expr_from_inner(pair)?),
        Rule::description_stmt => entity.description = Some(description_from_pair(pair)?),
        other => return Err(anyhow!("unexpected entity member: {:?}", other)),
    }
    Ok(())
}

fn ident_list_from_inherits(pair: Pair<Rule>) -> Vec<String> {
    // inherits = { ":" ~ ident_list }
    pair.into_inner()
        .filter(|p| p.as_rule() == Rule::ident_list)
        .flat_map(|il| ident_list_idents(il))
        .collect()
}

fn ident_list_idents(pair: Pair<Rule>) -> Vec<String> {
    pair.into_inner()
        .filter(|p| p.as_rule() == Rule::ident)
        .map(|p| p.as_str().to_string())
        .collect()
}

// ============================================================
// INSTANCE
// ============================================================

fn instance_from_pair(pair: Pair<Rule>) -> Result<InstanceDef> {
    // instance_def = { "instance" ~ ident ~ ":" ~ ident ~ "{" ~ assignment* ~ "}" }
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("instance missing name"))?
        .as_str()
        .to_string();
    let class_name = inner
        .next()
        .ok_or_else(|| anyhow!("instance missing class"))?
        .as_str()
        .to_string();

    let mut assignments = Vec::new();
    for p in inner {
        if p.as_rule() == Rule::assignment {
            assignments.push(assignment_from_pair(p)?);
        }
    }

    Ok(InstanceDef {
        name,
        class_name,
        assignments,
    })
}

// ============================================================
// ISLAND
// ============================================================

fn island_from_pair(pair: Pair<Rule>) -> Result<IslandDef> {
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("island missing name"))?
        .as_str()
        .to_string();

    let mut island = IslandDef {
        name,
        strategy: None,
        memory: None,
        contains: Vec::new(),
        in_ports: Vec::new(),
        out_ports: Vec::new(),
        processes: Vec::new(),
        classes: Vec::new(),
        data_fields: Vec::new(),
        description: None,
    };

    if let Some(body) = inner.find(|p| p.as_rule() == Rule::island_body) {
        for member in body.into_inner() {
            match member.as_rule() {
                Rule::strategy_stmt => {
                    let s = member
                        .into_inner()
                        .next()
                        .ok_or_else(|| anyhow!("strategy missing ident"))?
                        .as_str()
                        .to_string();
                    island.strategy = Some(s);
                }
                Rule::memory_stmt => {
                    // Keep as a list of expression statements for now.
                    let entries: Vec<Statement> = member
                        .into_inner()
                        .filter(|p| p.as_rule() == Rule::memory_entry)
                        .map(|e| Statement::Expr(memory_entry_as_expr(e)))
                        .collect();
                    island.memory = Some(entries);
                }
                Rule::contains_stmt => {
                    for p in member.into_inner() {
                        if p.as_rule() == Rule::ident_list {
                            island.contains = ident_list_idents(p);
                        }
                    }
                }
                Rule::description_stmt => {
                    island.description = Some(description_from_pair(member)?);
                }
                Rule::in_port => island.in_ports.push(in_port_from_pair(member)?),
                Rule::out_port => island.out_ports.push(out_port_from_pair(member)?),
                Rule::process_rule => island.processes.push(process_from_pair(member)?),
                Rule::class_def => island.classes.push(entity_from_pair(member)?),
                Rule::data_field => island.data_fields.push(data_field_from_pair(member)?),
                Rule::invariant_stmt => {
                    // Islands don't currently store invariants on the struct;
                    // attach to last process if any, else drop.
                    let e = expr_from_inner(member)?;
                    if let Some(last) = island.processes.last_mut() {
                        last.postconditions.push(e);
                    }
                }
                Rule::temporal_stmt => {
                    let _ = expr_from_inner(member)?;
                }
                other => return Err(anyhow!("unexpected island member: {:?}", other)),
            }
        }
    }

    Ok(island)
}

fn memory_entry_as_expr(pair: Pair<Rule>) -> Expr {
    // memory_entry = { ident ~ "(" ~ (expression ~ ("," ~ expression)*)? ~ ")" }
    let mut inner = pair.into_inner();
    let name = inner.next().map(|p| p.as_str().to_string()).unwrap_or_default();
    let args: Vec<Expr> = inner
        .filter(|p| p.as_rule() == Rule::expression)
        .map(|p| expr_from_pair(p).unwrap_or(Expr::Ident("?".into())))
        .collect();
    Expr::FnCall(name, args)
}

// ============================================================
// BRIDGE
// ============================================================

fn bridge_from_pair(pair: Pair<Rule>) -> Result<BridgeDef> {
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("bridge missing name"))?
        .as_str()
        .to_string();

    let mut from = String::new();
    let mut to = String::new();
    let mut contract: Option<ContractDef> = None;

    for p in inner {
        match p.as_rule() {
            Rule::from_stmt => {
                from = dotted_or_ident_string(p);
            }
            Rule::to_stmt => {
                to = dotted_or_ident_string(p);
            }
            Rule::contract_block => {
                let mut invariants = Vec::new();
                let mut temporals = Vec::new();
                for m in p.into_inner() {
                    match m.as_rule() {
                        Rule::invariant_stmt => invariants.push(expr_from_inner(m)?),
                        Rule::temporal_stmt => temporals.push(expr_from_inner(m)?),
                        _ => {}
                    }
                }
                contract = Some(ContractDef {
                    invariants,
                    temporals,
                });
            }
            _ => {}
        }
    }

    Ok(BridgeDef {
        name,
        from,
        to,
        contract,
    })
}

fn dotted_or_ident_string(pair: Pair<Rule>) -> String {
    // from_stmt / to_stmt = { "from:" ~ dotted_path_or_ident }
    for p in pair.into_inner() {
        if p.as_rule() == Rule::dotted_path_or_ident {
            return p.as_str().to_string();
        }
    }
    String::new()
}

// ============================================================
// REGISTRY
// ============================================================

fn registry_from_pair(pair: Pair<Rule>) -> Result<RegistryDef> {
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("registry missing name"))?
        .as_str()
        .to_string();

    let mut entries = Vec::new();
    for p in inner {
        if p.as_rule() == Rule::register_stmt {
            entries.push(register_from_pair(p)?);
        }
    }

    Ok(RegistryDef { name, entries })
}

fn register_from_pair(pair: Pair<Rule>) -> Result<RegistryEntry> {
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("register missing name"))?
        .as_str()
        .to_string();

    let mut meta = Vec::new();
    for p in inner {
        if p.as_rule() == Rule::meta_pair_list {
            meta = meta_pair_list_from_pair(p)?;
        }
    }

    Ok(RegistryEntry { name, meta })
}

// ============================================================
// VERIFY
// ============================================================

fn verify_from_pair(pair: Pair<Rule>) -> Result<VerifyDef> {
    let mut inner = pair.into_inner();
    let target = inner
        .next()
        .ok_or_else(|| anyhow!("verify missing target"))?
        .as_str()
        .to_string();

    let mut checks = Vec::new();
    for p in inner {
        if p.as_rule() == Rule::check_stmt {
            checks.push(check_from_pair(p)?);
        }
    }

    Ok(VerifyDef { target, checks })
}

fn check_from_pair(pair: Pair<Rule>) -> Result<CheckDef> {
    // check_stmt = { "check" ~ ident ~ ":" ~ expression }
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("check missing name"))?
        .as_str()
        .to_string();
    let expr_pair = inner
        .next()
        .ok_or_else(|| anyhow!("check missing expression"))?;
    Ok(CheckDef {
        name,
        expr: expr_from_pair(expr_pair)?,
    })
}

// ============================================================
// EXPRESSION DEF / PREDICATE DEF
// ============================================================

fn expression_def_from_pair(pair: Pair<Rule>) -> Result<ExpressionDef> {
    // expression_def = { "expression" ~ ident ~ "{" ~ expression_body ~ "}" }
    // expression_body = { "in:" ~ typed_field_list ~ "out:" ~ type_expr ~ "chain:" ~ expression }
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("expression_def missing name"))?
        .as_str()
        .to_string();

    // Find the expression_body child
    let body = inner
        .find(|p| p.as_rule() == Rule::expression_body)
        .ok_or_else(|| anyhow!("expression_def missing body"))?;

    let mut inputs: Vec<TypedField> = Vec::new();
    let mut output: Option<TypeExpr> = None;
    let mut chain: Option<Expr> = None;

    for p in body.into_inner() {
        match p.as_rule() {
            Rule::typed_field_list => {
                inputs = typed_field_list_from_pair(p)?;
            }
            Rule::generic_type | Rule::array_type | Rule::named_type => {
                output = Some(type_from_pair(p)?);
            }
            Rule::expression => {
                chain = Some(expr_from_pair(p)?);
            }
            _ => {}
        }
    }

    Ok(ExpressionDef {
        name,
        inputs,
        output: output.ok_or_else(|| anyhow!("expression_def missing out type"))?,
        chain: chain.ok_or_else(|| anyhow!("expression_def missing chain"))?,
        description: None,
    })
}

fn predicate_def_from_pair(pair: Pair<Rule>) -> Result<PredicateDef> {
    // predicate_def = { "predicate" ~ ident ~ "{" ~ predicate_body ~ "}" }
    // predicate_body = { "in:" ~ typed_field_list ~ "check:" ~ expression }
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("predicate_def missing name"))?
        .as_str()
        .to_string();

    let body = inner
        .find(|p| p.as_rule() == Rule::predicate_body)
        .ok_or_else(|| anyhow!("predicate_def missing body"))?;

    let mut inputs: Vec<TypedField> = Vec::new();
    let mut check: Option<Expr> = None;

    for p in body.into_inner() {
        match p.as_rule() {
            Rule::typed_field_list => {
                inputs = typed_field_list_from_pair(p)?;
            }
            Rule::expression => {
                check = Some(expr_from_pair(p)?);
            }
            _ => {}
        }
    }

    Ok(PredicateDef {
        name,
        inputs,
        check: check.ok_or_else(|| anyhow!("predicate_def missing check"))?,
        description: None,
    })
}

// ============================================================
// FOUR PRIMITIVES
// ============================================================

fn in_port_from_pair(pair: Pair<Rule>) -> Result<InPort> {
    let mut fields = Vec::new();
    for p in pair.into_inner() {
        if p.as_rule() == Rule::typed_field_list {
            fields = typed_field_list_from_pair(p)?;
        }
    }
    Ok(InPort { fields })
}

fn out_port_from_pair(pair: Pair<Rule>) -> Result<OutPort> {
    let mut meta = Vec::new();
    let mut fields = Vec::new();
    for p in pair.into_inner() {
        match p.as_rule() {
            Rule::empty_meta => {
                for inner in p.into_inner() {
                    if inner.as_rule() == Rule::meta_pair_list {
                        meta = meta_pair_list_from_pair(inner)?;
                    }
                }
            }
            Rule::typed_field_list => {
                fields = typed_field_list_from_pair(p)?;
            }
            _ => {}
        }
    }
    Ok(OutPort { meta, fields })
}

fn process_from_pair(pair: Pair<Rule>) -> Result<ProcessRule> {
    let mut meta = Vec::new();
    let mut pre = Vec::new();
    let mut post = Vec::new();
    let mut body = Vec::new();
    let mut description: Option<String> = None;

    for p in pair.into_inner() {
        match p.as_rule() {
            Rule::meta_brackets => {
                for inner in p.into_inner() {
                    if inner.as_rule() == Rule::meta_pair_list {
                        meta = meta_pair_list_from_pair(inner)?;
                    }
                }
            }
            Rule::process_body => {
                for stmt in p.into_inner() {
                    match stmt.as_rule() {
                        Rule::pre_stmt => pre.push(expr_from_inner(stmt)?),
                        Rule::post_stmt => post.push(expr_from_inner(stmt)?),
                        Rule::requires_stmt => pre.push(expr_from_inner(stmt)?),
                        Rule::description_stmt => {
                            description = Some(description_from_pair(stmt)?);
                        }
                        Rule::for_all_stmt => {
                            body.push(Statement::Expr(for_all_stmt_to_expr(stmt)?));
                        }
                        Rule::condition_stmt => {
                            // represent as Expr via FnCall for now
                            body.push(Statement::Expr(condition_stmt_to_expr(stmt)?));
                        }
                        Rule::assignment => {
                            let (lhs, rhs) = assignment_from_pair(stmt)?;
                            body.push(Statement::Assignment(lhs, rhs));
                        }
                        Rule::expression => {
                            body.push(Statement::Expr(expr_from_pair(stmt)?));
                        }
                        other => {
                            return Err(anyhow!("unexpected process stmt: {:?}", other));
                        }
                    }
                }
            }
            _ => {}
        }
    }

    Ok(ProcessRule {
        meta,
        preconditions: pre,
        postconditions: post,
        body,
        description,
    })
}

fn for_all_stmt_to_expr(pair: Pair<Rule>) -> Result<Expr> {
    // for_all_stmt = { "for_all" ~ ident ~ "as" ~ ident ~ ("where" ~ expression)? ~ ":" ~ for_all_tail }
    let mut inner = pair.into_inner();
    let ty = inner
        .next()
        .ok_or_else(|| anyhow!("for_all missing type"))?
        .as_str()
        .to_string();
    let var = inner
        .next()
        .ok_or_else(|| anyhow!("for_all missing var"))?
        .as_str()
        .to_string();

    let mut condition: Option<Box<Expr>> = None;
    let mut body: Vec<Statement> = Vec::new();

    for p in inner {
        match p.as_rule() {
            Rule::expression => {
                // Either the 'where' condition (if we haven't seen one yet)
                // or the bare-expression tail.
                if condition.is_none() && body.is_empty() {
                    condition = Some(Box::new(expr_from_pair(p)?));
                } else {
                    body.push(Statement::Expr(expr_from_pair(p)?));
                }
            }
            Rule::process_block => {
                body.extend(process_block_statements(p)?);
            }
            Rule::assignment => {
                let (lhs, rhs) = assignment_from_pair(p)?;
                body.push(Statement::Assignment(lhs, rhs));
            }
            _ => {}
        }
    }

    Ok(Expr::ForAll {
        ty,
        var,
        condition,
        body,
    })
}

fn condition_stmt_to_expr(pair: Pair<Rule>) -> Result<Expr> {
    // condition_stmt = { "condition" ~ expression ~ ":" ~ condition_tail }
    // We currently don't have a dedicated Statement::If variant, so encode as
    // FnCall("condition", [expr, ...]) to preserve the intent.
    let mut inner = pair.into_inner();
    let cond = inner
        .next()
        .ok_or_else(|| anyhow!("condition missing expr"))?;
    let cond_expr = expr_from_pair(cond)?;
    Ok(Expr::FnCall("__condition".into(), vec![cond_expr]))
}

fn process_block_statements(pair: Pair<Rule>) -> Result<Vec<Statement>> {
    let mut out = Vec::new();
    for p in pair.into_inner() {
        if p.as_rule() == Rule::process_body {
            for stmt in p.into_inner() {
                match stmt.as_rule() {
                    Rule::assignment => {
                        let (lhs, rhs) = assignment_from_pair(stmt)?;
                        out.push(Statement::Assignment(lhs, rhs));
                    }
                    Rule::expression => out.push(Statement::Expr(expr_from_pair(stmt)?)),
                    Rule::pre_stmt => out.push(Statement::Expr(expr_from_inner(stmt)?)),
                    Rule::post_stmt => out.push(Statement::Expr(expr_from_inner(stmt)?)),
                    _ => {}
                }
            }
        }
    }
    Ok(out)
}

fn data_field_from_pair(pair: Pair<Rule>) -> Result<DataField> {
    // data_field = { "$data" ~ ident ~ ":" ~ type_expr ~ constraint? ~ default_value? }
    let mut inner = pair.into_inner();
    let name = inner
        .next()
        .ok_or_else(|| anyhow!("data_field missing name"))?
        .as_str()
        .to_string();

    let mut ty: Option<TypeExpr> = None;
    let mut constraint: Option<Constraint> = None;
    let mut default: Option<Expr> = None;

    for p in inner {
        match p.as_rule() {
            Rule::generic_type | Rule::array_type | Rule::named_type => {
                ty = Some(type_from_pair(p)?);
            }
            Rule::range_constraint => {
                let mut it = p.into_inner();
                let lo = expr_from_pair(
                    it.next().ok_or_else(|| anyhow!("range missing lo"))?,
                )?;
                let hi = expr_from_pair(
                    it.next().ok_or_else(|| anyhow!("range missing hi"))?,
                )?;
                constraint = Some(Constraint::Range(lo, hi));
            }
            Rule::enum_constraint => {
                let mut values = Vec::new();
                for e in p.into_inner() {
                    if e.as_rule() == Rule::expression {
                        values.push(expr_from_pair(e)?);
                    }
                }
                constraint = Some(Constraint::EnumSet(values));
            }
            Rule::default_value => {
                for e in p.into_inner() {
                    if e.as_rule() == Rule::expression {
                        default = Some(expr_from_pair(e)?);
                    }
                }
            }
            _ => {}
        }
    }

    Ok(DataField {
        name,
        ty: ty.ok_or_else(|| anyhow!("data_field missing type"))?,
        constraint,
        default,
    })
}

// ============================================================
// TYPES
// ============================================================

fn type_from_pair(pair: Pair<Rule>) -> Result<TypeExpr> {
    match pair.as_rule() {
        Rule::named_type => {
            let ident = pair
                .into_inner()
                .next()
                .ok_or_else(|| anyhow!("named_type missing ident"))?;
            Ok(TypeExpr::Named(ident.as_str().to_string()))
        }
        Rule::generic_type => {
            let mut it = pair.into_inner();
            let name = it
                .next()
                .ok_or_else(|| anyhow!("generic_type missing name"))?
                .as_str()
                .to_string();
            let inner_ty_pair = it
                .next()
                .ok_or_else(|| anyhow!("generic_type missing inner type"))?;
            Ok(TypeExpr::Generic(name, Box::new(type_from_pair(inner_ty_pair)?)))
        }
        Rule::array_type => {
            let mut it = pair.into_inner();
            let inner_ty_pair = it
                .next()
                .ok_or_else(|| anyhow!("array_type missing inner"))?;
            let size = it.find(|p| p.as_rule() == Rule::number).and_then(|p| p.as_str().parse::<usize>().ok());
            Ok(TypeExpr::Array(
                Box::new(type_from_pair(inner_ty_pair)?),
                size,
            ))
        }
        other => Err(anyhow!("unexpected type rule: {:?}", other)),
    }
}

// ============================================================
// STATEMENTS
// ============================================================

fn assignment_from_pair(pair: Pair<Rule>) -> Result<(String, Expr)> {
    // assignment = { dotted_path_or_ident ~ "=" ~ expression }
    let mut inner = pair.into_inner();
    let lhs_pair = inner
        .next()
        .ok_or_else(|| anyhow!("assignment missing lhs"))?;
    let lhs = lhs_pair.as_str().to_string();
    let rhs = expr_from_pair(
        inner
            .next()
            .ok_or_else(|| anyhow!("assignment missing rhs"))?,
    )?;
    Ok((lhs, rhs))
}

fn description_from_pair(pair: Pair<Rule>) -> Result<String> {
    let inner = pair
        .into_inner()
        .next()
        .ok_or_else(|| anyhow!("description missing literal"))?;
    Ok(strip_quotes(inner.as_str()))
}

fn strip_quotes(s: &str) -> String {
    let t = s.trim();
    if t.len() >= 2 && t.starts_with('"') && t.ends_with('"') {
        t[1..t.len() - 1].to_string()
    } else {
        t.to_string()
    }
}

fn expr_from_inner(pair: Pair<Rule>) -> Result<Expr> {
    // For *_stmt rules that wrap a single expression.
    let inner = pair
        .into_inner()
        .find(|p| p.as_rule() == Rule::expression)
        .ok_or_else(|| anyhow!("stmt missing expression"))?;
    expr_from_pair(inner)
}

// ============================================================
// TYPED FIELDS / META
// ============================================================

fn typed_field_list_from_pair(pair: Pair<Rule>) -> Result<Vec<TypedField>> {
    let mut out = Vec::new();
    for p in pair.into_inner() {
        if p.as_rule() == Rule::typed_field {
            let mut it = p.into_inner();
            let name = it
                .next()
                .ok_or_else(|| anyhow!("typed_field missing name"))?
                .as_str()
                .to_string();
            let ty_pair = it
                .next()
                .ok_or_else(|| anyhow!("typed_field missing type"))?;
            out.push(TypedField {
                name,
                ty: type_from_pair(ty_pair)?,
            });
        }
    }
    Ok(out)
}

fn meta_pair_list_from_pair(pair: Pair<Rule>) -> Result<Vec<MetaPair>> {
    let mut out = Vec::new();
    for p in pair.into_inner() {
        if p.as_rule() == Rule::meta_pair {
            let mut it = p.into_inner();
            let key = it
                .next()
                .ok_or_else(|| anyhow!("meta_pair missing key"))?
                .as_str()
                .to_string();
            let val_pair = it
                .next()
                .ok_or_else(|| anyhow!("meta_pair missing value"))?;
            out.push(MetaPair {
                key,
                value: expr_from_pair(val_pair)?,
            });
        }
    }
    Ok(out)
}

// ============================================================
// EXPRESSIONS — fold the precedence-climbing chain
// ============================================================

fn expr_from_pair(pair: Pair<Rule>) -> Result<Expr> {
    match pair.as_rule() {
        Rule::expression => {
            let inner = pair
                .into_inner()
                .next()
                .ok_or_else(|| anyhow!("expression empty"))?;
            expr_from_pair(inner)
        }
        Rule::pipe_expr => {
            // pipe_expr = { or_expr ~ ("|>" ~ pipe_stage)* }
            // If there are no pipe stages, pass through to the or_expr.
            // If there are stages, build Expr::Pipe { head, stages }.
            let children: Vec<Pair<Rule>> = pair.into_inner().collect();
            // First child is always the or_expr (the head).
            let mut iter = children.into_iter();
            let head_pair = iter.next().ok_or_else(|| anyhow!("pipe_expr empty"))?;
            let head = expr_from_pair(head_pair)?;
            // Remaining children alternate: pipe_stage pairs ("|>" is silent/not captured)
            let stages: Result<Vec<PipeStage>> = iter
                .filter(|p| p.as_rule() == Rule::pipe_stage)
                .map(pipe_stage_from_pair)
                .collect();
            let stages = stages?;
            if stages.is_empty() {
                Ok(head)
            } else {
                Ok(Expr::Pipe {
                    head: Box::new(head),
                    stages,
                })
            }
        }
        Rule::or_expr => fold_binop_token(pair, "or"),
        Rule::and_expr => fold_binop_token(pair, "and"),
        Rule::cmp_expr => fold_binop_with_op(pair, Rule::cmp_op),
        Rule::add_expr => fold_binop_with_op(pair, Rule::add_op),
        Rule::mul_expr => fold_binop_with_op(pair, Rule::mul_op),
        Rule::temporal_expr => unary_temporal(pair),
        Rule::not_expr => {
            let inner = pair
                .into_inner()
                .next()
                .ok_or_else(|| anyhow!("not_expr empty"))?;
            Ok(Expr::UnaryOp("not".into(), Box::new(expr_from_pair(inner)?)))
        }
        Rule::paren_expr => {
            let inner = pair
                .into_inner()
                .next()
                .ok_or_else(|| anyhow!("paren_expr empty"))?;
            expr_from_pair(inner)
        }
        Rule::array_expr => {
            // Encode as FnCall("__array", items) since there's no dedicated variant.
            let items: Result<Vec<Expr>> =
                pair.into_inner().map(expr_from_pair).collect();
            Ok(Expr::FnCall("__array".into(), items?))
        }
        Rule::for_all_expr => for_all_stmt_to_expr(pair),
        Rule::number_expr => {
            let s = pair.as_str();
            let n = s.parse::<f64>().map_err(|e| anyhow!("bad number {s}: {e}"))?;
            Ok(Expr::Number(n))
        }
        Rule::string_expr => Ok(Expr::StringLit(strip_quotes(pair.as_str()))),
        Rule::true_expr => Ok(Expr::Bool(true)),
        Rule::false_expr => Ok(Expr::Bool(false)),
        Rule::path_call_expr => path_call_from_pair(pair),
        Rule::var_ref => {
            // var_ref = ${ "@" ~ ident }
            // The ident inner pair gives the name (without the "@").
            let name = pair
                .into_inner()
                .find(|p| p.as_rule() == Rule::ident)
                .map(|p| p.as_str().to_string())
                .unwrap_or_default();
            Ok(Expr::ParamRef {
                kind: RefKind::Var,
                name,
                path: Vec::new(),
                index: None,
                nested: None,
            })
        }
        Rule::prop_ref => {
            // prop_ref = { "[" ~ ident ~ ("." ~ ident)+ ~ "]" }
            // Inner pairs: all ident children — first is the head name, rest are path.
            let mut idents: Vec<String> = pair
                .into_inner()
                .filter(|p| p.as_rule() == Rule::ident)
                .map(|p| p.as_str().to_string())
                .collect();
            if idents.is_empty() {
                return Err(anyhow!("prop_ref has no idents"));
            }
            let name = idents.remove(0);
            Ok(Expr::ParamRef {
                kind: RefKind::Prop,
                name,
                path: idents,
                index: None,
                nested: None,
            })
        }
        Rule::idx_ref => {
            // idx_ref = ${ "#" ~ ident ~ "[" ~ number ~ "]" }
            // Collect all inner pairs up-front so we can scan for both ident and number.
            let children: Vec<Pair<Rule>> = pair.into_inner().collect();
            let name = children
                .iter()
                .find(|p| p.as_rule() == Rule::ident)
                .map(|p| p.as_str().to_string())
                .unwrap_or_default();
            let index = children
                .iter()
                .find(|p| p.as_rule() == Rule::number)
                .and_then(|p| p.as_str().parse::<i64>().ok());
            Ok(Expr::ParamRef {
                kind: RefKind::Idx,
                name,
                path: Vec::new(),
                index,
                nested: None,
            })
        }
        Rule::nested_ref => {
            // nested_ref = { "{" ~ expression ~ "}" }
            let inner_expr = pair
                .into_inner()
                .find(|p| p.as_rule() == Rule::expression)
                .ok_or_else(|| anyhow!("nested_ref missing expression"))?;
            let expr = expr_from_pair(inner_expr)?;
            Ok(Expr::ParamRef {
                kind: RefKind::Nested,
                name: String::new(),
                path: Vec::new(),
                index: None,
                nested: Some(Box::new(expr)),
            })
        }
        Rule::number => {
            let n = pair
                .as_str()
                .parse::<f64>()
                .map_err(|e| anyhow!("bad number: {e}"))?;
            Ok(Expr::Number(n))
        }
        Rule::ident => Ok(Expr::Ident(pair.as_str().to_string())),
        Rule::string_literal => Ok(Expr::StringLit(strip_quotes(pair.as_str()))),
        other => Err(anyhow!("unexpected expr rule: {:?}", other)),
    }
}

/// Left-fold a chain like `a op b op c` where `op` is a literal keyword
/// rule (not captured in the token stream). pest emits just the operand
/// pairs in that case, so we glue them with the supplied operator string.
fn fold_binop_token(pair: Pair<Rule>, op: &str) -> Result<Expr> {
    let mut iter = pair.into_inner();
    let first = iter
        .next()
        .ok_or_else(|| anyhow!("binop chain empty"))?;
    let mut result = expr_from_pair(first)?;
    for rhs_pair in iter {
        let rhs = expr_from_pair(rhs_pair)?;
        result = Expr::BinOp(Box::new(result), op.to_string(), Box::new(rhs));
    }
    Ok(result)
}

/// Left-fold a chain like `a OP b OP c` where OP is an explicit captured
/// rule (cmp_op / add_op / mul_op). Operand and op pairs alternate.
fn fold_binop_with_op(pair: Pair<Rule>, op_rule: Rule) -> Result<Expr> {
    let pairs: Vec<Pair<Rule>> = pair.into_inner().collect();
    if pairs.is_empty() {
        return Err(anyhow!("binop chain empty"));
    }
    let mut iter = pairs.into_iter();
    let first = iter.next().unwrap();
    let mut result = expr_from_pair(first)?;
    loop {
        let op_pair = match iter.next() {
            Some(p) => p,
            None => break,
        };
        if op_pair.as_rule() != op_rule {
            // Should not happen with a well-formed chain.
            return Err(anyhow!(
                "expected {:?}, got {:?}",
                op_rule,
                op_pair.as_rule()
            ));
        }
        let op = op_pair.as_str().to_string();
        let rhs_pair = iter
            .next()
            .ok_or_else(|| anyhow!("binop missing rhs"))?;
        let rhs = expr_from_pair(rhs_pair)?;
        result = Expr::BinOp(Box::new(result), op, Box::new(rhs));
    }
    Ok(result)
}

fn unary_temporal(pair: Pair<Rule>) -> Result<Expr> {
    let mut iter = pair.into_inner();
    let op_pair = iter
        .next()
        .ok_or_else(|| anyhow!("temporal missing op"))?;
    let op = op_pair.as_str().to_string();
    let rhs_pair = iter
        .next()
        .ok_or_else(|| anyhow!("temporal missing operand"))?;
    Ok(Expr::UnaryOp(op, Box::new(expr_from_pair(rhs_pair)?)))
}

fn path_call_from_pair(pair: Pair<Rule>) -> Result<Expr> {
    // path_call_expr = ${ ident ~ ("." ~ ident)* ~ call_tail? }
    // call_tail      = !{ "(" ~ (expression ~ ("," ~ expression)*)? ~ ")" }
    let mut idents = Vec::new();
    let mut call_args: Option<Vec<Expr>> = None;

    for p in pair.into_inner() {
        match p.as_rule() {
            Rule::ident => idents.push(p.as_str().to_string()),
            Rule::call_tail => {
                let args: Result<Vec<Expr>> = p
                    .into_inner()
                    .filter(|q| q.as_rule() == Rule::expression)
                    .map(expr_from_pair)
                    .collect();
                call_args = Some(args?);
            }
            _ => {}
        }
    }

    if idents.is_empty() {
        return Err(anyhow!("path_call with no ident"));
    }

    match call_args {
        Some(args) => {
            // foo(args) or foo.bar.baz(args) — collapse path into a single name
            let name = idents.join(".");
            Ok(Expr::FnCall(name, args))
        }
        None => {
            if idents.len() == 1 {
                Ok(Expr::Ident(idents.into_iter().next().unwrap()))
            } else {
                Ok(Expr::DottedPath(idents))
            }
        }
    }
}

fn pipe_stage_from_pair(pair: Pair<Rule>) -> Result<PipeStage> {
    // pipe_stage = { pipe_fn_ident ~ call_tail? }
    // pipe_fn_ident is @-atomic — its text is the full kebab-case name (e.g., "text-to-lower").
    let mut name = String::new();
    let mut args: Vec<Expr> = Vec::new();

    for p in pair.into_inner() {
        match p.as_rule() {
            Rule::pipe_fn_ident => {
                name = p.as_str().to_string();
            }
            Rule::call_tail => {
                args = p
                    .into_inner()
                    .filter(|q| q.as_rule() == Rule::expression)
                    .map(expr_from_pair)
                    .collect::<Result<Vec<_>>>()?;
            }
            _ => {}
        }
    }

    if name.is_empty() {
        return Err(anyhow!("pipe_stage missing function name"));
    }

    Ok(PipeStage { name, args })
}

// ============================================================
// TESTS
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_empty_file() {
        let f = parse("").unwrap();
        assert_eq!(f.items.len(), 0);
    }

    #[test]
    fn parses_import() {
        let f = parse("import stdlib.types").unwrap();
        assert_eq!(f.imports.len(), 1);
        assert_eq!(f.imports[0].0, vec!["stdlib", "types"]);
    }

    #[test]
    fn parses_minimal_class() {
        let src = r#"
            class Vehicle {
                $data speed: Float = 0
                @in{ throttle: Float }
                #process[strategy: code]{
                    pre: speed >= 0
                    speed' = speed + throttle
                    post: speed >= 0
                }
                @out[]{ speed: Float }
                invariant: speed >= 0
            }
        "#;
        let f = parse(src).unwrap();
        assert_eq!(f.items.len(), 1);
        match &f.items[0] {
            Item::Class(e) => {
                assert_eq!(e.name, "Vehicle");
                assert_eq!(e.data_fields.len(), 1);
                assert_eq!(e.processes.len(), 1);
                assert_eq!(e.processes[0].preconditions.len(), 1);
                assert_eq!(e.processes[0].postconditions.len(), 1);
                assert_eq!(e.processes[0].body.len(), 1);
                assert_eq!(e.invariants.len(), 1);
            }
            _ => panic!("expected class"),
        }
    }

    #[test]
    fn parses_binop_chain() {
        let src = r#"
            class C {
                #process[strategy: code]{
                    x = a + b * c + d
                }
            }
        "#;
        let f = parse(src).unwrap();
        // Just assert it parses — structure validated by ark_parser tests too.
        assert_eq!(f.items.len(), 1);
    }

    // ============================================================
    // Indices: classes / instances / island_classes
    // ============================================================

    #[test]
    fn top_level_classes_indexed() {
        let src = r#"
            abstraction Movable { @in{ dt: Float } }
            class Car : Movable { $data speed: Float = 0 }
            class Plane : Movable { $data altitude: Float = 0 }
        "#;
        let f = parse(src).unwrap();
        // Two top-level classes; the abstraction is NOT in classes_index.
        assert_eq!(f.classes_index.len(), 2);
        assert!(f.classes_index.contains_key("Car"));
        assert!(f.classes_index.contains_key("Plane"));
        assert!(!f.classes_index.contains_key("Movable"));
        // Accessor helper resolves to the actual EntityDef.
        let car = f.class("Car").expect("Car should resolve");
        assert_eq!(car.name, "Car");
    }

    #[test]
    fn instances_grouped_by_class_name_in_source_order() {
        let src = r#"
            class Vehicle { $data fuel: Float = 50 }
            instance V1 : Vehicle { fuel = 10 }
            instance V2 : Vehicle { fuel = 20 }
            instance V3 : Vehicle { fuel = 30 }
        "#;
        let f = parse(src).unwrap();
        let vs = f.instances_of("Vehicle");
        assert_eq!(vs.len(), 3);
        let names: Vec<&str> = vs.iter().map(|i| i.name.as_str()).collect();
        assert_eq!(names, vec!["V1", "V2", "V3"]); // source order
    }

    #[test]
    fn orphan_instance_still_indexed() {
        let src = r#"
            class Known { $data x: Int = 0 }
            instance K : Known { x = 1 }
            instance Orphan : Ghost { }
        "#;
        let f = parse(src).unwrap();
        // Known class indexed; Ghost is not (never declared).
        assert!(f.classes_index.contains_key("Known"));
        assert!(!f.classes_index.contains_key("Ghost"));
        // But the orphan instance is still grouped under "Ghost".
        let orphans = f.instances_of("Ghost");
        assert_eq!(orphans.len(), 1);
        assert_eq!(orphans[0].name, "Orphan");
        // Known instances indexed alongside.
        assert_eq!(f.instances_of("Known").len(), 1);
    }

    // ============================================================
    // Pipe expressions
    // ============================================================

    #[test]
    fn parses_pipe_expr_single_stage() {
        let src = r#"
            class C {
                #process[strategy: code]{
                    result = value |> text-to-lower
                }
            }
        "#;
        let f = parse(src).unwrap();
        assert_eq!(f.items.len(), 1);
        if let Item::Class(e) = &f.items[0] {
            if let Some(Statement::Assignment(_, expr)) = e.processes[0].body.first() {
                assert!(matches!(expr, Expr::Pipe { .. }), "expected Pipe, got {:?}", expr);
                if let Expr::Pipe { stages, .. } = expr {
                    assert_eq!(stages.len(), 1);
                    assert_eq!(stages[0].name, "text-to-lower");
                }
            } else {
                panic!("expected assignment statement");
            }
        } else {
            panic!("expected class");
        }
    }

    #[test]
    fn parses_pipe_expr_multi_stage() {
        let src = r#"
            class C {
                #process[strategy: code]{
                    result = value |> text-to-lower |> trim
                }
            }
        "#;
        let f = parse(src).unwrap();
        if let Item::Class(e) = &f.items[0] {
            if let Some(Statement::Assignment(_, expr)) = e.processes[0].body.first() {
                if let Expr::Pipe { head: _, stages } = expr {
                    assert_eq!(stages.len(), 2);
                    assert_eq!(stages[0].name, "text-to-lower");
                    assert_eq!(stages[1].name, "trim");
                } else {
                    panic!("expected Pipe");
                }
            } else {
                panic!("expected assignment");
            }
        }
    }

    // ============================================================
    // Parameter references
    // ============================================================

    #[test]
    fn parses_var_ref() {
        let src = r#"
            class C {
                #process[strategy: code]{
                    check = @myVar
                }
            }
        "#;
        let f = parse(src).unwrap();
        if let Item::Class(e) = &f.items[0] {
            if let Some(Statement::Assignment(_, expr)) = e.processes[0].body.first() {
                if let Expr::ParamRef { kind, name, .. } = expr {
                    assert!(matches!(kind, RefKind::Var));
                    assert_eq!(name, "myVar");
                } else {
                    panic!("expected ParamRef(Var), got {:?}", expr);
                }
            }
        }
    }

    #[test]
    fn parses_prop_ref() {
        let src = r#"
            class C {
                #process[strategy: code]{
                    check = [obj.field.sub]
                }
            }
        "#;
        let f = parse(src).unwrap();
        if let Item::Class(e) = &f.items[0] {
            if let Some(Statement::Assignment(_, expr)) = e.processes[0].body.first() {
                if let Expr::ParamRef { kind, name, path, .. } = expr {
                    assert!(matches!(kind, RefKind::Prop));
                    assert_eq!(name, "obj");
                    assert_eq!(path, &vec!["field".to_string(), "sub".to_string()]);
                } else {
                    panic!("expected ParamRef(Prop), got {:?}", expr);
                }
            }
        }
    }

    // ============================================================
    // Expression / Predicate items
    // ============================================================

    #[test]
    fn parses_expression_def() {
        let src = r#"
            expression NormalizeText {
                in: val: String
                out: String
                chain: val |> text-to-lower |> trim
            }
        "#;
        let f = parse(src).unwrap();
        assert_eq!(f.items.len(), 1);
        match &f.items[0] {
            Item::Expression(def) => {
                assert_eq!(def.name, "NormalizeText");
                assert_eq!(def.inputs.len(), 1);
                assert_eq!(def.inputs[0].name, "val");
                assert!(matches!(def.output, TypeExpr::Named(_)));
                assert!(matches!(def.chain, Expr::Pipe { .. }));
            }
            other => panic!("expected Expression item, got {:?}", other),
        }
    }

    #[test]
    fn parses_predicate_def() {
        let src = r#"
            predicate IsPositive {
                in: val: Float
                check: val > 0
            }
        "#;
        let f = parse(src).unwrap();
        assert_eq!(f.items.len(), 1);
        match &f.items[0] {
            Item::Predicate(def) => {
                assert_eq!(def.name, "IsPositive");
                assert_eq!(def.inputs.len(), 1);
                assert_eq!(def.inputs[0].name, "val");
                assert!(matches!(def.check, Expr::BinOp(..)));
            }
            other => panic!("expected Predicate item, got {:?}", other),
        }
    }

    #[test]
    fn expression_index_last_wins_on_duplicate() {
        let src = r#"
            expression Foo {
                in: x: Int
                out: Int
                chain: x
            }
            expression Foo {
                in: y: Float
                out: Float
                chain: y
            }
        "#;
        let f = parse(src).unwrap();
        assert_eq!(f.items.len(), 2);
        // Last-wins: index points to index 1 (the second Foo).
        let idx = f.expression_index.get("Foo").copied().expect("Foo indexed");
        assert_eq!(idx, 1);
    }

    #[test]
    fn island_classes_live_in_separate_per_island_map() {
        let src = r#"
            class Task { $data status: String = "todo" }
            island Backlog {
                strategy: script
                class Task { $data status: String = "done" }
            }
            island Other {
                strategy: code
                class Helper { $data count: Int = 0 }
            }
        "#;
        let f = parse(src).unwrap();
        // Top-level Task is present and not shadowed by Backlog's nested Task.
        assert!(f.classes_index.contains_key("Task"));
        // Helper (island-scoped) is NOT in the top-level index.
        assert!(!f.classes_index.contains_key("Helper"));
        // Per-island index has both islands.
        assert_eq!(f.island_classes_index.len(), 2);
        let backlog = f
            .island_classes_index
            .get("Backlog")
            .expect("Backlog island indexed");
        assert!(backlog.contains_key("Task"));
        let other = f
            .island_classes_index
            .get("Other")
            .expect("Other island indexed");
        assert!(other.contains_key("Helper"));
    }

    // ============================================================
    // JSON round-trip tests — parse → serialize → deserialize → assert_eq
    // These ensure Rust AST and Python parser can interop via JSON.
    // ============================================================

    #[test]
    fn pipe_expr_json_roundtrip() {
        let src = r#"
            class C {
                #process[strategy: code]{
                    result = x |> abs
                }
            }
        "#;
        let f = parse(src).unwrap();
        let json = serde_json::to_string(&f).unwrap();
        let f2: ArkFile = serde_json::from_str(&json).unwrap();
        assert_eq!(format!("{:?}", f), format!("{:?}", f2));
    }

    #[test]
    fn pipe_multi_stage_json_roundtrip() {
        let src = r#"
            class C {
                #process[strategy: code]{
                    result = x |> abs |> neg
                }
            }
        "#;
        let f = parse(src).unwrap();
        let json = serde_json::to_string(&f).unwrap();
        let f2: ArkFile = serde_json::from_str(&json).unwrap();
        assert_eq!(format!("{:?}", f), format!("{:?}", f2));
    }

    #[test]
    fn param_ref_var_json_roundtrip() {
        let src = r#"
            class C {
                #process[strategy: code]{
                    check = @myVar
                }
            }
        "#;
        let f = parse(src).unwrap();
        let json = serde_json::to_string(&f).unwrap();
        let f2: ArkFile = serde_json::from_str(&json).unwrap();
        assert_eq!(format!("{:?}", f), format!("{:?}", f2));
    }

    #[test]
    fn param_ref_prop_json_roundtrip() {
        let src = r#"
            class C {
                #process[strategy: code]{
                    check = [obj.field]
                }
            }
        "#;
        let f = parse(src).unwrap();
        let json = serde_json::to_string(&f).unwrap();
        let f2: ArkFile = serde_json::from_str(&json).unwrap();
        assert_eq!(format!("{:?}", f), format!("{:?}", f2));
    }

    #[test]
    fn expression_def_json_roundtrip() {
        let src = r#"
            expression NormalizeText {
                in: val: String
                out: String
                chain: val |> text-to-lower |> trim
            }
        "#;
        let f = parse(src).unwrap();
        let json = serde_json::to_string(&f).unwrap();
        let f2: ArkFile = serde_json::from_str(&json).unwrap();
        assert_eq!(format!("{:?}", f), format!("{:?}", f2));
    }

    #[test]
    fn predicate_def_json_roundtrip() {
        let src = r#"
            predicate IsPositive {
                in: val: Float
                check: val > 0
            }
        "#;
        let f = parse(src).unwrap();
        let json = serde_json::to_string(&f).unwrap();
        let f2: ArkFile = serde_json::from_str(&json).unwrap();
        assert_eq!(format!("{:?}", f), format!("{:?}", f2));
    }
}
