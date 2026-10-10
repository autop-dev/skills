---
name: autop-add-issue
description: Use when the user wants to add a task, issue, epic, or work item to an Autop project's backlog. Triggers include "add an autop issue", "add an autopilot issue", "add a task to the backlog", "file a backlog item", "create an epic", "create an issue on the board", and "queue work for Autop". Discovers the project's organisation board, repos and configured control repo, asks the uniform intake survey, drives GitHub spec-kit in the control repo (specify → clarify → plan → tasks → analyze → readiness checklist), commits a numbered feature spec there, then files one issue per user story pinned to that commit with `autop issue add` — labelled, on the board as Todo, with native sub-issue and blocked-by links.
---

# Add an Autop issue

Files uniform backlog work for Autop: asks the intake survey, writes the spec
with spec-kit, creates the GitHub issue(s) in the right repo(s), puts them on
the project's organisation board with Status=Todo, and links epics and
blockers natively — so Autop's board sweep picks them up in priority order.
Issue creation and relationship writes go through `autop issue` (installed
with the `autop` command). Spec pushes and integration refs use Git and `gh`
under the person's own login.

Do the steps in order. Confirm spec-kit initialization and spec publication
before the writes in Step 3. Confirm the assembled issue plan in Step 4 before
creating issues and integration refs in Step 5.

## What Autop needs from an issue (why each step exists)

- A **card on the project's board** (a Projects v2 board owned by the
  project's GitHub organisation) with **Status = `Todo`**. There is no "Ready"
  column; Autop does not add issues to the board by itself.
- A **priority label** `P0`–`P3`. The board's Priority field is cosmetic; an
  issue without a label is picked last and its comments are ignored. `P0`
  starts immediately from the webhook — use it sparingly.
- Every repo, the board, parent and blockers in the **same organisation**.
- **Epics**: label `epic` plus **native GitHub sub-issues**, one level deep.
  Task lists are not read. Only one sub-issue per epic runs at a time.
- **Ordering**: native "blocked by" relationships (read first) plus
  `Blocked-by:` body lines (the fallback, and what epic finalize re-checks).
- **Epic integration branch**: the epic body records `Integration branch:
  epic/NNN-<slug>`, every story body mirrors that exact line, and the branch
  exists in every repo a story changes. Story PRs branch from and target it;
  only the epic's release PRs target the default branch. ATC refuses a
  story's implement job when its parent's line or branch is missing.
- **Optional `Spec:` line** pinning a commit of the project's control repo; a
  spec in any other repo fails the implement job.
- `epic`, `human-task`, `needs-human` and `blocked-on-question` keep an issue
  from being picked.

## Step 1 — Discover the project

1. **`autop` and `gh`.** `autop --version` must work (else: install Autop's
   CLI, `curl -fsSL https://autop.dev/install.sh | sh`). `gh auth status` must show a login with the `project`
   scope; if not, have the user run `gh auth refresh -s project` and stop
   until they have. Every write in this skill uses *their* `gh` login.
2. **Control repo `$AP`.** Prefer the repository/path explicitly named by
   the user or the workspace's `AGENTS.md` / `README.md` as the **Control
   repository**. The name is arbitrary: `autop-dev/control` is valid. Resolve
   it to a local git checkout and verify `origin` matches that GitHub repo.
   Otherwise look for a conventional `*-autopilot/` checkout at/under cwd or
   its parent, then in the runner's `repos_dir`. Never select a repo merely
   because it contains `.specify/`. Zero or several candidates → ask which
   repository is configured as the project's control repo in the Autop console;
   offer to clone that exact repo if absent. No control repo → Step 3's fallback.
   Set `SPEC_REPO=<owner>/<actual-repo-name>` from the verified `origin`
   (SSH and HTTPS remotes are both valid); never synthesize a repository name.
