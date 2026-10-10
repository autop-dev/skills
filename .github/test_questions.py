"""Check autop-onboard-project's Step 2/3 contract: question order, the AGENTS.md section, the size caps."""
from pathlib import Path
import os
import re
import subprocess
import unittest

root = Path(__file__).resolve().parents[1]
SKILL = root / 'skills/autop-onboard-project'
DOC = (SKILL / 'references/questions.md').read_text()
BLOCK = re.search(r'```markdown\n(.*?)\n```', DOC, re.S)
FLAT = ' '.join(DOC.split())


def fenced(doc, start):
    """The one fenced sh block of a document that starts with the given text."""
    blocks = [b for b in re.findall(r'```sh\n(.*?)\n```', doc, re.S) if b.startswith(start)]
    assert len(blocks) == 1, f'{len(blocks)} sh blocks start with {start!r}'
    return blocks[0]


def risky(block):
    return re.search(r'^def risky\(s\):\n(?:    .*\n)+', block + '\n', re.M)[0]


CARRY = fenced(DOC, "printf '%s\\n' \"$p\" | python3")
FILTER = fenced((SKILL / 'references/discovery.md').read_text(), 'p=$(gh api ')


class Questions(unittest.TestCase):
    def test_skill_is_at_most_160_lines(self):
        self.assertLessEqual(len((SKILL / 'SKILL.md').read_text().splitlines()), 160)

    def test_questions_come_in_the_story_order(self):
        rows = re.findall(r'^\| (\d+) \| [^|]*\|[^|]*\|[^|]*\| ([^|]*)\|$', DOC, re.M)
        self.assertEqual(len(rows), len(re.findall(r'^\| \d+ \|', DOC, re.M)), 'a numbered row does not parse')
        self.assertEqual([int(n) for n, _ in rows], list(range(1, len(rows) + 1)))
        keys = [k.strip() for _, k in rows]
        order = ['branches.release', 'branches.develop', 'branches.model', 'ci.system', 'ci.gates',
                 'deploy[]', 'environments[]', 'services[]', 'data_stores[]', '## Notes']
        rows_of = [next(i for i, k in enumerate(keys) if f'`{o}' in k) for o in order]
        self.assertEqual(rows_of, sorted(rows_of))
        self.assertEqual(sorted(set(rows_of)), list(range(len(rows))))

    def test_one_workflow_and_one_manifest_take_at_most_eight_questions(self):
        """SC-001: lists are one question each, with no "another?" follow-up; question 4 is stated."""
        rows = re.findall(r'^\| (\d+) \| ([^|]*)\|', DOC, re.M)
        for n, question in rows:
            self.assertNotIn('another', question.lower(), f'question {n} asks a follow-up')
            self.assertNotRegex(question.lower(), r'^each ', f'question {n} is asked per entry')
        self.assertIn('CI system', dict(rows)['4'])
        self.assertLessEqual(len(rows) - 1, 8)
        for needle in ('**A list is one question.**', 'no separate "another?" question', 'at most eight questions'):
            self.assertIn(needle, FLAT)

    def test_unknown_keys_are_kept_unless_their_content_is_credential_looking(self):
        """FR-019: a key withheld only for its name is copied; a credential-looking key or value is dropped."""
        self.assertEqual(risky(CARRY), risky(FILTER), 'the check must use the filter\'s credential test')
        token = 'ghp_' + 'a1B2' * 9
        profile = '\n'.join([
            '---', 'profile: 1', 'repository: acme/api', 'updated: 2026-01-01',
            'branches: {default: main, release: main, develop: main, model: trunk, freeze: friday}',
            'ci: {system: none}', 'deploy:', '  - {name: web, kind: other, trigger: manual, region: eu, hook: "https://u:p@h"}',
            'environments: []', 'services: []', 'data_stores: []',
            'monkey_tests: [checkout, search]', 'owner_team: payments', 'deploy_token: ' + token,
            'api_key: ' + 'Ab1' * 10, token + ': x', 'note: "BUILD=1"', '---', '', '## Notes', '', 'Nothing recorded.', ''])
        result = subprocess.run(['bash', '-c', CARRY], capture_output=True, text=True, timeout=60,
                                env={'p': profile, 'PATH': os.environ['PATH']})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            'keep monkey_tests', 'keep owner_team', 'drop deploy_token', 'drop api_key', 'drop <withheld>', 'drop note',
            'keep branches.freeze', 'keep deploy[0].region', 'drop deploy[0].hook'])
        self.assertNotIn(token, result.stdout + result.stderr)
        self.assertIn('`monkey_tests` holds `KEY`) is `keep`', FLAT)

    def test_an_unchanged_profile_is_skipped_only_with_the_same_updated(self):
        """FR-019: `updated` counts in the comparison, so a later revisit refreshes it."""
        self.assertNotIn('identical but for `updated`', FLAT)
        for needle in ('a complete assembled profile, `updated` included, byte for byte the stored file',
                       'A stored `updated` from an earlier day is a change'):
            self.assertIn(needle, FLAT)

    def test_an_open_pull_request_branch_is_fetched_before_its_defaults_are_read(self):
        """FR-019: defaults, Notes and unknown keys come from a freshly fetched `origin/<branch>`."""
        for needle in ('`git -C <checkout> fetch origin <branch>` runs as soon as the person chooses it, before any default is read',
                       'again in Step 3 before the script re-fetches',
                       '`p=$(git -C "$AP" show origin/<branch>:profile/<repo>.md) &&`',
                       'Updating the branch fetches it at once (above), before the interview reads defaults.'):
            self.assertIn(needle, FLAT)

    def test_agents_section_template_fits_ten_lines(self):
        self.assertIsNotNone(BLOCK, 'no ```markdown template in questions.md')
        block = BLOCK[1]
        lines = block.splitlines()
        self.assertEqual(lines[0], '## Branches and delivery')
        self.assertLessEqual(len(lines), 10)
        for needle in ('<release>', '<develop>', '<ci.system>', 'profile/<repo>.md', '<AP_REPO>'):
            self.assertIn(needle, block)

    def test_rendered_section_has_no_query_or_user_info(self):
        self.assertIsNotNone(BLOCK, 'no ```markdown template in questions.md')
        block = BLOCK[1]
        for key, value in {'<AP_REPO>': 'acme/acme-autopilot', '<AP default branch>': 'main', '<repo>': 'api'}.items():
            block = block.replace(key, value)
        url = re.search(r'\((https://[^)]+)\)', block)[1]
        self.assertEqual(url, 'https://github.com/acme/acme-autopilot/blob/main/profile/api.md')

    def test_write_list_names_branches_and_commits(self):
        text = ' '.join((SKILL / 'SKILL.md').read_text().split())
        for needle in ('onboard/profile-<repo>', 'onboard/agents-<repo>', 'docs: profile <repo>',
                       'docs: link the project profile', 'gh pr create --repo', 'explicit yes', 'autop-add-issue',
                       'references/questions.md'):
            self.assertIn(needle, text)

    def test_report_names_the_next_step_and_never_files_work(self):
        text = (SKILL / 'SKILL.md').read_text()
        self.assertIn('\n## Report\n', text)
        report = ' '.join(text.split('\n## Report\n', 1)[1].split('\n## ', 1)[0].split())
        for needle in ('pull request links', 'profile/<repo>.md', '`autop-add-issue`', 'Never run `autop issue add`'):
            self.assertIn(needle, report)


if __name__ == '__main__':
    unittest.main()
