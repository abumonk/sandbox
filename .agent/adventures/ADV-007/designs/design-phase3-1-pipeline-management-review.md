# Phase 3.1: Pipeline Management Review - Design

## Overview
Review existing projects that use team-pipeline to find management failures. Design profiling, optimization, and self-healing skills. Review custom roles for effectiveness.

## Approach
1. Find projects using team-pipeline (search for usage patterns, config files)
2. Analyze pipeline execution logs and metrics from past adventures (ADV-001 through ADV-006)
3. Identify management failures:
   - Task routing mistakes
   - Role misassignment
   - Metric tracking gaps (known issue from knowledge base)
   - Permission blocks (known issue)
4. Design profiling skills (token usage tracking, duration estimation accuracy)
5. Design optimization skills (context pruning, smart caching, parallel dispatch)
6. Design self-healing skills (auto-retry, fallback strategies, error recovery)
7. Review custom roles for completeness and effectiveness

## Target Files (output artifacts)
- `.agent/adventures/ADV-007/research/phase3-1-management-failures.md` - Failure catalog
- `.agent/adventures/ADV-007/research/phase3-1-profiling-skills.md` - Profiling skill designs
- `.agent/adventures/ADV-007/research/phase3-1-optimization-skills.md` - Optimization skill designs
- `.agent/adventures/ADV-007/research/phase3-1-self-healing-skills.md` - Self-healing skill designs
- `.agent/adventures/ADV-007/research/phase3-1-role-review.md` - Role effectiveness review

## Dependencies
- design-phase1-project-review: Understanding of pipeline internals

## Target Conditions
- TC-007: Management failure catalog from past adventures documented
- TC-008: Profiling, optimization, and self-healing skill specifications produced
- TC-009: Role effectiveness review with improvement recommendations
