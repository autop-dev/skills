---
name: autop-setup-project
description: Use when the user wants to connect a GitHub organisation, repositories or a machine to Autop (the Development Autopilot), or asks "set up autop", "prepare this repo for autop", "onboard my project to autop", "install the autop runner", "why isn't autop picking my issues". Walks the real onboarding order (console sign-in, the three GitHub Apps on the organisation, the Projects v2 board, the control repo, labels, an enrolled runner), checks what is already done read-only, and prepares the repository-side files (AGENTS.md, control repo, labels) without touching the Autop console, App installations or secrets.
---

# Set up a project for Autop

Autop turns issues on a GitHub Projects board into reviewed pull requests,
using the coding CLI (`claude`, `codex`, `gemini`) already installed and logged in on
the customer's own machine. Setup has a console side (done by a person at
https://app.autop.dev) and a repository side (which this skill prepares).
Check first, change second, and never do the console side on the person's
behalf: installing Apps, creating projects and enrolling runners are explicit
human actions.

## What a working project needs

| Piece | Where | Who does it |
|---|---|---|
| Sign-in and a workspace | https://app.autop.dev (GitHub OAuth) | person |
| Three GitHub Apps installed on the **organisation** that owns the repos: *Autop ATC*, *Autop Coder*, *Autop Reviewer* | GitHub org settings, via the console's install links (Organisations page, in that order) | person (org owner) |
| A Projects v2 board **owned by that organisation** with a `Status` field holding `Todo`, `In Progress`, `Ready for Review`, `Blocked`, `Done` (a `Priority` field with `P0`–`P3` is optional, cosmetic) | GitHub | person, or this skill with `gh` |
| A **control repo** in the same organisation holding the playbook (`AGENTS.md`), `specs/` and spec-kit (`.specify/`) | GitHub | created by the console (or by the person from the console's prefilled link); this skill fills it |
| Every product repo and the control repo covered by all three App installations | GitHub | person, from the console's per-App links (the Organisations coverage table, the project page) |
| `AGENTS.md` in every product repo: how to build, test and lint, the code-review focus | repo | this skill |
| Autop's labels in every repo (`autop`, `P0`–`P3`, `epic`, `human-task`, `needs-human`, `blocked-on-question`) | repo | `autop issue labels` |
| A project in the console binding organisation + board + control repo + repos, with agent routes | console | person |
| At least one enrolled runner online, with ready repos and a usable coding CLI (ATC queues preparation jobs for missing policy repos) | the person's machine | person, with `autop runner setup` |

Personal-account repos and boards are rejected by design: everything lives
in one organisation the tenant owns. Why, and how to move repositories from a
personal account into a free organisation without losing history, issues or
pull requests: [references/personal-to-organisation.md](references/personal-to-organisation.md).

## Step 1 — Discover (read-only)

1. `gh auth status` must show a login; `autop --version` tells whether the CLI
   is installed (if not: `curl -fsSL https://autop.dev/install.sh | sh`).
2. Determine the organisation from the current checkout's `origin`
   (`gh repo view --json owner,nameWithOwner`). A personal owner is a blocker:
   say so, explain why and offer the move in
   [references/personal-to-organisation.md](references/personal-to-organisation.md);
   continue only once the repos live in an organisation the person owns.
3. Apps: `gh api orgs/<ORG>/installations --jq '.installations[].app_slug'`
   (needs org admin). Expect `autop-atc`, `autop-coder`, `autop-reviewer`.
   Missing ones go on the person's list; never try to install an App.
4. Board: `gh project list --owner <ORG> --format json`. If one looks like the
   project's board, check its fields with
   `gh project field-list <N> --owner <ORG> --format json` for the `Status`
   options above.
5. Control repo: look for `<something>-autopilot` or `control` in the org
   (`gh repo list <ORG> --json name`), or ask. Note whether it has
   `AGENTS.md`, `specs/` and `.specify/`.
6. Labels in each product repo: `gh label list --repo <ORG>/<repo>`.
7. Runner on this machine: `autop runner status` (reports config, ready repos
   and runtimes; non-zero exit means the local configuration could not be loaded).

Report the table above with ✓ / ✗ per row before changing anything.

## Step 2 — Prepare the repository side (ask once, then do)

Show the person the list of writes and get a yes.

- **Control repo.** Fill the existing control repo found in Step 1; do not
  create one. When none exists yet, the console creates it while the person
  creates the project (Step 3), or the person creates it from the console's
  prefilled link: hand over the console side first and fill the repository
  once it exists. Only when the person prefers the manual route and says so,
  offer `gh repo create <ORG>/<name> --private` with the name they confirm;
  with "Only select repositories" they then add it to each App themselves.
  Add an `AGENTS.md` that names the organisation, the board URL
  (`https://github.com/orgs/<ORG>/projects/<N>`), the product repos with one
  line each on their role, the "Source of truth:" repo, and the architecture
  invariants reviewers must enforce. Initialise spec-kit when absent:
  `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
  then `specify init --here --ai <claude|codex> --non-interactive`, and seed
  `.specify/memory/constitution.md` from those invariants. Commit and push.
- **Product repos.** For each repo without an `AGENTS.md`, draft one from
  what the repo already declares (package manifests, CI workflow, Makefile,
  existing README): the exact build, test and lint commands, the layout, the
  conventions, and a "Code review focus" section. Never invent a command;
  verify each one runs. A `CLAUDE.md` that is a one-line import of
  `AGENTS.md` keeps Claude Code and Codex on the same file. Commit on a
  branch and open a PR, unless the person asks for a direct push.
- **Labels.** `autop issue labels <ORG>/<repo> ...` for every product repo
  and the control repo (once it exists).
- **Board.** If no board exists and the person agrees, create one:
  `gh project create --owner <ORG> --title "<name>"`, then add the missing
  `Status` options and the optional `Priority` field through the GitHub UI
  (`gh` cannot edit single-select options). Say exactly which options to add.

## Step 3 — Hand over the console side

Print the remaining person-only steps in order, each with its link:

1. Sign in at https://app.autop.dev and open **Organisations**. Install
   *Autop ATC*, *Autop Coder* and *Autop Reviewer* on `<ORG>` in that order,
   from the page's numbered steps. GitHub asks which repositories each App
   may see; choose knowingly. **All repositories** is the simple path: it
   covers every repository, including ones created later such as the control
   repo. **Only select repositories** is the strict path: it covers only the
   chosen ones, so a repository created later must be added to each App.
   Both are supported; an uncovered cell in the page's coverage table links
   to the settings of the App that lacks the repository.
2. Create the project: organisation, board, control repo, product repos. For
   the control repo use **Create it for me** (the console creates
   `<slug>-autopilot`), or the prefilled link to create it on GitHub when
   that action is not offered (the form says when accepting Autop ATC's
   updated permissions would enable it). Check the agent routes (which
   profile implements, reviews, repairs) and the merge policy. If the control
   repo is new, come back so this skill fills it (Step 2's control repo
   bullet).
3. If the project starts paused ("waiting for App access to the control
   repository"), add the control repo to each App the project page lists,
   from its settings links, then Refresh. The project activates by itself once
   all three Apps cover it; there is no Resume to press.
4. On the machine that will do the work: `curl -fsSL https://autop.dev/install.sh | sh`,
   the installer runs `autop runner setup`; enter the enrollment token only
   at its hidden prompt. The wizard configures and starts the runner, and ATC
   queues `prepare_repo` jobs for missing policy repos. For container mode,
   check readiness with
   `docker compose -f ~/.autop/container/compose.yml run --rm runner runner status`;
   for direct-host mode use `autop runner status`. Status is local readiness,
   not proof the service is online; verify that in the console.
   The runner needs the coding CLI logged in on that machine; Autop never
   sees those credentials.
5. Smoke test: file one small, reversible story with `autop-add-issue` (a
   documentation change is ideal) and watch its job, PR, review and board
   move in the console.

## Guardrails

- Never install a GitHub App, create a console project, enroll a runner, or
  handle an enrollment token, App key or provider login. Those are the
  person's actions.
- Never put a repo or board from another organisation or a personal account
  into the setup; Autop rejects it and the person should know why.
- Do not run `autop issue add` here; filing work is `autop-add-issue`.
- Every write (repo creation, pushes, labels, board) is listed and confirmed
  before it happens.
