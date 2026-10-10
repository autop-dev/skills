---
name: autop-onboard-project
description: Use when the user wants to record how a product repository is delivered for Autop (the Development Autopilot), or asks "onboard my project", "record how we release", "fill the project profile", "autop onboarding interview", "which branch does autop use". Discovers branches, CI/CD, deploy targets, environments, third-party services and data stores read-only from the checkout, asks one question at a time only what it cannot infer, and writes the project profile `profile/<repo>.md` to the control repository through a pull request after one confirmation. Never touches the Autop console, App installations, enrollment tokens, provider logins or environment values.
---

# Onboard a project: the project profile

The project profile is one Markdown file per product repository,
`profile/<repo>.md` in the project's **control repository** (for `acme/api`:
`profile/api.md`). It records how that repository is delivered, in a YAML
front matter block that tools parse and prose sections that people own.
People read and edit it; `autop-add-issue` reads its branches when filing
work; the project audit reads its front matter. This skill fills it from the
checkout first and from the person second, then writes it once, confirmed.
The format is versioned (`profile: 1`) and documented in
[references/profile-format.md](references/profile-format.md); a complete
example is [references/example-profile.md](references/example-profile.md).

## What the profile records

- **Branches**: the default branch, the release branch (what production
  runs), the develop branch (where feature work integrates), the branching
  model, optional release-branch and tag globs.
- **CI**: the system, its configuration files, the checks a PR must pass.
- **Deploy**: each target with its kind, configuration files and trigger.
- **Environments**: each name with the branch it follows and its public URL.
- **Services**: by name and purpose, with the package or key *name* seen.
- **Data stores**: each store with its purpose and managing service.
- **Prose**: five sections, `## Branches and delivery` to `## Notes`.

## Step 1 — Discover (read-only)

Nothing is written in this step: no file, branch, commit, fetch, checkout or
install, in any checkout (only a clone of the control repository the person
accepts, placed next to the product checkout, never inside it).
`git status --porcelain` reads the same before and after.

1. **`gh` and the product repository.** `gh auth status` must show a login.
   In the checkout, read `origin` and `gh repo view` only through the
   command in [references/discovery.md](references/discovery.md) "Product
   repository", never printed whole: it keeps `<owner>/<name>` alone from
   the remote URL (user info, query string and fragment, which can hold a
   token, are dropped; SSH and HTTPS remotes are both valid) and masks a
   credential-looking repository or default branch name. It gives
   `REPO=<org>/<repo>` and the default branch. A fork → ask for the
   organisation repository's checkout. Not a git checkout → ask for
   the product repository's path. `isInOrganization` false → say the
   profile belongs to an organisation project, point at the setup skill's
   [personal-to-organisation.md](../autop-setup-project/references/personal-to-organisation.md),
   and stop.
2. **Control repo `$AP`.** Prefer the repository/path explicitly named by
   the user or the workspace's `AGENTS.md` / `README.md` as the **Control
   repository**. The name is arbitrary: `autop-dev/control` is valid. Resolve
   it to a local git checkout and verify `origin` matches that GitHub repo.
   Otherwise look for a conventional `*-autopilot/` checkout at/under cwd or
   its parent, then in the runner's `repos_dir`. Never select a repo merely
   because it contains `.specify/`. Zero or several candidates → ask which
   repository is configured as the project's control repo in the Autop console;
   offer to clone that exact repo if absent. No control repo → finish this
   step and stop after the table; the profile is never written to the product
   repository. Set `AP_REPO=<owner>/<actual-repo-name>` from the verified
   `origin` (SSH and HTTPS remotes are both valid); never synthesize a
   repository name. `$AP`'s owner must be `<org>` (case-insensitively);
   otherwise ask again. When `AP_REPO` equals `REPO` (compare owner/name
   case-insensitively, not remote URLs), the person is in the control
   repository: ask which product repository to profile and where its
   checkout is, and redo item 1 there. The candidates command in
   [references/discovery.md](references/discovery.md) "Control repository"
   lists the checkouts this rule allows.
3. **Existing profile.** Read `profile/<repo>.md` from `$AP`'s default
   branch on GitHub (offline, `origin/HEAD`) only through the filter in
   [references/discovery.md](references/discovery.md) "Existing profile",
   which validates it and withholds credential-looking values; never print
   it whole. Not found → no defaults, continue. With `profile: 1` its
   values are the defaults, and the evidence is shown next to them (the
   merge in discovery.md "The evidence table"). Any other version, or front
   matter that does not parse as YAML, is unreadable: say so and stop after
   the table; the skill never overwrites it.
   On a re-run Step 3 keeps the stored `## Notes` text and unknown keys,
   refreshes `updated`, and replaces the `AGENTS.md` section in place.
