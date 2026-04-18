# Pruning Catalog — ADV-011

Generated from `research/concept-mapping.md` rows where `bucket = out-of-scope`.
Seed rows from the adventure brief (ADV-011 manifest §What this adventure delivers).

## Table

| concept | source_adventure | justification | disposition | owner_risk |
|---------|------------------|---------------|-------------|------------|
| Darwinian optimizer mode | ADV-004 | NotImplementedError stub; no gateway or skill-manager call site; speculative phase-4 work parked pending evolution strategy. | DROP | none — replaced by explicit phase-4 code-evolution note in unified controller design |
| screenshot_manager, visual_search, html_previewer | ADV-006 | Electron/Pillow/Ollama UI surfaces with no descriptor, builder, or controller dependency in ADV-001..008. | OUT-OF-SCOPE → ADV-UI | ADV-006 loses its Pillow annotator path; no core consumer depends on it; UI adventure recovers it |
| Phase 1-7 ecosystem research artefacts | ADV-007 | Claudovka ecosystem research completed within ADV-007; no downstream core artefact consumes these notes. | DROP | none — artefacts remain archived in ADV-007 research/ |
| 10-phase master roadmap | ADV-007 | Prescriptive adventure-sequencing artefact superseded by ADV-011 downstream-adventure-plan; not a core concept. | DROP | none — downstream plan from T010 replaces the roadmap for ADV-011's scope |
| shape_grammar/ package contents | ADV-008 | ShapeML specific content; the sibling-package pattern is core but the ShapeML instance is domain content that lives in its own package. | OUT-OF-SCOPE → ADV-DU | package stays on disk; unified descriptor cites it as a reference integration, not a core artefact |
| Darwinian git-organism evolver | ADV-004 | Future-phase code-evolution experiment; no current core role consumes its output; depends on unimplemented evolver loop. | OUT-OF-SCOPE → ADV-CE | evolver remains a stub; ADV-CE will revisit when evolution controller lands |
| MCP server research catalog (14 servers) | ADV-007 | External-tool integration inventory; not part of descriptor/builder/controller; consumed by skill-manager only as input catalog, not as a concept. | DROP | skill-manager already pins its MCP list separately; catalog has no other consumer |
| MCP query surface | ADV-002 | Interactive MCP tooling layer sits above the Ark core query engine; not a codegen output, not a descriptor or builder concern. | DROP | none — skill-manager routes MCP queries at runtime independently of ark-core |
| visual screenshot surfaces | ADV-006 | Interactive UI screenshot catalog; not a codegen output of visual_codegen; no descriptor or builder dependency in ADV-001..008. | OUT-OF-SCOPE → ADV-UI | ADV-006 visual workflow loses screenshot catalog surface; no core pipeline step depends on it |
| MCP tier catalogue | ADV-007 | Ecosystem research artefact cataloguing external MCP server tiers; not a descriptor, builder, or controller concept. | DROP | none — MCP tier information is external to ark-core; skill-manager manages its own list |
| synthesis matrix | ADV-007 | Ecosystem research synthesis document; contains planning cross-references only, not ark-core DSL or runtime concepts. | DROP | none — synthesis conclusions are subsumed by ADV-011 unified design documents |
| interaction matrix | ADV-007 | Ecosystem inter-component interaction research document; not an ark-core descriptor, builder, or controller artefact. | DROP | none — interaction analysis is superseded by ADV-011 concept-mapping and dedup-matrix |
| phase1-cross-project-issues | ADV-007 | Phase-1 ecosystem research artefact; documents cross-project issues only, not ark-core DSL or runtime semantics. | DROP | none — archived in ADV-007; no core pipeline step references this artefact |
| phase2-concept-catalog | ADV-007 | Phase-2 ecosystem research artefact; concept catalog for Claudovka ecosystem, not for ark-core descriptor/builder/controller. | DROP | none — superseded by ADV-011 concept-inventory and concept-mapping |
| phase2-knowledge-architecture | ADV-007 | Phase-2 ecosystem research artefact; knowledge architecture design for Claudovka, not an ark-core DSL concern. | DROP | none — archived in ADV-007; ADV-011 owns the unified architecture design going forward |
| phase2-entity-redesign | ADV-007 | Phase-2 ecosystem research artefact; entity redesign proposals for Claudovka, not ark-core descriptor schema. | DROP | none — entity decisions absorbed into ADV-011 concept-mapping bucket assignments |
| phase3-1-management-failures | ADV-007 | Phase-3 ecosystem research artefact; documents management failure modes, not ark-core DSL or runtime behaviour. | DROP | none — no core pipeline step depends on failure-mode documentation |
| phase3-1-profiling-skills | ADV-007 | Phase-3 ecosystem research artefact; profiling skill design notes, not an ark-core descriptor, builder, or controller. | DROP | none — profiling skill designs remain in ADV-007 research; no core consumer |
| phase3-1-optimization-skills | ADV-007 | Phase-3 ecosystem research artefact; optimization skill design notes, not an ark-core descriptor, builder, or controller. | DROP | none — optimization skill designs archived in ADV-007; no ark-core consumer |
| phase3-1-self-healing-skills | ADV-007 | Phase-3 ecosystem research artefact; self-healing skill design notes; no descriptor, builder, or controller dependency. | DROP | none — self-healing skill designs archived in ADV-007; no core ark pipeline consumer |
| phase3-1-role-review | ADV-007 | Phase-3 ecosystem research artefact; agent role review document; not a descriptor, builder, or controller concern. | DROP | none — role definitions are covered by ADV-003 studio items and ADV-005 agent items |
| phase3-2-integration-matrix | ADV-007 | Phase-3 ecosystem research artefact; integration dependency matrix for Claudovka toolchain; not ark-core DSL. | DROP | none — integration analysis is superseded by ADV-011 deduplication-matrix |
| phase4-ui-requirements | ADV-007 | Phase-4 UI/Electron surface research; not an ark-core descriptor, builder, or controller artefact. | OUT-OF-SCOPE → ADV-UI | ADV-007 UI planning work; no core pipeline step depends on it; ADV-UI will revisit |
| phase4-ui-architecture | ADV-007 | Phase-4 UI/Electron architecture research; not an ark-core descriptor, builder, or controller artefact. | OUT-OF-SCOPE → ADV-UI | ADV-007 UI architecture planning; no core pipeline step depends on it; ADV-UI will revisit |
| phase4-technology-evaluation | ADV-007 | Phase-4 ecosystem technology evaluation research; not a descriptor, builder, or controller concept in ark-core. | DROP | none — technology evaluation findings archived in ADV-007; no forward obligation for ark-core |
| phase5-concept-designs | ADV-007 | Phase-5 speculative/research-only concept designs; not part of ark-core descriptor, builder, or controller surface. | DROP | none — speculative concepts archived in ADV-007; no downstream core artefact depends on them |
| phase5-integration-map | ADV-007 | Phase-5 speculative integration map research artefact; not an ark-core DSL or runtime concept. | DROP | none — integration map is speculative; superseded by ADV-011 deduplication matrix |
| phase6-mcp-operations | ADV-007 | Phase-6 ecosystem MCP operations research; not an ark-core descriptor, builder, or controller concern. | DROP | none — MCP operations are external tooling; no core ark-core pipeline step depends on it |
| phase6-autotest-strategy | ADV-007 | Phase-6 ecosystem autotesting strategy research; not an ark-core descriptor, builder, or controller concept. | DROP | none — autotesting strategy is external process guidance; no ark-core dependency |
| phase6-automation-first | ADV-007 | Phase-6 ecosystem automation-first principle document; not an ark-core descriptor, builder, or controller artefact. | DROP | none — automation principle is process guidance; no core ark pipeline step depends on it |
| phase6-1-complexity-analysis | ADV-007 | Phase-6 ecosystem complexity analysis research artefact; not a descriptor, builder, or controller concept. | DROP | none — complexity analysis is external tooling research; no core ark pipeline dependency |
| phase6-1-refactoring-strategy | ADV-007 | Phase-6 ecosystem refactoring strategy research; not an ark-core descriptor, builder, or controller concept. | DROP | none — refactoring strategy is process guidance; ark-core does not depend on it |
| phase6-1-abstract-representation | ADV-007 | Phase-6 ecosystem abstract representation research; not an ark-core descriptor, builder, or controller artefact. | DROP | none — abstract representation research archived in ADV-007; no ark-core consumer |
| phase6-2-benchmark-design | ADV-007 | Phase-6 ecosystem benchmark design artefact; not an ark-core descriptor, builder, or controller concept. | DROP | none — benchmark designs are external evaluation tooling; no core ark dependency |
| phase6-2-test-profiles | ADV-007 | Phase-6 ecosystem test profile artefact; not an ark-core descriptor, builder, or controller concept. | DROP | none — test profiles are external evaluation tooling; no core ark pipeline dependency |
| phase6-2-migration-strategy | ADV-007 | Phase-6 ecosystem migration strategy artefact; not an ark-core descriptor, builder, or controller concept. | DROP | none — migration strategy is external process guidance; no core ark dependency |
| phase7-optimization-loops | ADV-007 | Phase-7 ecosystem on-sail optimization loop research; not an ark-core descriptor, builder, or controller concept. | DROP | none — optimization loop research archived in ADV-007; no core ark pipeline dependency |
| phase7-self-healing | ADV-007 | Phase-7 ecosystem self-healing research artefact; not an ark-core descriptor, builder, or controller concept. | DROP | none — self-healing research archived in ADV-007; no core ark pipeline dependency |
| phase7-human-machine | ADV-007 | Phase-7 ecosystem human-machine model research; not an ark-core descriptor, builder, or controller concept. | DROP | none — human-machine model is external interaction research; no core ark dependency |
| phase7-operational-model | ADV-007 | Phase-7 ecosystem operational model research artefact; not an ark-core descriptor, builder, or controller concept. | DROP | none — operational model is external deployment guidance; no core ark pipeline dependency |
| master-roadmap | ADV-007 | Ecosystem roadmap artefact superseded by ADV-011 downstream-adventure-plan; not a descriptor, builder, or controller concept. | DROP | none — downstream plan from T010 replaces this roadmap; no core ark dependency |
| adventure-dependency-graph | ADV-007 | Ecosystem inter-adventure dependency graph; adventure sequencing concern, not an ark-core descriptor/builder/controller. | DROP | none — ADV-011 downstream plan (T010) owns inter-adventure dependency tracking |
| adventure-contracts | ADV-007 | Ecosystem inter-adventure contract artefact; adventure coordination concern, not an ark-core descriptor/builder/controller. | DROP | none — ADV-011 downstream plan (T010) owns inter-adventure contract definitions |
| host_language_contract | ADV-008 | Host-language feasibility study for sibling-package consumer binding; not an ark-core DSL construct or builder pass. | DROP | none — host-language binding is a sibling-package consumer responsibility, not ark-core |
| lazy-import circular-dep break | ADV-008 | Host-language Python implementation detail for circular import resolution; not an ark-core descriptor, builder, or controller. | DROP | none — circular import handling is a host-language packaging concern; no ark-core dependency |
| semantic-rendering research | ADV-008 | Speculative research-only artefact exploring semantic rendering ideas; not an ark-core descriptor, builder, or controller. | DROP | none — speculative research archived in ADV-008; no downstream core artefact depends on it |

