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
names and ask for the gates and trigger. The commands below assume
two-space YAML indentation; adjust the counts for other files. Read GitHub
Actions jobs and environments with
`awk '/^jobs:/{j=1; next} j && /^[^ #]/{j=0} j && (/^  [A-Za-z0-9_-]+: *$/ || /^    name:/ || /^    environment: *[A-Za-z0-9_-]* *$/){print NR": "$0; e=/environment: *$/; next} e && /^      name:/{print NR": "$0} {e=0}' <file>`
(job keys, job names and environment names only; an inline
`environment: {…}` map and every `with:` or `secrets:` value are skipped).
Read triggers with `awk '/^.?on.?:/{p=1; print; next} /^[^ #]/{p=0} p' <file>`,
which stops before the next top-level key.

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
- `firebase.json` hosting `target` values
  (`grep -nE '"(hosting|target|site)"' firebase.json`) and the
  `.firebaserc` `projects` and `targets` aliases;
- compose `profiles:`;
- the branches `staging` and `production`.

Read compose services, images and the `Dockerfile`s they build with
`grep -nE '^ {2}[A-Za-z0-9_.-]+:[[:space:]]*$|^ +(image|dockerfile):|^ +build: [^{]*$' <file> | sed -E 's#(image: *)([^/ $]+[.:][^/ ]*|localhost)/#\1<registry>/#; s#(:-)[^/ }]+[.:][^/ }]*\}/#\1<registry>}/#'`
(a registry host is replaced), and profiles with
`awk '/^ +profiles:/{p=1; print NR": "$0; next} p && /^ +- [A-Za-z0-9_-]+ *$/{print NR": "$0; next} {p=0}' <file>`.
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
| `@prisma/*` | `git grep -nE '^[[:space:]]*provider[[:space:]]*=' -- '*.prisma'` |

## Environment key names

Open only tracked example files; a name that starts with `secrets` or
`credentials` stays forbidden. Find them with
`git ls-files -- '*.env.example' '*.env.sample' '*.env.template' '*.env.dist'`.
For each one, print key names only, never a value:

```sh
sed -n 's/^[[:space:]]*\(export[[:space:]]\{1,\}\)\{0,1\}\([A-Za-z_][A-Za-z0-9_]*\)[[:space:]]*=.*/\2/p' <file>
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
