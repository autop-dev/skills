# Project profiles

Each file `profile/<repo>.md` in this directory describes how one product
repository of the project is delivered: its branches, CI/CD, deploy targets,
environments, third-party services and data stores. `<repo>` is the
repository's name without the organisation (`profile/api.md` for
`acme/api`). People read it; `autop-add-issue` reads its branches when it
files work; the project audit reads its front matter.

## Who writes it

The `autop-onboard-project` skill writes a profile: run it in the product
repository's checkout and it discovers what it can, asks what it cannot
infer, and opens a pull request here. After that the file is yours: edit it
by hand like any other document in this repository.

## Front matter and prose

The block between the two `---` lines at the top is YAML front matter, the
machine-readable part. Keep it valid YAML, keep `profile: 1` and every
required key, use the listed values for `branches.model`, `ci.system`,
`deploy[].kind` and `deploy[].trigger`, and set `updated` to the day of your
edit. To add a service, append a `name` and a `purpose` under `services`.

The prose below it is yours. It has five sections, in this order:

1. `## Branches and delivery` — how a change reaches production.
2. `## CI/CD` — what runs, where it is configured, what blocks a merge.
3. `## Deploy and environments` — the targets, the environments, who deploys.
4. `## Third-party services` — one line per service with its purpose.
5. `## Notes` — anything else; a later run of the skill keeps it verbatim.

A section with nothing to say carries the line "Nothing recorded."

## Never a credential

Never a credential, never a value from an environment file, never a URL with
a password or token. Services are recorded by name and purpose, with at
most a package name or an environment key *name* as evidence. URLs are
public hostnames with a path at most: no user information, no query string,
no fragment.

## The full format

Every key, its enumerations and the rules are in `profile-format.md` of the
public Autop skills repository:
https://github.com/autop-dev/skills/blob/main/skills/autop-onboard-project/references/profile-format.md

## Updating a profile

Run `autop-onboard-project` again in the product repository's checkout. It
shows the stored values as the defaults, rewrites the front matter and the
first four sections from your answers, keeps `## Notes` and any key it does
not know, refreshes `updated`, and opens a pull request.
