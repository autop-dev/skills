# Steps 2 and 3: the questions, the refusal rule, the AGENTS.md section, re-runs

## How to ask

One question per message; wait for the answer before the next. Each
question names the fact, shows the proposed default and, where the evidence
offers more than one value, numbered choices with "other" last:

```text
Release branch: the branch whose head is what production runs.
Default: main (profile), checkout: main
  1. main   2. production   3. other (type the name)
Enter or "yes" keeps the default; a number or a name changes it.
```

- **The default** is the stored profile's value on a re-run, otherwise the
  evidence table's proposed default, otherwise none (the question then has
  no default and needs an answer, or "none" where the key is optional).
- **Stated, not asked.** When the evidence settles a fact beyond doubt,
  state it in one line and move on: "Release and develop branch: `main`
  (the only branch), model `trunk`, releases tagged `v*` (or: no release
  tags). Say *change* to correct it." Every value it fills is named. Settled
  means: one long-lived branch (questions 1–3); the files of exactly one CI
  system (question 4, with its files); a stored value the checkout agrees
  with. Anything else is asked.
- **The answer wins over the evidence.** Record what the person says, even
  when the checkout suggests otherwise; never argue. A value outside an
  enumeration is recorded as `other` and the person's words go into the
  matching prose section.
- Every answer passes the refusal rule below before it is kept.

## The questions, in order

| # | Question | Default rule | Choices | Key |
|---|---|---|---|---|
| — | Default branch | `gh repo view` (stated, never asked) | — | `branches.default` |
| 1 | Release branch: what production runs | the evidence table's proposal (the model rule in [discovery.md](discovery.md) "Branches") | the long-lived branches from `git ls-remote --heads` | `branches.release` |
| 2 | Develop branch: where feature work integrates | the evidence table's proposal (same rule) | the long-lived branches | `branches.develop` |
| 3 | Branching model, release-branch glob, tag glob | the model rule in [discovery.md](discovery.md) "Branches"; `"v*"` when `v*` tags exist | 1. trunk 2. git-flow 3. release-branches 4. other | `branches.model`, `branches.release_pattern` (only for release-branches, default `"release/*"`), `branches.tags` (only when releases are tagged) |
| 4 | CI system and its files | the system whose files were found, else `none` | 1. github-actions 2. gitlab-ci 3. jenkins 4. cloud-build 5. circleci 6. other 7. none | `ci.system`, `ci.config` (the files found; the person may add or drop paths; a system other than `none` with no file found → ask for the paths, required; left out for `none`) |
| 5 | Checks a pull request must pass | the job and required-check names from the evidence | the names, numbered; "all", numbers, or "none" | `ci.gates` (left out for none) |
| 6 | Each deploy target: name, kind, config, trigger (one question per target, then "another target?") | the evidence row: kind from the manifest, trigger from the workflow | kind: 1. firebase-hosting 2. cloud-run 3. compute-vm 4. kubernetes 5. docker-compose 6. serverless 7. static-site 8. app-store 9. package-registry 10. other; trigger: 1. push-to-release 2. tag 3. manual 4. other | `deploy[]`: `name`, `kind`, `config`, `trigger`; "nothing is deployed" → `[]` |
| 7 | Each environment: name, branch it follows, public URL (one per environment, then "another?") | names from workflow `environment:` keys; branch the release branch for `production`; URL none, never guessed | the long-lived branches for the branch | `environments[]`: `name`, `branch`, `url` (optional keys left out when unanswered) |
| 8 | Each service hint: confirm or correct its name and purpose; then "a service missing?" with name and purpose | the name and purpose from the evidence table | 1. keep 2. correct 3. drop | `services[]`: `name`, `purpose`, `evidence` (the package or key *name* that showed it; none for an added one) |
| 9 | Each data store: confirm name and purpose, managing service; then "a store missing?" | the evidence's name; purpose `primary store` for the first; `managed_by` none | 1. keep 2. correct 3. drop | `data_stores[]`: `name`, `purpose`, `managed_by` |
| 10 | Anything else to record (who deploys, release checklist, freeze windows)? | nothing; on a re-run the stored `## Notes` text is kept and an answer is appended below it | free text | `## Notes` |

The skill writes the four factual prose sections from the answers, one or
two sentences each, in the person's terms; a section with nothing to say
carries "Nothing recorded.". The front matter keys follow the order of
[profile-format.md](profile-format.md); a key the person left unanswered
and the contract marks optional is left out, never written as `null`.

## The refusal rule

