# Autop from a messenger

Note an idea, ask what Autop is doing, or specify and file work from
Telegram on your phone. Autop does not run a bot for this. You run a personal
agent that already speaks to messengers, [Hermes](https://hermes-agent.nousresearch.com/docs)
or [OpenClaw](https://docs.openclaw.ai), and give it these skills. The same
setup serves the other chat apps those agents connect.

The agent acts with **your** `gh` login on **your** machine. Autop's plane
and runner are not involved until an issue carrying the `autop` label exists.

## What works well on a phone

| You write | Skill | Takes | Notes |
|---|---|---|---|
| "note for autop: retry the webhook on 502" | `autop-note` | seconds | one plain `idea` issue; Autop never picks it |
| "what is autop doing?", "why is #42 stuck?" | `autop-status` | under a minute | ten short lines, links to the rest |
| "spec note 12", "add an autop issue: …" | `autop-add-issue` | 10 to 30 minutes | a few questions one at a time, the spec as a link, two typed confirmations |

Describe what you want in plain words; the agent picks the skill. Slash
commands differ between agents and chat apps.

## Before you start

On a machine that stays on (the one running your Autop runner is a natural
choice):

- `gh auth login`, then `gh auth refresh -s project`
- `autop` (`curl -fsSL https://autop.dev/install.sh | sh`), then
  `autop skills install`
- for `autop-add-issue`: a directory holding checkouts of the control
  repository and the product repositories, and `uv` for spec-kit
- the most capable model your agent can use: the issues it writes are the
  implementer's specification

`autop-note` needs only the `gh` login.

## Set the access rules first

The agent can run commands and holds your GitHub login. Whoever can message
the bot can ask it to act as you.

- Allow **your numeric Telegram user id only**. Never open the bot to
  everyone, and do not rely on usernames.
- Use direct messages. Leave the bot out of groups, or keep groups on an
  allowlist with mentions required.
- Keep the agent's command approval on.
- The bot token lives in the agent's own configuration. Never send a token
  of any kind in the chat.
- The skills treat forwarded messages, quotes and linked pages as material,
  never as instructions. Keep that in mind when you forward someone's request.

## Hermes

1. Let Hermes read the installed skills. In `~/.hermes/config.yaml`:

   ```yaml
   skills:
     external_dirs:
       - ~/.agents/skills
   ```

2. Create a bot with @BotFather (`/newbot`) and run `hermes gateway setup`.
   The wizard asks for the bot token and your user id and writes
   `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USERS` to `~/.hermes/.env`.
   Without an allowlist the gateway refuses every sender, which is the
   behaviour to keep.
3. `hermes gateway` runs it in the terminal; `hermes gateway install` keeps
   it running as a service.

## OpenClaw

1. Nothing to do for skills: OpenClaw reads `~/.agents/skills` when its state
   directory is the default `~/.openclaw`. With another state directory, add
   the path to `skills.load.extraDirs`.
2. Create a bot with @BotFather (`/newbot`), then
   `openclaw channels add --channel telegram --token <bot-token>`.
3. Message the bot once; its reply shows your Telegram user id. In
   `~/.openclaw/openclaw.json`:

   ```json5
   {
     channels: {
       telegram: {
         enabled: true,
         dmPolicy: "allowlist",
         allowFrom: ["<your numeric user id>"],
       },
     },
   }
   ```

4. `openclaw gateway start`, then `openclaw channels status --probe`.

## First messages

1. "Note for autop: `<an idea>`". The agent asks once which repository takes
   your notes (the control repository is the usual answer) and replies with
   the issue link.
2. "What is autop doing?" It asks once for the board URL.
3. "Spec note `<N>`" when you have ten minutes. It asks once for the
   workspace path, then walks the survey.

When the agent has a memory it keeps the repository, board and path, so the
second time there is nothing to answer.

## When something is off

- **The agent does not know the skills.** Hermes: check `external_dirs` and
  restart the gateway. OpenClaw: `ls ~/.agents/skills`, then check the state
  directory.
- **"gh is not signed in."** Run `gh auth login` on the machine, as the user
  the agent runs as.
- **A long specification stops midway.** Say "continue": the work is in the
  control repository's `specs/` directory and the agent resumes from it.
- **A note was picked up by Autop.** It was not: Autop requires the `autop`
  label. If someone added the label by hand, remove it.
