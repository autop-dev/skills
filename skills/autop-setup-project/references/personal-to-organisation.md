# Personal account → organisation

Read this when the person's repositories or board are owned by a personal
GitHub account. Autop rejects that by design; explain why, then walk the move.
Every step is a write that the **person** confirms or performs. A transfer
changes a repository's owner and URL, so name each repository and the target
organisation, and wait for an explicit yes before running anything.

## Why Autop needs an organisation

1. **The board.** Autop schedules from a GitHub Projects (v2) board. GitHub
   Apps can read and write a Projects board only when an organisation owns
   it (the organisation *Projects* permission); a board on a personal account
   is closed to every App. The only other way in is a personal access token.
2. **No personal access token, ever.** A token acts as the person on every
   repository they can reach until revoked. The three Autop Apps instead get
   short-lived per-job tokens, limited to the repositories selected for each
   App, and uninstalling them removes all access at once.
3. **Verified authority.** Autop links an organisation only after GitHub
   confirms the signed-in account is an *owner*, re-checks it, and pauses
   projects if ownership is lost. Teammates get roles instead of a shared
   account.
4. **One boundary per project.** Board, product repos and the control repo
   live in one organisation under the same three installations; nothing
   outside it can join the project, and personal repositories stay untouched.
5. **Free.** GitHub Free for organisations includes unlimited public and
   private repositories.

## The move

1. **Organisation.** Create one at
   https://github.com/account/organizations/new on the *Free* plan (the
   person does this; you become owner). Skip if they already own one; check
   with `gh api user/memberships/orgs --jq '.[] | "\(.organization.login) \(.role)"'`
   (`admin` = owner). To give the organisation the person's current name,
   follow "Keeping the personal account's name" below instead.
2. **Transfer each repository** (requires admin on the repository and
   permission to create repositories in the organisation). Web: *Settings →
   General → Danger Zone → Transfer ownership*. CLI, after confirmation:
   ```sh
   gh api repos/<LOGIN>/<REPO>/transfer -f new_owner=<ORG>
   ```
   The organisation must not already have a repository of the same name.
3. **Update clones.** GitHub redirects the old address, but update anyway:
   ```sh
   git remote set-url origin https://github.com/<ORG>/<REPO>.git
   ```
4. **Board.** A personal Projects board cannot be transferred. Create one in
   the organisation (*Projects → New project*, or `gh project create --owner
   <ORG> --title <TITLE>`), give it the `Status` options from SKILL.md, and add
   the transferred issues. The personal board can stay as a private view.
5. **Apps.** The person installs *Autop ATC*, *Autop Coder* and *Autop
   Reviewer* on the organisation and selects the repositories.
6. **Link.** With github.com signed in as the account they use for Autop,
   the person opens https://app.autop.dev/orgs → *Link another organisation*.
   A different GitHub account in the browser is the usual reason nothing
   links: Autop puts an unknown account on the waitlist instead.

## Keeping the personal account's name

If the person wants the organisation to carry their current GitHub name, so
every repository keeps the same `github.com/<LOGIN>/<REPO>` address, use
GitHub's documented route ("Converting a personal account into an
organization", the keep-your-personal-account steps), in one sitting:

1. The person renames their personal account (*Settings → Account → Change
   username*), e.g. `<LOGIN>` → `<LOGIN>-personal`.
2. The person immediately creates the organisation named `<LOGIN>`; the old
   name is free for anyone to claim in between.
3. Transfer the repositories from `<LOGIN>-personal` to `<LOGIN>`. Addresses
   match the old ones, so clones need no `set-url`.

Creating the organisation first and renaming it afterwards also works but adds
a rename. Effects of the username change: profile and gists move to the new
username; links and @mentions of the old name now reach the organisation;
commits made with an email on the account stay attributed. The Autop account
is keyed to the GitHub user id, so it survives the rename; sign in again.
Reference:
https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-your-personal-account/converting-a-user-into-an-organization

## What a transfer keeps, and what to check

GitHub's reference:
https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository

- **Moves:** code, branches, tags and history; issues and pull requests with
  comments; releases; wiki; stars and watchers. Webhooks, secrets and deploy
  keys stay attached.
- **Redirected:** web links and `git clone`/`fetch`/`push` to the old address,
  until a new repository with the old name is created on the personal account.
- **Check afterwards:** collaborator access (prefer organisation teams), branch
  protection or rulesets, CI that names the old owner, and packages. A default
  `github.io` Pages address is **not** redirected; a custom domain is unaffected.

Public guide for the person: https://app.autop.dev/guide/organisations
