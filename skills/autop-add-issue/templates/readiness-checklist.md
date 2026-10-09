# Autop readiness checklist

Run as `/speckit.checklist autop readiness: one PR per story, at most 300 changed code lines per story excluding comments and tests, every FR has a scenario, every scenario has a test task` after `/speckit.tasks` and `/speckit.analyze`. Every item must be `[x]` before any issue is filed. A failing item sends the author back to `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, or `/speckit.tasks` — never to a weaker issue.

- [ ] CHK001 — Does spec.md contain zero `[NEEDS CLARIFICATION]` markers? [Completeness, Spec]
- [ ] CHK002 — Is every user story independently testable and shippable as ONE pull request against the current codebase? [Coverage, Spec §User Scenarios]
- [ ] CHK003 — Does every FR-### appear in at least one Given/When/Then acceptance scenario? [Coverage, Spec §Requirements]
- [ ] CHK004 — Does every acceptance scenario have a named test task in tasks.md tagged with its story (`[USn]`)? [Coverage, Tasks]
- [ ] CHK005 — Does every task in tasks.md name the exact file path(s) it changes? [Clarity, Tasks]
- [ ] CHK006 — Does every story have at most 12 tasks as well as passing the code sizing gate (split if either limit fails)? [Scope, Tasks]
- [ ] CHK007 — Are Foundational-phase tasks assigned to the P1 story, with later stories marked as depending on it? [Consistency, Tasks]
- [ ] CHK008 — Does plan.md name every contract change (schema, API, config key, label, board field) and its consumers? [Completeness, Plan]
- [ ] CHK009 — Does the constitution reflect this workspace's architecture invariants and code-review hazards, and does the spec contradict none of them? [Consistency, Constitution]
- [ ] CHK010 — Can a fresh agent implement each story from spec.md + plan.md + its `[USn]` tasks alone, with no chat history? [Clarity, Gap]
- [ ] CHK011 — Does every story have evidence-based per-file code estimate ranges in tasks.md and its issue body, with a combined upper bound <=300 added + deleted production-code lines across all repos, excluding blank lines, comments, docs and tests? [Scope, Tasks, Issue]
- [ ] CHK012 — Has oversized or insufficiently bounded work been split into an epic with individually bounded story sub-issues, preserving acceptance/test coverage, shared contracts and explicit blockers? [Coverage, Spec, Dependencies]
- [ ] CHK013 — Are required gates and observed runtime (or unknown) recorded separately, with implementation/review/publication headroom considered and no gate skipped or timeout increased to fit oversized work? [Feasibility, Plan, Issue]
