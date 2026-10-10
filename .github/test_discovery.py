"""Run the read commands of autop-onboard-project's discovery.md on fixtures: names out, values never."""
from pathlib import Path
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

root = Path(__file__).resolve().parents[1]
SKILL = root / 'skills/autop-onboard-project'
DOC = (SKILL / 'references/discovery.md').read_text()


def fenced(start, has=''):
    """The one fenced sh block of discovery.md that starts with the given text and holds `has`."""
    blocks = [b for b in re.findall(r'```sh\n(.*?)\n```', DOC, re.S) if b.startswith(start) and has in b]
    assert len(blocks) == 1, f'{len(blocks)} sh blocks start with {start!r} and hold {has!r}'
    return blocks[0]


def inline(start):
    """The one inline code span of discovery.md that starts with the given text."""
    spans = [s for s in re.findall(r'`([^`\n]+)`', DOC) if s.startswith(start)]
    assert len(spans) == 1, f'{len(spans)} code spans start with {start!r}'
    return spans[0]


def run(command, cwd=None):
    return subprocess.run(['bash', '-c', command], capture_output=True, text=True, timeout=60, cwd=cwd)


def on_file(command, text, name='file.yml'):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(text)
        return run(command.replace('<file>', shlex.quote(str(path))).replace(' firebase.json', ' ' + shlex.quote(str(path))))


JOBS = fenced("awk 'function clean(v,", 'jobs:')
TRIGGERS = fenced("awk 'function clean(v,", 'function each(')
COMPOSE = fenced("awk 'function find(", 'services:')
COMPOSE_PROFILES = fenced("awk 'function out(v,")
PROFILE = fenced('p=$(gh api ')
BRANCHES = fenced('d=${DEFAULT:-')
PROFILE_OFFLINE = inline('p=$(git -C "$AP" show')
CONTROL = fenced('name() {', 'want=$(')
MERGE = fenced("printf '%s\\n' \"$defaults\"")
FIREBASE = inline("jq -r 'def safe:")
ENV_FILES = inline("git ls-files -co --exclude-standard -- '*.env.example'")
ENV_NAMES = fenced("awk 'function closes(")
PRISMA = fenced("git grep -hE '^[[:space:]]*provider")
GUARD = fenced('while IFS= read -r f;')
FORBIDDEN = fenced('for d in . <directories>;')
MANIFESTS = inline("git ls-files -- ':(exclude).github/*'")
GH_ENVIRONMENTS = inline('gh api repos/$REPO/environments --jq ')
GH_RULES = inline('gh api repos/$REPO/rules/branches/<default> --jq ')
GH_PROTECTION = inline('gh api repos/$REPO/branches/<default>/protection/required_status_checks --jq ')
PRODUCT = fenced('r=$(git remote get-url origin')
MODEL = fenced("awk '$1 == \"default\"")
PACKAGE_JSON, COMPOSER_JSON = fenced("jq -r 'def safe:").splitlines()
TERRAFORM = fenced("grep -hoE '^(resource|provider)")

WORKFLOW = """\
name: Deploy
'on':
  push:
    branches: [main, 'release/*']   # releases
    tags:
      - "v*"
    paths: ['src/**']
  pull_request:
    branches:
    - main
  workflow_dispatch:
    inputs:
      token:
        default: hardcoded-dispatch-secret
  schedule:
    - cron: '0 3 * * *'
env:
  TOP: top-level-env-value
jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - name: step-name-value
        with:
          name: with-name-value
  quoted:
    environment: "staging" # comment
  inline:
    environment: { name: production, url: https://user:inline-url-secret@example.com }
  block:
    environment:
      url: https://deploy.example.com/?sig=block-url-secret
      name: 'preview'
  expression:
    environment: ${{ inputs.target }}
  odd:
    environment: "prod@odd-name-secret"
  release:
    name: Deploy https://user:display-name-secret@example.com
  lint:
    name: Lint  # TOKEN=comment-secret
  token:
    name: Push Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9
"""

FOUR_SPACE = """\
on: [push, pull_request]
jobs:
    deploy:
        environment:
            url: https://example.com
            name: production
        steps:
            - run: echo
"""