## Per-Row Notes

**screenshot_manager, visual_search, html_previewer** (`OUT-OF-SCOPE → ADV-UI`)
Forward reference: ADV-UI = "Ark UI Surface" — the provisional downstream adventure that will host all Electron/Pillow/Ollama-based interactive UI work pruned from ADV-006. T010 must materialise ADV-UI or rewrite this row to DROP. Concept-mapping source row: `visual screenshot surfaces` (ADV-006).

**visual screenshot surfaces** (`OUT-OF-SCOPE → ADV-UI`)
Forward reference: ADV-UI = "Ark UI Surface". Same downstream adventure as `screenshot_manager, visual_search, html_previewer` above. This row corresponds directly to the `visual_screenshot_surfaces` canonical name in concept-mapping.

**shape_grammar/ package contents** (`OUT-OF-SCOPE → ADV-DU`)
Forward reference: ADV-DU = "Descriptor Unification" — the mandatory downstream adventure that will document how sibling-package consumers bind to the unified grammar. The shape_grammar/ contents are not pruned from disk; they are pruned from ADV-011's unified core design surface. T010 must materialise ADV-DU (it is in the canonical mandatory set).

**Darwinian git-organism evolver** (`OUT-OF-SCOPE → ADV-CE`)
Forward reference: ADV-CE = "Ark Code Evolution" — the provisional downstream adventure that will host the full Darwinian git-organism evolver once the evolution controller loop is implemented. Concept-mapping source: this concept is a seed row from the ADV-011 manifest; the mapping bucket for the evolution stubs (ADV-004) is `out-of-scope` by the per-bucket rationale for future-phase work. T010 must materialise ADV-CE or rewrite this row to DROP.

