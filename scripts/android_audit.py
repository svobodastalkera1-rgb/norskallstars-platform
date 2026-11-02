"""Fail-closed OSV audit of locked Maven dependencies; prints identifiers, never data."""

import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def inventory(root=ROOT):
    packages = set()
    directory = root / "apps/android"
    required = (directory / "buildscript-gradle.lockfile", directory / "app/gradle.lockfile")
    if any(not path.is_file() for path in required):
        raise SystemExit("Missing Android app/buildscript dependency locks")
    lockfiles = sorted(directory.glob("**/*gradle.lockfile"))
    for lockfile in lockfiles:
        for line in lockfile.read_text().splitlines():
            if line.startswith("#") or "=" not in line:
                continue
            coordinate = line.split("=", 1)[0].split(":")
            if len(coordinate) == 3:
                packages.add(tuple(coordinate))
    build = (directory / "build.gradle.kts").read_text()
    agp = re.search(r'id\("com.android.application"\) version "([^"]+)"', build)
    if not agp:
        raise SystemExit("Missing AGP pin")
    packages.add(("com.android.tools.build", "gradle", agp[1]))
    packages.update(tuple(c.split(":")) for c in re.findall(r'classpath\("([^\"]+)"\)', build))
    if len(packages) < 10:
        raise SystemExit("Incomplete Android dependency lock inventory")
    return sorted(packages)


def main():
    failures = []
    coordinates = inventory()
    for start in range(0, len(coordinates), 100):
        batch = coordinates[start:start + 100]
        queries = [{"package": {"ecosystem": "Maven", "name": f"{group}:{artifact}"}, "version": version}
            for group, artifact, version in batch]
        request = urllib.request.Request("https://api.osv.dev/v1/querybatch",
            data=json.dumps({"queries": queries}).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read(2097152))
        entries = result.get("results")
        if not isinstance(entries, list) or len(entries) != len(batch):
            raise SystemExit("Incomplete OSV response; audit cannot pass")
        for coordinate, entry in zip(batch, entries, strict=True):
            if not isinstance(entry, dict) or "error" in entry:
                raise SystemExit("OSV query failed; audit cannot pass")
            for vulnerability in entry.get("vulns", []):
                failures.append(f"{':'.join(coordinate)}: {vulnerability['id']}")
    if failures:
        raise SystemExit("Android dependency vulnerabilities:\n" + "\n".join(failures))
    print(f"Android OSV audit passed: {len(coordinates)} locked Maven/toolchain coordinates; no known findings")


if __name__ == "__main__":
    main()
