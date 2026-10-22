# Autop issue body

The uniform body every issue filed by `autop-add-issue` carries. Omit a
section that would be empty boilerplate; never omit a known constraint.

`## Spec` / `## Tasks` come from the spec-kit artifacts committed to the
project's configured control repo (any name, for example `autop-dev/control`).
The `Spec:` line is machine-read
by Autop: the implementer and both reviewers get that exact commit's
`spec.md`, `plan.md`, `tasks.md` and constitution. An issue filed without
spec-kit omits both sections and is implemented and reviewed against its
`## Acceptance criteria`.

```
## Problem
<current behaviour or gap, desired outcome, who/what is affected, why it matters>

## Type / Priority
<feature | fix | tech-debt | infra | docs> · <P0 | P1 | P2 | P3>

## Affected repo(s)
<owner/repo (primary)>, <owner/repo>

## Size budget
<!-- Required for every implementation story, including without spec-kit.
     The range is an estimate; 300 is the only limit and formatting is never
     compressed to meet either. -->
- Changed production code: estimate <low–high> lines; limit 300 across all repos (the estimate is not a cap).
- Per-file estimates and assumptions: <repo/path: low–high; evidence/uncertainty>.
- Count added + deleted code; exclude comments, blank lines, docs and tests.
- Excluded test work: <fixtures/scenarios/files; still required>.
- Verification: <required gates; observed runtime or unknown; job-time headroom>.

## Spec
<the story's acceptance scenarios (Given/When/Then), copied verbatim from spec.md>

Spec: <org>/<control-repo>@<40-hex sha>:specs/NNN-<slug>/spec.md#user-story-<n>

## Tasks
<the [USn] tasks from tasks.md — none of them needs a browser, a signed-in
session, a screenshot or DevTools; the implementer is headless>

<!-- only when the story changes UI or needs an interactive check -->
## Verification (human)
<the browser / screenshot / DevTools steps a person runs after the PR opens,
with the seed data they need; the PR records them as
"Visual verification: pending human" and review never blocks on them>

<!-- only when there is no ## Spec; the heading is parsed verbatim by the
     reviewer, so never append to that line -->
## Acceptance criteria
- [ ] ...

## Backwards compatibility
<"Backwards compatible" OR "BREAKING — ships coordinated across: <consumers>">

<!-- Required only for --human / human: true. No placeholders in filed issues. -->
## Human intervention
- Action: <precise human action and role>
- Why automation cannot: <specific authority, access, decision or manual boundary>
- Evidence: <observed failure or explicit policy/source; recovery tried or ruled out>
- Resume when: <observable completion condition>

## Depends on
<human-readable refs, or "none">

Blocked-by: #N
Blocked-by: owner/repo#N

<!-- only for a story under an epic: the epic's line, verbatim -->
Integration branch: epic/NNN-<slug>

## Links
<...>

## Out of scope / notes
<...>
```

For an **epic** body add: the end-to-end outcome, the shared contract or
architecture, rollout/compatibility strategy, ordering, a checklist mapping
every sub-issue to its repo, deliverable and code budget (each <=300), and the line

```
Integration branch: epic/NNN-<slug>
```

which Autop reads when building and merging the epic's work. Every story
sub-issue repeats that line verbatim, and the branch exists in each repo a
story changes; ATC refuses a story whose line or branch is missing.
