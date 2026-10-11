"""Regression tests for check.py, run on a copy of the repository with an edited profile example or scaffold."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

root = Path(__file__).resolve().parents[1]
EXAMPLE = 'skills/autop-onboard-project/references/example-profile.md'
SCAFFOLD = 'templates/control-repo'


def run_check(extra='', edit=None):
    """Run check.py on a copy whose example front matter ends with the given YAML lines and whose
    scaffold directory has been passed to edit, when given."""
    with tempfile.TemporaryDirectory() as tmp:
        for name in ('skills', 'templates', '.github'):
            shutil.copytree(root / name, Path(tmp) / name, ignore=shutil.ignore_patterns('__pycache__'))
        example = Path(tmp) / EXAMPLE
        head, sep, body = example.read_text().partition('\n---\n')
        example.write_text(f'{head}\n{extra}{sep}{body}')
        if edit:
            edit(Path(tmp) / SCAFFOLD)
        return subprocess.run([sys.executable, str(Path(tmp) / '.github/check.py')],
                              capture_output=True, text=True, timeout=60)


def rehash(scaffold, rel, mode='template'):
    """List rel in the scaffold manifest with its current sha256, as an author adding a file would."""
    manifest = json.loads((scaffold / 'manifest.json').read_text())
    digest = hashlib.sha256((scaffold / rel).read_bytes()).hexdigest()
    manifest['files'][rel] = {'sha256': digest, 'mode': mode}
    (scaffold / 'manifest.json').write_text(json.dumps(manifest))


class CheckTest(unittest.TestCase):
    def test_rejects_question_mark_in_key(self):
        result = run_check('"?": x')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{EXAMPLE}: ?: URL with user info or query string', result.stderr)

    def test_rejects_question_mark_in_set_and_ordered_maps(self):
        for extra in ('extra: !!set {"?": null}', 'extra: !!omap [x: "?"]', 'extra: !!pairs [x: "?"]'):
            with self.subTest(extra=extra):
                result = run_check(extra)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('URL with user info or query string', result.stderr)

    def test_recursive_alias_terminates(self):
        result = run_check('extra: &loop [*loop]')
        self.assertEqual(result.returncode, 0, result.stderr)


class ScaffoldTest(unittest.TestCase):
    def test_shipped_tree_passes(self):
        result = run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('scaffold manifest', result.stdout)

    def test_shipped_manifest_lists_every_file_with_its_mode(self):
        scaffold = root / SCAFFOLD
        manifest = json.loads((scaffold / 'manifest.json').read_text())
        self.assertEqual(manifest['version'], 1)
        self.assertEqual(manifest['source']['repo'], 'autop-dev/control')
        present = {p.relative_to(scaffold).as_posix() for p in scaffold.rglob('*') if p.is_file()} - {'manifest.json'}
        self.assertEqual(set(manifest['files']), present)
        templates = {rel for rel, entry in manifest['files'].items() if entry['mode'] == 'template'}
        self.assertEqual(templates, {'AGENTS.md.tmpl', '.specify/memory/constitution.md.tmpl'})
        self.assertIn('specs/README.md', present)
        self.assertNotIn('.specify/memory/constitution.md', present)
        self.assertNotIn('.specify/port-manifest.json', present)

    def test_mutated_copy_file_fails_naming_it(self):
        rel = '.specify/scripts/bash/common.sh'
        result = run_check(edit=lambda s: (s / rel).write_bytes((s / rel).read_bytes() + b'\n'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{SCAFFOLD}/{rel}: sha256 does not match manifest', result.stderr)

    def test_unlisted_file_fails_naming_it(self):
        result = run_check(edit=lambda s: (s / 'specs/extra.md').write_text('extra\n'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{SCAFFOLD}/specs/extra.md: not listed in manifest', result.stderr)

    def test_unlisted_os_and_cache_files_are_not_exempt(self):
        def edit(scaffold):
            (scaffold / '.DS_Store').write_bytes(b'\0')
            (scaffold / '.specify/scripts/bash/__pycache__').mkdir()
            (scaffold / '.specify/scripts/bash/__pycache__/x.pyc').write_bytes(b'\0')
        result = run_check(edit=edit)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{SCAFFOLD}/.DS_Store: not listed in manifest', result.stderr)
        self.assertIn(f'{SCAFFOLD}/.specify/scripts/bash/__pycache__/x.pyc: not listed in manifest', result.stderr)

    def test_readme_describes_the_scaffold(self):
        readme = (root / 'README.md').read_text()
        _, sep, section = readme.partition('\n## Control repository scaffold\n')
        self.assertTrue(sep, 'README.md has no "Control repository scaffold" section')
        section = ' '.join(section.split('\n## ')[0].split())
        self.assertIn(f'`{SCAFFOLD}/`', section)
        self.assertIn('"Set up" chat writes into a customer\'s control repository', section)
        self.assertIn('`manifest.json` lists every other file', section)
        self.assertIn('`sha256`', section)
        self.assertIn('Change a file and its manifest entry in the same commit', section)

    def test_listed_file_absent_fails_naming_it(self):
        result = run_check(edit=lambda s: (s / 'specs/README.md').unlink())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{SCAFFOLD}/specs/README.md: listed in manifest but absent', result.stderr)

    def test_unknown_placeholder_fails_naming_it(self):
        def edit(scaffold):
            path = scaffold / 'AGENTS.md.tmpl'
            path.write_text(path.read_text() + 'Owner: {{owner}}\n')
            rehash(scaffold, 'AGENTS.md.tmpl')
        result = run_check(edit=edit)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{SCAFFOLD}/AGENTS.md.tmpl: unknown placeholder {{{{owner}}}}', result.stderr)

    def test_unterminated_or_stray_placeholder_fails(self):
        rel = '.specify/memory/constitution.md.tmpl'
        for extra in ('Owner: {{org\n', 'Owner: {{{org}}}\n', 'Owner: org}}\n'):
            def edit(scaffold, extra=extra):
                path = scaffold / rel
                path.write_text(path.read_text() + extra)
                rehash(scaffold, rel)
            with self.subTest(extra=extra):
                result = run_check(edit=edit)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f'{SCAFFOLD}/{rel}: unterminated, nested or stray placeholder braces', result.stderr)

    def test_mode_must_match_tmpl_suffix(self):
        result = run_check(edit=lambda s: rehash(s, 'AGENTS.md.tmpl', mode='copy'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{SCAFFOLD}/AGENTS.md.tmpl: manifest entry needs sha256 and mode template', result.stderr)

    def test_invalid_or_missing_manifest_fails(self):
        for edit in (lambda s: (s / 'manifest.json').unlink(),
                     lambda s: (s / 'manifest.json').write_text('{"version": 2, "files": {}}')):
            with self.subTest():
                result = run_check(edit=edit)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f'{SCAFFOLD}/manifest.json: missing or invalid manifest', result.stderr)


if __name__ == '__main__':
    unittest.main()