class WorkflowTest(unittest.TestCase):
    def test_jobs_and_environment_names_only(self):
        result = on_file(JOBS, WORKFLOW)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line.split(': ', 1)[1] for line in result.stdout.splitlines()]
        self.assertEqual(lines, ['job test', 'name Test', 'job quoted', 'environment staging', 'job inline',
                                 'environment production', 'job block', 'environment preview', 'job expression',
                                 'environment <expression>', 'job odd', 'environment <withheld>',
                                 'job release', 'name <withheld>', 'job lint', 'name Lint', 'job token',
                                 'name <withheld>'])
        self.assertNotIn('secret', result.stdout)
        self.assertNotIn('Ab1Cd2', result.stdout)

    def test_job_ids_are_masked(self):
        result = on_file(JOBS, 'jobs:\n  lint:\n    name: Lint\n  ghp_jobCredential:\n    name: Test\n'
                               '  Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9:\n    runs-on: ubuntu-latest\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['2: job lint', '3: name Lint', '4: job <withheld>', '5: name Test',
                                                      '6: job <withheld>'])
        self.assertNotIn('Credential', result.stdout)
        self.assertNotIn('Ab1Cd2', result.stdout)

    @unittest.skipUnless(shutil.which('jq'), 'jq is not installed')
    def test_api_environment_names_are_masked(self):
        """The `gh api … --jq` filter, run by jq on a recorded response."""
        self.assertTrue(GH_ENVIRONMENTS.startswith("gh api repos/$REPO/environments --jq '"))
        response = ('{"total_count":6,"environments":[{"name":"production","protection_rules":[]},{"name":"Preview 2"},'
                    '{"name":"ghp_envCredential"},{"name":"Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9"},'
                    '{"name":"0123456789abcdef0123456789abcdef"},{"name":"prod@odd-name-secret"}]}')
        command = GH_ENVIRONMENTS.replace('gh api repos/$REPO/environments --jq', 'jq -r', 1) + ' <file>'
        result = on_file(command, response, 'environments.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         ['production', 'Preview 2', '<withheld>', '<withheld>', '<withheld>', '<withheld>'])
        self.assertNotIn('Credential', result.stdout)
        self.assertNotIn('secret', result.stdout)

    @unittest.skipUnless(shutil.which('jq'), 'jq is not installed')
    def test_required_check_names_are_masked(self):
        """FR-013: the two required-check `gh api … --jq` filters, run by jq on recorded responses."""
        rules = ('[{"type":"pull_request","parameters":{"required_approving_review_count":1}},'
                 '{"type":"required_status_checks","ruleset_source":"acme/api","parameters":{'
                 '"strict_required_status_checks_policy":true,"required_status_checks":[{"context":"lint"},'
                 '{"context":"ci / test (ubuntu-latest, 3.12)","integration_id":15368},{"context":"ghp_ruleCredential"},'
                 '{"context":"deploy https://user:rule-url-secret@example.com"},{"context":"TOKEN=rule-value-secret"}]}}]')
        protection = ('{"url":"https://api.github.com/repos/acme/api/branches/main/protection/required_status_checks",'
                      '"strict":true,"contexts":["lint","Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9","https://example.com/?sig=ctx-secret"],'
                      '"checks":[{"context":"lint","app_id":1},{"context":"test","app_id":null},'
                      '{"context":"0123456789abcdef0123456789abcdef","app_id":2}]}')
        for api, response, expected in (
                (GH_RULES, rules, ['lint', 'ci / test (ubuntu-latest, 3.12)', '<withheld>', '<withheld>', '<withheld>']),
                (GH_PROTECTION, protection, ['<withheld>', '<withheld>', '<withheld>', 'lint', 'test'])):
            with self.subTest(api=api.split(' --jq', 1)[0]):
                command = re.sub(r'^gh api \S+ --jq', 'jq -r', api) + ' <file>'
                self.assertNotEqual(command, api + ' <file>')
                result = on_file(command, response, 'response.json')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), expected)
                for value in ('Credential', 'secret', 'Ab1Cd2', '0123'):
                    self.assertNotIn(value, result.stdout)

    def test_quoted_keys(self):
        """FR-010: `'jobs':` and `"environment":` are the same YAML keys as the plain ones."""
        workflow = ("'on': [pull_request]\n{jobs}:\n  \"build\":\n    'name': Build\n    'environment': 'staging'\n"
                    "  deploy:\n    \"environment\":\n      'url': https://deploy.example.com/?sig=quoted-url-secret\n"
                    "      \"name\": production\n"
                    "  inline:\n    'environment': { 'name': preview, url: https://user:inline-quoted-secret@example.com }\n"
                    "  plain:\n    environment: { \"name\": review }\n")
        for jobs in ("'jobs'", '"jobs"', 'jobs'):
            with self.subTest(jobs=jobs):
                result = on_file(JOBS, workflow.replace('{jobs}', jobs))
                self.assertEqual((result.returncode, result.stderr), (0, ''))
                self.assertEqual([line.split(': ', 1)[1] for line in result.stdout.splitlines()], [
                    'job build', 'name Build', 'environment staging', 'job deploy', 'environment production',
                    'job inline', 'environment preview', 'job plain', 'environment review'])
                self.assertNotIn('secret', result.stdout)

    def test_any_indentation(self):
        result = on_file(JOBS, FOUR_SPACE)
        self.assertEqual(result.stdout.splitlines(), ['3: job deploy', '6: environment production'])

    def test_triggers_without_values(self):
        result = on_file(TRIGGERS, WORKFLOW)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line.split(': ', 1)[1] for line in result.stdout.splitlines()]
        self.assertEqual(lines, ['trigger push', 'push branches main', 'push branches release/*', 'push tags v*',
                                 'trigger pull_request', 'pull_request branches main', 'trigger workflow_dispatch',
                                 'trigger schedule'])
        for value in ('secret', 'top-level', 'src/', '3 *'):
            self.assertNotIn(value, result.stdout)

    def test_inline_triggers(self):
        result = on_file(TRIGGERS, FOUR_SPACE)
        self.assertEqual(result.stdout.splitlines(), ['1: trigger push', '1: trigger pull_request'])


