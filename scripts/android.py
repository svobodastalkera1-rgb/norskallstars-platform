"""Run pinned native checks without inherited provider/application secrets."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "apps/android"


def environment():
    # Build tools need platform/toolchain configuration, not ambient provider
    # credentials. An allowlist also covers unknown future secret variable names.
    allowed = {
        "HOME", "USER", "LOGNAME", "PATH", "JAVA_HOME", "ANDROID_HOME",
        "ANDROID_SDK_ROOT", "ANDROID_USER_HOME", "ANDROID_AVD_HOME",
        "GRADLE_USER_HOME", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP",
        "SystemRoot", "SYSTEMROOT", "WINDIR", "PATHEXT", "APPDATA",
        "LOCALAPPDATA", "USERPROFILE", "SYSTEMDRIVE", "NUMBER_OF_PROCESSORS",
        "PROCESSOR_ARCHITECTURE", "TERM", "COLORTERM", "NO_COLOR", "CI",
    }
    return {key: value for key, value in os.environ.items() if key in allowed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build", "device", "wrapper"))
    args = parser.parse_args()
    if args.command == "wrapper":
        expected = urllib.request.urlopen(
            "https://services.gradle.org/distributions/gradle-9.6.0-wrapper.jar.sha256", timeout=30
        ).read(256).decode().strip()
        actual = hashlib.sha256((ANDROID / "gradle/wrapper/gradle-wrapper.jar").read_bytes()).hexdigest()
        pin = (ANDROID / "gradle/wrapper/wrapper.sha256").read_text().strip()
        if actual != expected or actual != pin:
            raise SystemExit("Gradle wrapper JAR checksum mismatch")
        print("Gradle wrapper JAR matches the upstream SHA-256")
        return
    jobs = {
        "check": [":app:testDebugUnitTest", ":app:lintDebug"],
        "build": [":app:assembleDebug", ":app:assembleRelease"],
        "device": [":app:connectedDebugAndroidTest", "-PdevelopmentOrigin=http://10.0.2.2:8001"],
    }
    command = [str(ANDROID / "gradlew"), *jobs[args.command], "--no-daemon"]
    private = ROOT / ".cache/android-e2e/login.json"
    result = subprocess.run(command, cwd=ANDROID, env=environment(), stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=1800)
    output = result.stdout.decode(errors="replace")
    if args.command == "device" and private.exists():
        for account in json.loads(private.read_text())["accounts"].values():
            for value in account.values():
                output = output.replace(value, "[synthetic credential redacted]")
    print(output, end="")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
