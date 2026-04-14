---
name: Update task frontmatter before declaring done
description: Implementer must write stage=completed + status=done + iterations count to the task file frontmatter before its final chat message, not rely on the lead to amend
type: feedback
---

Before reporting "complete" in chat, the implementer MUST update the task file's YAML frontmatter: `stage: completed`, `status: done`, `iterations: N`, and check off acceptance criteria in the body.

**Why**: ADV-008 T18 (and one other task) reported success in chat but left the task file frontmatter as `status: in_progress`. The lead had to amend post-hoc, breaking the invariant that task files are the single source of truth for task state and costing a round-trip.

**How to apply**: In the final step of the implementer checklist, (1) edit the task file frontmatter, (2) check the acceptance-criteria boxes in the task body, (3) append the metrics row, *then* (4) post the completion message. Do not invert this order.