class ManifestTest(unittest.TestCase):
    def test_compose_withholds_remote_build_contexts(self):
        result = on_file(COMPOSE, """\
services:
  app:
    build: https://user:compose-build-secret@git.example.com/org/app.git#main
    image: registry.example.com/org/app:1
  worker:
    build: ./worker
  remote:
    build: git@github.com:org/remote-build-secret.git
  db:
    image: postgres:17@sha256:abc
    environment:
      POSTGRES_PASSWORD: compose-env-secret
  cache: # TOKEN=service-comment-secret
    image: redis:7 # PASSWORD=image-comment-secret
  odd:
    image: postgres:17 PASSWORD=image-value-secret
    build: ./odd # TOKEN=build-comment-secret
  tagged:
    image: acme/app:ghp_composeTagSecret
    build: ./Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9
  ghp_serviceNameSecret:
    image: postgres:17@sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
""")
        self.assertEqual(result.stdout.splitlines(), [
            '2:  app:', '3:    build: <withheld>', '4:    image: <registry>/org/app:1', '5:  worker:',
            '6:    build: ./worker', '7:  remote:', '8:    build: <withheld>', '9:  db:',
            '10:    image: postgres:17@sha256:<digest>', '13:  cache:', '14:    image: redis:7', '15:  odd:',
            '16:    image: <withheld>', '17:    build: ./odd', '18:  tagged:', '19:    image: <withheld>',
            '20:    build: <withheld>', '21:  <withheld>:', '22:    image: postgres:17@sha256:<digest>'])
        self.assertNotIn('secret', result.stdout.lower())
        self.assertNotIn('Ab1Cd2', result.stdout)
        self.assertNotIn('0123', result.stdout)

    def test_compose_reads_service_fields_only(self):
        result = on_file(COMPOSE, """\
x-common: &common
    image: anchor-image-secret
services:
    app:
        build:
            context: .
            dockerfile: docker/App.Dockerfile
            args:
                dockerfile: args-dockerfile-secret
        environment:
            image: env-image-secret
            build: env-build-secret
            dockerfile: env-dockerfile-secret
        labels:
            image: label-image-secret
    worker:
        environment:
          - image=list-image-secret
        image: worker:1
volumes:
    data:
        image: volume-image-secret
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            '4:    app:', '7:            dockerfile: docker/App.Dockerfile', '16:    worker:',
            '19:        image: worker:1'])
        self.assertNotIn('secret', result.stdout)

    def test_compose_merges_inherit_anchored_fields(self):
        """FR-011: `<<: *database` gives the service the anchor's image, so the PostgreSQL hint is found."""
        result = on_file(COMPOSE, """\
x-database: &database
  image: postgres:17
  environment:
    image: merge-env-secret
x-base: &base # TOKEN=anchor-comment-secret
  image: redis:7
x-cache: &cache
  <<: *base
  restart: always
x-bad: &bad
  image: acme/db:ghp_mergeImageSecret
x-inline: &inline { image: inline-anchor-secret }
services:
  db:
    <<: *database
    ports: ["5432:5432"]
  replica:
    <<: [*database]
    image: postgres:16
  cache:
    <<: *cache
  app: &app
    build: ./app
    image: acme/app:1
  worker:
    build: ./worker
    <<: [*app, *database]
  bad:
    <<: *bad
  flow:
    <<: *inline
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            '14:  db:', '15:    image: postgres:17', '17:  replica:', '19:    image: postgres:16', '20:  cache:',
            '21:    image: redis:7', '22:  app:', '23:    build: ./app', '24:    image: acme/app:1', '25:  worker:',
            '26:    build: ./worker', '27:    image: acme/app:1', '28:  bad:', '29:    image: <withheld>', '30:  flow:'])
        self.assertNotIn('secret', result.stdout.lower())

    def test_compose_profile_names_only(self):
        result = on_file(COMPOSE_PROFILES, """\
x-common: &common
  profiles: [anchor-profile-secret]
services:
  app:
    profiles: [prod, "dev"] # TOKEN=inline-profile-secret
    image: app
    environment:
      profiles: env-profile-secret
    labels:
      profiles:
        - label-profile-secret
  backup:
    profiles:
      - backup # PASSWORD=list-profile-secret
      - 'odd name!'
      - ghp_listProfileSecret
      - Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9
    environment:
      - KEY=after-profiles-secret
  worker:
    profiles:
    - jobs
    - sk-sameIndentSecret
    deploy:
      profiles: [deploy-profile-secret]
volumes:
  data:
    profiles: [volume-profile-secret]
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            '5: profile prod', '5: profile dev', '14: profile backup', '15: profile <withheld>',
            '16: profile <withheld>', '17: profile <withheld>', '22: profile jobs', '23: profile <withheld>'])
        self.assertNotIn('secret', result.stdout.lower())
        self.assertNotIn('Ab1Cd2', result.stdout)

    @unittest.skipUnless(shutil.which('jq'), 'jq is not installed')
    def test_firebase_hosting_names_only(self):
        minified = ('{"hosting":[{"target":"prod","site":"acme-prod","headers":[{"source":"**","headers":'
                    '[{"key":"Authorization","value":"Bearer firebase-header-secret"}]}]},{"target":"bad name!"},'
                    '{"target":"ghp_firebaseTargetSecret","site":"Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9"},'
                    '{"target":"staging","site":"0123456789abcdef0123456789abcdef"}],'
                    '"functions":{"predeploy":["TOKEN=firebase-command-secret npm run build"]}}')
        result = on_file(FIREBASE, minified, 'firebase.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         ['hosting target=prod site=acme-prod', 'hosting target=<withheld> site=',
                          'hosting target=<withheld> site=<withheld>', 'hosting target=staging site=<withheld>'])
        self.assertNotIn('secret', result.stdout.lower())

    @unittest.skipUnless(shutil.which('jq'), 'jq is not installed')
    def test_package_names_are_masked(self):
        package = ('{"name":"app","scripts":{"build":"TOKEN=script-secret npm run build"},'
                   '"dependencies":{"stripe":"^14","@sentry/node":"^8","ghp_packageCredential":"1",'
                   '"git+https://user:pw-secret@example.com/x":"1"},'
                   '"devDependencies":{"Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9":"1","pg":"^8"}}')
        result = on_file(PACKAGE_JSON.replace('<package.json>', '<file>'), package, 'package.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         ['@sentry/node', '<withheld>', '<withheld>', 'stripe', '<withheld>', 'pg'])
        composer = ('{"require":{"php":">=8.2","stripe/stripe-php":"^13","acme/sk-composerCredential":"1"},'
                    '"require-dev":{"0123456789abcdef0123456789abcdef":"1","phpunit/phpunit":"^11",'
                    '"vendor/Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9":"1"},'
                    '"config":{"github-oauth":{"github.com":"composer-config-secret"}}}')
        result = on_file(COMPOSER_JSON.replace('<composer.json>', '<file>'), composer, 'composer.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         ['<withheld>', 'php', 'stripe/stripe-php', '<withheld>', 'phpunit/phpunit',
                          '<withheld>'])
        self.assertNotIn('Credential', result.stdout)
        self.assertNotIn('Ab1Cd2', result.stdout)
        self.assertNotIn('secret', result.stdout)

    @unittest.skipUnless(shutil.which('jq'), 'jq is not installed')
    def test_invalid_package_fields_fail_without_values(self):
        """FR-013: jq names a value it cannot take keys of; a field that is not an object stops value-free."""
        for command, manifest, name in (
                (PACKAGE_JSON, '{"dependencies":{"pg":"^8"},"devDependencies":"ghp_fieldCredential"}', 'package.json'),
                (PACKAGE_JSON, '{"dependencies":["git+https://user:pw-secret@example.com/x"]}', 'package.json'),
                (PACKAGE_JSON, '"ghp_manifestCredential"', 'package.json'),
                (COMPOSER_JSON, '{"require":"sk-composerCredential"}', 'composer.json'),
                (COMPOSER_JSON, '{"require-dev":12345678901234567890}', 'composer.json')):
            result = on_file(command.replace(f'<{name}>', '<file>'), manifest, name)
            self.assertNotEqual(result.returncode, 0, manifest)
            self.assertIn('is not an object', result.stderr)
            for value in ('Credential', 'secret', '12345'):
                self.assertNotIn(value, result.stdout + result.stderr)

    def test_terraform_types_are_masked(self):
        """FR-013: a resource or provider label can hold a credential; only the masked type is printed."""
        with tempfile.TemporaryDirectory() as tmp:
            main, other = Path(tmp) / 'main.tf', Path(tmp) / 'other.tf'
            main.write_text('provider "google" {\n  project = "project-value-secret"\n}\n'
                            'resource "google_cloud_run_v2_service" "api" {\n  name = "name-value-secret"\n}\n'
                            'resource "ghp_resourceLabelCredential" "x" {}\n'
                            'provider "0123456789abcdef0123456789abcdef" {}\n'
                            'variable "token" {\n  default = "ghp_variableCredential"\n}\n')
            other.write_text('resource "aws_instance" "web" {}\nresource "my_github_pat_label" "y" {}\n'
                             'resource "google_cloud_run_v2_service" "worker" {}\n')
            result = run(TERRAFORM.replace('<files>', f'{shlex.quote(str(main))} {shlex.quote(str(other))}'))
            self.assertEqual((result.returncode, result.stderr), (0, ''))
            self.assertEqual(sorted(result.stdout.splitlines()), [
                'provider "<withheld>"', 'provider "google"', 'resource "<withheld>"', 'resource "aws_instance"',
                'resource "google_cloud_run_v2_service"'])
            for value in ('Credential', 'secret', '0123456789abcdef', 'github_pat'):
                self.assertNotIn(value, result.stdout)

    def test_symlinked_and_forbidden_manifests_are_not_opened(self):
        """A tracked `compose.yml` that points at `.env`, and other paths the guard keeps every read from."""
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            git_repo(Path(tmp) / 'app', 'https://github.com/acme/app.git', commit={
                '.env': 'services:\n  ghp_envServiceSecret:\n    image: env-image-secret\n',
                'deploy/Dockerfile': 'FROM node:22\n', 'secrets-compose.yml': 'services:\n  forbidden-name-secret:\n'})
            app = Path(tmp) / 'app'
            (app / 'compose.yml').symlink_to('.env')
            (app / 'deploy/docker-compose.yml').symlink_to('../.env')
            (app / 'linked').symlink_to(outside)
            (Path(outside) / 'compose.yml').write_text('services:\n  outside-service-secret:\n')
            git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', '-C', str(app)]
            subprocess.run(git + ['add', 'compose.yml', 'deploy/docker-compose.yml'], check=True)
            subprocess.run(git + ['commit', '-qm', 'symlinks'], check=True)
            for path in (app / '.env', app / 'secrets-compose.yml', Path(outside) / 'compose.yml'):
                path.chmod(0)  # any read of these files now fails loudly on stderr

            listed = run(f"{{ {MANIFESTS}; echo linked/compose.yml; }} | {GUARD}", cwd=app)
            self.assertEqual((listed.returncode, listed.stderr), (0, ''))
            self.assertEqual(listed.stdout.splitlines(), [
                'skipped compose.yml: not opened', 'deploy/Dockerfile', 'skipped deploy/docker-compose.yml: not opened',
                'skipped secrets-compose.yml: not opened', 'skipped linked/compose.yml: not opened'])
            opened = [line for line in listed.stdout.splitlines() if not line.startswith('skipped ')]
            self.assertEqual(opened, ['deploy/Dockerfile'])
            for path in (app / '.env', app / 'secrets-compose.yml', Path(outside) / 'compose.yml'):
                path.chmod(0o600)

    def test_credential_looking_paths_are_withheld(self):
        """FR-013: a file name can hold a credential; the guard never prints or opens such a path."""
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp) / 'app'
            risky = ('deploy/ghp_pathCredential-compose.yml', 'Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9/Dockerfile',
                     'ops/compose=query-secret.yml', 'xoxb-exampleCredential.env.example')
            git_repo(app, 'https://github.com/acme/app.git',
                     commit={'deploy/Dockerfile': 'FROM node:22\n', **{path: 'services:\n  x:\n' for path in risky}})
            for path in risky:
                (app / path).chmod(0)  # any read of these files now fails loudly on stderr
            listed = run(f"{{ {MANIFESTS}; {ENV_FILES}; echo secrets-Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9.yml; }} | {GUARD}",
                         cwd=app)
            self.assertEqual((listed.returncode, listed.stderr), (0, ''))
            self.assertEqual(sorted(listed.stdout.splitlines()),
                             ['deploy/Dockerfile'] + ['skipped <withheld>: not opened'] * 5)
            for value in ('Credential', 'Ab1Cd2', 'secret'):
                self.assertNotIn(value, listed.stdout)
            for path in risky:
                (app / path).chmod(0o600)

    def test_forbidden_names_only_and_masked(self):
        """FR-013: forbidden files are listed by name, and a name holding a credential is withheld."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            names = ('.env', '.env.example', '.env.ghp_envNameCredential', 'README.md', 'id_rsa', 'package.json',
                     'deploy/secrets-Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9.json', 'deploy/prod.key', 'deploy/compose.yml',
                     'deploy/.env.sample', 'deploy/credentials.env.example', 'deploy/app.tfstate.backup')
            for name in names:
                (root / name).parent.mkdir(exist_ok=True)
                (root / name).write_text('TOKEN=must-never-appear\n')
                (root / name).chmod(0)  # listing names never reads a file
            result = run(FORBIDDEN.replace('<directories>', 'deploy'), cwd=root)
            self.assertEqual((result.returncode, result.stderr), (0, ''))
            self.assertEqual(sorted(result.stdout.splitlines()), sorted([
                'forbidden .env: not opened', 'forbidden <withheld>: not opened', 'forbidden id_rsa: not opened',
                'forbidden <withheld>: not opened', 'forbidden deploy/prod.key: not opened',
                'forbidden deploy/credentials.env.example: not opened',
                'forbidden deploy/app.tfstate.backup: not opened']))
            for value in ('Credential', 'Ab1Cd2', 'must-never-appear'):
                self.assertNotIn(value, result.stdout)
            for name in names:
                (root / name).chmod(0o600)


EXAMPLE_VALUES = [
    'profile: 1', 'repository: acme/api', 'updated: 2026-10-10', 'branches.default: main', 'branches.release: main',
    'branches.develop: main', 'branches.model: trunk', 'branches.tags: v*', 'ci.system: github-actions',
    'ci.config[0]: .github/workflows/ci.yml', 'ci.config[1]: .github/workflows/deploy.yml', 'ci.gates[0]: lint',
    'ci.gates[1]: test', 'deploy[0].name: api', 'deploy[0].kind: cloud-run', 'deploy[0].config[0]: Dockerfile',
    'deploy[0].config[1]: .github/workflows/deploy.yml', 'deploy[0].trigger: push-to-release',
    'environments[0].name: production', 'environments[0].branch: main',
    'environments[0].url: https://api.example.com', 'environments[1].name: staging', 'environments[1].branch: main',
    'environments[1].url: https://staging.api.example.com', 'services[0].name: Stripe',
    'services[0].purpose: payments and subscription billing', 'services[0].evidence[0]: stripe (package)',
    'services[0].evidence[1]: STRIPE_SECRET_KEY (environment key name)', 'services[1].name: Sentry',
    'services[1].purpose: error reporting', 'services[1].evidence[0]: sentry-sdk (package)',
    'services[1].evidence[1]: SENTRY_DSN (environment key name)', 'data_stores[0].name: PostgreSQL',
    'data_stores[0].purpose: primary store', 'data_stores[0].managed_by: Cloud SQL']


class ProfileTest(unittest.TestCase):
    def read(self, text):
        """The filter's output for a fetched profile, `gh api` replaced by a file, run in a checkout that plants
        modules named like the ones the filter imports."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'profile.md'
            path.write_text(text)
            for module in ('yaml', 're'):
                (Path(tmp) / f'{module}.py').write_text('print("planted module ran"); raise SystemExit(0)\n')
            command = re.sub(r'^p=\$\(gh api [^\n]*\) &&', f'p=$(cat {shlex.quote(str(path))}) &&', PROFILE)
            self.assertNotEqual(command, PROFILE)
            result = run(command, cwd=tmp)
            self.assertNotIn('planted', result.stdout)
            return result

    def test_unreadable_profiles_print_nothing_from_the_file(self):
        for text, reason in (('password: malformed-profile-secret\n', 'no front matter'),
                             ('---\nprofile: 2\ntoken: newer-profile-secret\n---\n', 'not profile: 1'),
                             ('---\nprofile: 1\nkey: unclosed-profile-secret\n', 'front matter not closed'),
                             ('---\nprofile: 1\nbranches: [\nkey: bracket-profile-secret\n---\n',
                              'front matter does not parse'),
                             ('---\nprofile: 1\n  token: indent-profile-secret\n---\n', 'front matter does not parse'),
                             ('---\n- profile: 1\n- list-profile-secret\n---\n', 'not profile: 1'),
                             ('---\nprofile: true\ntoken: bool-profile-secret\n---\n', 'not profile: 1')):
            with self.subTest(reason=reason):
                result = self.read(text)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, f'unreadable: {reason}\n')

    def test_example_profile_prints_every_value(self):
        result = self.read((SKILL / 'references/example-profile.md').read_text())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), EXAMPLE_VALUES)

    def test_credentials_in_a_valid_profile_are_withheld(self):
        example = (SKILL / 'references/example-profile.md').read_text()
        head, sep, body = example.partition('\n---\n')
        extra = ('notes_url: https://user:url-profile-secret@example.com/x # comment-profile-secret\n'
                 'api_token: plain-profile-secret\n'
                 'extra:\n  - STRIPE_SECRET_KEY=assignment-profile-secret\n  - Bearer Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9\n'
                 'api_key: |\n  multiline-profile-secret\n  second-line-profile-secret\n'
                 'auth:\n  user: subtree-user-secret\n  method: subtree-method-secret\n'
                 'tokens:\n  - list-under-secret-key\n'
                 'deploy_notes: >\n  run it with\n  TOKEN=folded-profile-secret\n'
                 'empty_password:\n'
                 'Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9: key-is-the-secret')
        result = self.read(f'{head}\n{extra}{sep}{body}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), EXAMPLE_VALUES + [
            'notes_url: <withheld>', 'api_token: <withheld>', 'extra[0]: <withheld>', 'extra[1]: <withheld>',
            'api_key: <withheld>', 'auth: <withheld>', 'tokens: <withheld>', 'deploy_notes: <withheld>',
            'empty_password: null', '<withheld>: <withheld>'])
        self.assertNotIn('secret', result.stdout)
        self.assertNotIn('Ab1Cd2', result.stdout)
        self.assertNotIn('## ', result.stdout)


