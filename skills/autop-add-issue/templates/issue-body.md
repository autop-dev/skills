# Autop issue body

Every issue filed by `autop-add-issue` is a short brief for a person. The
pinned spec is the specification for the implementer and both reviewers, who
receive that commit's `spec.md`, `plan.md`, `tasks.md` and constitution.

Story, standalone and human-task bodies have a 4,096-byte ceiling; epic
bodies have a 6,144-byte ceiling. These are UTF-8 byte counts of the whole
body after `autop issue add` appends any `Spec:` and `Blocked-by:` lines. The
CLI refuses a longer body. Omit an optional section or machine line when it
does not apply, but never omit a known constraint.

## Story or standalone issue

```
<1–3 sentences: what is wrong or missing today, what is true once this is done, who notices.>

## What changes
- <2–6 bullets in plain words, each naming the repo, surface or module it touches. No code, SQL, line numbers or file lists.>

## Done when
Full scenarios: [spec, user story N](https://github.com/<org>/<control>/blob/<SPEC_SHA>/specs/NNN-<slug>/spec.md#user-story-N)
- <3–6 one-line checks derived from the scenarios, never copied: happy path, a failure or edge case, and the test or gate that proves it.>

## Out of scope
- <0–3 bullets; omit this section when empty.>

## Size budget
upper bound <= N changed code lines (estimate in tasks.md)

Blocked-by: #N
Integration branch: epic/NNN-<slug>
Spec: <org>/<control>@<SPEC_SHA>:specs/NNN-<slug>/spec.md#user-story-N
```

For a story in a direct repository, omit `Integration branch:`; its PR
targets the default branch. An integration-repository story keeps the line.

## Human-task issue

Use this variant only for a genuinely human action. It replaces `## What
changes` with the exact intervention evidence section; no placeholders may
remain in a filed issue.

```
<1–3 sentences: what is blocked, what becomes true after the action, who notices.>

## Human intervention
- Action: <precise human action and responsible role>
- Why automation cannot: <specific permission, capability or decision boundary>
- Evidence: <observed failure or explicit policy/source, and recovery tried or ruled out>
- Resume when: <observable completion condition>

## Done when
Full scenarios: [spec, user story N](https://github.com/<org>/<control>/blob/<SPEC_SHA>/specs/NNN-<slug>/spec.md#user-story-N)
- <3–6 one-line checks derived from the scenarios, never copied.>

## Out of scope
- <0–3 bullets; omit this section when empty.>

## Size budget
upper bound <= N changed code lines (estimate in tasks.md)

Blocked-by: #N
Integration branch: epic/NNN-<slug>
Spec: <org>/<control>@<SPEC_SHA>:specs/NNN-<slug>/spec.md#user-story-N
```

## Issue without a pinned spec

Use this story/standalone fallback and write 3–8 checks. The heading is
machine-read, so never append text to it. A human-task fallback replaces
`## What changes` with `## Human intervention` as above.

```
<1–3 sentences: what is wrong or missing today, what is true once this is done, who notices.>

## What changes
- <2–6 bullets in plain words, each naming the repo, surface or module it touches.>

## Acceptance criteria
- <3–8 one-line, atomic, observable checks.>

## Out of scope
- <0–3 bullets; omit this section when empty.>

## Size budget
upper bound <= N changed code lines (estimate in tasks.md)

Blocked-by: #N
Integration branch: epic/NNN-<slug>
```

## Epic issue

```
<2–4 sentences: the outcome when every story is done, who benefits.>

## Stories
- [ ] `<org>/<repo>` — <one-line deliverable> (#N)

## Rollout
- <1–4 bullets: order, compatibility, what deploys when, any human step.>

Full plan: [spec](https://github.com/<org>/<control>/blob/<SPEC_SHA>/specs/NNN-<slug>/spec.md) · [plan](https://github.com/<org>/<control>/blob/<SPEC_SHA>/specs/NNN-<slug>/plan.md)

Integration branch: epic/NNN-<slug>
Integration repositories: <org>/<a>, <org>/<b>
Direct repositories: <org>/<c>, <org>/<d>
Release order: `<org>/<a>` → `<org>/<b>`
Blocked-by: #N
Spec: <org>/<control>@<SPEC_SHA>:specs/NNN-<slug>/spec.md#user-story-1
```

`Integration repositories:`, `Direct repositories:`, `Release order:` and
`Blocked-by:` appear only when they apply. The epic always keeps its
`Integration branch:` line, including when every repository is direct. The
shared contract, architecture and rollout detail stay in `plan.md`. Every
story sub-issue has its own distinct brief. An integration-repository story
repeats the epic's `Integration branch:` line verbatim; a direct story omits
that line.
