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
- **Services**: third-party integrations by name and purpose, with the
  package or environment key *name* that showed them.
- **Data stores**: each store with its purpose and managing service.
- **Prose**: Branches and delivery, CI/CD, Deploy and environments,
  Third-party services, Notes.

Keys, enumerations and section order:
[references/profile-format.md](references/profile-format.md). The control
repository's `profile/README.md` is written once, verbatim from
[references/profile-README.md](references/profile-README.md).

## Step 1 — Discover (read-only)

Nothing is written in this step: no file, branch, commit, fetch, checkout or
install, in any checkout (only a clone of the control repository the person
accepts). `git status --porcelain` reads the same before and after.

1. **`gh` and the product repository.** `gh auth status` must show a login.
   In the checkout, `git remote get-url origin` and
   `gh repo view --json nameWithOwner,isInOrganization,defaultBranchRef`
   give `REPO=<org>/<repo>` and the default branch. Not a git checkout →
   ask for the product repository's path. `isInOrganization` false → say the
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
   repository. `$AP`'s owner must be `<org>`. When `$AP`'s `origin` is the
   checkout's own `origin`, the person is in the control repository: ask
   which product repository to profile and where its checkout is, and
   continue there.
3. **Existing profile.** Read `$AP/profile/<repo>.md` if it exists. With
   `profile: 1` its values are the defaults, and the evidence is shown next
   to them. Any other version, or front matter that does not parse, is
   unreadable: say so, and Step 3 will not overwrite it.
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

Ask one question at a time, in the order branches, CI/CD, deploy and
environments, third-party services, data stores, anything else.
Each question shows the proposed default and numbered choices; what the
evidence settles is stated, not asked, and the person's answer wins.

## Step 3 — Write (ask once, then do)

Assemble the profile exactly as the contract says and show the full write
list once: the control repository's branch and files, the product
repository's `## Branches and delivery` section of `AGENTS.md` that links to
the profile, and every commit message. After an explicit yes, commit on a
branch in each repository and open the pull requests with the person's `gh`
login, or push directly only when asked.

## Report

Print the pull request links (or the pushed commits), the profile path in
the control repository, and the next step: file the first story with
`autop-add-issue`.

## Guardrails

- Never the console, App installations, enrollment tokens or provider
  logins: those are the person's actions in https://app.autop.dev and on
  GitHub.
- Every write is listed and confirmed once before it happens; nothing is
  written before an explicit yes.
- Never run `autop issue add`; filing work is `autop-add-issue`.
- Nothing from an environment file beyond key names reaches the profile or
  the transcript: open only `.env.example`, `.env.sample`, `.env.template`
  and `.env.dist`, read names only, never a value, and never open `.env`,
  `.env.local`, `.env.production`, `*.pem`, `*.key`, `secrets*` or
  `credentials*`. No credential, URL with user information or query string,
  or internal hostname the person did not volunteer goes into the profile
  ([references/profile-format.md](references/profile-format.md), "What must
  never appear").
- Run in a product repository's checkout, not the control repository; the
  profile is written only to the control repository, never to the product
  repository, which gets only its `AGENTS.md` section.
- Organisation projects only: a checkout owned by a personal account stops
  the skill; `autop-setup-project` explains the move to an organisation.
