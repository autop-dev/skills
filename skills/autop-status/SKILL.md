---
name: autop-status
description: Use when the user asks what Autop is doing or why it isn't, such as "autop status", "what is autop working on", "why is my issue still in Todo", "is the runner online", "what needs a human", "show me autop's open PRs", "what did the audit find". Reads the project's GitHub board, issues, pull requests and labels with gh, and this machine's runner with autop runner status, then explains each item's state in Autop's terms and what, if anything, a person must do. Read-only.
---

# Autop status

Autop's state is visible in three places: the organisation's Projects v2
board (cards and `Status`), the issues and PRs themselves (labels, native
sub-issue and blocked-by links, bot comments), and the console at
https://app.autop.dev (jobs, runners, logs). This skill reads the first two
with `gh` and the local runner with `autop`, and points at the console for
the rest. It changes nothing.

## Step 1 — Find the project

Reuse the discovery from `autop-add-issue` Step 1: the control repo's
`AGENTS.md` names the board (`https://github.com/orgs/<ORG>/projects/<N>`)
and the repos. Without it, ask for the board URL once.

## Step 2 — Read the board

```bash
gh project item-list <N> --owner <ORG> --format json --limit 200
```

Group the open cards by `Status` and show them with their repo, number,
title, priority label and blockers. Then explain each column in Autop's
terms:

- **Todo**: waits for the sweep. It is picked in priority order (`P0` first,
  `P0` also dispatches straight from the webhook). It will **not** be picked
  while it carries `epic`, `human-task`, `needs-human` or
  `blocked-on-question`, while it has an open blocker (native blocked-by or
  a `Blocked-by:` line), or while no runner
  is online that has its repo cloned and the routed runtime ready. Name
  which of these applies to each stuck card. Missing priority labels put work
  last; they do not by themselves prevent dispatch.
- **In Progress**: a job holds it. The console shows the job and its log.
- **Ready for Review**: a PR exists and Autop's reviewer has posted or is
  posting its verdict; merge follows the project's policy (required checks,
  reviewer approval on the current head, any required human approvals).
- **Blocked**: a blocker is open, or a hold applies (an epic's `human-task`
  hold covers its children).
- **Done**: merged or closed.

## Step 3 — Read issues and PRs that need attention

```bash
gh issue list --repo <ORG>/<repo> --label needs-human --state open --json number,title,url
gh issue list --repo <ORG>/<repo> --label blocked-on-question --state open --json number,title,url
gh pr list --repo <ORG>/<repo> --state open --json number,title,isDraft,author,baseRefName,reviewDecision,statusCheckRollup,url
```

For each `needs-human` or `blocked-on-question` issue, read the last comment
by `autop-coder[bot]` / `autop-reviewer[bot]` and summarise the question or
the evidence. For each open PR authored by `autop-coder[bot]`: draft or
ready, check status, review decision, and whether it targets the default
branch or an `epic/…` integration branch. For an epic
(`autop issue subs <ORG>/<repo>#<N>`), list its sub-issues and their states.

**Audit issues.** The project audit (a read-only review of the project's
repositories) files each finding as an issue labelled `audit`. Query every
product repo and the control repo:

```bash
gh issue list --repo <ORG>/<repo> --label audit --state all --json number,title,labels,state,url
```

The title carries the severity, `Audit S1: …` to `Audit S4: …`, at one of
four levels:

- **S1 critical**: an exposed credential or private key, an authentication bypass, unauthenticated data exposure.
- **S2 high**: credential handling that leaks under a common failure, a missing signature, CSRF or origin check, a dependency with a known critical advisory, CI running untrusted code with write tokens.
- **S3 medium**: missing branch protection or required checks, unpinned dependencies, weak session settings, verbose errors, over-broad tokens.
- **S4 low**: hygiene.

The body names one of six categories: `secrets-and-credentials`,
`dependencies-and-supply-chain`, `ci-cd-and-branch-protection`,
`authentication-and-sessions`, `data-exposure-and-logging`,
`infrastructure-configuration`. The first, fourth and fifth add the
`security` label. The priority label follows the severity: S1 → `P1`, S2 →
`P2`, S3 and S4 → `P3` (never `P0`). Every finding issue carries `autop`,
which puts it on the board as Todo. An S1 issue also carries `needs-human`
and waits for a person to confirm the finding before Autop changes anything:
the person removes `needs-human` to let Autop fix it, or closes the issue as
not planned (the audit never files it again). S2 and below are worked like
any other issue. Only findings at or above the project's floor (S2 unless the
project sets `audit.floor`) get their own issue; an S1 or S2 finding in a
public repository is filed in the control repository with the repository
name in its title (`Audit S1 [<ORG>/<repo>]: …`). One summary issue per
audit run, `Audit summary <date>` in the control repository and labelled
`audit` only (no `autop`, so it stays off the board and Autop never works
it), gives the counts per severity and lists the rest: the issues filed, the
findings below the floor, and any withheld because the control repository is
public. The report itself is committed to the control repository under
`audits/<date>/` (`audits/<YYYY-MM-DD>/<project slug>-<job id prefix>.md`)
when that repository is private, and is shown on the audit job's page in the
console.

## Step 4 — This machine's runner

```bash
autop runner status  # direct-host configuration
# Container configuration:
docker compose -f ~/.autop/container/compose.yml run --rm runner runner status
```

Report whether it is configured here, which repos are `ready` and which are
`workspace missing` or `not a clone`, and which runtimes are listed. A repo
missing here means jobs for it cannot be served by this machine. Whether
the runner is *online* and whether other runners exist is only in the
console (Runners page); say so rather than guessing.

## Step 5 — Answer the question

Lead with the direct answer ("#42 is still in Todo because its blocker #41 is open"), then the full picture, then
what a person must do, with the exact command or console page:

- "What did the audit find?": open the most recently created
  `Audit summary <date>` issue in the control repository, give its counts per severity, list the filed
  `audit` issues with their state, name each S1 waiting on `needs-human`,
  and point at the report under `audits/<date>/` or the job in the console.
- A missing label: `gh issue edit <N> --repo <ORG>/<repo> --add-label P2`.
- A question from the bot: answer in the issue, then remove
  `blocked-on-question`.
- A `needs-human` incident: inspect the evidence linked in the comment
  before re-running anything; Autop may already have published.
- Steering by comment (write access only): `@autop-coder` or `/autop`
  instructs the coder, even on a held item, without changing labels;
  `@autop-reviewer` with a ruling forces a review that clears `needs-human`;
  removing `needs-human` retries. Neither changes policy. Details and a
  ruling template: [references/steering-prs.md](references/steering-prs.md).
- Pausing or resuming a project or runner, re-running a job, and reading a
  job log: console only.

## Guardrails

- Read-only: no label edits, comments, re-runs or merges from this skill;
  suggest the command and let the person run it.
- Never print tokens or authenticated URLs.
- Do not infer a job's state from the board alone when the console
  disagrees; the console is the authority for jobs and runners.
