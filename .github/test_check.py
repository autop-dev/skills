"""Regression tests for check.py, run on a copy of the repository with an edited profile example."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

root = Path(__file__).resolve().parents[1]
EXAMPLE = 'skills/autop-onboard-project/references/example-profile.md'


def run_check(extra):
    """Run check.py on a copy whose example front matter ends with the given YAML lines."""
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(root / 'skills', Path(tmp) / 'skills')
        shutil.copytree(root / '.github', Path(tmp) / '.github', ignore=shutil.ignore_patterns('__pycache__'))
        example = Path(tmp) / EXAMPLE
        head, sep, body = example.read_text().partition('\n---\n')
        example.write_text(f'{head}\n{extra}{sep}{body}')
        return subprocess.run([sys.executable, str(Path(tmp) / '.github/check.py')],
                              capture_output=True, text=True, timeout=60)


class CheckTest(unittest.TestCase):
    def test_rejects_question_mark_in_key(self):
        result = run_check('"?": x')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{EXAMPLE}: ?: URL with user info or query string', result.stderr)

    def test_recursive_alias_terminates(self):
        result = run_check('extra: &loop [*loop]')
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
