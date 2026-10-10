# Decisions

## Issue #2: autop-setup-project describes the guided connect flow (032 US6)

Spec: autop-dev/control@6ef1ef133290138af94dffac724f8b4f04558148:specs/032-connect-organisation/spec.md#user-story-6

- **D2-1 (2026-10-10) Console copy source.** The skill names console labels
  ("Organisations" numbered steps, "All repositories" / "Only select
  repositories", "Create it for me", the prefilled link, "waiting for App
  access to the control repository", Refresh, no Resume) as fixed in spec
  US4/US5 and plan §US4/§US5, because the web sources were not readable from
  this repository's job. Rejected: generic wording without the labels, which
  would not let the person find the actions the console shows.
- **D2-2 (2026-10-10) Agent routes check kept.** The old Step 3 item 3 (agent
  routes and merge policy) is folded into the new item 2 (create the project)
  so T038's five-item order holds. Rejected: dropping the check, which the
  spec does not ask for.
- **D2-3 (2026-10-10) Fill after the console creates it.** Step 2 runs before
  Step 3, so when no control repo exists yet the skill hands over the console
  side first, then fills and labels the repository (with a fresh
  confirmation) before the runner and smoke-test steps; `gh repo create` is
  offered only when the person asks for the manual route. Rejected: keeping
  creation in Step 2 as the default, which FR-023 removes.
