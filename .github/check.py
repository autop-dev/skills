"""Validate skill metadata, the profile example and the control-repository scaffold manifest, and reject
recognizable credential formats."""
from pathlib import Path
import hashlib
import json
import re
import yaml

root = Path(__file__).resolve().parents[1]
files = [p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts]
patterns = [
    r'\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})\b',
    r'\b(?:sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|AIza[A-Za-z0-9_-]{35})\b',
    r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b',
]
errors = []
skills = sorted((root / 'skills').glob('*/SKILL.md'))
if not skills:
    errors.append('no skills found')
for path in skills:
    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)', path.read_text(), re.S)
    try:
        meta = yaml.safe_load(match[1]) if match else None
        assert isinstance(meta, dict) and meta.get('name') == path.parent.name
        assert isinstance(meta.get('description'), str) and meta['description'].strip()
    except (AssertionError, yaml.YAMLError):
        errors.append(f'{path.relative_to(root)}: invalid name/description frontmatter')
PROFILE_KEYS = ('repository', 'updated', 'branches.default', 'branches.release', 'branches.develop',
                'branches.model', 'ci.system', 'deploy', 'environments', 'services', 'data_stores')
example = root / 'skills/autop-onboard-project/references/example-profile.md'
rel = example.relative_to(root)
match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)', example.read_text() if example.is_file() else '', re.S)
try:
    profile = yaml.safe_load(match[1]) if match else None
except (yaml.YAMLError, ValueError):
    profile = None
if not isinstance(profile, dict):
    errors.append(f'{rel}: invalid profile front matter')
    profile = {}
elif type(profile.get('profile')) is not int or profile['profile'] != 1:
    errors.append(f'{rel}: profile version must be 1')
for key in PROFILE_KEYS:
    node = profile
    for part in key.split('.'):
        node = node.get(part) if isinstance(node, dict) else None
    if node is None:
        errors.append(f'{rel}: missing {key}')
values, seen = [('', profile)], set()
while values:
    key, value = values.pop()
    if isinstance(value, (dict, list, tuple, set, frozenset)):
        if id(value) in seen:  # YAML aliases can share or nest a container in itself
            continue
        seen.add(id(value))
    if isinstance(value, dict):
        for k, v in value.items():
            path = f'{key}.{k}' if key else str(k)
            values.extend(((path, k), (path, v)))
    elif isinstance(value, (list, tuple, set, frozenset)):  # !!omap/!!pairs load as tuples, !!set as a set
        values.extend((f'{key}[{i}]', v) for i, v in enumerate(value))
    elif isinstance(value, str) and (re.search(r'[A-Za-z][A-Za-z0-9+.-]*://\S*@', value) or '?' in value):
        errors.append(f'{rel}: {key}: URL with user info or query string')
# The plane copies templates/control-repo/ into customers' control repositories after checking each sha256, so
# the manifest must list exactly the files present, with current hashes and only the documented placeholders.
SCAFFOLD = 'templates/control-repo'
PLACEHOLDERS = {'org', 'board_url', 'control_repo', 'repos', 'source_of_truth', 'invariants', 'review_focus', 'date'}
PLACEHOLDER = re.compile(r'\{\{([^{}\n]*)\}\}')
scaffold = root / SCAFFOLD
try:
    manifest = json.loads((scaffold / 'manifest.json').read_text())
    listed = manifest['files']
    assert manifest['version'] == 1 and manifest['source']['repo'] == 'autop-dev/control' and isinstance(listed, dict)
    assert re.fullmatch(r'[0-9a-f]{40}', manifest['source']['commit'])
except (OSError, ValueError, KeyError, TypeError, AssertionError):
    errors.append(f'{SCAFFOLD}/manifest.json: missing or invalid manifest (version 1, source, files)')
    listed = {}
present = {p.relative_to(scaffold).as_posix() for p in scaffold.rglob('*') if p.is_file() or p.is_symlink()}
present -= {'manifest.json'}
for item in sorted(present - listed.keys()):
    errors.append(f'{SCAFFOLD}/{item}: not listed in manifest')
for item, entry in sorted(listed.items()):
    path = scaffold / item
    if not isinstance(entry, dict) or entry.get('mode') != ('template' if item.endswith('.tmpl') else 'copy'):
        errors.append(f'{SCAFFOLD}/{item}: manifest entry needs sha256 and mode template for .tmpl files, else copy')
    elif item not in present or path.is_symlink():  # listed paths outside the tree are never read
        errors.append(f'{SCAFFOLD}/{item}: listed in manifest but absent or a symlink')
    elif hashlib.sha256(path.read_bytes()).hexdigest() != entry.get('sha256'):
        errors.append(f'{SCAFFOLD}/{item}: sha256 does not match manifest')
    elif entry['mode'] == 'template':
        text = path.read_text(errors='replace')
        names = PLACEHOLDER.findall(text)
        for name in sorted(set(names) - PLACEHOLDERS):
            errors.append(f'{SCAFFOLD}/{item}: unknown placeholder {{{{{name}}}}}')
        rest = PLACEHOLDER.sub('', text)
        if '{{' in rest or '}}' in rest or re.search(r'\{\{\{|\}\}\}', text):
            errors.append(f'{SCAFFOLD}/{item}: unterminated, nested or stray placeholder braces')
for path in files:
    content = path.read_bytes().decode('utf-8', errors='replace')
    if any(re.search(pattern, content) for pattern in patterns):
        errors.append(f'{path.relative_to(root)}: token-looking content (value withheld)')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Checked {len(skills)} skills, {rel}, {len(listed)} scaffold files and {len(files)} files: '
      'metadata, profile example, scaffold manifest and token scan passed')
