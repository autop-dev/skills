# Gate declarations

`.github/autop-gates.toml` version 1 tells Autop which required gates the
runner must make green locally and which ones CI proves. Propose it from the
repository's `AGENTS.md` gates and the check names produced by
`.github/workflows/*.yml`; copy each CI name exactly as it appears in a pull
request's checks list.

## Version 1 format

| Key | Required | Meaning |
|---|---|---|
| `version` | yes | Integer `1`. |
| `[[gate]]` | yes | One table per gate; 1–50 tables. At least one gate must be `local`. |
| `gate.name` | yes | 1–80 characters after trimming; unique case-insensitively. |
| `gate.run` | yes | 1–500 characters after trimming, with no newline or NUL. For a `ci` gate this documents the command CI owns; the runner does not execute it. |
| `gate.where` | no | `local` (the default) or `ci`. |
| `gate.ci_check` | for `ci` only | 1–200 characters; exact, case-sensitive check-run name or status context from the PR checks list. It is forbidden for a local gate. |
| `gate.why` | no | Short explanation, at most 200 characters. |

The UTF-8 file may be at most 16 KiB. Unknown keys, wrong types, duplicate
names, unsupported versions, and any other rule violation make the whole
declaration invalid. Autop then treats it as absent. Keep at least one gate
local so the runner always has something it can prove before publishing.

Both the runner and the plane read the declaration at the **base branch tip**,
not from the pull request's head or the worktree. A declaration change
therefore takes effect only after it merges. A declared `ci` gate is never run
locally by an Autop job; the plane holds the merge until the named check passes
on the pull request head. If the repository has no CI, every gate must stay
`local` or the declaration must be omitted—nothing can prove a `ci` gate.

## Worked example

Suppose `AGENTS.md` requires lint, unit, Testcontainers integration, and a
sibling-repository drift check. The workflow gives the CI-owned jobs explicit
names:

```yaml
# .github/workflows/checks.yml
jobs:
  integration:
    name: Testcontainers integration
    steps:
      - run: pnpm test:integration
  sibling-drift:
    name: Sibling repository drift
    steps:
      - run: ./scripts/check-sibling-drift.sh
```

After confirming those exact names in a pull request's checks list, propose:

```toml
# .github/autop-gates.toml
version = 1

[[gate]]
name = "lint"
run = "pnpm lint"
where = "local"

[[gate]]
name = "unit"
run = "pnpm test:unit"
where = "local"

[[gate]]
name = "integration"
run = "pnpm test:integration"
where = "ci"
ci_check = "Testcontainers integration"
why = "Needs the container services provided by CI"

[[gate]]
name = "sibling-drift"
run = "./scripts/check-sibling-drift.sh"
where = "ci"
ci_check = "Sibling repository drift"
why = "CI checks out the sibling repository at the required revision"
```

Do not infer `ci_check` from a filename or a guessed job identifier. If the
workflow omits `jobs.<id>.name`, verify the displayed check name on a real pull
request and copy that value. Present the file as a proposal and create or
commit it only after the person confirms the write.
