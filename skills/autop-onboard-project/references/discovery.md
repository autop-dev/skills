# Step 1 discovery: what to read, how, and what it suggests

Read this during Step 1 of `autop-onboard-project`. Every command here only
reads. Run them from the root of the product repository's checkout. Never
`git fetch`, `pull`, `checkout`, `switch` or `stash`, and never install,
build or start anything. Afterwards `git status --porcelain` must print what
it printed before. Every finding is a hint for the interview, and the
person's answer wins.

## The evidence table

Print one row per fact, and keep the rows in this order. The evidence is the
path or the command that showed the fact. The proposed default is a value
from the contract's enumerations ([profile-format.md](profile-format.md)), or
`none` when nothing was found. If an existing profile was read, show its
value as the default and add "(profile)". When the checkout disagrees, add
"checkout: <value>".

| Fact | Evidence | Proposed default |
|---|---|---|
| Default branch | `gh repo view --json defaultBranchRef` | `main` |
| Long-lived branches | `git ls-remote --heads origin` | `main` only |
| Release tags | `git ls-remote --tags origin 'v*'` | none |
| Branching model | the rule below | `trunk` (release = develop = `main`) |
| CI system and files | `.github/workflows/ci.yml` | `github-actions` |
| Gates | job names in `.github/workflows/ci.yml` | `lint`, `test` |
| Deploy target | `Dockerfile`, `deploy/compose.yml` | `docker-compose`, trigger `manual` |
| Environments | workflow `environment:` keys | none |
| Environment key names | `.env.example` (names only) | none |
| Services | `package.json`: `stripe` | Stripe (payments) |
| Data stores | `deploy/compose.yml` image `postgres:17` | PostgreSQL |

Below the table, list every file you opened, by path. Then list the
forbidden files you saw in the checkout, by name only, marked "not opened".
To see them, use `ls -a` on the root and on each directory that holds a
manifest; it prints names only.

To fill the last column, keep the profile filter's output as `defaults` and
write the checkout's proposals in the same `key: value` form as `checkout`
(for example `branches.model: git-flow`). This merge keeps the profile's
value, marks it "(profile)", and adds the checkout's value only when it
differs:

```sh
printf '%s\n' "$defaults" '# checkout' "$checkout" | awk '$0 == "# checkout" { c = 1; next }
/^$/ { next }
{ k = $0; sub(/: .*/, "", k); v = substr($0, length(k) + 3) }
!(k in pv) && !(k in cv) { o[++n] = k }
!c { pv[k] = v; next }
{ cv[k] = v }
END { for (i = 1; i <= n; i++) { k = o[i]
  if (k in pv) print k ": " pv[k] " (profile)" ((k in cv) && cv[k] != pv[k] ? ", checkout: " cv[k] : ""); else print k ": " cv[k] } }'
```

## Control repository