**phase4-ui-requirements** (`OUT-OF-SCOPE → ADV-UI`)
Forward reference: ADV-UI = "Ark UI Surface". Phase-4 UI requirements from ADV-007 are the canonical input for the future UI adventure. T010 must materialise ADV-UI.

**phase4-ui-architecture** (`OUT-OF-SCOPE → ADV-UI`)
Forward reference: ADV-UI = "Ark UI Surface". Phase-4 UI architecture from ADV-007 is a companion artefact to `phase4-ui-requirements`; both route to ADV-UI.

**Darwinian optimizer mode** (`DROP`)
This is the NotImplementedError stub in the evolution module (ADV-004), distinct from the `Darwinian git-organism evolver`. The stub has no call site in any gateway or skill-manager module; dropping it is safe. The unified controller design (T008) records a forward note for phase-4 code-evolution work instead.

**10-phase master roadmap / master-roadmap** (two DROP rows)
The seed row "10-phase master roadmap" refers to the strategic roadmap document produced in ADV-007. The concept-mapping row `master-roadmap` (canonical: `master_roadmap`) is the same artefact. Both rows are retained to satisfy the seed-row mandate and to keep the concept name consistent with concept-mapping. T011 cross-check: both names may appear; the mapping name `master-roadmap` is the authoritative concept identifier.
