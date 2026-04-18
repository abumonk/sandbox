# Implement IR Extractor (live adventure dir → populated IR) - Design

## Approach

Author a stdlib-only Python IR extractor under the sibling package
`adventure_pipeline/tools/` created in T015. The extractor reads a live
`.agent/adventures/ADV-NNN/` directory and returns an
`AdventurePipelineIR` dataclass whose shape mirrors the Ark entity
declarations authored in T015's `specs/adventure.ark`. A CLI entry point
(`python -m adventure_pipeline.tools.ir ADV-NNN`) prints the IR as JSON.

Parsing reuses the regex-driven frontmatter and markdown-table scan
patterns established in `.agent/adventure-console/server.py` (see
`parse_frontmatter`, `_target_conditions`, `get_adventure`). No new
dependencies; pure stdlib (`dataclasses`, `json`, `pathlib`, `re`,
`argparse`, `sys`).

## Target Files

- `adventure_pipeline/tools/__init__.py` - Package marker; re-exports
  `extract_ir`, `to_json`, `AdventurePipelineIR` and the record
  dataclasses for programmatic use.
- `adventure_pipeline/tools/ir.py` - Core module. Declares dataclasses
  mirroring `specs/adventure.ark` entity shapes (`Adventure`, `Task`,
  `Document` with `kind` discriminator, `TargetCondition`, `Permission`,
  `Decision`, `Agent`, `Role` plus the top-level `AdventurePipelineIR`
  container). Implements:
  - `parse_frontmatter(text) -> (dict, str)` - lifted pattern from
    `server.py` (flat scalars + inline lists; no PyYAML).
  - `_parse_tc_table(body) -> list[TargetCondition]` - markdown-table
    scan under `## Target Conditions` heading.
  - `_load_task(path) -> Task` - reads task frontmatter, returns record.
  - `_load_document(path, kind) -> Document` - reads frontmatter if
    present else infers id from stem; populates `kind` enum.
  - `_load_permissions(path) -> list[Permission]` - scans the four
    permission sections (Shell / File / MCP / External) by markdown
    heading and table.
  - `extract_ir(adv_id_or_path, adventures_root=None) -> AdventurePipelineIR`
    - top-level assembler.
  - `to_json(ir) -> str` - `json.dumps(asdict(ir), indent=2,
    default=str)`; enum members serialize via `str` (dataclass `kind`
    fields stored as plain strings in the IR so JSON is straight
    `asdict`).
- `adventure_pipeline/tools/__main__.py` - `argparse`-based CLI: accepts
  a positional `ADV-NNN` id or a path; optional `--adventures-root`
  (default: resolve repo root from `__file__` parents, point to
  `.agent/adventures`); prints `to_json(extract_ir(...))` to stdout and
  exits 0. Writes errors to stderr and exits 2 on bad input.

## Implementation Steps

1. **Scaffold the tools package.** Create
   `adventure_pipeline/tools/__init__.py` with a module docstring and
   star-imports from `ir`. (T015 created `adventure_pipeline/__init__.py`
   and `adventure_pipeline/specs/`; tools/ is new.)

2. **Declare the IR dataclasses in `ir.py`.** Mirror the entity field
   names from `specs/adventure.ark` (see design-ark-pipeline-spec §1):
   - `@dataclass Task` — `id, title, stage, status, assignee,
     iterations, depends_on: list[str], target_conditions: list[str],
     files: list[str], tags: list[str], adventure_id, adventure_plan,
     role` (role optional).
   - `@dataclass Document` — `id, kind: str, path, title`. `kind` is one
     of `"design" | "plan" | "research" | "review"` (plain string, so
     `asdict` serializes cleanly; the enum lives on the Ark side).
   - `@dataclass TargetCondition` — `id, description, source, design,
     plan, tasks: list[str], proof_method, proof_command, status`.
   - `@dataclass Decision` — `kind, label, state_hint, route` (sourced
     from the manifest body / log; leave empty list if the adventure
     hasn't emitted any — ADV-007/008 won't, ADV-009 will later).
   - `@dataclass Permission` — `category ("shell"|"file"|"mcp"|
     "external"), agent, scope, reason, tasks: list[str]`.
   - `@dataclass Agent` — `name, role, permissions: list[str]`
     (permission indices or descriptors).
   - `@dataclass Role` — `name`.
   - `@dataclass AdventurePipelineIR` — `id, title, state, created,
     updated, concept, tasks: list[Task], documents: list[Document],
     tcs: list[TargetCondition], decisions: list[Decision],
     permissions: list[Permission], agents: list[Agent], roles:
     list[Role], log_tail: list[str]`.

