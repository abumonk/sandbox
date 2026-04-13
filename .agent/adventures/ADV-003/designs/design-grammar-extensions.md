# Grammar Extensions for Studio Hierarchy — Design

## Overview
Extend the Ark DSL grammar (both Lark EBNF and pest PEG) with new top-level item kinds for studio hierarchy: `role`, `studio`, `workflow_command`, `hook`, `rule`, and `template`. These are first-class items at the same level as `class`, `island`, `bridge`, etc.

## Target Files
- `tools/parser/ark_grammar.lark` — Add Lark EBNF rules for the 6 new items
- `dsl/grammar/ark.pest` — Add pest PEG rules mirroring the Lark grammar

## Approach

### New Grammar Rules

Each new item follows existing Ark patterns (keyword + IDENT + `{` body `}`):

```
// 1. role — specialist definition
role_def: "role" IDENT inherits? "{" role_body "}"
role_body: role_member*
role_member: tier_stmt | responsibility_stmt | escalates_to_stmt
           | skills_stmt | tools_stmt | data_field | description_stmt
           | in_port | out_port | process_rule

tier_stmt: "tier:" expr          // 1=Director, 2=Lead, 3=Specialist
responsibility_stmt: "responsibility:" STRING
escalates_to_stmt: "escalates_to:" IDENT
skills_stmt: "skills:" "[" ident_list "]"
tools_stmt: "tools:" "[" ident_list "]"

// 2. studio — island grouping roles into tiers
studio_def: "studio" IDENT "{" studio_body "}"
studio_body: studio_member*
studio_member: tier_group | contains_stmt | description_stmt
             | data_field | invariant_stmt | process_rule | bridge_def
tier_group: "tier" expr "{" ident_list "}"

// 3. workflow_command — slash-command binding
command_def: "command" IDENT "{" command_body "}"
command_body: command_member*
command_member: phase_stmt | prompt_stmt | role_ref_stmt | output_stmt
             | description_stmt | data_field
phase_stmt: "phase:" IDENT
prompt_stmt: "prompt:" STRING
role_ref_stmt: "role:" IDENT
output_stmt: "output:" IDENT

// 4. hook — event-driven rule
hook_def: "hook" IDENT "{" hook_body "}"
hook_body: hook_member*
hook_member: event_stmt | pattern_stmt | action_stmt | description_stmt | data_field
event_stmt: "event:" IDENT
pattern_stmt: "pattern:" STRING
action_stmt: "action:" STRING

// 5. rule — path-scoped policy
rule_def: "rule" IDENT "{" rule_body "}"
rule_body: rule_member*
rule_member: path_stmt | constraint_stmt_rule | severity_stmt | description_stmt | data_field
path_stmt: "path:" STRING
constraint_stmt_rule: "constraint:" STRING
severity_stmt: "severity:" IDENT

// 6. template — document skeleton
template_def: "template" IDENT "{" template_body "}"
template_body: template_member*
template_member: sections_stmt | bound_to_stmt | description_stmt | data_field
sections_stmt: "sections:" "[" string_list "]"
bound_to_stmt: "bound_to:" IDENT
string_list: STRING ("," STRING)*
```

### Integration into `item` Rule

Add to the `item` rule in both grammars:
```
item: ... | role_def | studio_def | command_def | hook_def | rule_def | template_def
```

### Design Decisions
- Reuse existing patterns: `inherits?` on `role`, `description_stmt`, `data_field`, etc.
- `tier_stmt` uses expr (number literal) for tier level
- `tools_stmt` and `skills_stmt` use `ident_list` (bracket-delimited)
- `studio` uses `tier_group` blocks instead of flat contains — more expressive grouping
- `hook` events use IDENT (enum-like), patterns use STRING (glob)
- `template` sections use a string list for required section names

## Dependencies
None — this is the foundation layer.

## Target Conditions
- TC-001: Lark grammar parses all 6 new item kinds without errors
- TC-002: Pest grammar mirrors Lark for all 6 new item kinds
- TC-003: Existing .ark files continue to parse after grammar changes (no regressions)
