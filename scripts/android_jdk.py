"""Download the exact, checksum-pinned CI JDK; never resolve a floating version."""

import argparse
import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request

FILENAME = "microsoft-jdk-17.0.20.1-linux-x64.tar.gz"
URL = f"https://aka.ms/download-jdk/{FILENAME}"
SHA256 = "d00e5b04e9726b63d915706c7049e5297c9f40239ce8a12fcc68b7267fa91ad2"
MAX_BYTES = 256 * 1024 * 1024


def download(destination, opener=urllib.request.urlopen):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        digest = hashlib.sha256()
        size = 0
        with opener(URL, timeout=60) as response, tempfile.NamedTemporaryFile(
            dir=destination.parent, delete=False
        ) as output:
            temporary = Path(output.name)
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise SystemExit("JDK archive exceeds download size limit")
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != SHA256:
            raise SystemExit("JDK archive checksum mismatch; installation refused")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print("Microsoft JDK 17.0.20.1 archive checksum verified")


def verify_installed():
    release = Path(os.environ["JAVA_HOME"]) / "release"
    fields = dict(line.split("=", 1) for line in release.read_text().splitlines() if "=" in line)
    if fields.get("JAVA_VERSION") != '"17.0.20.1"' or fields.get("IMPLEMENTOR") != '"Microsoft"':
        raise SystemExit("Installed JDK identity differs from the verified toolchain pin")
    print("Installed Microsoft JDK 17.0.20.1 identity verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify_installed()
    else:
        root = Path(os.environ.get("RUNNER_TEMP", ".cache/android-toolchain"))
        download(root / FILENAME)


if __name__ == "__main__":
    main()
