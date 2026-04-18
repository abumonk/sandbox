# Validation Coverage Matrix — ADV-001..008 → ADV-011 Unified Designs

## Source

Harvested from ADV-001..008 using regex `^\| TC-\d+ \|` per the harvest procedure in
`designs/ADV011-T009-design.md`. Row verdicts assigned by reading `research/descriptor-delta.md`,
`research/builder-delta.md`, `research/controller-delta.md`, `research/pruning-catalog.md`.

**Harvest counts (re-grepped at write time):**
- ADV-001 manifest: 30 rows
- ADV-002 test-strategy: 28 rows
- ADV-003 test-strategy: 29 rows (design expected 35; 6-row discrepancy — see validation-report.md § Open gaps)
- ADV-004 manifest: 46 rows
- ADV-005 manifest: 44 rows
- ADV-006 manifest: 37 rows
- ADV-007 manifest: 34 rows
- ADV-008 manifest: 24 rows
- **Total: 272 rows**

---

## Coverage Matrix

| tc_id | source_adventure | source_description | verdict | citation |
|-------|------------------|--------------------|---------|----------|
| ADV-001 TC-001 | ADV-001 | .ark files can declare expression Name { in, out, chain } items producing Item::Expression | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-001 TC-002 | ADV-001 | .ark files can declare predicate Name { in, check } items producing Item::Predicate | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-001 TC-003 | ADV-001 | \|> operator parses left-associative in any expression context | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-001 TC-004 | ADV-001 | Param-ref sigils @var, [a.b], #items[n], {nested} parse into tagged AST nodes | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-001 TC-005 | ADV-001 | Python and Rust parsers produce equivalent JSON AST for expression forms | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-001 TC-006 | ADV-001 | Kebab-case function names accepted only inside pipe stages | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-001 TC-007 | ADV-001 | expression / predicate top-level items reach AST with all fields populated | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-001 TC-008 | ADV-001 | Malformed expression/predicate items produce ArkParseError with file:line:col | DEFERRED-TO | ADV-DU |
| ADV-001 TC-009 | ADV-001 | import stdlib.expression and import stdlib.predicate resolve and populate the new indices | COVERED-BY | descriptor-delta.md#target-two-level-stdlib-layout |
| ADV-001 TC-010 | ADV-001 | Every v1 numeric expression has a valid EXPR_PRIMITIVES entry | COVERED-BY | builder-delta.md#shared-verify-passes |
| ADV-001 TC-011 | ADV-001 | Every v1 text expression has a valid EXPR_PRIMITIVES entry | COVERED-BY | builder-delta.md#shared-verify-passes |
| ADV-001 TC-012 | ADV-001 | Every v1 predicate parses with Bool-typed check: | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-001 TC-013 | ADV-001 | python ark.py verify translates numeric pipes into Z3 and returns PASS | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-001 TC-014 | ADV-001 | Predicate check: expressions participate in Z3 verify blocks | COVERED-BY | builder-delta.md#opaque_primitive |
| ADV-001 TC-015 | ADV-001 | Opaque primitives (regex, temporal, file-io) report PASS_OPAQUE not crash | COVERED-BY | builder-delta.md#opaque_primitive |
| ADV-001 TC-016 | ADV-001 | User-defined expressions inline in verifier when called from process bodies | COVERED-BY | builder-delta.md#opaque_primitive |
| ADV-001 TC-017 | ADV-001 | Unknown pipe stage produces error with fuzzy suggestions | DEFERRED-TO | ADV-DU |
| ADV-001 TC-018 | ADV-001 | ark.py codegen --target rust emits one pub fn per expression item | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-001 TC-019 | ADV-001 | Every numeric stdlib expression emits compilable Rust | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-001 TC-020 | ADV-001 | Every text stdlib expression emits compilable Rust | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-001 TC-021 | ADV-001 | Every predicate emits pub fn ... -> bool | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-001 TC-022 | ADV-001 | Inline pipes inside process bodies emit valid Rust | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-001 TC-023 | ADV-001 | C++ / Proto codegen raises NotImplementedError with follow-up adventure note | DEFERRED-TO | ADV-DU |
| ADV-001 TC-024 | ADV-001 | specs/test_expression.ark parses, verifies, and codegens end-to-end | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-001 TC-025 | ADV-001 | All new pytest files pass under pytest tests/ -q | DEFERRED-TO | ADV-DU |
| ADV-001 TC-026 | ADV-001 | cargo test -p ark-dsl passes all new Rust AST tests | DEFERRED-TO | ADV-DU |
| ADV-001 TC-027 | ADV-001 | specs/examples/expressif_examples.ark parses cleanly | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-001 TC-028 | ADV-001 | Line coverage for expression/predicate modules >= 80% | DEFERRED-TO | ADV-DU |
| ADV-001 TC-029 | ADV-001 | docs/DSL_SPEC.md documents expression/predicate subsystem | DEFERRED-TO | ADV-DU |
| ADV-001 TC-030 | ADV-001 | Backlog updated with adventure entry | DEFERRED-TO | ADV-DU |
| ADV-002 TC-001 | ADV-002 | code_graph.ark parses cleanly | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-002 TC-002 | ADV-002 | All struct fields use defined types | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-002 TC-003 | ADV-002 | Schema covers Function, Class, Method, Module, Parameter, Edge, Complexity | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-002 TC-004 | ADV-002 | specs/infra/code_graph.ark parses without errors | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-002 TC-005 | ADV-002 | CodeGraphIsland registered in root.ark SystemRegistry | DEFERRED-TO | ADV-DU |
| ADV-002 TC-006 | ADV-002 | Bridge between CodeGraphIsland and Orchestrator defined | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-002 TC-007 | ADV-002 | No-dangling-edges invariant expressed in verify block | COVERED-BY | builder-delta.md#reference_exists |
| ADV-002 TC-008 | ADV-002 | code_graph_queries.ark parses without errors | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-002 TC-009 | ADV-002 | All graph-* primitives registered in EXPR_PRIMITIVES | COVERED-BY | builder-delta.md#shared-verify-passes |
| ADV-002 TC-010 | ADV-002 | Graph query expressions compile to Rust via codegen | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-002 TC-011 | ADV-002 | Graph predicates verify via Z3 (PASS_OPAQUE) | COVERED-BY | builder-delta.md#opaque_primitive |
| ADV-002 TC-012 | ADV-002 | Python indexer extracts functions, classes, methods, imports | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-013 | ADV-002 | Rust indexer extracts functions, structs, impls, use statements | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-014 | ADV-002 | Ark adapter extracts entities, islands, bridges, expressions | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-015 | ADV-002 | Graph store supports add/query/serialize operations | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-016 | ADV-002 | Complexity calculator produces cyclomatic complexity for Python | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-017 | ADV-002 | ark codegraph index CLI subcommand works end-to-end | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-018 | ADV-002 | No-dangling-edges invariant checkable on concrete graph | COVERED-BY | builder-delta.md#reference_exists |
| ADV-002 TC-019 | ADV-002 | No-inheritance-cycles check works on concrete graph | COVERED-BY | builder-delta.md#dag_acyclicity |
| ADV-002 TC-020 | ADV-002 | Verification integrates with ark.py verify for code_graph.ark | COVERED-BY | builder-delta.md#shared-verify-passes |
| ADV-002 TC-021 | ADV-002 | ark codegraph graph produces a valid HTML file | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-022 | ADV-002 | HTML contains code-graph nodes with correct styling | DEFERRED-TO | ADV-UI |
| ADV-002 TC-023 | ADV-002 | LOD switching works in visualization | DEFERRED-TO | ADV-UI |
| ADV-002 TC-024 | ADV-002 | Self-indexing produces non-empty graph JSON | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-025 | ADV-002 | Graph contains nodes from all three languages (Python, Rust, .ark) | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-026 | ADV-002 | At least one query returns meaningful results on self-indexed graph | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-002 TC-027 | ADV-002 | Test strategy document exists and covers all TCs | DEFERRED-TO | ADV-DU |
| ADV-002 TC-028 | ADV-002 | All autotest TCs have passing tests | DEFERRED-TO | ADV-DU |
| ADV-003 TC-001 | ADV-003 | Lark grammar parses all 6 new item kinds without errors | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-003 TC-002 | ADV-003 | Pest grammar mirrors Lark for all 6 new item kinds | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-003 TC-003 | ADV-003 | Existing .ark files continue to parse after grammar changes (no regressions) | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-003 TC-004 | ADV-003 | Parser produces correct JSON AST for role_def items | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-003 TC-005 | ADV-003 | Parser produces correct JSON AST for studio_def items | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-003 TC-006 | ADV-003 | Parser produces correct JSON AST for command, hook, rule, template items | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-003 TC-007 | ADV-003 | ArkFile indices include roles, studios, commands dicts | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-003 TC-008 | ADV-003 | stdlib/studio.ark parses without errors via python ark.py parse | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-003 TC-009 | ADV-003 | All enum and struct definitions are well-formed and referenceable | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-003 TC-010 | ADV-003 | Escalation cycle detection catches cycles and passes acyclic hierarchies | COVERED-BY | builder-delta.md#dag_acyclicity |
| ADV-003 TC-011 | ADV-003 | Command verification catches missing roles and insufficient tools | COVERED-BY | builder-delta.md#reference_exists |
| ADV-003 TC-012 | ADV-003 | Hook event verification catches invalid event types | COVERED-BY | builder-delta.md#reference_exists |
| ADV-003 TC-013 | ADV-003 | Rule constraint satisfiability check works correctly | COVERED-BY | builder-delta.md#domain-specific-residue |
| ADV-003 TC-014 | ADV-003 | Tool permission cross-check detects violations | COVERED-BY | builder-delta.md#domain-specific-residue |
| ADV-003 TC-015 | ADV-003 | Agent .md files generated correctly from role items | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-003 TC-016 | ADV-003 | Command .md files generated correctly from command items | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-003 TC-017 | ADV-003 | Hook settings.json fragment generated correctly | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-003 TC-018 | ADV-003 | Template skeleton files generated correctly | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-003 TC-019 | ADV-003 | --target studio CLI flag works end-to-end | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-003 TC-020 | ADV-003 | ark.py parse specs/meta/ark_studio.ark exits 0 | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-003 TC-021 | ADV-003 | ark.py parse specs/meta/game_studio.ark exits 0 | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-003 TC-022 | ADV-003 | ark.py verify specs/meta/ark_studio.ark passes all studio checks | COVERED-BY | builder-delta.md#shared-verify-passes |
| ADV-003 TC-023 | ADV-003 | ark_studio.ark parses without errors and correctly models Ark's team | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-003 TC-024 | ADV-003 | game_studio.ark parses without errors with ~18 roles, ~20 commands | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-003 TC-025 | ADV-003 | Both studios pass escalation acyclicity verification | COVERED-BY | builder-delta.md#dag_acyclicity |
| ADV-003 TC-026 | ADV-003 | Both studios pass command-role resolution verification | COVERED-BY | builder-delta.md#reference_exists |
| ADV-003 TC-027 | ADV-003 | Both files are registered in root.ark | DEFERRED-TO | ADV-DU |
| ADV-003 TC-028 | ADV-003 | All autotest TCs have passing tests | DEFERRED-TO | ADV-DU |
| ADV-003 TC-029 | ADV-003 | All autotest TCs have passing tests (full suite) | DEFERRED-TO | ADV-DU |
| ADV-004 TC-001 | ADV-004 | evolution.ark parses without errors | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-004 TC-002 | ADV-004 | All enums/structs follow existing stdlib patterns | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-004 TC-003 | ADV-004 | Lark grammar parses all 7 evolution items | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-004 TC-004 | ADV-004 | Pest grammar mirrors Lark for all 7 items | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-004 TC-005 | ADV-004 | Existing .ark files parse after grammar changes | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-004 TC-006 | ADV-004 | Parser produces correct AST for 7 evolution types | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-004 TC-007 | ADV-004 | ArkFile indices populated for evolution items | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-004 TC-008 | ADV-004 | Dataset builder generates valid JSONL from synthetic | COVERED-BY | controller-delta.md#24-evaluator |
| ADV-004 TC-009 | ADV-004 | Dataset builder correctly assigns splits | COVERED-BY | controller-delta.md#24-evaluator |
| ADV-004 TC-010 | ADV-004 | Fitness scorer produces 0.0-1.0 scores per dimension | COVERED-BY | controller-delta.md#24-evaluator |
| ADV-004 TC-011 | ADV-004 | Aggregation methods compute correctly | COVERED-BY | controller-delta.md#24-evaluator |
| ADV-004 TC-012 | ADV-004 | evaluate_dataset returns mean fitness | COVERED-BY | controller-delta.md#24-evaluator |
| ADV-004 TC-013 | ADV-004 | Optimizer runs full loop for 2+ generations | COVERED-BY | controller-delta.md#25-evolution |
| ADV-004 TC-014 | ADV-004 | Pareto-front selection identifies non-dominated variants | COVERED-BY | controller-delta.md#25-evolution |
| ADV-004 TC-015 | ADV-004 | Convergence detection stops optimization | COVERED-BY | controller-delta.md#25-evolution |
| ADV-004 TC-016 | ADV-004 | MIPROv2 mode uses history-based selection | COVERED-BY | controller-delta.md#25-evolution |
| ADV-004 TC-017 | ADV-004 | Darwinian mode raises NotImplementedError | RETIRED-BY | pruning-catalog.md row 1 |
| ADV-004 TC-018 | ADV-004 | Size limit blocks variants exceeding threshold | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-004 TC-019 | ADV-004 | Size limit passes variants within threshold | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-004 TC-020 | ADV-004 | Semantic preservation uses judge callback | COVERED-BY | controller-delta.md#24-evaluator |
| ADV-004 TC-021 | ADV-004 | Caching compatibility checks prefix preservation | COVERED-BY | controller-delta.md#24-evaluator |
| ADV-004 TC-022 | ADV-004 | should_block returns True only for block failures | COVERED-BY | controller-delta.md#24-evaluator |
| ADV-004 TC-023 | ADV-004 | Runner executes full pipeline to EvolutionReport | COVERED-BY | controller-delta.md#25-evolution |
| ADV-004 TC-024 | ADV-004 | Runner resolves cross-references correctly | COVERED-BY | builder-delta.md#reference_exists |
| ADV-004 TC-025 | ADV-004 | Runner stops on block constraint violation | COVERED-BY | controller-delta.md#25-evolution |
| ADV-004 TC-026 | ADV-004 | CLI ark evolution run executes evolution | COVERED-BY | controller-delta.md#25-evolution |
| ADV-004 TC-027 | ADV-004 | CLI ark evolution status displays status | COVERED-BY | controller-delta.md#25-evolution |
| ADV-004 TC-028 | ADV-004 | Codegen produces valid JSONL templates | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-004 TC-029 | ADV-004 | Codegen produces Python scoring skeletons | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-004 TC-030 | ADV-004 | Codegen produces JSON config files | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-004 TC-031 | ADV-004 | ark codegen --target evolution works e2e | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-004 TC-032 | ADV-004 | Split ratio verification catches bad ratios | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-004 TC-033 | ADV-004 | Fitness weight verification catches bad weights | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-004 TC-034 | ADV-004 | Gate tolerance verification catches bad bounds | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-004 TC-035 | ADV-004 | Cross-reference verification catches unknowns | COVERED-BY | builder-delta.md#reference_exists |
| ADV-004 TC-036 | ADV-004 | ark verify runs evolution checks when present | COVERED-BY | builder-delta.md#shared-verify-passes |
| ADV-004 TC-037 | ADV-004 | Visualizer extracts evolution nodes and edges | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-004 TC-038 | ADV-004 | Generated HTML includes evolution color coding | DEFERRED-TO | ADV-UI |
| ADV-004 TC-039 | ADV-004 | ark graph renders evolution items | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-004 TC-040 | ADV-004 | evolution_skills.ark parses without errors | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-004 TC-041 | ADV-004 | evolution_roles.ark parses without errors | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-004 TC-042 | ADV-004 | Both reflexive specs pass verify | COVERED-BY | builder-delta.md#shared-verify-passes |
| ADV-004 TC-043 | ADV-004 | Both specs registered in root.ark | DEFERRED-TO | ADV-DU |
| ADV-004 TC-044 | ADV-004 | Codegen generates from reflexive specs | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-004 TC-045 | ADV-004 | Test strategy document complete | DEFERRED-TO | ADV-DU |
| ADV-004 TC-046 | ADV-004 | All automated tests pass | DEFERRED-TO | ADV-DU |
| ADV-005 TC-001 | ADV-005 | stdlib/agent.ark parses without errors | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-005 TC-002 | ADV-005 | All agent enum/struct definitions well-formed and referenceable | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-005 TC-003 | ADV-005 | Lark grammar parses all 8 new agent item types | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-005 TC-004 | ADV-005 | Pest grammar mirrors all 8 new Lark rules | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-005 TC-005 | ADV-005 | Parser produces correct AST dataclasses for each agent item | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-005 TC-006 | ADV-005 | ArkFile indices populated for all 8 agent item types | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-005 TC-007 | ADV-005 | Existing .ark files still parse without regression | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-005 TC-008 | ADV-005 | Gateway normalizes terminal input to Message dataclass | COVERED-BY | controller-delta.md#21-gateway |
| ADV-005 TC-009 | ADV-005 | Gateway route matching works with priority ordering | COVERED-BY | controller-delta.md#21-gateway |
| ADV-005 TC-010 | ADV-005 | Gateway formats responses per platform format spec | COVERED-BY | controller-delta.md#21-gateway |
| ADV-005 TC-011 | ADV-005 | LocalBackend executes a command and returns ExecutionResult | COVERED-BY | controller-delta.md#23-scheduler |
| ADV-005 TC-012 | ADV-005 | DockerBackend constructs correct docker run command with limits | COVERED-BY | controller-delta.md#23-scheduler |
| ADV-005 TC-013 | ADV-005 | backend_from_spec dispatches to Local/Docker backends | COVERED-BY | controller-delta.md#23-scheduler |
| ADV-005 TC-014 | ADV-005 | SkillManager matches triggers correctly with priority ordering | COVERED-BY | controller-delta.md#22-skill-manager |
| ADV-005 TC-015 | ADV-005 | SkillManager CRUD operations work correctly | COVERED-BY | controller-delta.md#22-skill-manager |
| ADV-005 TC-016 | ADV-005 | LearningEngine records sessions and searches by query | COVERED-BY | controller-delta.md#22-skill-manager |
| ADV-005 TC-017 | ADV-005 | LearningEngine generates a skill from execution trace | COVERED-BY | controller-delta.md#22-skill-manager |
| ADV-005 TC-018 | ADV-005 | Cron expression parsing correctly computes next run times | COVERED-BY | controller-delta.md#23-scheduler |
| ADV-005 TC-019 | ADV-005 | Scheduler.get_due_tasks returns correct tasks for timestamp | COVERED-BY | controller-delta.md#23-scheduler |
| ADV-005 TC-020 | ADV-005 | Scheduler.tick executes due tasks and updates timestamps | COVERED-BY | controller-delta.md#23-scheduler |
| ADV-005 TC-021 | ADV-005 | AgentRunner initializes all subsystems from config | COVERED-BY | controller-delta.md#3-module-verdict-table |
| ADV-005 TC-022 | ADV-005 | AgentRunner.process_message routes through skill then fallback | COVERED-BY | controller-delta.md#22-skill-manager |
| ADV-005 TC-023 | ADV-005 | AgentRunner.tick delegates to scheduler | COVERED-BY | controller-delta.md#23-scheduler |
| ADV-005 TC-024 | ADV-005 | Gateway references validated — invalid names caught | COVERED-BY | builder-delta.md#reference_exists |
| ADV-005 TC-025 | ADV-005 | Cron task references validated — invalid names caught | COVERED-BY | builder-delta.md#reference_exists |
| ADV-005 TC-026 | ADV-005 | Model fallback cycles detected via Z3 ordinals | COVERED-BY | builder-delta.md#dag_acyclicity |
| ADV-005 TC-027 | ADV-005 | Resource limit violations detected | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-005 TC-028 | ADV-005 | Skill trigger overlap warnings generated | COVERED-BY | builder-delta.md#domain-specific-residue |
| ADV-005 TC-029 | ADV-005 | Agent completeness catches missing model/backend refs | COVERED-BY | builder-delta.md#reference_exists |
| ADV-005 TC-030 | ADV-005 | Agent config YAML generated from agent + model_config specs | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-005 TC-031 | ADV-005 | Gateway routing table YAML generated from gateway specs | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-005 TC-032 | ADV-005 | Cron entries generated in valid crontab format | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-005 TC-033 | ADV-005 | Skill markdown generated in agentskills.io format | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-005 TC-034 | ADV-005 | Docker compose fragment generated from Docker backend specs | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-005 TC-035 | ADV-005 | Visualizer generates graph data with agent nodes and edges | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-005 TC-036 | ADV-005 | HTML output renders agent architecture with colors and labels | DEFERRED-TO | ADV-UI |
| ADV-005 TC-037 | ADV-005 | agent_system.ark parses without errors | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-005 TC-038 | ADV-005 | agent_system.ark passes all agent verification checks | COVERED-BY | builder-delta.md#shared-verify-passes |
| ADV-005 TC-039 | ADV-005 | ark_agent.ark parses without errors | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-005 TC-040 | ADV-005 | ark_agent.ark passes all agent verification checks | COVERED-BY | builder-delta.md#shared-verify-passes |
| ADV-005 TC-041 | ADV-005 | Both specs registered in root.ark SystemRegistry | DEFERRED-TO | ADV-DU |
| ADV-005 TC-042 | ADV-005 | Codegen produces valid artifacts from agent_system.ark | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-005 TC-043 | ADV-005 | Test strategy document covers all target conditions | DEFERRED-TO | ADV-DU |
| ADV-005 TC-044 | ADV-005 | All automated tests pass | DEFERRED-TO | ADV-DU |
| ADV-006 TC-001 | ADV-006 | stdlib/visual.ark parses without errors | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-006 TC-002 | ADV-006 | All visual enums and structs well-formed and referenceable | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-006 TC-003 | ADV-006 | Lark grammar accepts all 7 new visual item types | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-006 TC-004 | ADV-006 | Pest grammar mirrors Lark for all 7 visual items | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-006 TC-005 | ADV-006 | Parser produces correct AST for each visual item type | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-006 TC-006 | ADV-006 | Existing .ark files parse without regression | COVERED-BY | descriptor-delta.md#grammar-authoring-contract |
| ADV-006 TC-007 | ADV-006 | ArkFile indices populated for visual items | COVERED-BY | descriptor-delta.md#ast-family-spec |
| ADV-006 TC-008 | ADV-006 | Mermaid renderer generates valid .mmd files | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-006 TC-009 | ADV-006 | Renderer handles all DiagramType variants | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-006 TC-010 | ADV-006 | Invalid Mermaid source produces meaningful errors | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-006 TC-011 | ADV-006 | HTML previewer generates valid self-contained HTML | RETIRED-BY | pruning-catalog.md row 2 |
| ADV-006 TC-012 | ADV-006 | Viewport sizes correctly configured | RETIRED-BY | pruning-catalog.md row 2 |
| ADV-006 TC-013 | ADV-006 | Annotator applies rect, arrow, text, blur elements | RETIRED-BY | pruning-catalog.md row 2 |
| ADV-006 TC-014 | ADV-006 | Annotation coordinates validated against bounds | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-006 TC-015 | ADV-006 | Review loop creates valid manifest JSON | COVERED-BY | controller-delta.md#27-review |
| ADV-006 TC-016 | ADV-006 | Feedback parsing handles all FeedbackStatus variants | COVERED-BY | controller-delta.md#27-review |
| ADV-006 TC-017 | ADV-006 | Review cycles prevent circular feedback | COVERED-BY | builder-delta.md#dag_acyclicity |
| ADV-006 TC-018 | ADV-006 | Screenshot manager registers entries correctly | RETIRED-BY | pruning-catalog.md row 9 |
| ADV-006 TC-019 | ADV-006 | Catalog persistence round-trip works | RETIRED-BY | pruning-catalog.md row 9 |
| ADV-006 TC-020 | ADV-006 | Keyword search returns correct matches | RETIRED-BY | pruning-catalog.md row 9 |
| ADV-006 TC-021 | ADV-006 | Tag search filters by tag intersection | RETIRED-BY | pruning-catalog.md row 9 |
| ADV-006 TC-022 | ADV-006 | Visual runner dispatches diagrams to mermaid renderer | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-006 TC-023 | ADV-006 | Visual runner dispatches previews to html previewer | DEFERRED-TO | ADV-UI |
| ADV-006 TC-024 | ADV-006 | CLI ark visual subcommand works | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-006 TC-025 | ADV-006 | Every diagram references valid DiagramType | COVERED-BY | builder-delta.md#reference_exists |
| ADV-006 TC-026 | ADV-006 | Every visual_review references existing target | COVERED-BY | builder-delta.md#reference_exists |
| ADV-006 TC-027 | ADV-006 | Annotation coordinates within bounds (Z3) | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-006 TC-028 | ADV-006 | Render configs have valid positive dimensions (Z3) | COVERED-BY | builder-delta.md#numeric_interval |
| ADV-006 TC-029 | ADV-006 | Review cycles acyclic (Z3 ordinals) | COVERED-BY | builder-delta.md#dag_acyclicity |
| ADV-006 TC-030 | ADV-006 | Codegen produces .mmd from diagram items | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-006 TC-031 | ADV-006 | Codegen produces .html from preview items | DEFERRED-TO | ADV-UI |
| ADV-006 TC-032 | ADV-006 | Codegen produces annotation JSON | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-006 TC-033 | ADV-006 | Codegen produces render config JSON | COVERED-BY | builder-delta.md#codegen-emitter-catalog |
| ADV-006 TC-034 | ADV-006 | Visual island spec parses and verifies | COVERED-BY | descriptor-delta.md#verdict-table |
| ADV-006 TC-035 | ADV-006 | Example visual specs produce rendered output | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-006 TC-036 | ADV-006 | Visualizer renders visual pipeline items | COVERED-BY | builder-delta.md#module-verdicts |
| ADV-006 TC-037 | ADV-006 | VisualIsland registered in root.ark | DEFERRED-TO | ADV-DU |
| ADV-007 TC-001 | ADV-007 | All 5 Claudovka projects researched with documented findings | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-002 | ADV-007 | Cross-project dependency map created | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-003 | ADV-007 | Problem/failure catalog with severity ratings produced | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-004 | ADV-007 | Concept catalog covering all 5 projects created | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-005 | ADV-007 | Knowledge architecture with parallelism/token constraints documented | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-006 | ADV-007 | Entity redesign proposal with before/after comparison | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-007 | ADV-007 | Management failure catalog from past adventures documented | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-008 | ADV-007 | Profiling, optimization, and self-healing skill specs produced | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-009 | ADV-007 | Role effectiveness review with improvement recommendations | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-010 | ADV-007 | All external tools researched with capability summaries | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-011 | ADV-007 | Integration potential matrix (tool x phase) produced | RETIRED-BY | pruning-catalog.md row 12 |
| ADV-007 TC-012 | ADV-007 | MCP server catalog with 14 servers analyzed | RETIRED-BY | pruning-catalog.md row 7 |
| ADV-007 TC-013 | ADV-007 | UI requirements for all workflow entity types cataloged | RETIRED-BY | pruning-catalog.md row 23 |
| ADV-007 TC-014 | ADV-007 | UI component architecture with data flow design produced | RETIRED-BY | pruning-catalog.md row 24 |
| ADV-007 TC-015 | ADV-007 | Technology stack evaluation with recommendation | RETIRED-BY | pruning-catalog.md row 25 |
| ADV-007 TC-016 | ADV-007 | All 7 new concepts designed with use cases and entity models | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-017 | ADV-007 | Integration map showing concept dependencies and interaction points | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-007 TC-018 | ADV-007 | MCP-only operations architecture designed | RETIRED-BY | pruning-catalog.md row 26 |
| ADV-007 TC-019 | ADV-007 | Autotest orientation strategy with coverage targets defined | RETIRED-BY | pruning-catalog.md row 27 |
| ADV-007 TC-020 | ADV-007 | Automation-first principle with human escalation criteria documented | RETIRED-BY | pruning-catalog.md row 28 |
| ADV-007 TC-021 | ADV-007 | Complexity analysis with reduction targets produced | RETIRED-BY | pruning-catalog.md row 29 |
| ADV-007 TC-022 | ADV-007 | Iterative refactoring strategy with milestone criteria defined | RETIRED-BY | pruning-catalog.md row 30 |
| ADV-007 TC-023 | ADV-007 | Abstract representation layer specification produced | RETIRED-BY | pruning-catalog.md row 31 |
| ADV-007 TC-024 | ADV-007 | Benchmark specification with baseline and target metrics defined | RETIRED-BY | pruning-catalog.md row 32 |
| ADV-007 TC-025 | ADV-007 | Test/profile design covering full stack scenarios | RETIRED-BY | pruning-catalog.md row 33 |
| ADV-007 TC-026 | ADV-007 | Migration strategy with backward compatibility plan | RETIRED-BY | pruning-catalog.md row 34 |
| ADV-007 TC-027 | ADV-007 | Optimization loop design with metrics and triggers | RETIRED-BY | pruning-catalog.md row 35 |
| ADV-007 TC-028 | ADV-007 | Self-healing architecture with error classification taxonomy | RETIRED-BY | pruning-catalog.md row 36 |
| ADV-007 TC-029 | ADV-007 | Human-machine balance model with escalation criteria | RETIRED-BY | pruning-catalog.md row 37 |
| ADV-007 TC-030 | ADV-007 | Futuring (proactive improvement) system design | RETIRED-BY | pruning-catalog.md row 38 |
| ADV-007 TC-031 | ADV-007 | Master roadmap mapping all 10 phases to adventure IDs produced | RETIRED-BY | pruning-catalog.md row 4 |
| ADV-007 TC-032 | ADV-007 | Adventure dependency graph with parallelism analysis | RETIRED-BY | pruning-catalog.md row 39 |
| ADV-007 TC-033 | ADV-007 | Inter-adventure data contracts defined | RETIRED-BY | pruning-catalog.md row 40 |
| ADV-007 TC-034 | ADV-007 | Research validation strategy and final validation report | RETIRED-BY | pruning-catalog.md row 3 |
| ADV-008 TC-01 | ADV-008 | shape_grammar/ package layout exists with specs + tools + tests + examples + rust subtree | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-02 | ADV-008 | ark verify shape_grammar/specs/shape_grammar.ark exits 0 under vanilla Ark | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-03 | ADV-008 | IR extraction returns populated ShapeGrammarIR from every spec island | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-05 | ADV-008 | Python evaluator round-trip produces deterministic terminals under fixed seed | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-06 | ADV-008 | Rust skeleton compiles via cargo check | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-07 | ADV-008 | End-to-end round-trip grammar evaluator OBJ produces non-empty file | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-08 | ADV-008 | Semantic label propagation: every terminal carries an inherited-or-overridden label | DEFERRED-TO | ADV-DU |
| ADV-008 TC-09 | ADV-008 | Semantic-rendering research document exists with exactly 2 prototypes | RETIRED-BY | pruning-catalog.md row 43 |
| ADV-008 TC-10 | ADV-008 | No Ark modifications by ADV-008 | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-11 | ADV-008 | Visualizer adapter produces annotated HTML for a shape-grammar island | DEFERRED-TO | ADV-DU |
| ADV-008 TC-12 | ADV-008 | Impact adapter returns augmented report with rule-tree edges | DEFERRED-TO | ADV-DU |
| ADV-008 TC-13 | ADV-008 | Diff adapter returns rule-tree structural diff | DEFERRED-TO | ADV-DU |
| ADV-008 TC-14 | ADV-008 | Full integration adapter test suite green | DEFERRED-TO | ADV-DU |
| ADV-008 TC-15 | ADV-008 | ShapeML architecture research document exists with >=6 H2 sections | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-16 | ADV-008 | Test strategy document covers every autotest TC with a named test function | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-17 | ADV-008 | Four example grammars exist and parse + verify under vanilla Ark | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-18 | ADV-008 | Ark-as-host feasibility study documents every entity with a feasibility verdict and zero BLOCKED | RETIRED-BY | pruning-catalog.md row 44 |
| ADV-008 TC-19 | ADV-008 | RNG determinism: SeededRng(42).fork produces identical sequence across runs | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-20 | ADV-008 | Example-driven end-to-end tests: parse + verify + IR + evaluate each of 4 examples | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-21 | ADV-008 | Full shape_grammar test suite green | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-22 | ADV-008 | Test strategy authored before implementation starts | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-23 | ADV-008 | Dependency direction is one-way — shape_grammar/ is not imported anywhere under ark/ | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-24 | ADV-008 | Verifier passes are invokable via CLI | RETIRED-BY | pruning-catalog.md row 5 |
| ADV-008 TC-25 | ADV-008 | ir.py is invokable via CLI and emits JSON-shaped IR | RETIRED-BY | pruning-catalog.md row 5 |
