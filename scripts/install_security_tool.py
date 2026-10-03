"""Install Gitleaks from a checksum-pinned upstream release, or an offline archive."""
import argparse
import hashlib
import io
from pathlib import Path
import platform
import tarfile
import urllib.request
import zipfile

from repository import ROOT

VERSION = '8.30.0'
ARCHIVES = {
    ('Linux', 'x86_64'): ('linux_x64.tar.gz', '79a3ab579b53f71efd634f3aaf7e04a0fa0cf206b7ed434638d1547a2470a66e'),
    ('Linux', 'aarch64'): ('linux_arm64.tar.gz', 'b4cbbb6ddf7d1b2a603088cd03a4e3f7ce48ee7fd449b51f7de6ee2906f5fa2f'),
    ('Darwin', 'x86_64'): ('darwin_x64.tar.gz', 'ca221d012d247080c2f6f61f4b7a83bffa2453806b0c195c795bbe9a8c775ed5'),
    ('Darwin', 'arm64'): ('darwin_arm64.tar.gz', 'b251ab2bcd4cd8ba9e56ff37698c033ebf38582b477d21ebd86586d927cf87e7'),
    ('Windows', 'AMD64'): ('windows_x64.zip', '54fe94f644b832dd08e8c3a5915efb3bfa862386d59fb27ca0792cb687a83573'),
}
TOOLS = ROOT / '.cache' / 'tools' / VERSION
BINARY = TOOLS / ('gitleaks.exe' if platform.system() == 'Windows' else 'gitleaks')


def verified_binary() -> Path:
    stamp = BINARY.with_suffix('.sha256')
    if not BINARY.is_file() or not stamp.is_file():
        raise ValueError('Run scripts/install_security_tool.py before secret checks')
    if hashlib.sha256(BINARY.read_bytes()).hexdigest() != stamp.read_text().strip():
        raise ValueError('Cached scanner checksum differs; reinstall the pinned tool')
    return BINARY


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Offline upstream archive; same checksum required')
    args = parser.parse_args()
    suffix, expected = ARCHIVES[(platform.system(), platform.machine())]
    name = f'gitleaks_{VERSION}_{suffix}'
    if args.archive:
        data = args.archive.read_bytes()
    else:
        url = f'https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}/{name}'
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Upstream archive checksum mismatch; installation aborted')
    # Extract exactly one regular executable; never unpack arbitrary archive paths.
    if suffix.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            executable = archive.read('gitleaks.exe')
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            member = archive.getmember('gitleaks')
            if not member.isfile():
                raise ValueError('Expected a regular executable member')
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError('Executable missing')
            executable = stream.read()
    TOOLS.mkdir(parents=True, exist_ok=True)
    BINARY.write_bytes(executable)
    BINARY.chmod(0o755)
    BINARY.with_suffix('.sha256').write_text(hashlib.sha256(executable).hexdigest() + '\n')
    print(f'Installed checksum-verified Gitleaks {VERSION} for {platform.system()}/{platform.machine()}')


if __name__ == '__main__':
    main()