Before keeping any answer, free text included, refuse it when it would put
into the profile: a credential or a credential-looking string (what the
credential test of the filter in [discovery.md](discovery.md) "Existing
profile" withholds: the prefixes `gh[pousr]_`, `github_pat_`, `sk-`,
`xox[abprs]-`, `AKIA`, `AIza`, `eyJ`; a private key; a long mixed-case or
hex string, tested per `/`-separated part so a file path passes; a
password); a value
from an environment file or a `NAME=value` pair; a URL with user
information (`@` after `://`), a query string (`?`) or a fragment (`#`). A
`?` anywhere in a front matter value fails the skills repository's profile
check (`.github/check.py`, which CI runs on the example only; nothing checks
the control repository), so a question mark in a purpose is rephrased too.
Never repeat the refused value. Say this one line and ask the same
question again:

> That can't go in the profile: no credentials, no environment values, no
> URL with a user, a query string or a fragment. Give a name, or a public
> URL with a path at most.

Internal hostnames and addresses are never proposed as defaults; the
person may volunteer one.

## The `## Branches and delivery` section of AGENTS.md

At most ten lines, heading included, filled from the answers. One deploy
line per target, at most three; more targets → "see the profile". With
`ci.system: none` the CI line reads "CI: none."; with no deploy target the
deploy line reads "Deploy: nothing is deployed.".

```markdown
## Branches and delivery

- Release branch `<release>` (what production runs); develop branch `<develop>` (feature work integrates here); model `<model>`.
- CI: `<ci.system>` (`<ci.config>`); a pull request must pass <gates, or "the CI checks">.
- Deploy: `<name>` (`<kind>`), <trigger>.
- How this repository is delivered: [`profile/<repo>.md`](https://github.com/<AP_REPO>/blob/<AP default branch>/profile/<repo>.md) in the control repository `<AP_REPO>`; edit it there.
```

`AGENTS.md` absent → create it with this section only. A section with this
exact heading outside a code fence → replace it in place, from the heading
to the next `# ` or `## ` heading outside a code fence, or the end of the
file; a second such section is removed; nothing else in the file changes.
Otherwise append it at the end, after one blank line. The link resolves
once the control repository's pull request merges.

## Re-runs

- **Defaults** come from the stored profile through the filter in
  [discovery.md](discovery.md) "Existing profile"; a value it prints as
  `<withheld>` is never a default and is never written back: ask afresh.
- **Rewritten:** the front matter keys this contract names and the four
  factual prose sections, from the new answers. Unknown keys inside a
  `deploy`, `environments`, `services` or `data_stores` entry stay with the
  entry the person kept or corrected (renamed included); a dropped entry's
  keys go with it, named in the write list.
- **Kept verbatim:** the `## Notes` text, never edited (a new answer to
  question 10 is appended below it; a lone "Nothing recorded." gives way to
  it); front matter keys the contract does not name, after the known keys
  of their mapping. Step 3 copies both with one script that re-fetches the
  raw file (the first line of the Step 1 command, `gh api …` or `git show`,
  not the filter: a shell variable does not outlive its call), takes the
  YAML of the unknown keys and the Notes text from it, and writes the new
  file without printing it. When an open pull request's branch is updated
  (below), the stored file is the one on `origin/<branch>` (`git show`
  form), for the defaults as well as for Notes and unknown keys. The
  profile shown in Step 3 prints the Notes as "(kept verbatim, N lines)"
  and unknown keys as the filter prints them; an unknown key the filter
  printed as `<withheld>` is dropped, not copied, and named in the write
  list.
- **`updated`** is set to today. A repository whose file would not change
  (the same `AGENTS.md` section; a profile identical but for `updated`) is
  left out of the write list and said so; nothing changes → nothing to
  write.
- A stored profile whose version is not `1` or whose front matter does not
  parse is never overwritten (Step 1 stops).
- An existing `## Branches and delivery` section in `AGENTS.md` is replaced
  in place.
- After Step 1 and before the interview, first run included, check each
  branch `onboard/profile-<repo>` and `onboard/agents-<repo>`:
  `git ls-remote --heads origin <branch>` and `gh pr list --repo
  <owner>/<name> --head <branch> --state open`. On `origin` with an open
  pull request → ask now: update that branch and its pull request
  (`git worktree add -B <branch> <tmp> origin/<branch>`, apply the new
  files, commit, push; no new pull request), or a new branch. On `origin`
  without an open pull request (merged or closed), or a new branch chosen
  → the first free name of `<branch>-2`, `<branch>-3`, …. The write list
  then names the branch that will be used; nothing is asked after the yes.
  A local branch of that name with commits not on its base (`origin/<branch>`
  when it exists, else `origin/<default>`) → show
  `git log --oneline <base>..<branch>` and ask, also before the interview,
  before `-B` resets it.
- A worktree left by an interrupted run: `git worktree list` names its
  path; `git worktree remove --force <path>`, then `git worktree prune`.
