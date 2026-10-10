# Autop skills

Agent Skills for working with [Autop](https://autop.dev), the Development
Autopilot: file backlog work the way Autop's board sweep expects it, prepare a
repository and organisation for Autop, and read what Autop is doing. They run
in the coding agent you already use (Claude Code, Codex, or any host that
reads the open Agent Skills layout) and never need Autop's own credentials:
every GitHub write goes through your `gh` login.

| Skill | Use it when |
|---|---|
| [`autop-add-issue`](skills/autop-add-issue/SKILL.md) | you want to add a task, story or epic to an Autop project. Runs the intake survey, drives spec-kit in the control repo, files one issue per user story with `autop issue add`, on the board as Todo, with native sub-issue and blocked-by links |
| [`autop-setup-project`](skills/autop-setup-project/SKILL.md) | you are connecting an organisation, repos or a machine to Autop. Checks what exists, prepares `AGENTS.md`, the control repo and labels, hands over the console-side steps, then hands over to `autop-onboard-project` for the project profile |
| [`autop-onboard-project`](skills/autop-onboard-project/SKILL.md) | you want Autop and your team to share how a repository is released: branches, CI/CD, deploy targets, environments, third-party services. Discovers read-only, asks what it cannot infer, writes `profile/<repo>.md` to the control repo through a PR |
| [`autop-status`](skills/autop-status/SKILL.md) | you want to know what Autop is working on, why an issue is stuck, or what needs a human. Read-only |
| `speckit-*` | the seven [GitHub spec-kit](https://github.com/github/spec-kit) authoring skills (`specify`, `clarify`, `plan`, `tasks`, `analyze`, `checklist`, `constitution`) that `autop-add-issue` drives, vendored authoring instructions; the control repo still needs spec-kit's `.specify/` scripts and templates |

## Install

With Autop (requires Git):

```sh
autop skills install
autop skills install --ref <tag-or-commit>  # pin a revision
autop skills list                         # installed managed skills
```

This clones or fast-forward-updates this repository at `~/.autop/skills` and
copies skills to `~/.claude/skills/` and `~/.agents/skills/`. Only copies with
the `.autop-bundled` marker are refreshed; unmarked directories are preserved.
A marked legacy `add-autop-issue` copy is removed during installation.

With the [skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add autop-dev/skills
```

By hand, for Claude Code and for Codex and other hosts that read the portable
directory:

```sh
mkdir -p ~/.autop ~/.claude/skills ~/.agents/skills
git clone https://github.com/autop-dev/skills ~/.autop/skills
ln -s ~/.autop/skills/skills/* ~/.claude/skills/
ln -s ~/.autop/skills/skills/* ~/.agents/skills/
```

The `autop` command (`curl -fsSL https://autop.dev/install.sh | sh`) is needed
by `autop-add-issue` and `autop-status`; `gh` with the `project` scope
(`gh auth refresh -s project`) is needed by all three.

## Layout

```text
skills/<name>/SKILL.md        one skill per directory, frontmatter name = directory
skills/<name>/templates/      files the skill reads
```

## Contributing

Open an issue or a PR. Keep a skill's `description` as the trigger list a host
matches against, keep every GitHub write behind an explicit confirmation, and
never let a skill read, print or pass a token.

## Licence

Apache-2.0 (see `LICENSE`). The `speckit-*` skills are derived from GitHub's
spec-kit, MIT licensed; see `NOTICE`.
