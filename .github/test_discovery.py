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


JOBS = fenced("awk 'function clean(v)", 'jobs:')
TRIGGERS = fenced("awk 'function clean(v)", 'function each(')
COMPOSE = fenced("grep -nE '^ {2}")
PROFILE = fenced('p=$(gh api ')
FIREBASE = inline("jq -r 'def safe:")
ENV_FILES = inline("git ls-files -- '*.env.example'")
ENV_NAMES = fenced("sed -n 's/^[[:space:]]*")

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
                                 'environment <expression>', 'job odd', 'environment <withheld>'])
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
""")
        self.assertEqual(result.stdout.splitlines(), [
            '2:  app:', '3:    build: <withheld>', '4:    image: <registry>/org/app:1', '5:  worker:',
            '6:    build: ./worker', '7:  remote:', '8:    build: <withheld>', '9:  db:',
            '10:    image: postgres:17@sha256:abc'])

    @unittest.skipUnless(shutil.which('jq'), 'jq is not installed')
    def test_firebase_hosting_names_only(self):
        minified = ('{"hosting":[{"target":"prod","site":"acme-prod","headers":[{"source":"**","headers":'
                    '[{"key":"Authorization","value":"Bearer firebase-header-secret"}]}]},{"target":"bad name!"}],'
                    '"functions":{"predeploy":["TOKEN=firebase-command-secret npm run build"]}}')
        result = on_file(FIREBASE, minified, 'firebase.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         ['hosting target=prod site=acme-prod', 'hosting target=<withheld> site='])


class ProfileTest(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'profile.md'
            path.write_text(text)
            command = re.sub(r'^p=\$\(gh api [^\n]*\) &&', f'p=$(cat {shlex.quote(str(path))}) &&', PROFILE)
            self.assertNotEqual(command, PROFILE)
            return run(command)

    def test_unreadable_profiles_print_nothing_from_the_file(self):
        for text, reason in (('password: malformed-profile-secret\n', 'no front matter'),
                             ('---\nprofile: 2\ntoken: newer-profile-secret\n---\n', 'not profile: 1'),
                             ('---\nprofile: 1\nkey: unclosed-profile-secret\n', 'front matter not closed')):
            with self.subTest(reason=reason):
                result = self.read(text)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, f'unreadable: {reason}\n')

    def test_example_profile_front_matter_prints_unchanged(self):
        example = (SKILL / 'references/example-profile.md').read_text()
        result = self.read(example)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, example.split('\n---\n', 1)[0][4:] + '\n')

    def test_credentials_in_a_valid_profile_are_withheld(self):
        example = (SKILL / 'references/example-profile.md').read_text()
        head, sep, body = example.partition('\n---\n')
        extra = ('notes_url: https://user:url-profile-secret@example.com/x\napi_token: plain-profile-secret\n'
                 'extra:\n  - STRIPE_SECRET_KEY=assignment-profile-secret\n  - Bearer Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9')
        result = self.read(f'{head}\n{extra}{sep}{body}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('repository: acme/api', result.stdout)
        self.assertTrue(result.stdout.endswith(
            'notes_url: <withheld>\napi_token: <withheld>\nextra:\n  - <withheld>\n  - <withheld>\n'), result.stdout)
        self.assertNotIn('secret', result.stdout)
        self.assertNotIn('Ab1Cd2', result.stdout)
        self.assertNotIn('## ', result.stdout)


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

            listed = run(ENV_FILES, cwd=tmp)
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


if __name__ == '__main__':
    unittest.main()