def git_repo(path, origin, *, commit=None, remote_branches=()):
    """A local checkout at `path` with `origin` and remote-tracking branches, and no network."""
    git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', '-C', str(path)]
    path.mkdir(parents=True)
    subprocess.run(git + ['init', '-q', '-b', 'main'], check=True)
    subprocess.run(git + ['remote', 'add', 'origin', origin], check=True)
    for name, text in (commit or {'README.md': 'fixture\n'}).items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(text)
    subprocess.run(git + ['add', '.'], check=True)
    subprocess.run(git + ['commit', '-qm', 'fixture'], check=True)
    for branch in ('main', *remote_branches):
        subprocess.run(git + ['update-ref', f'refs/remotes/origin/{branch}', 'HEAD'], check=True)
    subprocess.run(git + ['symbolic-ref', 'refs/remotes/origin/HEAD', 'refs/remotes/origin/main'], check=True)


class BranchesTest(unittest.TestCase):
    """FR-013: branch and tag names reach the transcript only through the filter."""

    def refs(self, app, default=''):
        result = subprocess.run(['bash', '-c', BRANCHES], capture_output=True, text=True, timeout=60, cwd=app,
                                env={**os.environ, 'DEFAULT': default})
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        return result.stdout.splitlines()

    BRANCH_NAMES = ('develop', 'staging', 'release/1.2', 'release/ghp_releaseCredential', 'hotfix/Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9',
                    'feature/plain-secret', 'sk-branchCredential', 'production')
    EXPECTED = ['default main', 'branch develop', 'branch hotfix/<withheld>', 'branch main', 'branch production',
                'branch release/1.2', 'branch release/<withheld>', 'branch staging', 'tags v*']

    def test_remote_refs_are_filtered_and_masked(self):
        with tempfile.TemporaryDirectory() as tmp:
            remote = Path(tmp) / 'remote.git'
            subprocess.run(['git', 'init', '-q', '--bare', str(remote)], check=True)
            git_repo(Path(tmp) / 'app', str(remote))
            app = Path(tmp) / 'app'
            for tag in ('v1.0', 'v2-ghp_tagCredential', 'other-tag-secret'):
                subprocess.run(['git', '-C', str(app), 'tag', tag], check=True)
            subprocess.run(['git', '-C', str(app), 'push', '-q', 'origin', 'HEAD:refs/heads/main', '--tags',
                            *[f'HEAD:refs/heads/{b}' for b in self.BRANCH_NAMES]], check=True, capture_output=True)
            subprocess.run(['git', '-C', str(app), 'tag', '-d', 'v1.0', 'v2-ghp_tagCredential', 'other-tag-secret'],
                           check=True, capture_output=True)
            status = run('git status --porcelain', cwd=app).stdout
            out = self.refs(app)
            self.assertEqual(out, self.EXPECTED)
            self.assertEqual(self.refs(app, 'ghp_defaultCredential')[0], 'default <withheld>')
            self.assertEqual(run('git status --porcelain', cwd=app).stdout, status)
            for value in ('Credential', 'Ab1Cd2', 'secret', 'v1.0', 'v2'):
                self.assertNotIn(value, '\n'.join(out))

    def test_offline_reads_tracking_branches_and_local_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            git_repo(Path(tmp) / 'app', 'https://user:remote-url-secret@127.0.0.1:9/acme/app.git',
                     remote_branches=self.BRANCH_NAMES)
            app = Path(tmp) / 'app'
            self.assertEqual(self.refs(app), self.EXPECTED[:-1])
            subprocess.run(['git', '-C', str(app), 'tag', 'v1-sk-localTagCredential'], check=True)
            out = self.refs(app, 'main')
            self.assertEqual(out, self.EXPECTED)
            self.assertNotIn('secret', '\n'.join(out))
            self.assertNotIn('Credential', '\n'.join(out))


