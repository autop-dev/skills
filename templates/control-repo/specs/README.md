# Feature specifications

New work lives in `NNN-<slug>/`, numbered sequentially by spec-kit
(`001-…`, `002-…`). The number is a spec ID, not a GitHub issue number.
Author on this repository's default branch; the helper stores the local
feature selection in the ignored `.specify/feature.json` and needs no
implementation branch here.

Each ready feature contains `spec.md`, `plan.md`, `tasks.md`, a checked
readiness checklist under `checklists/`, and `DECISIONS.md` when decisions
were made. Optional research, contracts and data models belong beside them.
Acceptance scenarios and `[USn]` tasks define the story boundaries: one issue
per user story.

Commit and push before pinning. An issue names its story with a line of the
form `Spec: <owner>/<control-repo>@<full-sha>:specs/NNN-<slug>/spec.md#user-story-N`;
Autop fetches `spec.md`, `plan.md`, `tasks.md` and
`.specify/memory/constitution.md` from that commit. A change after filing is a
new commit and requires explicitly re-pinning the issue.
