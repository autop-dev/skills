"""Validate skill metadata and the profile example, and reject recognizable credential formats."""
from pathlib import Path
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
values = [profile]
while values:
    value = values.pop()
    if isinstance(value, dict):
        values.extend(value.values())
    elif isinstance(value, list):
        values.extend(value)
    elif isinstance(value, str) and (re.search(r'://[^/\s]*@', value) or '?' in value):
        errors.append(f'{rel}: URL with user info or query string')
for path in files:
    content = path.read_bytes().decode('utf-8', errors='replace')
    if any(re.search(pattern, content) for pattern in patterns):
        errors.append(f'{path.relative_to(root)}: token-looking content (value withheld)')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Checked {len(skills)} skills, {rel} and {len(files)} files: metadata, profile example and token scan passed')
