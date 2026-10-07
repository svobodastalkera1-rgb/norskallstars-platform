"""Real Phase 0 checks: syntax, internal documentation links, ADR inventory and pins."""
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

from repository import ROOT, git

REQUIRED = ('AGENTS.md', 'PROJECT_STATE.md', 'ROADMAP.md', 'TASKS.md', 'README.md',
            'SECURITY.md', 'CHANGELOG.md', '.env.example', '.python-version',
            'docs/adr/README.md', 'docs/development.md', 'docs/ci.md',
            'docs/phase-0-review.md', 'contracts/course-package/handoff-manifest.json',
            '.github/workflows/ci.yml', '.github/workflows/application-gates.yml')


def main() -> int:
    errors = []
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            errors.append(f'Missing required bootstrap file: {name}')
    for path in (ROOT / 'scripts').glob('*.py'):
        try:
            compile(path.read_text(), str(path), 'exec')
        except SyntaxError as exc:
            errors.append(f'Invalid tooling syntax: {path.name}: {exc.msg}')
    # Inspect public repository candidates, not installed virtualenv/vendor READMEs.
    docs = [ROOT / raw.decode() for raw in git(
        'ls-files', '--cached', '--others', '--exclude-standard', '-z'
    ).split(b'\0') if raw and raw.endswith(b'.md')]
    for path in set(docs):
        if not path.exists():
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            target = target.strip('<>').split('#', 1)[0]
            if not target or '://' in target or target.startswith('mailto:'):
                continue
            resolved = (path.parent / unquote(target)).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                errors.append(f'Invalid local link in {path.relative_to(ROOT)}: {target}')
    for path in (ROOT / '.github' / 'workflows').glob('*.yml'):
        for action in re.findall(r'uses:\s*([^\s#]+)', path.read_text()):
            if not re.fullmatch(r'[\w./-]+@[0-9a-f]{40}', action):
                errors.append(f'Action must be full-SHA pinned: {path.name}: {action}')
    adrs = list((ROOT / 'docs' / 'adr').glob('[0-9][0-9][0-9][0-9]-*.md'))
    if len(adrs) < 7:
        errors.append('Key Phase 0 ADRs missing')
    try:
        json.loads((ROOT / 'contracts' / 'course-package' / 'handoff-manifest.json').read_text())
    except (ValueError, FileNotFoundError):
        errors.append('Handoff manifest is not valid JSON')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Bootstrap checks passed: tooling syntax, local links, {len(adrs)} ADRs, '
          'required files and Action pins. Android gate remains pending; Web has real Phase 5 checks.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
