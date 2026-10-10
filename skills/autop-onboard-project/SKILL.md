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

Resolve the product repository, its organisation and the control repository,
and read any existing profile there as the defaults.
Gather the evidence the checkout already holds and show it as a table of
fact, evidence and proposed default; nothing is written.

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