4. **Evidence.** Follow [references/discovery.md](references/discovery.md):
   branches and `v*` tags with the model rule, CI files and gates, deploy
   manifests with kind and trigger, environments, package manifests to
   services, example environment files to key *names* only (secret-looking
   names marked), compose images and driver packages to data stores. Never
   open a forbidden file.
5. **Show** the evidence table (fact · evidence · proposed default), the
   files opened, and the forbidden files seen but not opened. No value from
   an environment file and no credential-looking string appears.

## Step 2 — Interview

Ask one question at a time, in the order of
[references/questions.md](references/questions.md): branches (release,
develop, model), CI/CD (system, gates), deploy targets (kind, trigger) and
environments (branch, public URL), third-party services (confirm or correct
each hint, add missing ones with a purpose), data stores, then "anything
else to record". Each shows the proposed default (stored value on a re-run,
else the evidence) and numbered choices (the enumeration, or the values the
evidence offers). What the evidence settles beyond doubt (one branch, one
CI system) is stated, not asked. The person's answer wins over the
evidence. Refuse an answer that would put a credential, an environment
value or a URL with user information, a query string or a fragment in the
profile: say the one-line rule of questions.md, never echo it, ask again.

## Step 3 — Write (ask once, then do)

1. **Assemble** `profile/<repo>.md`: front matter in the key order of
   [references/profile-format.md](references/profile-format.md) with
   `profile: 1`, `repository: <org>/<repo>`, `updated` today and every
   required key, then the five prose sections in order; on a re-run keep
   `## Notes` and unknown keys (questions.md "Re-runs"). Fill the
   `AGENTS.md` section from the template in questions.md (≤ 10 lines).
2. **Show once** the profile, the section and the write list. `$AP_REPO`:
   branch `onboard/profile-<repo>` from its default branch with a pull
   request (the default branch itself only when the person asks for a
   direct push); `profile/README.md` only when absent there, verbatim from
   [references/profile-README.md](references/profile-README.md);
   `profile/<repo>.md`; commit `docs: profile <repo>`. `$REPO`: branch
   `onboard/agents-<repo>`, `AGENTS.md` gaining or replacing `## Branches
   and delivery`, commit `docs: link the project profile`, a pull request.
   Write nothing before an explicit yes.
3. **Write** in a temporary worktree per repository (`git fetch origin`,
   `git worktree add -B <branch> <tmp> origin/<default>`; an existing
   branch or worktree → questions.md "Re-runs"), so no checkout's working tree
   changes: commit, `git push -u origin <branch>`, `gh pr create --repo
   <owner>/<name> --base <default> --head <branch>` under the person's
   login. A direct push is `git push origin HEAD:<default>`; rejected →
   offer the branch and pull request. `gh pr create` refused → print
   `https://github.com/<owner>/<name>/compare/<default>...<branch>`. Remove
   the worktrees.

## Report

Print the pull request links (or the pushed commits, or the compare links),
the profile path `<AP_REPO>:profile/<repo>.md`, and the next step: file the
first story with `autop-add-issue`. Never run `autop issue add`.

## Guardrails

- Never the console, App installations, enrollment tokens or provider
  logins: those are the person's actions in https://app.autop.dev and on
  GitHub.
- Every write is listed and confirmed once; nothing before an explicit yes.
- Never run `autop issue add`; filing work is `autop-add-issue`.
- Nothing from an environment file beyond key names reaches the profile or
  the transcript: open only `.env.example`, `.env.sample`, `.env.template`
  and `.env.dist`, read names only, never a value, and never open `.env`,
  `.env.local`, `.env.production`, `*.pem`, `*.key`, `secrets*`,
  `credentials*` or the other files listed in
  [references/discovery.md](references/discovery.md). No credential, URL
  with user information or query string, or internal hostname the person
  did not volunteer goes into the profile
  ([references/profile-format.md](references/profile-format.md), "What must
  never appear").
- Run in a product repository's checkout, not the control repository; the
  profile is written only to the control repository, never to the product
  repository, which gets only its `AGENTS.md` section.
- Organisation projects only: a checkout owned by a personal account stops
  the skill; `autop-setup-project` explains the move to an organisation.
