"""Check autop-onboard-project's Step 2/3 contract: question order, the AGENTS.md section, the size caps."""
from pathlib import Path
import re
import unittest

root = Path(__file__).resolve().parents[1]
SKILL = root / 'skills/autop-onboard-project'
DOC = (SKILL / 'references/questions.md').read_text()
BLOCK = re.search(r'```markdown\n(.*?)\n```', DOC, re.S)


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
        self.assertEqual([next(i for i, k in enumerate(keys) if f'`{o}' in k) for o in order], list(range(len(order))))

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