3. **Port `parse_frontmatter`** directly from `server.py` (lines
   56-82) — same regex (`^---\s*\n(.*?)\n---\s*\n(.*)$`, DOTALL) and
   scalar/list handling. Keep the implementation byte-identical in
   behavior to avoid divergence.

4. **Implement `_parse_tc_table(body)`.** Mirror
   `server.py::_target_conditions` (lines 144-177). Walk lines, enter
   the table when `## Target Conditions` is seen, exit on the next `##
   ` heading, skip the header row and the separator row (`set("".join
   (cells)) <= set("-: ")`), emit a `TargetCondition` per data row.

5. **Implement document loaders.** For each of `designs/`, `plans/`,
   `research/`, `reviews/`:
   - List `*.md` files via `pathlib.Path.iterdir()`.
   - For each, read and call `parse_frontmatter`; if frontmatter is
     present use its `id`/`title`, else derive `id` from `path.stem`
     and `title` from the first `# ` heading in the body.
   - Emit `Document(id, kind=<subdir-name-singular>, path=<rel path>,
     title)`. Subdir → kind: `designs→design`, `plans→plan`,
     `research→research`, `reviews→review`.

6. **Implement task loader.** For each `tasks/ADV*-T*.md`, read
   frontmatter, map fields to `Task`. `files`, `depends_on`,
   `target_conditions`, `tags` arrive as inline lists from the
   frontmatter parser; default to `[]`. `iterations` is cast to
   `int` if numeric else kept as string. `role` comes from `assignee`
   when no explicit `role` field exists.

7. **Implement `_load_permissions(path)`.** `permissions.md` uses
   four tables with consistent column layouts:
   - `### Shell Access` → columns `# | Agent | Stage | Command | Reason
     | Tasks` → `Permission(category="shell", agent, scope=<Command>,
     reason, tasks=<Tasks split on comma>)`.
   - `### File Access` → columns `# | Agent | Stage | Scope | Mode |
     Reason | Tasks` → `category="file"`, `scope=<Scope> + " (" + Mode +
     ")"`.
   - `### MCP Tools` → columns `# | Agent | Stage | Tool | Reason |
     Tasks` → `category="mcp"`, `scope=<Tool>`.
   - `### External Access` → columns `# | Agent | Stage | Type | Target
     | Reason | Tasks` → `category="external"`, `scope=<Type> + " " +
     <Target>`.
   Use a single helper `_walk_tables(body, heading_pattern) -> list[dict
   cell rows]` that, given a `### Foo` heading, yields the rows of the
   next `|`-delimited table under it (stop at blank or `### ` / `## `).
   Skip rows whose leading cell is `-` (placeholder "none" rows like
   `ADV-008` T-23's MCP-none entry).

8. **Implement `extract_ir(adv_id_or_path, adventures_root=None)`.**
   - Resolve the adventure directory: if input matches `r"ADV-\d{3}"`,
     join with `adventures_root` (default: resolve via
     `Path(__file__).resolve().parents[2] / ".agent" / "adventures"`);
     else treat as a filesystem path.
   - Read `manifest.md`, parse frontmatter → `meta`, body → `body`.
   - Extract `concept` via `re.search(r"^## Concept\s*\n(.*?)(?=\n## |
     \Z)", body, DOTALL|MULTILINE)` (mirrors `server.py`).
   - Build `tasks`, `documents` (merge four subdirs), `tcs`,
     `permissions`, `decisions` (empty list for now — populated once
     ADV-009 emits decisions; keep the field for forward compatibility),
     `agents`/`roles` (derive distinct role names from task
     `assignee` fields; agents from permission `agent` column).
   - `log_tail` = last 40 lines of `adventure.log` if present.
   - Return the composed `AdventurePipelineIR`.

9. **Implement `to_json(ir) -> str`.** `json.dumps(asdict(ir),
   indent=2, sort_keys=False, default=str)`.

10. **Implement the CLI (`__main__.py`).**
    ```python
    import argparse, sys
    from .ir import extract_ir, to_json

    def main(argv=None) -> int:
        p = argparse.ArgumentParser(prog="adventure_pipeline.tools.ir")
        p.add_argument("adventure", help="ADV-NNN id or path")
        p.add_argument("--adventures-root", default=None)
        args = p.parse_args(argv)
        try:
            ir = extract_ir(args.adventure, args.adventures_root)
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(to_json(ir))
        return 0

    if __name__ == "__main__":
        sys.exit(main())
    ```

11. **Smoke-verify both target adventures.** Run against ADV-007 (34
    TCs, 24 tasks, many designs/plans/research) and ADV-008 (27 TCs,
    19 tasks, 6 designs, 5 plans). Each must emit non-empty `tasks`,
    `documents`, `tcs`, `permissions`; every task id must match the
    manifest's `tasks:` frontmatter list (implementer adds an inline
    assertion as a `--strict` flag for debugging; CLI default is
    permissive to avoid breaking downstream consumers).