class ModelRuleTest(unittest.TestCase):
    """FR-009: the model rule on the branches command's output; trunk when only the default exists."""

    def model(self, *lines):
        result = run(f"printf '%s\\n' {' '.join(shlex.quote(line) for line in lines)} | {MODEL}")
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        return result.stdout.splitlines()

    def test_only_the_default_is_trunk_whatever_its_name(self):
        for name in ('main', 'production', 'develop', 'master'):
            with self.subTest(default=name):
                self.assertEqual(self.model(f'default {name}', f'branch {name}', 'tags v*'), [
                    'branches.model: trunk', f'branches.release: {name}', f'branches.develop: {name}'])

    def test_first_match_wins(self):
        for lines, expected in (
                (('default main', 'branch main', 'branch staging', 'branch hotfix/1'), ['trunk', 'main', 'main']),
                (('default main', 'branch develop', 'branch main', 'branch production'), ['git-flow', 'main', 'develop']),
                (('default develop', 'branch develop', 'branch master'), ['git-flow', 'master', 'develop']),
                (('default trunk', 'branch development', 'branch trunk'), ['git-flow', 'trunk', 'development']),
                (('default main', 'branch main', 'branch release/1.2', 'branch production'), ['release-branches']),
                (('default main', 'branch main', 'branch production'), ['other', 'production', 'main']),
                (('default production', 'branch production', 'branch staging'), ['trunk', 'production', 'production']),
                (('default master', 'branch main', 'branch master'), ['other', 'main', 'master']),
                (('default main', 'branch main', 'branch master'), ['other', 'master', 'main'])):
            with self.subTest(lines=lines):
                out = self.model(*lines)
                self.assertEqual([line.split(': ', 1)[1] for line in out[:len(expected)]], expected)
                if expected == ['release-branches']:
                    self.assertEqual(out, ['branches.model: release-branches', 'branches.release_pattern: release/*'])