3. **Organisation `ORG`** = the owner of `$AP`'s `origin`.
4. **Board.** Look for the board URL
   (`https://github.com/orgs/<ORG>/projects/<N>`) in `$AP/AGENTS.md`, then
   `$AP/README.md`. Not found → list the org's open boards with
   `gh project list --owner <ORG> --format json` and ask the user which one
   is the Autop project's board (it is the one selected in the Autop console
   under the project). Keep `BOARD=<ORG>/<N>`; offer to add the URL to
   `$AP/AGENTS.md` so the next run finds it.
5. **In-scope repos.** The repo table/list in `$AP/AGENTS.md` if it has one;
   else the sibling checkouts in the workspace whose `origin` is in `ORG`, and
   confirm the list with the user once. The repos must be the ones the Autop
   project covers (console → project → repositories). **Source of truth:**
   the "Source of truth:" line in `$AP/AGENTS.md`, else ask.
6. **Profiles.** For every in-scope repo read `$AP/profile/<repo>.md` when
   present (written by `autop-onboard-project`; `<repo>` is the name without
   the organisation) and note only `branches.default`, `branches.develop` and
   `branches.release` from its front matter. A repo without one is fine; a
   `profile:` other than `1` or unreadable front matter counts as absent, say so.

Tell the user briefly what you found (board, repos, source of truth).

## Step 2 — Run the intake survey (ASK)

The survey seeds `/speckit.specify`; the spec — not the survey — becomes the
contract. Collect **Title**, **Problem/why**, **Type**, **Priority**,
**Affected repo(s)** and any hard constraints; acceptance criteria are
produced by spec-kit as Given/When/Then scenarios, so do not draft them by
hand. Use structured choices when the host supports them and plain text for
exact values:

- **Affected repo(s)** — **infer first, ask only when ambiguous.** Map the
  request onto the in-scope repos using their roles from Step 1: a request
  naming a repo, a surface ("console", "API", "runner"), or a file path
  usually decides it. When the mapping is clear, don't ask — state the
  inference and its reason in the Step 4 confirmation so the user can veto
  it. Ask a multi-select question (source of truth labelled) only when the
  scope is genuinely ambiguous or a judgment call.
- **Type** — feature · fix · tech-debt · infra · docs.
- **Priority** — P0 (now/blocks others) · P1 (foundations) · P2 (features,
  the default) · P3 (cleanup).
- **Backwards-incompatible? (API/SQL)** — no · YES (then it MUST ship
  coordinated across every consumer).
- **Human-only?** — a step only a person can do (create an account, add a
  secret, provision infra) becomes a `human-task`, which Autop never picks.
- Free text: **Title** (short imperative), **Problem/why** (current
  behaviour, desired outcome, impact, evidence), **Hard constraints**,
  **Depends on** (`owner/repo#N` or bare `#N`), **Links**, **Out of scope**.

Don't ask for anything you can infer. Before asking for missing prose,
inspect `$AP`, the relevant repo docs/code and linked issues read-only. Infer
technical context, not product decisions. Never invent endpoints, files,
metrics, constraints or existing behaviour; label an unresolved detail as an
assumption and ask only when it changes scope or outcome.

## Step 2.5 — Enforce the issue-authoring route

The final issue title and body are implementation specifications. Apply this
purpose matrix exactly:

