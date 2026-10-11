---
description: "Story-scoped AUTOP tasks with acceptance tests and exact repo paths"
---
# Tasks: [FEATURE NAME]

**Input**: `spec.md`, `plan.md`, optional research/contracts/data model.
**Prerequisites**: clarified spec, constitution check, named target repositories.

Every task has a unique ID, an owning `[USn]`, and exact paths prefixed by the
product repository. `[P]` means parallelizable file work, not permission to
start competing agents or board loops. Every acceptance scenario has a test
task; write coverage alongside the code and run tests only after the story
and self-review fixes are complete, before PR creation. Apply autop-add-issue's sizing gate: at most 300
changed production-code lines across all repos per story (added + deleted;
comments, blank lines, docs and tests excluded), and at most 12 tasks. Split
oversized or uncertain work into an epic with bounded stories. Record estimates
including foundation work; preserve tests and account for gate runtime separately.

The examples below are scaffolding. Replace them with this feature's actual
paths and observable acceptance coverage; do not keep generic setup work.

## Story size budgets

| Story | Repo/file | Estimated code lines (low–high) | Evidence / assumptions |
|---|---|---|---|
| US1 | [repo/path] | [range] | [inspected implementation surface] |

Record each story's combined upper bound (<=300), excluded test work, required
gates and their observed runtime (or unknown). Allow implementation, review and
publication headroom. Copy each budget into its issue; recheck after scope changes.

## Phase 1: Shared foundation — User Story 1 (P1)

Assign all required shared setup to the P1 story. If no shared foundation is
needed, remove this phase and make the independent stories explicit.

- [ ] T001 [US1] Add coverage for [scenario/FR] in [repo]/tests/[file]
- [ ] T002 [US1] Implement the shared contract in [repo]/[path]

## Phase 2: User Story 1 — [Title]

**Goal**: [Outcome]
**Independent test**: [Acceptance scenario and verification command]

- [ ] T003 [US1] Add acceptance coverage in [repo]/tests/[file]
- [ ] T004 [US1] Implement [behavior] in [repo]/[path]
- [ ] T005 [US1] After implementation and self-review, run [repo] gates with observable output; record evidence in [feature]/DECISIONS.md

## Phase 3: User Story 2 — [Title]

**Goal**: [Outcome]
**Independent test**: [Acceptance scenario and verification command]
**Depends on**: [US1 when it supplies required foundation; otherwise none]

- [ ] T006 [US2] Add acceptance coverage in [repo]/tests/[file]
- [ ] T007 [US2] Implement [behavior] in [repo]/[path]
- [ ] T008 [US2] After implementation and self-review, run [repo] gates with observable output; record evidence in [feature]/DECISIONS.md

## Dependencies and delivery

- Map every story to its issue repository and required PR(s).
- If there is foundational work, later dependent stories block on the P1 story.
- One issue per story, native sub-issues for epics, native blocked-by links and
  `Blocked-by:` body lines. Do not turn individual task IDs into issues.
- Record the epic integration branch and each PR's target base.
- Name API/schema/protocol consumers and compatible rollout order.
- Assign any necessary polish to its owning story; no unowned task phase.
- Operator-only deployment, credentials and infrastructure steps become
  human-task work; implementation agents never perform them implicitly.