class ProductRepositoryTest(unittest.TestCase):
    """FR-013: the remote URL and `gh repo view` reach the transcript only through the filter."""

    def read(self, origin, response=None):
        with tempfile.TemporaryDirectory() as tmp:
            git_repo(Path(tmp) / 'app', origin)
            bin_dir = Path(tmp) / 'bin'
            bin_dir.mkdir()
            gh = bin_dir / 'gh'
            gh.write_text('#!/bin/bash\n[ -z "$GH_RESPONSE" ] && { echo "viewed $3"; exit; }\n'
                          'while [ "$1" != --jq ]; do shift; done; exec jq -r "$2" "$GH_RESPONSE"\n')
            gh.chmod(0o755)
            env = {**os.environ, 'PATH': f'{bin_dir}:{os.environ["PATH"]}'}
            if response is not None:
                (Path(tmp) / 'view.json').write_text(response)
                env['GH_RESPONSE'] = str(Path(tmp) / 'view.json')
            result = subprocess.run(['bash', '-c', PRODUCT], capture_output=True, text=True, timeout=60,
                                    cwd=Path(tmp) / 'app', env=env)
            self.assertEqual(result.stderr, '')
            return result.stdout.splitlines()

    def test_origin_keeps_owner_and_name_only(self):
        for origin, expected in (
                ('https://user:userinfo-secret@github.com/acme/api.git?token=ghp_queryCredential', 'acme/api'),
                ('https://github.com/acme/api?access_token=query-secret#frag-secret', 'acme/api'),
                ('https://github.com/acme/api.git/', 'acme/api'),
                ('git@github.com:acme/api.git', 'acme/api'),
                ('ssh://git@github.com/acme/my.app.git', 'acme/my.app')):
            with self.subTest(origin=origin):
                self.assertEqual(self.read(origin), [f'origin {expected}', f'viewed {expected}'])
        for origin in ('https://github.com/acme/ghp_repoCredential.git', 'https://github.com/acme/Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9',
                       '/srv/git/api-path-secret.git', 'https://user:pa?ss-secret@github.com/acme/api.git',
                       'https://github.com/acme/api/extra-path-secret'):
            with self.subTest(origin=origin):
                self.assertEqual(self.read(origin), ['origin <withheld>'])

    def test_origin_must_be_on_github(self):
        """FR-008: a remote on another host never names a GitHub repository, whatever its owner/name."""
        for origin in ('https://GitHub.com/acme/api.git', 'ssh://git@github.com:22/acme/api.git',
                       'https://evil.example@github.com/acme/api'):
            with self.subTest(origin=origin):
                self.assertEqual(self.read(origin), ['origin acme/api', 'viewed acme/api'])
        for origin in ('https://gitlab.com/acme/api.git', 'git@bitbucket.org:acme/api.git',
                       'ssh://git@git.example.com/acme/api.git', 'https://github.com.evil.example/acme/api',
                       'https://github.com@evil.example/acme/api', 'git@github.com@evil.example:acme/api.git',
                       'https://evil.example/github.com/acme/api', 'acme/api', 'file:///acme/api'):
            with self.subTest(origin=origin):
                self.assertEqual(self.read(origin), ['origin <withheld>'])

    @unittest.skipUnless(shutil.which('jq'), 'jq is not installed')
    def test_view_masks_the_default_branch(self):
        origin = 'https://github.com/acme/api.git?sig=query-secret'
        for branch, shown in (('main', 'main'), ('ghp_defaultCredential', '<withheld>'),
                              ('Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9', '<withheld>'), ('main?token=branch-secret', '<withheld>')):
            with self.subTest(branch=branch):
                response = ('{"nameWithOwner":"acme/api","isInOrganization":true,"isFork":false,'
                            f'"defaultBranchRef":{{"name":"{branch}"}}}}')
                out = self.read(origin, response)
                self.assertEqual(out, ['origin acme/api', 'repo acme/api', 'organization true', 'fork false',
                                       f'default {shown}'])
                for value in ('Credential', 'secret', 'Ab1Cd2'):
                    self.assertNotIn(value, '\n'.join(out))


