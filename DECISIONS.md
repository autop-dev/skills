# Decisions

## Issue #2 — autop-setup-project describes the guided connect flow (032 US6)

Spec: autop-dev/control@6ef1ef133290138af94dffac724f8b4f04558148:specs/032-connect-organisation/spec.md#user-story-6

- **D2-1 Console copy source.** `autop-dev/web` is outside this job's token
  scope (404), so the skill's wording for the console (Organisations steps,
  "All repositories" / "Only select repositories", "Create it for me", the
  prefilled link, "waiting for App access to the control repository",
  Refresh, no Resume) follows the copy fixed in spec US4/US5 and plan §US4/§US5.
- **D2-2 Agent routes check kept.** The old Step 3 item 3 (agent routes and
  merge policy) is folded into the new item 2 (create the project) so the
  five-item order of T038 holds without dropping the check.
- **D2-3 Fill after the console creates it.** Step 2 runs before Step 3, so
  when no control repo exists yet the skill hands over the console side first
  and fills the repository once the console (or the person, from the prefilled
  link) has created it; `gh repo create` is offered only when the person asks
  for the manual route.
