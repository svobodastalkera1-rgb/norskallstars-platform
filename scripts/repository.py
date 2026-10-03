"""Shared Git readers: exact indexed bytes and reachable commit trees."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str, root: Path = ROOT) -> bytes:
    return subprocess.check_output(['git', '-C', str(root), *args])


def index_files(root: Path = ROOT) -> dict[str, tuple[str, bytes]]:
    files = {}
    for record in git('ls-files', '--stage', '-z', root=root).split(b'\0'):
        if not record:
            continue
        metadata, path = record.split(b'\t', 1)
        mode, oid, stage = metadata.decode().split()
        if stage != '0':
            raise ValueError('Resolve index conflicts before running checks')
        name = path.decode('utf-8')
        if mode not in ('100644', '100755'):
            raise ValueError(f'Unsupported tracked symlink/submodule: {name}')
        files[name] = (mode, git('cat-file', 'blob', oid, root=root))
    return files


def tree_files(commit: str, root: Path = ROOT) -> dict[str, tuple[str, bytes]]:
    files = {}
    for record in git('ls-tree', '-r', '-z', commit, root=root).split(b'\0'):
        if not record:
            continue
        metadata, path = record.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        name = path.decode('utf-8')
        if mode not in ('100644', '100755') or kind != 'blob':
            raise ValueError(f'Unsupported historical symlink/submodule: {name}')
        files[name] = (mode, git('cat-file', 'blob', oid, root=root))
    return files


def history_refs(requested: str) -> list[str]:
    if requested.startswith('-'):
        raise ValueError('History must be a revision, not a Git option')
    git('rev-parse', '--verify', requested + '^{commit}')
    refs = [requested, 'HEAD']
    # A PR checkout might not have a local main branch.
    for ref in ('refs/heads/main', 'refs/remotes/origin/main'):
        if subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--verify', ref],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            refs.append(ref)
    return list(dict.fromkeys(refs))
