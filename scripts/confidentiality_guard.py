"""Reject confidential paths/content and verify public handoff index bytes.

This is an artifact/provenance guard, not a semantic privacy classifier.
"""
import argparse
import fnmatch
import hashlib
import json
from pathlib import PurePosixPath
import re
import sys

from repository import git, history_refs, index_files, tree_files

MANIFEST = 'contracts/course-package/handoff-manifest.json'
RESERVATIONS = {'contracts/course-package/README.md', MANIFEST,
                'fixtures/course-package/README.md'}
BLOCKED_DIRS = {'private', '.private', 'corpus', 'norwegian-course',
                'course-packages', 'private-packages', 'production-packages',
                'production-assets', 'generation-prompts', 'private-qa',
                'character-references', 'backups', 'dumps', 'exports',
                'recordings', 'logs', 'artifacts', 'reports'}
BLOCKED_NAMES = ('private-*', 'private_*', '.gitleaksignore', 'master*spec*', 'тз*.md', 'тз*.pdf', 'тз*.docx',
                 'credentials*.json', 'service-account*.json',
                 '*.pem', '*.key', '*.p12', '*.pfx', '*.jks', '*.keystore',
                 '*.dump', '*.bak', '*.log', '*.sqlite', '*.sqlite3', '*.db', '*.sarif')
ARTIFACT_SUFFIXES = {'.zip', '.tar', '.gz', '.tgz', '.7z', '.rar',
                     '.mp3', '.wav', '.ogg', '.m4a', '.mp4', '.webm'}
PRIVATE_HEADER = re.compile(rb'(?im)^\s*MASTER\s+TECHNICAL\s+SPECIFICATION\s*$')


def forbidden_path(name: str) -> bool:
    p = PurePosixPath(name)
    parts = [part.lower() for part in p.parts]
    if p.is_absolute() or '..' in parts or '\\' in name:
        return True
    if any(part in BLOCKED_DIRS or part.startswith(('private-', 'private_'))
           for part in parts[:-1]):
        return True
    lower = parts[-1]
    if lower.startswith('.env') and lower != '.env.example':
        return True
    return any(fnmatch.fnmatchcase(lower, pattern) for pattern in BLOCKED_NAMES)


def validate(files: dict[str, tuple[str, bytes]], label: str) -> list[str]:
    errors = []
    allowed = {}
    if MANIFEST in files:
        try:
            manifest = json.loads(files[MANIFEST][1])
            status = manifest['status']
            artifacts = manifest['artifacts']
            if status not in ('pending', 'received') or not isinstance(artifacts, list):
                raise ValueError('Invalid inventory status or artifacts')
            if status == 'pending' and (artifacts or manifest.get('approval') is not None):
                raise ValueError('Pending handoff must be empty and unapproved')
            if status == 'received' and (not isinstance(manifest.get('approval'), str)
                                       or not manifest['approval'].strip() or not artifacts):
                raise ValueError('Received handoff needs approval and artifacts')
            for artifact in artifacts:
                path, sha, role = artifact['path'], artifact['sha256'], artifact['role']
                if (not isinstance(path, str) or forbidden_path(path)
                        or path in RESERVATIONS or path in allowed
                        or not path.startswith(('contracts/course-package/', 'fixtures/course-package/'))
                        or not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha)
                        or not isinstance(role, str) or not role.strip()):
                    raise ValueError('Invalid/duplicate artifact record')
                allowed[path] = sha
                if path not in files or hashlib.sha256(files[path][1]).hexdigest() != sha:
                    raise ValueError('Approved artifact missing or checksum mismatch')
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            errors.append(f'{label}: invalid handoff inventory ({type(exc).__name__})')
    for name, (_, content) in files.items():
        if forbidden_path(name):
            errors.append(f'{label}: prohibited artifact path: {name}')
        if PRIVATE_HEADER.search(content):
            errors.append(f'{label}: private specification signature detected: {name}')
        is_handoff = name.startswith(('contracts/course-package/', 'fixtures/course-package/'))
        if is_handoff and name not in RESERVATIONS and name not in allowed:
            errors.append(f'{label}: handoff artifact lacks approval/checksum: {name}')
        if PurePosixPath(name).suffix.lower() in ARTIFACT_SUFFIXES and name not in allowed:
            errors.append(f'{label}: package/media artifact requires controlled approval: {name}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', help='Also check reachable history (never dangling objects)')
    args = parser.parse_args()
    try:
        errors = validate(index_files(), 'index')
        commits = []
        if args.history:
            commits = git('rev-list', *history_refs(args.history)).decode().splitlines()
            for commit in commits:
                errors.extend(validate(tree_files(commit), 'history ' + commit[:12]))
        if errors:
            print('\n'.join(errors), file=sys.stderr)
            return 1
        print(f'Confidentiality guard passed: index and {len(commits)} reachable commits. '
              'Human public-content review remains required.')
        return 0
    except (ValueError, UnicodeError) as exc:
        print(f'Confidentiality guard failed closed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
