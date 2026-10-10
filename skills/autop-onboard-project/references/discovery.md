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

## Branches

- **Default branch**: `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`.
  If that fails, use `git symbolic-ref --short refs/remotes/origin/HEAD`
  and drop the `origin/` prefix.
- **Long-lived branches**: from `git ls-remote --heads origin`, keep only
  the default branch and `main`, `master`, `develop`, `development`,
  `staging`, `production`, `release/*` and `hotfix/*`. Feature branches are not evidence. Offline,
  use `git branch -r`.
- **Release tags**: if `git ls-remote --tags origin 'v*'` prints anything,
  propose `tags: "v*"`. Offline, use `git tag -l 'v*'`.
- **Model rule**, first match wins:
  1. `develop` or `development` exists: `git-flow`. That branch is
     `develop`. `release` is the default branch, or `main`/`master` if the
     default branch is `develop`.
  2. `release/*` exists: `release-branches`, with
     `release_pattern: "release/*"`.
  3. `production` (or `master` next to a `main` default) exists: `other`,
     with that branch proposed as `release` and the default as `develop`.
  4. Otherwise, the default branch alone, or with only `staging` or
     `hotfix/*`: `trunk`, and `release = develop = default`.

## CI and deploy files

List tracked files only, for example with
`git ls-files -- '.github/workflows/*.yml' '.github/workflows/*.yaml' .gitlab-ci.yml Jenkinsfile 'cloudbuild.y*ml' .circleci/config.yml`
and
`git ls-files -- '*Dockerfile*' '*compose*.y*ml' '*serverless.yml' '*firebase.json' '*.tf' app.yaml '*/app.yaml' '*fly.toml' '*render.yaml' '*vercel.json' '*netlify.toml' '*Procfile' '*k8s/*' '*helm/*'`.

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
one gates pull requests. Gates are the job names under `jobs:`. Read
jobs and environments with
`sed -n '/^jobs:/,$p' <file> | grep -nE '^ {2}[A-Za-z0-9_-]+:[[:space:]]*$|^ {4}(name|environment):|^ {6}name:'`.
Read triggers with
`sed -n "/^[\"']\{0,1\}on[\"']\{0,1\}:/,/^[a-z]/p" <file>`.

| Deploy manifest (any directory) | Proposed `kind` |
|---|---|
| `firebase.json` with `hosting` | `firebase-hosting` |
| `Dockerfile` with a workflow running `gcloud run deploy` | `cloud-run` |
| `compose*.yml`, `docker-compose*.yml` (or `.yaml`) with the `Dockerfile`s it builds (one target) | `docker-compose` |
| `k8s/`, `helm/` | `kubernetes` |
| `serverless.yml` | `serverless` |
| `vercel.json`, `netlify.toml` | `static-site` |
| `*.tf` | from the resource types: `google_cloud_run_*` → `cloud-run`, `*_instance` → `compute-vm` |
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

- workflow `environment:` keys;
- `firebase.json` hosting `target` values
  (`grep -nE '"(hosting|target|site)"' firebase.json`) and the
  `.firebaserc` `projects` and `targets` aliases;
- compose `profiles:`;
- the branches `staging` and `production`.

Read compose files with
`grep -nE '^ {2}[A-Za-z0-9_.-]+:[[:space:]]*$|^ +(image|profiles):|^ +build: [^{]*$' <file> | grep -v '@'`
(services, images, the `Dockerfile`s they build, profiles; never a line
with user information or inline build arguments).
Never read their `environment:` blocks. If no source names an environment,
propose `none`.

## Services and data stores

Print package names, not whole manifests, because URLs, scripts and
config blocks can carry a token. For `package.json` use
`jq -r '(.dependencies // {}), (.devDependencies // {}) | keys[]'`, and for
`composer.json` the same over `require` and `require-dev`. For
`requirements*.txt`, `pyproject.toml`, `go.mod`, `Gemfile`, `Cargo.toml`,
`pubspec.yaml` and `*.csproj` use
`grep -viE '://|index-url|registry|password|secret|token *=' <file>`.
Match a package by its name, without version or extras:
`psycopg[binary]>=3` matches `psycopg`. A row ending in `*` matches by
prefix.

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
| `segment`, `datadog`, `dd-trace`, `newrelic` | Segment (analytics), Datadog, New Relic (monitoring) |
| `pusher`, `ably` | Pusher, Ably (realtime) |
| `auth0`, `@clerk/*`, `supabase`, `@supabase/*` | Auth0, Clerk (authentication), Supabase (backend) |

| Driver package or compose image | Data store |
|---|---|
| `pg`, `psycopg`, `psycopg2`, `asyncpg`; image `postgres` | PostgreSQL |
| `mysql2`, `mysqlclient`; image `mysql`, `mariadb` | MySQL, MariaDB |
| `mongoose`, `pymongo`; image `mongo` | MongoDB |
| `redis`, `ioredis`; image `redis` | Redis |
| `sqlite3` | SQLite |
| image `elasticsearch`, `rabbitmq` | Elasticsearch, RabbitMQ |
| `@prisma/*` | `grep -nE '^[[:space:]]*provider[[:space:]]*=' schema.prisma` |

## Environment key names

Open only tracked example files. Find them with
`git ls-files -- '*.env.example' '*.env.sample' '*.env.template' '*.env.dist'`.
For each one, print key names only, never a value:

```sh
sed -n 's/^[[:space:]]*\(export[[:space:]]\{1,\}\)\{0,1\}\([A-Za-z_][A-Za-z0-9_]*\)[[:space:]]*=.*/\2/p' <file>
```

- **Secret-looking**: a name that contains `KEY`, `SECRET`, `TOKEN`,
  `PASSWORD`, `PASSWD`, `DSN`, `CREDENTIAL`, `PRIVATE` or `AUTH`, or that
  ends in `_URL`. Connection strings embed passwords. List these names
  marked "secret-looking".
- **Prefix to service**: `STRIPE_` → Stripe, `SENTRY_` → Sentry, `AWS_` →
  AWS, `GOOGLE_`/`GCP_` → Google Cloud, `FIREBASE_` → Firebase, `TWILIO_` →
  Twilio, `SENDGRID_` → SendGrid, `OPENAI_` → OpenAI, `ANTHROPIC_` →
  Anthropic, `SLACK_` → Slack, `MONGO_` → MongoDB. `DATABASE_URL` → a SQL
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
