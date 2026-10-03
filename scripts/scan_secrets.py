"""Scan exact index bytes and selected reachable history without publishing secret values."""
import argparse
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile

from install_security_tool import verified_binary
from repository import ROOT, history_refs, index_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', help='History revision; scans current main and HEAD as well')
    args = parser.parse_args()
    try:
        binary = verified_binary()
        files = index_files()
        with tempfile.TemporaryDirectory(prefix='norskallstars-index-scan-') as tmp:
            for name, (_, content) in files.items():
                path = PurePosixPath(name)
                if path.is_absolute() or '..' in path.parts or '\\' in name:
                    raise ValueError('Unsafe index path')
                target = Path(tmp) / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            result = subprocess.run([str(binary), 'dir', '--redact', '--no-banner', '--ignore-gitleaks-allow', '--config', str(ROOT / '.gitleaks.toml'), tmp])
            if result.returncode:
                return result.returncode
        if args.history:
            for ref in history_refs(args.history):
                result = subprocess.run([str(binary), 'git', '--redact', '--no-banner', '--ignore-gitleaks-allow', '--config', str(ROOT / '.gitleaks.toml'),
                                         '--log-opts=' + ref, str(ROOT)])
                if result.returncode:
                    return result.returncode
        print('Secret checks passed for exact index and requested reachable history; '
              'this does not prove arbitrary content is public-safe.')
        return 0
    except ValueError as exc:
        print(f'Secret check failed closed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