| Purpose | Eligible final author | Not eligible for that purpose |
|---|---|---|
| Issue authoring/refinement | Claude **Fable** with high thinking (`think-hard` or stronger), or Codex **SOL** with high reasoning effort | Claude Opus/Sonnet and Codex Terra |
| Later implementation (by Autop's runner) | as the project's routing configures | — |

Before Step 3, determine the current host and model. If it is eligible, use
it. Otherwise delegate explicitly to an eligible model through the host's
supported mechanism, passing the user's request plus only the read-only
evidence gathered in Steps 1–2. Never let an ineligible session author the
final body, silently fall back, or perform a GitHub write. If the host cannot
delegate, stop before Step 3 and tell the user which route is unavailable and
how to select it. The user still confirms before anything is created.

## Step 3 — Author the spec with spec-kit (in `$AP`)

**Bootstrap (lazy).** If `$AP/.specify/` does not exist: `uv tool install
specify-cli --from git+https://github.com/github/spec-kit.git` (skip if
`specify --version` works), then in `$AP` `specify init --here --ai <claude|codex>
--non-interactive`. Seed `$AP/.specify/memory/constitution.md` with
`/speckit.constitution`, fed from the architecture invariants in `$AP/AGENTS.md`
and every in-scope repo's `AGENTS.md` code-review focus — the constitution is
the reviewer's checklist. Commit and push `$AP` `main`. If spec-kit cannot be
installed or initialised, say so, skip the rest of Step 3, and file without
`--spec`, with a hand-written `## Acceptance criteria` section held to the
specificity contract below.

The installed CLI may name the commands `/speckit-*` (hyphen) instead of
`/speckit.*`; use whichever the host lists. Work in `$AP` on `main`; read code
from the sibling checkouts when planning.

1. `/speckit.specify <the survey, verbatim>` → `specs/NNN-<slug>/spec.md` with
   prioritized user stories, Given/When/Then scenarios, `FR-###`, `SC-###`.
2. `/speckit.clarify` — ask the user every question it raises, repeat until
   spec.md has **zero `[NEEDS CLARIFICATION]` markers**. Autop implements
   headlessly and cannot ask later.
3. `/speckit.plan` → `plan.md`; `/speckit.tasks` → `tasks.md`, every task
   tagged `[USn]`. Apply the story sizing gate below before analysis.
4. `/speckit.analyze` — fix every reported inconsistency.
5. `/speckit.checklist autop readiness: one PR per story, at most 300 changed
   code lines per story excluding comments and tests, every FR has a scenario,
   every scenario has a test task` — compare with
   `templates/readiness-checklist.md` (in this skill) and make every item
   `[x]`. Split stories exceeding either 300 code lines or 12 tasks; a small
   task count alone does not establish readiness.
6. **Declare every extra file a task binds to.** Autop ships an implement job
   only `spec.md`, `plan.md`, `tasks.md`, the constitution and the files listed
   in the feature's `inputs.json`; the job's token cannot read the control repo.
   When a task or FR points at a file under `contracts/` or `inputs/` (copy,
   a schema, a source SVG), write `specs/NNN-<slug>/inputs.json`:
   `{"version": 1, "files": [{"path": "contracts/content.md", "sha256": "<hex>"}]}`
   with `sha256` from `shasum -a 256` of the committed bytes. Limits: 16 files,
   64 KiB each, 256 KiB in total, UTF-8 text. Re-hash after every edit of a
   declared file.
7. **The spec must be on GitHub before anything pins it** (Autop fetches the
   pinned files from the control repo at that commit):
   `git -C "$AP" remote get-url origin` must succeed, else STOP.
8. Commit and push, staging `.specify` too:
   `git -C "$AP" add specs .specify && git -C "$AP" commit -m "spec: <slug>" && git -C "$AP" push`.
   Record `SPEC_SHA=$(git -C "$AP" rev-parse HEAD)` and
   `SPEC_REPO` from the verified origin (for example `autop-dev/control`).

### Story sizing gate (also applies without spec-kit)

Every implementation story must fit **at most 300 changed lines of code**
across all its files and repositories combined. Count added + deleted
nonblank production-code lines in the intended diff; a replacement counts
both sides. Exclude comments, docstrings, documentation and tests (including
test-only fixtures); include SQL migrations, executable scripts, production
configuration, UI markup and styles. A line containing code still counts when
it has an inline comment. Do not use net line growth or compress formatting to
meet the limit.

Before filing, inspect the likely code and record a per-file estimate range,
its total upper bound, assumptions, and excluded test work in each story's
`## Size budget` and, when using spec-kit, `tasks.md`. Include foundational work
in its owning story's budget. If the upper bound exceeds 300, or uncertainty
prevents a credible bound, narrow the scope and split it before filing. Recheck after planning,
analysis and any scope change; never rubber-stamp a 300-line estimate.

Split by small, independently verifiable outcomes with explicit contracts and
blockers, preserving every acceptance scenario and required test. Even a
single user-visible feature becomes an **epic with multiple story sub-issues**
when it exceeds the budget. Repeat until every child fits; neither an epic nor
one large task hides implementation work. Prefer repo-local stories, while
keeping genuinely atomic cross-repo contract changes coordinated within the
same combined budget. Use the existing 12-task ceiling as an additional guard.

Code size is not a runtime guarantee. Record the required gates and their
observed runtime where available (otherwise mark it unknown), separately from
the code estimate. Allow time for implementation, gates, review and publication
within the configured job deadline; split further when the work is still too
large. Excluding tests from the line count never permits skipping required
gates or raising the timeout to make an oversized story fit.

### Issue structure

- **One user story passing the sizing gate →** one plain issue (no epic).
- **Two or more stories →** one **epic** in the source-of-truth repo + one
  issue per story. The epic body records `Integration branch:
  epic/NNN-<slug>` and every story body carries the same line verbatim; the
  branch is created from the default branch in each repo a story changes
  (Step 5) before that repo's stories are filed. If tasks.md has a non-empty
  Foundational phase, every story after the P1 story is blocked by it;
  otherwise stories are independent.
- File each story in the repo its `[USn]` tasks change. A story spanning
  repos still gets ONE issue, in the source-of-truth repo, naming the others.
- At most 100 stories per epic (GitHub's sub-issue limit), all in `ORG`.
  Otherwise revise the plan before filing anything.
- Epic sub-PR automerge is the project's configuration, not a per-epic
  question; add no labels to authorize merging.

## Step 4 — Assemble + confirm

Build one body per issue from `templates/issue-body.md` (in this skill): the
story's Given/When/Then scenarios copied verbatim from spec.md, the `[USn]`
tasks, compatibility, dependencies with `Blocked-by:` lines, links, non-goals.
Write each body to its own temp file.

### Specificity contract

Each issue is a standalone implementation brief a fresh agent can execute
without the chat. Concise is fine; vague is not.

- **Problem:** current behaviour or gap, desired outcome, who/what is
  affected, why it matters; concrete surfaces found during discovery. Not a
  restated title.
- **Scope:** the repo-specific responsibility, constraints, integration
  points, verified likely files; required behaviour vs hints.
- **Acceptance:** 3–8 atomic, observable, pass/fail checks (the spec's
  scenarios) covering happy path, failure/edge cases and verification. Never
  "works correctly", "handle edge cases", or "add tests" without saying what.
- **Boundaries:** non-goals, preserved behaviour, labelled assumptions.

For an **epic** add the end-to-end outcome, shared contract, rollout,
ordering, and a checklist mapping every sub-issue to its repo and
deliverable. Every **sub-issue** gets a distinct body for its repo: the epic
link, the epic's `Integration branch:` line verbatim, its inputs/outputs, its
exact deliverable, its dependencies, repo-local acceptance. Never copy the
epic body into the sub-issues.

**Quality gate** before showing the plan: a fresh implementer can tell what
changes, where, why, and what stays; every criterion is testable; claims are
grounded or labelled; every story passes the sizing gate, including the
no-spec fallback; sub-issues are non-duplicative and cover the epic;
swapping two sub-issue bodies would be obviously wrong. Revise until true.

**Show the user the planned issues** — titles, repos (with the inference
reason), priority, board, epic/sub-issue structure, blockers, per-story code
estimates and verification runtime assumptions — and get an
explicit yes. Issue creation is outward-facing. For an epic, name for each
repo a story changes the branch its integration branch is cut from:
"integration branch cut from `<default>`", the GitHub default branch Step 5
cuts from, read with
`gh repo view <ORG>/<repo> --json defaultBranchRef -q .defaultBranchRef.name`.
When that repo's profile records a `develop` that differs from it, add one
sentence: "the profile records `<develop>` as the develop branch; Autop
integrates and releases on the default branch today, the profile's branch is
for a later plane feature".

## Step 5 — Create + register

Use `autop issue add` for every issue. It validates everything first (same
organisation, `--spec` format, the board is visible and has `Status`/`Todo`),
then creates the issue with the `autop` and priority labels (plus `epic` /
`human-task`), adds it to the board with Status=Todo and the Priority field
when the board has one, appends the `Spec:` / `Blocked-by:` lines the body
lacks, and writes the native sub-issue and blocked-by links. It prints the new
issue's URL on the first line (`created <url>`).

```bash
autop issue add --board "$BOARD" --repo <ORG>/<repo> --priority P2 \
  --title '<title>' --body-file <body.md> \
  [--spec "$SPEC_REPO@$SPEC_SHA:specs/NNN-<slug>/spec.md#user-story-<n>"] \
  [--epic] [--human] [--parent <ORG>/<repo>#<epic>] [--blocked-by <ref>]...
```

**Epic — create in this order** (a link can only name an issue that exists):

1. The **epic**, in the source-of-truth repo: `--epic --spec …#user-story-1`.
2. The **integration branch**, in every repo a story changes, when absent:

   ```bash
   gh api -X POST repos/<ORG>/<repo>/git/refs -f ref=refs/heads/epic/NNN-<slug> \
     -f sha="$(gh api repos/<ORG>/<repo>/git/ref/heads/<default branch> --jq .object.sha)"
   ```

   (`gh repo view <ORG>/<repo> --json defaultBranchRef -q .defaultBranchRef.name`
   names the default branch). An existing `epic/NNN-<slug>` is kept as is;
   never reset or delete it.
3. The **P1 story**: `--parent <epic ref> --spec …#user-story-1`; note its
   number.
4. The remaining stories: `--parent <epic ref> --spec …#user-story-<n>`, plus
   `--blocked-by <P1 story ref>` when tasks.md has a Foundational phase, and
   any other known blockers.
5. Verify: `autop issue subs <epic ref>` must list exactly the story issues
   created in this session. Retry only a missing link with
   `autop issue link <story ref> --parent <epic ref>`; stop with the exact
   mismatch if GitHub refuses.

If `autop issue add` exits non-zero **after** printing `created <url>`, the
issue exists: do not re-run `add` for it. Finish the named missing step —
`autop issue link …` for relationships; for the board, add the card and set
Status=Todo in the GitHub UI or with `gh project item-add` /
`gh project item-edit` — then continue. `autop issue labels <ORG>/<repo>…`
creates or refreshes every label Autop uses.

## Step 6 — Report

Print each issue URL, repo, priority and board placement (Status=Todo); for an
epic, the epic and its sub-issues. Autop's sweep picks Todo cards in priority
order (blockers first); `P0` starts immediately. Nothing else to do.

## Guardrails

- Never file while spec.md has `[NEEDS CLARIFICATION]` or the readiness
  checklist has an unchecked item, or a story lacks a credible code estimate
  with an upper bound of at most 300 lines (including the no-spec fallback).
- Never file a story whose tasks bind to a `contracts/` or `inputs/` file
  that the feature's `inputs.json` does not declare with its current hash.
- Never edit a spec after filing without re-pinning: a spec change is a new
  commit and every `Spec:` line must move to it.
- Never file a story under an epic without the epic's `Integration branch:`
  line in its body and that branch present in its repo; never tell a story
  to target the default branch as a shortcut.
- Never hard-code the board, repos or organisation; discover them (Step 1).
- Only file into the project's repos in `ORG`; a repo outside them → flag it
  and ask.
- Don't start implementing — this skill only files the work.
- Every issue filed by an agent carries the `autop` label (`autop issue add`
  adds it); do not remove it.
- Never print, store or pass a token; `gh` holds the login.