List the checkouts that can be `$AP` (SKILL.md Step 1 item 2) with the
command below, run from the product checkout. It takes the first
`owner/name` on a line of `AGENTS.md` or `README.md` (the checkout's or its
parent's) that mentions the control repository, prints it as `named`, and
prints each git checkout at or under the current directory, its parent, or
`$REPOS_DIR` whose `origin` is that repository (case-insensitively). With no
name, it prints the `*-autopilot` checkouts instead. A checkout is never a
candidate because it holds `.specify/`. The remote's user information is
dropped. One `candidate` line gives `AP=<path>` and `AP_REPO=<owner/name>`;
zero or several mean ask.

```sh
want=$(cat AGENTS.md README.md ../AGENTS.md ../README.md 2>/dev/null | grep -i 'control repo' |
  sed -E 's#(https?://|git@)github\.com[:/]##g' | grep -oE '[A-Za-z0-9-]+/[A-Za-z0-9_.-]+' | sed 's/\.git$//' | head -n 1)
[ -n "$want" ] && echo "named $want"
for d in "$PWD" "$PWD"/* "${PWD%/*}" "${PWD%/*}"/* ${REPOS_DIR:+"$REPOS_DIR"/*}; do
  [ -e "$d/.git" ] || continue
  r=$(git -C "$d" remote get-url origin 2>/dev/null | sed -E 's#^[a-z+]+://[^/]*/##; s#^[^/:]*:##; s#\.git/?$##')
  if [ -n "$want" ]; then [ "$(echo "$r" | tr A-Z a-z)" = "$(echo "$want" | tr A-Z a-z)" ] || continue
  else case "${d##*/}" in *-autopilot) ;; *) continue ;; esac; fi
  echo "candidate $d $r"
done | sort -u
```

## Existing profile

Never print the profile as fetched. Hold it in a variable and pass it
through this filter, which parses its front matter with PyYAML first. A
file that does not open with a `---` front matter block, whose block is not
closed or does not parse as YAML, or whose `profile` is not the number `1`
prints one `unreadable:` line and nothing from the file; so does a machine
without PyYAML (the person can install it and re-run). The checkout's own
files are dropped from Python's import path, so none of them runs. A readable one
prints each front matter value as one `key.path: value` line
(`ci.gates[0]: lint`), comments dropped. A key named like a secret (it
contains `KEY`, `SECRET`, `TOKEN`, `PASS`, `PWD`, `DSN`, `CREDENTIAL`,
`PRIVATE` or `AUTH`) prints `<withheld>` for its whole value, a block, list
or multi-line string included. Any other value that looks like a credential
(a URL with user information, a fragment or a query string; a known token
prefix; a private key; a `NAME=value` pair; a long mixed-case or hex
string), on any of its lines, prints `<withheld>`. A missing file prints
nothing, and `gh` reports `HTTP 404`. Offline, the first line is
`p=$(git -C "$AP" show origin/HEAD:profile/<repo>.md) &&`.

```sh
p=$(gh api -H 'Accept: application/vnd.github.raw' "repos/$AP_REPO/contents/profile/<repo>.md") &&
printf '%s\n' "$p" | python3 -E -c '
import sys; sys.path[:] = [x for x in sys.path if x not in ("", ".")]
import re
def stop(why): print("unreadable: " + why); sys.exit(1)
try: import yaml
except ImportError: stop("PyYAML is not installed")
t = sys.stdin.read().replace("\r\n", "\n").split("\n")
if t[0] != "---": stop("no front matter")
if "---" not in t[1:]: stop("front matter not closed")
try: d = yaml.safe_load("\n".join(t[1:t.index("---", 1)]))
except Exception: stop("front matter does not parse")
if not isinstance(d, dict) or type(d.get("profile")) is not int or d["profile"] != 1: stop("not profile: 1")
SECRET = re.compile("KEY|SECRET|TOKEN|PASS|PWD|DSN|CREDENTIAL|PRIVATE|AUTH")
def risky(s):
    return bool(re.search(r"://[^/\s]*@|://\S*#|\?|-----BEGIN|PRIVATE KEY|[A-Za-z_]\w*=\S|(^|[^A-Za-z0-9])(gh[pousr]_|github_pat_|sk-|xox[abprs]-|AKIA|AIza|eyJ)", s)) or any(
        len(r) >= 24 and re.search("[0-9]", r) and re.search("[a-z]", r) and re.search("[A-Z]", r) or len(r) >= 32 and re.fullmatch("[0-9A-Fa-f]+", r)
        for r in re.findall(r"[A-Za-z0-9+/=_-]+", s))
def show(path, v, up=()):
    if id(v) in up: v = "<alias>"
    if isinstance(v, dict) and v:
        for k, x in v.items():
            k = str(k); bad = risky(k) or SECRET.search(k.upper()) and x not in (None, "", [], {})
            show((path + "." if path else "") + ("<withheld>" if risky(k) else k), "<withheld>" if bad else x, up + (id(v),))
    elif isinstance(v, list) and v:
        for i, x in enumerate(v): show("%s[%d]" % (path, i), x, up + (id(v),))
    else:
        s = "[]" if v == [] else "{}" if v == {} else "null" if v is None else str(v).lower() if isinstance(v, bool) else str(v)
        print(path + ": " + ("<withheld>" if risky(s) else s.replace("\n", "\\n")))
show("", d)'
```

## Branches

- **Default branch**: `defaultBranchRef` from Step 1 item 1. If that
  failed, use `git symbolic-ref --short refs/remotes/origin/HEAD`
  and drop the `origin/` prefix; if neither works, ask.
- **Long-lived branches**: from `git ls-remote --heads origin`, keep only
  the default branch and `main`, `master`, `develop`, `development`,
  `staging`, `production`, `release/*` and `hotfix/*`. Feature branches are not evidence. Offline,
  use `git branch -r`.
- **Release tags**: if `git ls-remote --tags origin 'v*'` prints anything,
  propose `tags: "v*"`. Offline, use `git tag -l 'v*'`.
- **Model rule**, first match wins:
  1. `develop` or `development` exists: `git-flow`. That branch is
     `develop`. `release` is `main`, else `master`, else the default
     branch.
  2. `release/*` exists: `release-branches`, with
     `release_pattern: "release/*"`.
  3. `production` exists, or `main` and `master` both exist: `other`, with
     `production` or the non-default one of the pair proposed as `release`
     and the default as `develop`.
  4. Otherwise (for example the default branch alone, or with `staging` or
     `hotfix/*`): `trunk`, and `release = develop = default`.

## CI and deploy files

List tracked files only, for example with
`git ls-files -- '.github/workflows/*.yml' '.github/workflows/*.yaml' .gitlab-ci.yml Jenkinsfile 'cloudbuild.y*ml' .circleci/config.yml azure-pipelines.yml bitbucket-pipelines.yml .travis.yml '.buildkite/*'`
and
`git ls-files -- ':(exclude).github/*' ':(exclude)*.md' '*Dockerfile*' '*compose*.y*ml' '*serverless.yml' '*firebase.json' '*.tf' app.yaml '*/app.yaml' '*fly.toml' '*render.yaml' '*vercel.json' '*netlify.toml' '*Procfile' '*k8s/*' '*helm/*'`.

| CI file | `ci.system` |
|---|---|
| `.github/workflows/*.yml`, `*.yaml` | `github-actions` |
| `.gitlab-ci.yml` | `gitlab-ci` |
| `Jenkinsfile` | `jenkins` |
| `cloudbuild.yaml`, `cloudbuild.yml` | `cloud-build` |
| `.circleci/config.yml` | `circleci` |
| another CI file (`azure-pipelines.yml`, `bitbucket-pipelines.yml`, `.travis.yml`, `.buildkite/`) | `other` |
| no CI file | `none` |

If files from several CI systems are present, list them all and ask which
one gates pull requests. Gates are the job names under `jobs:` of the
workflows triggered by `pull_request` (not deploy, release or scheduled
jobs); `gh api repos/$REPO/rules/branches/<default>` and
`gh api repos/$REPO/branches/<default>/protection/required_status_checks`
show required checks when the login can read them. For another CI system, list its job or stage
names and ask for the gates and trigger. The two GitHub Actions commands
below follow the file's own indentation and print nothing but names. A job
display name, environment or branch name outside letters, digits, spaces and
`_ . / * + ! -`, or holding a known token prefix or a long mixed-case or hex
string, prints as `<withheld>`, and a `${{ … }}` expression as
`<expression>`; ask for those. Read job keys, job names and environment names (plain, quoted,
an inline `{name: …}` map, or `name:` anywhere in an `environment:` block)
with:

```sh
awk 'function clean(v,   s, r) { sub(/^[[:space:]]+/, "", v); sub(/[[:space:]]+#.*$/, "", v); sub(/[[:space:]]+$/, "", v)
  gsub(/"/, "", v); gsub(sprintf("%c", 39), "", v)
  if (v ~ /\$\{\{/) return "<expression>"
  if (v ~ /(^|[^A-Za-z0-9])(gh[pousr]_|github_pat_|sk-|xox[abprs]-|AKIA|AIza|eyJ)/) return "<withheld>"
  for (s = v; match(s, /[A-Za-z0-9+\/=_-]+/); s = substr(s, RSTART + RLENGTH)) { r = substr(s, RSTART, RLENGTH)
    if (length(r) >= 24 && r ~ /[0-9]/ && r ~ /[a-z]/ && r ~ /[A-Z]/ || length(r) >= 32 && r ~ /^[0-9A-Fa-f]+$/) return "<withheld>" }
  return v ~ /^[A-Za-z0-9_.\/*+! -]+$/ ? v : "<withheld>" }
{ sub(/\r$/, "") }
/^[[:space:]]*(#|$)/ { next }
{ i = match($0, /[^ ]/) - 1; l = substr($0, i + 1) }
i == 0 { j = (l ~ /^jobs:[[:space:]]*(#.*)?$/); ji = pi = ei = -1; next }
!j { next }
ei >= 0 && i > ei { if (l ~ /^name:/) print NR ": environment " clean(substr(l, 6)); next }
{ ei = -1 }
ji < 0 { ji = i }
i == ji { if (l ~ /^[A-Za-z0-9_-]+:[[:space:]]*(#.*)?$/) { sub(/:.*/, "", l); print NR ": job " l }; pi = -1; next }
pi < 0 { pi = i }
i != pi { next }
l ~ /^name:/ { print NR ": name " clean(substr(l, 6)); next }
l !~ /^environment:/ { next }
{ v = clean(substr(l, 13)) }
v == "<withheld>" && substr(l, 13) ~ /^[[:space:]]*(#.*)?$/ { ei = i; next }
v == "<withheld>" && match(l, /[{,][[:space:]]*name:[^,}]*/) { v = substr(l, RSTART, RLENGTH); sub(/^[{,][[:space:]]*name:/, "", v); v = clean(v) }
{ print NR ": environment " v }' <file>
```

Read the triggers with the command below. It prints each trigger type
and the `branches`, `branches-ignore`, `tags` and `tags-ignore` names, and
nothing else: no `workflow_dispatch` input, `paths` or `cron` value.

```sh
awk 'function clean(v,   s, r) { sub(/^[[:space:]]+/, "", v); sub(/[[:space:]]+#.*$/, "", v); sub(/[[:space:]]+$/, "", v)
  gsub(/"/, "", v); gsub(sprintf("%c", 39), "", v)
  if (v ~ /\$\{\{/) return "<expression>"
  if (v ~ /(^|[^A-Za-z0-9])(gh[pousr]_|github_pat_|sk-|xox[abprs]-|AKIA|AIza|eyJ)/) return "<withheld>"
  for (s = v; match(s, /[A-Za-z0-9+\/=_-]+/); s = substr(s, RSTART + RLENGTH)) { r = substr(s, RSTART, RLENGTH)
    if (length(r) >= 24 && r ~ /[0-9]/ && r ~ /[a-z]/ && r ~ /[A-Z]/ || length(r) >= 32 && r ~ /^[0-9A-Fa-f]+$/) return "<withheld>" }
  return v ~ /^[A-Za-z0-9_.\/*+! -]+$/ ? v : "<withheld>" }
function each(p, v,   n, t, x) { sub(/[[:space:]]+#.*$/, "", v); gsub(/[][,]/, " ", v); n = split(v, t, " ")
  for (x = 1; x <= n; x++) print NR ": " p clean(t[x]) }
{ sub(/\r$/, "") }
/^[[:space:]]*(#|$)/ { next }
{ i = match($0, /[^ ]/) - 1; l = substr($0, i + 1) }
i == 0 { o = 0; k = l; gsub(/"/, "", k); gsub(sprintf("%c", 39), "", k)
  if (k !~ /^on:/) next; k = substr(k, 4); sub(/^[[:space:]]+/, "", k)
  if (k ~ /^(#.*)?$/) { o = 1; ti = -1 } else if (k ~ /^\{/) print NR ": on <inline map, ask>"; else each("trigger ", k); next }
!o { next }
ti < 0 { ti = i }
i == ti { t = l; sub(/^-[[:space:]]*/, "", t); sub(/:.*/, "", t); t = clean(t); print NR ": trigger " t; f = ""; si = -1; next }
si < 0 { si = i }
i == si && l !~ /^-/ { f = ""; if (l ~ /^(branches|branches-ignore|tags|tags-ignore):/) { f = l; sub(/:.*/, "", f); each(t " " f " ", substr(l, length(f) + 2)) }; next }
f != "" && l ~ /^-/ { each(t " " f " ", substr(l, 2)) }' <file>
```

| Deploy manifest (any directory) | Proposed `kind` |
|---|---|
| `firebase.json` with `hosting` | `firebase-hosting` |
| `Dockerfile` with a workflow running `gcloud run deploy` | `cloud-run` |
| `compose*.yml`, `docker-compose*.yml` (or `.yaml`) with the `Dockerfile`s it builds (one target) | `docker-compose` |
| `k8s/`, `helm/` | `kubernetes` |
| `serverless.yml` | `serverless` |
| `vercel.json`, `netlify.toml` | `static-site` |
| `*.tf` | from the resource types: `google_cloud_run_*` → `cloud-run`, `google_compute_instance`, `aws_instance` → `compute-vm` |
| `app.yaml`, `fly.toml`, `render.yaml`, `Procfile`, or a `Dockerfile` alone | `other`, named in the target (App Engine, Fly.io, Render, Heroku) |

Read Terraform resource types only, never variables:
`grep -hoE '^(resource|provider) "[a-z0-9_]+"' <files>`.
If the only compose file holds just a database for local development, it is
a data-store hint and not a deploy target. To find the trigger, look for the
workflow that deploys, using
`grep -lE 'deploy|docker push|gcloud|firebase|kubectl|helm|flyctl|serverless|vercel|netlify' <workflows>`.
The trigger follows that workflow's `on:` section:

- `push: branches` with the release branch: `push-to-release`.
- `push: tags`: `tag`.
- `workflow_dispatch` only, or no workflow deploys: `manual`.
- anything else (`workflow_run`, `release`, `schedule`): `other`.

## Environments

Take names from these sources:

- workflow `environment:` keys, and
  `gh api repos/$REPO/environments --jq '.environments[].name'` when the
  login can read them;
- `firebase.json` hosting `target` and `site` names, read structurally
  (no other value is printed, and a name outside letters, digits and
  `_ . -` prints as `<withheld>`):
  `jq -r 'def safe: if type == "string" and test("^[A-Za-z0-9_.-]*$") then . else "<withheld>" end; if type == "object" and has("hosting") then [.hosting] | flatten[] | "hosting target=\(.target? // "" | safe) site=\(.site? // "" | safe)" else empty end' firebase.json`,
  and the `.firebaserc` `projects` and `targets` aliases;
- compose `profiles:`;
- the branches `staging` and `production`.

Read compose services, images and the `Dockerfile`s they build with the
command below. It follows the file's own indentation and reads only the
service names under `services:`, each service's own `image:` and `build:`,
and `dockerfile:` directly under a `build:` block; a key of the same name
in `environment:`, `labels:`, `args:` or any other block is never read.
Trailing comments are dropped. A value holding a URL, a space or `=`, and a
`build:` or `dockerfile:` value holding `:`, `@` or `?` (a remote Git
context can carry `user:token@`), prints as `<withheld>`; a registry host is
replaced.

```sh
awk '{ sub(/\r$/, "") }
/^[[:space:]]*(#|$)/ { next }
{ i = match($0, /[^ ]/) - 1; l = substr($0, i + 1) }
i == 0 { s = (l ~ /^services:[[:space:]]*(#.*)?$/); si = -1; next }
!s { next }
si < 0 { si = i }
i == si { if (l ~ /^[A-Za-z0-9_.-]+:[[:space:]]*(#.*)?$/) print NR ":" $0; fi = -1; b = 0; next }
i < si { next }
fi < 0 { fi = i }
i == fi { b = (l ~ /^build:[[:space:]]*(#.*)?$/); bi = -1; if (l ~ /^image:|^build:[[:space:]]+[^{[:space:]#]/) print NR ":" $0; next }
!b || i < fi { next }
bi < 0 { bi = i }
i == bi && l ~ /^dockerfile:/ { print NR ":" $0 }' <file> | sed -E 's/[[:space:]]+#.*$//; s#^([0-9]+: +[a-z]+:).*://.*#\1 <withheld>#; s#^([0-9]+: +(build|dockerfile):).*[:@?].*#\1 <withheld>#; s#^([0-9]+: +[a-z]+:)[[:space:]]*[^[:space:]]+[[:space:]]+[^[:space:]].*#\1 <withheld>#; s#^([0-9]+: +[a-z]+:).*=.*#\1 <withheld>#; s#(image: *)([^/ $]+[.:][^/ ]*|localhost)/#\1<registry>/#; s#(:-)[^/ }]+[.:][^/ }]*\}/#\1<registry>}/#'
```

Read profile names (inline or as a list; comments dropped, a name outside
letters, digits and `_ . -` prints as `<withheld>`) with:

```sh
awk 'function out(v) { gsub(/"/, "", v); gsub(sprintf("%c", 39), "", v); print NR ": profile " (v ~ /^[A-Za-z0-9_.-]+$/ ? v : "<withheld>") }
{ sub(/\r$/, ""); l = $0; sub(/[[:space:]]+#.*$/, "", l); sub(/[[:space:]]+$/, "", l) }
l ~ /^ +profiles:/ { p = 1; sub(/^ +profiles:/, "", l); gsub(/[][,]/, " ", l); n = split(l, t, " "); for (x = 1; x <= n; x++) out(t[x]); next }
p && l ~ /^ +- / { sub(/^ +- +/, "", l); out(l); next }
{ p = 0 }' <file>
```

Never read `environment:`, `command:`, `secrets:` or `args:` blocks. If no source names an environment,
propose `none`.

## Services and data stores

Print package names, never whole manifests: URLs, scripts, authors and
config blocks can carry a token or an internal address. For `package.json`
use `jq -r '(.dependencies // {}), (.devDependencies // {}) | keys[]'`, and
for `composer.json` use `jq -r '(.require // {}), (.["require-dev"] // {}) | keys[]'`. For
`requirements*.txt`, `pyproject.toml`, `go.mod`, `Gemfile`, `Cargo.toml`,
`pubspec.yaml` and `*.csproj` (list them with
`git ls-files -- '*package.json' '*requirements*.txt' '*pyproject.toml' '*go.mod' '*Gemfile' '*Cargo.toml' '*pubspec.yaml' '*composer.json' '*.csproj'`),
print only the table names they contain:

```sh
grep -ohiE '(^|[^a-z])(stripe|sentry|firebase-admin|boto3|aws-sdk|twilio|sendgrid|resend|postmark|mailgun|openai|anthropic|googleapis|slack|algoliasearch|algolia|launchdarkly|segment|datadog|dd-trace|ddtrace|newrelic|pusher|ably|auth0|clerk|supabase|prisma|psycopg[a-z0-9-]*|pg|lib/pq|asyncpg|pgx|npgsql|mysql[a-z0-9-]*|pymysql|pymongo|mongo[a-z]*|motor|redis|sqlite3?)([^a-z]|$)' <files> | sort -u
```

Match a package by its name, without version or extras:
`psycopg[binary]>=3` matches `psycopg`. A row ending in `*` matches by
prefix, and Go module paths or .NET packages that contain a row's name
(`github.com/stripe/stripe-go`, `Stripe.net`) match it.

| Package | Service (purpose) |
|---|---|
| `stripe` | Stripe (payments) |
| `@sentry/*`, `sentry-sdk` | Sentry (error tracking) |
| `firebase-admin` | Firebase (backend services) |
| `boto3`, `@aws-sdk/*` | AWS (cloud APIs) |
| `twilio` | Twilio (SMS and voice) |
| `@sendgrid/*`, `sendgrid` | SendGrid (email) |
| `resend`, `postmark`, `mailgun` | Resend, Postmark, Mailgun (email) |
| `openai`, `anthropic` | OpenAI, Anthropic (LLM API) |
| `googleapis` | Google APIs |
| `@slack/*` | Slack (messaging) |
| `algoliasearch` | Algolia (search) |
| `launchdarkly-*` | LaunchDarkly (feature flags) |
| `segment`, `datadog`, `dd-trace`, `ddtrace`, `newrelic` | Segment (analytics), Datadog, New Relic (monitoring) |
| `pusher`, `ably` | Pusher, Ably (realtime) |
| `auth0`, `@clerk/*`, `supabase`, `@supabase/*` | Auth0, Clerk (authentication), Supabase (backend) |

| Driver package or compose image | Data store |
|---|---|
| `pg`, `lib/pq`, `psycopg*`, `asyncpg`, `pgx`, `Npgsql`; image `postgres` | PostgreSQL |
| `mysql2`, `mysqlclient`, `pymysql`, `mysql-connector-*`; image `mysql`, `mariadb` | MySQL, MariaDB |
| `mongodb`, `mongo-driver`, `mongoose`, `pymongo`, `motor`; image `mongo` | MongoDB |
| `redis`, `ioredis`; image `redis` | Redis |
| `sqlite3` | SQLite |
| image `elasticsearch`, `rabbitmq` | Elasticsearch, RabbitMQ |
| `@prisma/*` | the `provider` names of the tracked `*.prisma` schemas, read with the command below |

For Prisma, list the schemas with `git ls-files -- '*.prisma'` and print
the provider names only. The rest of the line, a trailing comment included,
is never printed, and a provider outside Prisma's own names prints as
`<withheld>`:

```sh
git grep -hE '^[[:space:]]*provider[[:space:]]*=' -- '*.prisma' | sed -E 's/^[[:space:]]*provider[[:space:]]*=[[:space:]]*"(postgresql|postgres|mysql|sqlite|sqlserver|mongodb|cockroachdb|prisma-client-js|prisma-client)".*/provider \1/; s/^[[:space:]]*provider[[:space:]]*=.*/provider <withheld>/'
```

## Environment key names

Open only tracked example files; a name that starts with `secrets` or
`credentials` stays forbidden. Find them with
`git ls-files -- '*.env.example' '*.env.sample' '*.env.template' '*.env.dist'`.
For each one, print key names only, never a value. The command below
opens the file only when it is a regular file, not a symlink, in a
directory inside the checkout (a tracked `.env.example` can point at
`.env`); otherwise it prints one `skipped` line with the name. A value that
opens a quote (`"`, `'` or a backtick) and does not close it on the same
line runs on until the closing quote, and none of its lines is read as a
key:

```sh
f=<file>; d=$(CDPATH= cd -- "$(dirname -- "$f")" 2>/dev/null && pwd -P)
case "$d/" in "$(pwd -P)/"*) ;; *) d= ;; esac
if [ -z "$d" ] || [ -L "$f" ] || [ ! -f "$f" ]; then echo "skipped $f: not a regular file in the checkout"
else awk 'function closes(v, c) { if (c == "\"") gsub(/\\./, "", v); return index(v, c) > 0 }
{ sub(/\r$/, "") }
q != "" { if (closes($0, q)) q = ""; next }
match($0, /^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=/) {
  k = substr($0, 1, RLENGTH - 1); sub(/^[[:space:]]*(export[[:space:]]+)?/, "", k); sub(/[[:space:]]+$/, "", k); print k
  v = substr($0, RLENGTH + 1); sub(/^[[:space:]]+/, "", v); c = substr(v, 1, 1)
  if ((c == "\"" || c == sprintf("%c", 39) || c == "`") && !closes(substr(v, 2), c)) q = c }' "$f"; fi
```

- **Secret-looking**: a name that contains `KEY`, `SECRET`, `TOKEN`,
  `PASSWORD`, `PASSWD`, `DSN`, `CREDENTIAL`, `PRIVATE` or `AUTH`, or that
  ends in `_URL`. Connection strings embed passwords. Also mark, stricter
  than the spec, names containing `PASS` or `PWD` or ending in `_URI`. List
  these names marked "secret-looking".
- **Prefix to service**: `STRIPE_` → Stripe, `SENTRY_` → Sentry, `AWS_` →
  AWS, `GOOGLE_`/`GCP_` → Google Cloud, `FIREBASE_` → Firebase, `TWILIO_` →
  Twilio, `SENDGRID_` → SendGrid, `OPENAI_` → OpenAI, `ANTHROPIC_` →
  Anthropic, `SLACK_` → Slack, `MONGO_`/`MONGODB_` → MongoDB. `DATABASE_URL` → a SQL
  data store (the driver tells which), `REDIS_URL` → Redis. Evidence reads
  `<NAME> (environment key name)`.

## Forbidden files

Never open, print, `grep`, `sed`, `cat`, `head`, `source` or copy any of
these, even when asked during Step 1:

- `.env`, `.env.local`, `.env.*.local`, `.env.production`,
  `.env.development`, and every other `.env*` file that is not one of the
  four example names;
- `*.pem`, `*.key`, `*.p12`, `secrets*`, `credentials*`, `.npmrc`,
  `.pypirc`, `.netrc`, `id_rsa*`, `id_ed25519*`, `kubeconfig*`,
  `*.tfstate*`, `*.tfvars`, and service-account JSON key files;
- `~/.config/gh/`, and `~/.autop/` apart from the installed skills (for the
  runner's `repos_dir`, `grep` that one setting and print nothing else).

Their names may appear in the list of files "not opened". Nothing more
about them may appear.

## What never goes in the transcript

- A value from any environment file, the example files included.
- A literal from a compose `environment:` block, a workflow `env:` block or
  a Terraform variable. Do not read those blocks.
- Anything credential-looking: a token, a key, a password, a connection
  string, a signed URL, or a URL with user information or a query string.
  If a permitted command prints one by accident, do not repeat it. Say a
  value was withheld, and note the file so that the person can review it.
