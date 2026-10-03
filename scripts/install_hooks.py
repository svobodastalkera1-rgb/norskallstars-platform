"""Install an opt-in local hook without overwriting unrelated Git configuration."""
from pathlib import Path
import os
import shlex
import subprocess

from repository import ROOT, git

MARKER = '# NorskAllstars confidentiality hook'


def main() -> None:
    setting = subprocess.run(['git', '-C', str(ROOT), 'config', '--get', 'core.hooksPath'],
                             stdout=subprocess.PIPE)
    if setting.returncode == 0:
        raise SystemExit('Existing core.hooksPath detected; integrate checks manually, do not overwrite it.')
    hook = Path(os.fsdecode(git('rev-parse', '--git-path', 'hooks/pre-commit')).strip())
    if not hook.is_absolute():
        hook = ROOT / hook
    if hook.exists() and MARKER not in hook.read_text():
        raise SystemExit('Existing pre-commit hook detected; integrate checks manually.')
    python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        raise SystemExit('Create .venv before installing hooks')
    quoted = shlex.quote(str(python))
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(f'#!/bin/sh\n{MARKER}\nset -eu\ncd {shlex.quote(str(ROOT))}\n'
                    f'{quoted} scripts/confidentiality_guard.py\n'
                    f'{quoted} scripts/scan_secrets.py\n')
    hook.chmod(0o755)
    print('Installed local pre-commit guard and secret scan (no remote changes)')


if __name__ == '__main__':
    main()
