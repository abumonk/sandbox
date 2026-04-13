use pest_derive::Parser;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub mod parse;

#[derive(Parser)]
#[grammar = "grammar/ark.pest"]
pub struct ArkParser;

// ============================================================
// AST — Abstract Syntax Tree для .ark файлов
// ============================================================

/// Корень AST — один .ark файл.
///
/// The indices below (`classes_index`, `instances_index`, `island_classes_index`)
/// are built in `parse::build_indices` after items are assembled. They store
/// usize offsets into `items` (or into `IslandDef.classes` for island-scoped
/// classes) so lookups are O(log n) without cloning AST nodes.
///
/// `items` is the source of truth — the indices are pure-additive derived data.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ArkFile {
    pub imports: Vec<ImportPath>,
    pub items: Vec<Item>,
    /// Top-level classes only: class name → index into `items`.
    #[serde(default)]
    pub classes_index: BTreeMap<String, usize>,
    /// Instances grouped by declared `class_name`: class name → indices into `items`.
    /// Orphan instances (class_name not declared at top level) are still indexed —
    /// callers can detect them by checking `classes_index`.
    #[serde(default)]
    pub instances_index: BTreeMap<String, Vec<usize>>,
    /// Per-island nested classes: island name → (class name → index into that
    /// island's `classes` vector). Kept separate from `classes_index` to avoid
    /// name collisions between top-level and island-scoped classes.
    #[serde(default)]
    pub island_classes_index: BTreeMap<String, BTreeMap<String, usize>>,
}

impl ArkFile {
    /// Return references to all `InstanceDef`s declared for `class_name`.
    /// Empty iterator if none declared. Preserves source order.
    pub fn instances_of<'a>(&'a self, class_name: &str) -> Vec<&'a InstanceDef> {
        let Some(ids) = self.instances_index.get(class_name) else {
            return Vec::new();
        };
        ids.iter()
            .filter_map(|i| match self.items.get(*i) {
                Some(Item::Instance(inst)) => Some(inst),
                _ => None,
            })
            .collect()
    }

    /// Return a reference to the top-level class `name`, if present.
    pub fn class(&self, name: &str) -> Option<&EntityDef> {
        let idx = *self.classes_index.get(name)?;
        match self.items.get(idx)? {
            Item::Class(def) => Some(def),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportPath(pub Vec<String>);

/// Верхнеуровневый элемент
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "kind")]
pub enum Item {
    Abstraction(EntityDef),
    Class(EntityDef),
    Instance(InstanceDef),
    Island(IslandDef),
    Bridge(BridgeDef),
    Registry(RegistryDef),
    Verify(VerifyDef),
}

// ============================================================
// ЧЕТЫРЕ ПРИМИТИВА
// ============================================================

/// @in{} — входной порт
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InPort {
    pub fields: Vec<TypedField>,
}

/// @out[] — выходной порт
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutPort {
    pub meta: Vec<MetaPair>,
    pub fields: Vec<TypedField>,
}

/// #process[]{} — правило обработки
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessRule {
    pub meta: Vec<MetaPair>,
    pub preconditions: Vec<Expr>,
    pub postconditions: Vec<Expr>,
    pub body: Vec<Statement>,
    pub description: Option<String>,
}

/// $data — поле данных
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataField {
    pub name: String,
    pub ty: TypeExpr,
    pub constraint: Option<Constraint>,
    pub default: Option<Expr>,
}

// ============================================================
// СУЩНОСТИ
// ============================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityDef {
    pub name: String,
    pub inherits: Vec<String>,
    pub data_fields: Vec<DataField>,
    pub in_ports: Vec<InPort>,
    pub out_ports: Vec<OutPort>,
    pub processes: Vec<ProcessRule>,
    pub invariants: Vec<Expr>,
    pub temporals: Vec<Expr>,
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstanceDef {
    pub name: String,
    pub class_name: String,
    pub assignments: Vec<(String, Expr)>,
}

// ============================================================
// ОСТРОВА
// ============================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IslandDef {
    pub name: String,
    pub strategy: Option<String>,
    pub memory: Option<Vec<Statement>>,
    pub contains: Vec<String>,
    pub in_ports: Vec<InPort>,
    pub out_ports: Vec<OutPort>,
    pub processes: Vec<ProcessRule>,
    pub classes: Vec<EntityDef>,
    pub data_fields: Vec<DataField>,
    pub description: Option<String>,
}

// ============================================================
// МОСТЫ
// ============================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BridgeDef {
    pub name: String,
    pub from: String,
    pub to: String,
    pub contract: Option<ContractDef>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractDef {
    pub invariants: Vec<Expr>,
    pub temporals: Vec<Expr>,
}

// ============================================================
// РЕЕСТР И ВЕРИФИКАЦИЯ
// ============================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegistryDef {
    pub name: String,
    pub entries: Vec<RegistryEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegistryEntry {
    pub name: String,
    pub meta: Vec<MetaPair>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerifyDef {
    pub target: String,
    pub checks: Vec<CheckDef>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckDef {
    pub name: String,
    pub expr: Expr,
}

// ============================================================
// ТИПЫ И ВЫРАЖЕНИЯ
// ============================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TypeExpr {
    Named(String),
    Generic(String, Box<TypeExpr>),
    Array(Box<TypeExpr>, Option<usize>),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Constraint {
    Range(Expr, Expr),
    EnumSet(Vec<Expr>),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Expr {
    Ident(String),
    Number(f64),
    StringLit(String),
    Bool(bool),
    DottedPath(Vec<String>),
    BinOp(Box<Expr>, String, Box<Expr>),
    UnaryOp(String, Box<Expr>),
    FnCall(String, Vec<Expr>),
    ForAll {
        ty: String,
        var: String,
        condition: Option<Box<Expr>>,
        body: Vec<Statement>,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Statement {
    Assignment(String, Expr),
    Invariant(Expr),
    Temporal(Expr),
    Process(ProcessRule),
    Expr(Expr),
    Description(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TypedField {
    pub name: String,
    pub ty: TypeExpr,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetaPair {
    pub key: String,
    pub value: Expr,
}

// ============================================================
// PARSER API (placeholder — will be implemented with pest)
// ============================================================

pub fn parse_ark_file(input: &str) -> anyhow::Result<ArkFile> {
    parse::parse(input)
}

/// Serialize AST to JSON (for interop with other tools)
pub fn ast_to_json(file: &ArkFile) -> anyhow::Result<String> {
    Ok(serde_json::to_string_pretty(file)?)
}

/// Deserialize AST from JSON
pub fn json_to_ast(json: &str) -> anyhow::Result<ArkFile> {
    Ok(serde_json::from_str(json)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_file_parses() {
        let result = parse_ark_file("");
        assert!(result.is_ok());
    }

    #[test]
    fn ast_roundtrips_json() {
        let file = ArkFile {
            imports: vec![ImportPath(vec!["stdlib".into(), "types".into()])],
            items: vec![],
            ..Default::default()
        };
        let json = ast_to_json(&file).unwrap();
        let back = json_to_ast(&json).unwrap();
        assert_eq!(back.imports.len(), 1);
    }
}
