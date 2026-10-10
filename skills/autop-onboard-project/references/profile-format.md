# The project profile format (version 1)

A project profile is `profile/<repo>.md` in the project's control
repository, one file per product repository. `<repo>` is the product
repository's name without the organisation (every repository of a project
lives in one organisation, so the name is unique): `profile/api.md` for
`acme/api`. `profile/README.md` is written once, when the directory is
created, and the skill never rewrites it.

The file is Markdown with a YAML front matter block delimited by `---` lines,
followed by prose sections. A consumer that needs only the facts parses the
front matter and ignores the prose. This page restates the contract of the
Autop control repository (`specs/034-onboarding-interview/contracts/project-profile.md`);
the two do not diverge, and the skills repository's CI validates
[example-profile.md](example-profile.md) against the required keys below.

## Front matter

Required keys are marked **required**. Unknown keys are ignored by consumers
and preserved by the skill. Values are strings unless stated.

```yaml
---
profile: 1                       # required; the format version of this file
repository: acme/api             # required; owner/name
updated: 2026-10-10              # required; ISO date of the last write
branches:                        # required
  default: main                  # required; GitHub's default branch
  release: main                  # required; the branch whose head is what production runs
  develop: main                  # required; the branch feature work integrates into (equal to release on trunk-based projects)
  model: trunk                   # required; one of trunk | git-flow | release-branches | other
  release_pattern: "release/*"   # optional; glob of release branches when model is release-branches
  tags: "v*"                     # optional; glob of release tags, when releases are tagged
ci:                              # required
  system: github-actions         # required; one of github-actions | gitlab-ci | jenkins | cloud-build | circleci | other | none
  config:                        # required when system is not none; list of paths relative to the repository root
    - .github/workflows/ci.yml
  gates:                         # optional; list of the checks a PR must pass, by their visible names
    - lint
    - test
deploy:                          # required; may be an empty list when nothing is deployed
  - name: api                    # required; a label for the deploy target
    kind: cloud-run              # required; one of firebase-hosting | cloud-run | compute-vm | kubernetes | docker-compose | serverless | static-site | app-store | package-registry | other
    config:                      # optional; paths relative to the repository root
      - Dockerfile
      - deploy/compose.yml
    trigger: push-to-release     # required; one of push-to-release | tag | manual | other
environments:                    # required; may be an empty list
  - name: production             # required
    branch: main                 # optional; the branch this environment follows
    url: https://api.example.com # optional; a public URL without credentials, user info or query string
services:                        # required; may be an empty list; names and purposes only
  - name: Stripe                 # required; the integration's name
    purpose: payments            # required; one line
    evidence:                    # optional; how the skill found it: a package name or an environment key NAME
      - stripe (package)
      - STRIPE_SECRET_KEY (environment key name)
data_stores:                     # required; may be an empty list
  - name: PostgreSQL             # required
    purpose: primary store       # required
    managed_by: Cloud SQL        # optional; the hosting service, by name
---
```

### Required keys

`profile` (the number `1`), `repository`, `updated`, `branches.default`,
`branches.release`, `branches.develop`, `branches.model`, `ci.system`,
`ci.config` (when `ci.system` is not `none`), `deploy`, `environments`,
`services`, `data_stores`. Inside the lists: `deploy[].name`, `deploy[].kind`,
`deploy[].trigger`, `environments[].name`, `services[].name`,
`services[].purpose`, `data_stores[].name`, `data_stores[].purpose`.
`deploy`, `environments`, `services` and `data_stores` may be empty lists.

### Enumerations

| Key | Values |
|---|---|
| `branches.model` | `trunk`, `git-flow`, `release-branches`, `other` |
| `ci.system` | `github-actions`, `gitlab-ci`, `jenkins`, `cloud-build`, `circleci`, `other`, `none` |
| `deploy[].kind` | `firebase-hosting`, `cloud-run`, `compute-vm`, `kubernetes`, `docker-compose`, `serverless`, `static-site`, `app-store`, `package-registry`, `other` |
| `deploy[].trigger` | `push-to-release`, `tag`, `manual`, `other` |

## Prose sections

After the front matter, in this order, each introduced by a level-two
heading. A section the person had nothing to say about carries the single
line "Nothing recorded."

1. `## Branches and delivery` — how a change reaches production, in words.
2. `## CI/CD` — what runs, where it is configured, what blocks a merge.
3. `## Deploy and environments` — the targets, the environments, who deploys.
4. `## Third-party services` — one line per service with its purpose.
5. `## Notes` — anything else the person wanted recorded. The skill never
   edits this section's text on a later run; it only keeps it.

## What must never appear

- A credential of any kind: API keys, tokens, passwords, private keys,
  connection strings with a password, signed URLs. The skills repository's
  credential scan rejects recognisable formats; the rule is stricter: no
  value from an environment file, only key names.
- A URL that carries user information (`user:pass@host`), a query string or
  a fragment. Environment URLs are public hostnames with a path at most.
- Anything read from `.env`, `.env.local`, `.env.production`, `*.pem`,
  `*.key`, `secrets*`, `credentials*` or a secret store. The skill opens only
  `.env.example`, `.env.sample`, `.env.template` and `.env.dist`, and reads
  key names only.
- Internal hostnames or addresses the person did not volunteer.

## Who reads it

- **People** edit the file by hand; the prose sections are theirs.
- **`autop-add-issue`** reads `branches` for every repository a story
  changes and names them in its confirmation. Autop's epic integration
  branches are cut from, and its release pull requests target, the
  repository's default branch; a profile whose `develop` differs is
  information for the person until the control plane reads profiles.
- **The project audit** reads the front matter of every profile at the
  control commit its job pins, when present; a missing profile is not an
  error.
- **The control plane** does not read the profile yet.

## Editing by hand

Edit `profile/<repo>.md` in the control repository like any other document.
Keep the front matter between the two `---` lines
valid YAML, keep every required key, use only the enumeration values above,
and refresh `updated` to the day of the edit. To add a service, append an
entry with `name` and `purpose` (and `evidence` if you like) to `services`
and a line to `## Third-party services`. Write prose under the five headings
in their order; put anything that fits nowhere else under `## Notes`, which
a later run of the skill keeps verbatim, together with any key it does not
know.

## Compatibility

`profile: 1` is the only version. A future version adds keys without
renaming or removing the ones above; a consumer reading an unknown version
treats the file as absent and says so.
