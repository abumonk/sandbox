---
name: ark-dsl
description: |
  Skill for working with ARK DSL — a declarative system description language
  for game engine architecture. Use this skill whenever the user mentions
  ARK, DSL, system specification, island architecture, entity graphs,
  tenzor/tensor strategy, formal verification of game systems, codegen
  from specifications, @in/@out/#process/$data primitives, or anything
  related to declarative game engine design. Also trigger when the user
  wants to: define a new game subsystem, create/modify an island,
  add bridges between systems, verify invariants, generate C++/Rust code
  from specs, orchestrate build/agent pipelines using ARK notation,
  or do anything involving .ark files. This is the primary skill for
  the project — use it for every task.
---

# ARK DSL — Claude Code Skill

## First: Read CLAUDE.md

Before doing ANYTHING in this project, read the master instruction file:

```bash
cat CLAUDE.md
```

It contains: project structure, all CLI commands, workflows, backlog,
and principles. This skill file is a quick-reference supplement.

## Quick Reference

### CLI commands (all via ark.py)

```bash
python ark.py parse    <file.ark>                # JSON AST
python ark.py verify   <file.ark>                # Z3 checks
python ark.py impact   <file.ark> <entity>       # dependency analysis
python ark.py codegen  <file.ark> --target rust   # Rust / cpp / proto
python ark.py graph    <file.ark>                # interactive HTML
python ark.py pipeline <file.ark>                # all of the above
```

### Four primitives (exist at EVERY level)

| Symbol | Meaning | Example |
|--------|---------|---------|
| `@in{}` | Input port | `@in{ throttle: Float, dt: DeltaTime }` |
| `#process[]{}` | Processing rule | `#process[strategy: tensor, priority: 10]{ ... }` |
| `@out[]` | Output port | `@out[guaranteed: true]{ speed: Float }` |
| `$data` | Stored state | `$data fuel: Float [0..100] = 50.0` |

### Three entity levels

| Level | Purpose | Has instances? |
|-------|---------|----------------|
| `abstraction` | Contract skeleton | No |
| `class` | Concrete implementation | Yes |
| `instance` | Live object | Is one |

### Strategy selection

| Data shape | Strategy | Use when |
|------------|----------|----------|
| Homogeneous batch | `tensor` | Positions of 10K entities |
| Branching logic | `code` | AI behavior, quests |
| Protocol/contract | `verified` | Entity handoff, sync |
| Hot inner loop | `asm_avx2` | Collision broadphase |
| GPU parallel | `gpu_compute` | Erosion, particles |
| Frequently changed | `script` | Quest scripts, balance |

### Execution priority (orchestrator)

```
100  script/codegen   deterministic, no AI
 80  verify           Z3 solver, deterministic
 50  agent            Claude Code, reasoning needed
```

**RULE**: If a task can be done by a script or codegen — DO IT THAT WAY.
AI is the LAST resort.

## Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Master instructions |
| `docs/DSL_SPEC.md` | Language specification |
| `specs/root.ark` | Anchor point |
| `dsl/stdlib/types.ark` | Standard types |
| `tools/parser/ark_grammar.lark` | Grammar |
| `tools/parser/ark_parser.py` | Parser |
| `tools/verify/ark_verify.py` | Z3 verifier |
| `tools/verify/ark_impact.py` | Impact analyzer |
| `tools/codegen/ark_codegen.py` | Code generator |
| `tools/visualizer/ark_visualizer.py` | Graph visualizer |

## Workflow: New Subsystem

1. `cat docs/DSL_SPEC.md`
2. Create .ark: abstraction, class, island, bridge, verify
3. `python ark.py parse specs/game/new.ark`
4. `python ark.py verify specs/game/new.ark`
5. Fix if failed, repeat step 4
6. `python ark.py codegen specs/game/new.ark --target rust --out generated/`
7. `python ark.py impact specs/game/new.ark IslandName`
8. Register in root.ark
9. `python ark.py graph specs/game/new.ark`

## Workflow: Modify Existing

1. `python ark.py impact specs/game/existing.ark EntityName` (BEFORE change)
2. Edit .ark
3. `python ark.py verify specs/game/existing.ark`
4. `python ark.py codegen specs/game/existing.ark --target rust`

## Workflow: Improve Tooling

Edit files in tools/, test with:
```bash
python ark.py pipeline specs/test_minimal.ark
```

## ARK Syntax Cheat Sheet

```ark
import stdlib.types

abstraction Drivable {
  @in{ throttle: Float }
  @out[]{ movement: Vec3 }
  invariant: throttle >= 0
}

class Vehicle : Drivable {
  $data fuel: Float [0..100] = 50.0
  $data speed: Float = 0.0

  @in{ throttle: Float, dt: Float }

  #process[strategy: tensor, priority: 10]{
    pre: fuel > 0
    speed' = speed + throttle * dt
    fuel' = fuel - throttle * 0.1 * dt
    post: fuel' >= 0
  }

  @out[guaranteed: true]{ speed: Float, fuel: Float }
  invariant: fuel >= 0
  temporal: □(fuel == 0 -> speed == 0)
}

island VehiclePhysics {
  strategy: tensor
  memory: { pool(Vehicle, 10000), arena(16MB, per_frame) }
  contains: [Vehicle]
  @in{ tick: DeltaTime }
  @out[]{ results: [Transform] }
}

bridge Physics_to_Terrain {
  from: VehiclePhysics.results
  to: TerrainSystem.collisions
  contract { invariant: results.valid() }
}

verify VehiclePhysics {
  check fuel_positive: fuel >= 0
  check speed_bounded: speed <= max_speed
}

registry SystemRegistry {
  register VehiclePhysics { phase: runtime, priority: 10 }
}
```