class ControlRepositoryTest(unittest.TestCase):
    """US2 scenario 1: resolve the control repository, read its profile, and let the stored values win."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name).resolve()
        self.api = self.ws / 'api'
        git_repo(self.api, 'https://user:remote-url-secret@github.com/acme/api.git', remote_branches=('develop',))
        example = (SKILL / 'references/example-profile.md').read_text()
        git_repo(self.ws / 'control', 'git@github.com:Acme/Control.git', commit={'profile/api.md': example})
        git_repo(self.ws / 'acme-autopilot', 'https://github.com/acme/acme-autopilot.git')
        git_repo(self.ws / 'specs', 'https://github.com/acme/specs.git', commit={'.specify/memory/x.md': 'x\n'})

    def tearDown(self):
        self.tmp.cleanup()

    def candidates(self, env=None):
        result = subprocess.run(['bash', '-c', CONTROL], capture_output=True, text=True, timeout=60, cwd=self.api,
                                env={**os.environ, 'PWD': str(self.api), **(env or {})})
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        return result.stdout.splitlines()

    def test_named_control_repository_wins_over_conventional_names(self):
        (self.ws / 'AGENTS.md').write_text('# Workspace\n\n- **Control repository**: `acme/control` (specs, profiles)\n')
        self.assertEqual(self.candidates(), ['named acme/control', f'candidate {self.ws}/control Acme/Control'])

    def test_named_as_a_url_in_the_checkout_readme(self):
        (self.api / 'README.md').write_text('Control repository: https://github.com/acme/control.git\n')
        self.assertEqual(self.candidates(), ['named acme/control', f'candidate {self.ws}/control Acme/Control'])

    def test_symlinked_readme_is_not_opened(self):
        (self.api / '.env').write_text('Control repository: acme/env-control-secret\n')
        (self.api / 'README.md').unlink()
        (self.api / 'README.md').symlink_to('.env')
        self.assertEqual(self.candidates(), [f'candidate {self.ws}/acme-autopilot acme/acme-autopilot'])

    def test_autopilot_sibling_otherwise_and_several_mean_ask(self):
        self.assertEqual(self.candidates(), [f'candidate {self.ws}/acme-autopilot acme/acme-autopilot'])
        git_repo(self.ws / 'repos/beta-autopilot', 'git@github.com:acme/beta-autopilot.git')
        self.assertEqual(self.candidates({'REPOS_DIR': str(self.ws / 'repos')}), [
            f'candidate {self.ws}/acme-autopilot acme/acme-autopilot',
            f'candidate {self.ws}/repos/beta-autopilot acme/beta-autopilot'])

    def set_origin(self, path, origin):
        subprocess.run(['git', '-C', str(path), 'remote', 'set-url', 'origin', origin], check=True)

    def test_remote_names_are_masked(self):
        """FR-013: a sibling's origin can carry a credential in its query string, fragment or name."""
        self.set_origin(self.ws / 'acme-autopilot', 'https://github.com/acme/acme-autopilot.git?access_token=ghp_queryCredential')
        git_repo(self.ws / 'repos/beta-autopilot', 'https://github.com/acme/ghp_repoCredential.git')
        git_repo(self.ws / 'repos/gamma-autopilot', 'git@github.com:acme/gamma-autopilot.git#frag-secret')
        git_repo(self.ws / 'repos/delta-autopilot', 'https://user:userinfo-secret@github.com/acme/Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9')
        out = self.candidates({'REPOS_DIR': str(self.ws / 'repos')})
        self.assertEqual(out, [f'candidate {self.ws}/acme-autopilot acme/acme-autopilot',
                               f'candidate {self.ws}/repos/beta-autopilot <withheld>',
                               f'candidate {self.ws}/repos/delta-autopilot <withheld>',
                               f'candidate {self.ws}/repos/gamma-autopilot acme/gamma-autopilot'])
        for value in ('Credential', 'secret', 'Ab1Cd2'):
            self.assertNotIn(value, '\n'.join(out))

    def test_remote_must_be_on_github(self):
        """FR-008: a checkout whose origin is on another host never matches the named repository."""
        (self.ws / 'AGENTS.md').write_text('Control repository: acme/control\n')
        self.set_origin(self.ws / 'control', 'https://gitlab.com/acme/control.git')
        git_repo(self.ws / 'repos/mirror', 'git@github.com.evil.example:acme/control.git')
        self.assertEqual(self.candidates({'REPOS_DIR': str(self.ws / 'repos')}), ['named acme/control'])
        (self.ws / 'AGENTS.md').unlink()
        self.set_origin(self.ws / 'acme-autopilot', 'ssh://git@git.example.com/acme/acme-autopilot.git')
        self.assertEqual(self.candidates(), [f'candidate {self.ws}/acme-autopilot <withheld>'])

    def test_candidate_paths_are_masked(self):
        """FR-013: a checkout's directory name can hold a credential; the path prints as `<withheld>`."""
        for name in ('ghp_pathCredential-autopilot', 'Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9-autopilot', 'q=secret-autopilot'):
            git_repo(self.ws / 'repos' / name, 'https://github.com/acme/acme-autopilot.git')
        out = self.candidates({'REPOS_DIR': str(self.ws / 'repos')})
        self.assertEqual(out, [f'candidate {self.ws}/acme-autopilot acme/acme-autopilot',
                               'candidate <withheld> acme/acme-autopilot'])
        for value in ('Credential', 'secret', 'Ab1Cd2'):
            self.assertNotIn(value, '\n'.join(out))

    def test_named_control_origin_is_masked(self):
        (self.ws / 'AGENTS.md').write_text('Control repository: acme/control\n')
        self.set_origin(self.ws / 'control', 'https://github.com/Acme/Control.git?token=ghp_controlCredential#frag-secret')
        self.assertEqual(self.candidates(), ['named acme/control', f'candidate {self.ws}/control Acme/Control'])

    def test_credential_looking_named_repository_matches_nothing(self):
        (self.ws / 'AGENTS.md').write_text('Control repository: acme/ghp_namedCredential\n')
        git_repo(self.ws / 'leak', 'https://github.com/acme/Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9')
        self.assertEqual(self.candidates(), ['named <withheld>'])

    def test_stored_profile_values_are_the_defaults(self):
        (self.ws / 'AGENTS.md').write_text('Control repository: acme/control\n')
        status = {path: run('git status --porcelain', cwd=path).stdout for path in (self.api, self.ws / 'control')}
        candidate = self.candidates()[-1].split(' ')
        self.assertEqual(candidate, ['candidate', str(self.ws / 'control'), 'Acme/Control'])

        read = PROFILE.replace(PROFILE.split('\n', 1)[0], PROFILE_OFFLINE).replace('<repo>', 'api')
        profile = subprocess.run(['bash', '-c', read], capture_output=True, text=True, timeout=60,
                                 env={**os.environ, 'AP': candidate[1]})
        self.assertEqual(profile.returncode, 0, profile.stderr)
        self.assertIn('branches.model: trunk', profile.stdout.splitlines())

        # The checkout says git-flow: it has a remote `develop` branch.
        self.assertIn('origin/develop', run('git branch -r', cwd=self.api).stdout)
        checkout = 'branches.develop: develop\nbranches.model: git-flow\nbranches.tags: v*\ndeploy[1].kind: docker-compose'
        merged = subprocess.run(['bash', '-c', MERGE], capture_output=True, text=True, timeout=60,
                                env={**os.environ, 'defaults': profile.stdout, 'checkout': checkout})
        self.assertEqual(merged.returncode, 0, merged.stderr)
        lines = merged.stdout.splitlines()
        for line in ('branches.default: main (profile)', 'branches.develop: main (profile), checkout: develop',
                     'branches.model: trunk (profile), checkout: git-flow', 'branches.tags: v* (profile)',
                     'data_stores[0].managed_by: Cloud SQL (profile)'):
            self.assertIn(line, lines)
        self.assertEqual(lines[-1], 'deploy[1].kind: docker-compose')
        self.assertEqual(len(lines), len(EXAMPLE_VALUES) + 1)
        for path, before in status.items():
            self.assertEqual(run('git status --porcelain', cwd=path).stdout, before)


class PrismaTest(unittest.TestCase):
    def test_provider_names_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            git_repo(Path(tmp) / 'app', 'https://github.com/acme/app.git', commit={'prisma/schema.prisma': (
                'generator client {\n  provider = "prisma-client-js" // TOKEN=generator-comment-secret\n}\n'
                'datasource db {\n  provider = "postgresql" // DATABASE_URL=postgres://u:comment-pw-secret@db/app\n'
                '  url      = env("DATABASE_URL")\n}\n'
                'datasource other {\n  provider = "sk-provider-secret"\n}\n')})
            listed = run(f"git ls-files -- '*.prisma' | {GUARD}", cwd=Path(tmp) / 'app')
            self.assertEqual(listed.stdout.splitlines(), ['prisma/schema.prisma'])
            result = run(PRISMA.replace('<files>', listed.stdout.strip()), cwd=Path(tmp) / 'app')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(),
                             ['provider prisma-client-js', 'provider postgresql', 'provider <withheld>'])
            self.assertNotIn('secret', result.stdout)