## Testing Strategy

Per acceptance criteria, smoke-level verification at the CLI:

1. `python -m adventure_pipeline.tools.ir ADV-007` — exit 0; pipe to
   `python -c "import json,sys; d=json.load(sys.stdin); assert
   d['tasks'] and d['documents'] and d['tcs'] and d['permissions']"`.
2. Same for `ADV-008`.
3. Task-id parity: `python -c "import json,sys;
   d=json.load(sys.stdin); m=set(d['tasks_list'] if 'tasks_list' in d
   else [t['id'] for t in d['tasks']]);
   e=set(t['id'] for t in d['tasks']); assert m==e, (m^e)"` — but
   because the manifest's `tasks:` frontmatter list is the authoritative
   set, include it in the IR as either a top-level `tasks_list`
   alongside `tasks`, or assert parity inside `extract_ir` and raise.
   **Decision**: include `tasks_list` (the frontmatter list) as a
   separate field on the IR. Round-trip parity becomes a
   one-line comparison for the reviewer.
4. Stdlib-only: `python -c "import adventure_pipeline.tools.ir"` with
   `sys.modules` snapshot before/after shows only stdlib modules
   pulled in.

Round-trip unit tests (`tests/test_ir_roundtrip.py`,
`tests/test_ir_entities.py`) are covered by the sibling plan's test
tasks; this task only owns the three files above.

## Risks

- **T015 not landed yet.** This task `depends_on: [ADV009-T015]` — the
  implementer must confirm `adventure_pipeline/__init__.py` and
  `specs/adventure.ark` exist before starting; otherwise dataclass
  field names may drift from the spec. Mitigation: the design pins
  field names to the spec listing in
  `design-ark-pipeline-spec.md` §1, which T015 is bound to produce
  verbatim.
- **Permissions table column drift.** ADV-007 and ADV-008 both use the
  6-7 column layouts listed above, but earlier adventures may differ.
  Mitigation: `_walk_tables` accepts extra trailing cells silently
  (tuple unpacking with `*rest`); rows that fall short of the
  minimum column count are skipped rather than raising.
- **Frontmatter list quoting edge cases.** The lifted
  `parse_frontmatter` handles `["a", 'b', c]` forms but not
  block-style lists. Both ADV-007 and ADV-008 use inline lists
  throughout — confirmed by inspection. Keep behavior identical to
  `server.py` so regressions surface in one place.
- **Decisions are empty for ADV-007/008.** The IR includes a
  `decisions: []` field for forward compatibility (ADV-009 emits
  decisions via the console backend). No risk — just a stable schema.
- **Windows path normalization.** Paths in the IR are stored as
  `str(path.relative_to(REPO_ROOT)).replace("\\", "/")` — mirrors
  `server.py`. CLI must work from any CWD; `extract_ir` resolves
  everything from `Path(__file__).resolve().parents[2]` (= repo root).
