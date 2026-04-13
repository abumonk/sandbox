---
pipeline_version: "0.13.0"
build_command: ""
test_command: ""
max_iterations: 3
git:
  mode: "current-branch"
  branch_template: "task/{id}-{slug}"
  base_branch: "main"
  auto_detect_repos: true
  commit_style: "conventional"
  commit_template: "{type}({id}): {message}"
  pr_template: "default"
adventure:
  max_task_tokens: 100000
  max_task_duration: "30min"
  token_cost_per_1k:
    opus: 0.015
    sonnet: 0.003
    haiku: 0.001
active_roles:
  - lead
  - messenger
  - planner
  - coder
  - code-reviewer
  - researcher
  - qa-tester
stage_assignments:
  planning: planner
  implementing: coder
  reviewing: code-reviewer
  fixing: coder
  researching: researcher
project_type: rust
roles_initialized: "2026-04-11T00:00:00Z"
roles_plugin_version: 0.1.0
---

# Project Pipeline Configuration

Edit the frontmatter above to match your project's build and test commands.
See the `git:` block for git integration settings.
See the `adventure:` block for feature adventure thresholds and cost settings.