class EnvironmentKeyNamesTest(unittest.TestCase):
    """US2 scenario 5: a checkout with `.env.example` and `.env`."""

    def test_example_names_only_and_env_never_opened(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', '-C', tmp]
            subprocess.run(git + ['init', '-q'], check=True)
            (Path(tmp) / 'deploy').mkdir()
            (Path(tmp) / '.env.example').write_text(
                '# Stripe\nSTRIPE_SECRET_KEY=placeholder\nexport DATABASE_URL="postgres://u:example-pw@db/app"\n'
                '  APP_NAME = demo-value\n\nnot a key line\n')
            (Path(tmp) / 'deploy/.env.sample').write_text('SENTRY_DSN=https://sample-dsn@example.com/1\n')
            (Path(tmp) / '.env').write_text('STRIPE_SECRET_KEY=must-never-appear\n')
            (Path(tmp) / '.env.local').write_text('LOCAL_TOKEN=must-never-appear\n')
            subprocess.run(git + ['add', '-f', '.'], check=True)  # worst case: even .env is tracked
            subprocess.run(git + ['commit', '-qm', 'fixture'], check=True)
            status = run('git status --porcelain', cwd=tmp).stdout
            forbidden = [Path(tmp) / '.env', Path(tmp) / '.env.local']
            for path in forbidden:
                path.chmod(0)  # any read of a forbidden file now fails loudly on stderr

            listed = run(f'{ENV_FILES} | {GUARD}', cwd=tmp)
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(listed.stdout.splitlines(), ['.env.example', 'deploy/.env.sample'])
            names = []
            for file in listed.stdout.splitlines():
                result = run(ENV_NAMES.replace('<file>', shlex.quote(file)), cwd=tmp)
                self.assertEqual((result.returncode, result.stderr), (0, ''))
                names += result.stdout.splitlines()

            self.assertEqual(names, ['STRIPE_SECRET_KEY', 'DATABASE_URL', 'APP_NAME', 'SENTRY_DSN'])
            if os.geteuid() != 0:
                self.assertEqual(listed.stderr, '')
            for path in forbidden:
                path.chmod(0o600)
            self.assertEqual(run('git status --porcelain', cwd=tmp).stdout, status)
            self.assertEqual((Path(tmp) / '.env').read_text(), 'STRIPE_SECRET_KEY=must-never-appear\n')

    def test_multiline_quoted_values_are_not_keys(self):
        result = on_file(ENV_NAMES, (
            'PRIVATE_KEY="-----BEGIN KEY-----\nabc123TOKEN=\n  ESCAPED=\\" still-inside\n-----END KEY-----"\n'
            "SINGLE='first\nSINGLEVALUE=line\n'\n"
            'TICK=`one\nTICKVALUE=two`\n'
            'INLINE="closed" # LATER="open\n'
            'AFTER=1\n'), '.env.example')
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(result.stdout.splitlines(), ['PRIVATE_KEY', 'SINGLE', 'TICK', 'INLINE', 'AFTER'])

    def test_escaped_quotes_do_not_close_a_value(self):
        """FR-013: an escaped apostrophe or backtick keeps a multiline value open."""
        result = on_file(ENV_NAMES, (
            "SINGLE='it\\'s\nSINGLEVALUE=line-secret\nend'\n"
            'TICK=`one\\`\nTICKVALUE=two-secret`\n'
            "CLOSED='done\\\\'\n"
            'AFTER=1\n'), '.env.example')
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(result.stdout.splitlines(), ['SINGLE', 'TICK', 'CLOSED', 'AFTER'])

    def test_credential_looking_key_names_are_masked(self):
        """FR-013: a valid identifier can itself be a credential."""
        result = on_file(ENV_NAMES, (
            'STRIPE_SECRET_KEY=placeholder\nghp_exampleKeyCredential=1\nexport Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9=1\n'
            'X_AKIAIOSFODNN7EXAMPLE=1\n0123456789abcdef0123456789abcdef=1\nNEXT_PUBLIC_SUPABASE_ANON_KEY=x\n'), '.env.example')
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(result.stdout.splitlines(), ['STRIPE_SECRET_KEY', '<withheld>', '<withheld>', '<withheld>',
                                                      'NEXT_PUBLIC_SUPABASE_ANON_KEY'])
        for value in ('Credential', 'Ab1Cd2', 'AKIA', '0123'):
            self.assertNotIn(value, result.stdout)

    def test_untracked_example_files_are_listed(self):
        """US2 scenario 5 holds before the example file is committed; `.env` is never opened."""
        with tempfile.TemporaryDirectory() as tmp:
            git_repo(Path(tmp) / 'app', 'https://github.com/acme/app.git',
                     commit={'.gitignore': '.env\n.env.local\nignored/\n', 'deploy/.env.dist': 'TRACKED_NAME=x\n'})
            app = Path(tmp) / 'app'
            (app / '.env.example').write_text('STRIPE_SECRET_KEY=placeholder\nAPP_NAME=untracked-value\n')
            (app / 'secrets.env.example').write_text('FORBIDDEN_NAME=forbidden-value-secret\n')
            (app / '.env').write_text('STRIPE_SECRET_KEY=must-never-appear\n')
            (app / '.env.local').write_text('LOCAL_TOKEN=must-never-appear\n')
            (app / 'ignored').mkdir()
            (app / 'ignored/.env.sample').write_text('IGNORED_NAME=x\n')
            status = run('git status --porcelain', cwd=app).stdout
            for path in (app / '.env', app / '.env.local', app / 'secrets.env.example'):
                path.chmod(0)  # any read of a forbidden file now fails loudly on stderr

            listed = run(f'{ENV_FILES} | {GUARD}', cwd=app)
            self.assertEqual((listed.returncode, listed.stderr), (0, ''))
            self.assertEqual(sorted(listed.stdout.splitlines()),
                             ['.env.example', 'deploy/.env.dist', 'skipped secrets.env.example: not opened'])
            names = []
            for file in listed.stdout.splitlines():
                if not file.startswith('skipped '):
                    result = run(ENV_NAMES.replace('<file>', shlex.quote(file)), cwd=app)
                    self.assertEqual((result.returncode, result.stderr), (0, ''))
                    names += result.stdout.splitlines()
            self.assertEqual(sorted(names), ['APP_NAME', 'STRIPE_SECRET_KEY', 'TRACKED_NAME'])
            for path in (app / '.env', app / '.env.local', app / 'secrets.env.example'):
                path.chmod(0o600)
            self.assertEqual(run('git status --porcelain', cwd=app).stdout, status)

    def test_symlinked_example_files_are_not_opened(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', '-C', tmp]
            subprocess.run(git + ['init', '-q'], check=True)
            (Path(tmp) / '.env').write_text('STRIPE_SECRET_KEY=must-never-appear\n')
            (Path(tmp) / '.env.example').symlink_to('.env')
            (Path(tmp) / 'deploy').mkdir()
            (Path(tmp) / 'deploy/.env.sample').symlink_to('../.env')
            (Path(outside) / '.env.dist').write_text('OUTSIDE_TOKEN=must-never-appear\n')
            subprocess.run(git + ['add', '-f', '.env.example', 'deploy/.env.sample'], check=True)
            subprocess.run(git + ['commit', '-qm', 'fixture'], check=True)
            (Path(tmp) / 'linked').symlink_to(outside)
            (Path(tmp) / '.env').chmod(0)  # any read of the forbidden file now fails loudly on stderr

            listed = run(f'{{ {ENV_FILES}; echo linked/.env.dist; }} | {GUARD}', cwd=tmp)
            self.assertEqual((listed.returncode, listed.stderr), (0, ''))
            self.assertEqual(listed.stdout.splitlines(), ['skipped .env.example: not opened',
                                                          'skipped deploy/.env.sample: not opened',
                                                          'skipped linked/.env.dist: not opened'])
            (Path(tmp) / '.env').chmod(0o600)


if __name__ == '__main__':
    unittest.main()
