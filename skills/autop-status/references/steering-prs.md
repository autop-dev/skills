# Steering the coder and reviewer

Read this when the person asks how to unblock, redirect or overrule Autop on
a pull request or issue. Autop follows comments only from people with write
access (GitHub association `OWNER`, `MEMBER` or `COLLABORATOR`); comments
from bots and other users are ignored. This skill is read-only: suggest the
comment or label change and let the person make it.

| The person wants | They do | Autop then |
|---|---|---|
| A change on a PR | Comment, review or inline-comment on a PR labelled `autop` | The coder addresses it (push or reply). Ignored while the PR has `needs-human`. |
| To instruct the coder directly | `@autop-coder …`, or a comment starting with `/autop`, on a PR (comment, review body, inline) or an issue | The coder acts on it even on a held item. On an issue it may open or advance a PR. Labels and the board card are unchanged. A parent epic's `human-task` hold still refuses it. |
| To settle a reviewer finding / unblock a PR | `@autop-reviewer` plus a ruling | Forced review: removes `needs-human`, skips the draft, CI and round-cap gates, passes the comment to the reviewer as context. |
| To retry after fixing the cause | Remove `needs-human` | Draft: pre-review counter reset and a fresh bounded pre-review on the current head. Ready PR: forced review with no note. |

A plain comment on a `needs-human` PR does nothing.

## A finding only a human can decide

The pre-reviewer reads the diff, the PR title and body, the pinned spec and
the coder's decline. When it keeps blocking on a finding the person has
already decided, the PR reaches the round cap and gets `needs-human`;
removing the label alone repeats that. Suggest a reviewer mention instead:

```text
@autop-reviewer Ruling on the finding at path/to/file.yml:123:
<what was decided, and why>. This finding does not apply here.
Do not block on it; review the rest.
```

- **Weighed, not obeyed.** The reviewer is told to weigh the note and reach
  its own verdict. A specific ruling (file, line, decision, reason) should
  drop the finding, but the pinned spec can still lead back to it.
- **Draft may stay draft.** Only an approved `pre_review` marks a draft ready
  (control C15). If the forced review approves and the PR is still a draft,
  the person chooses *Ready for review* or merges.
- **Make it stick.** Record the ruling as a clarification in that spec's
  `DECISIONS.md` in the control repo. Issues pin the spec at a commit, so
  issues filed afterwards carry it; open work relies on the mention.

Public version for the person: https://app.autop.dev/guide/collaborate
