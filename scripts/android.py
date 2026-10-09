"""Run pinned native checks without inherited provider/application secrets."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = ROOT / "apps/android"
DEVICE_RESULTS = ANDROID / "app/build/outputs/androidTest-results/connected/debug"
REQUIRED_DEVICE_TESTS = {
    ("com.norskallstars.platform.NativeSecurityTest", "vaultEncryptsAndTamperingFailsClosed"),
    ("com.norskallstars.platform.NativeSecurityTest", "microphoneIsBoundedPrivateAndStoppedWithLifecycle"),
    ("com.norskallstars.platform.PlatformJourneyTest", "accountPinnedLearningPlacementReplayAndErasure"),
}


def verify_device_results(directory):
    reports = list(directory.glob("TEST-*.xml"))
    if not reports:
        raise SystemExit("Native device gate failed: no fresh JUnit reports")
    for report in reports:
        raw = report.read_bytes()
        if len(raw) > 1048576 or b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
            raise SystemExit("Native device gate failed: invalid JUnit report")
        try:
            document = ET.fromstring(raw)
        except ET.ParseError:
            raise SystemExit("Native device gate failed: invalid JUnit report") from None
        cases = document.findall(".//testcase")
        actual = {(case.get("classname"), case.get("name")) for case in cases}
        if not REQUIRED_DEVICE_TESTS <= actual or len(actual) != len(cases):
            raise SystemExit("Native device gate failed: required journeys missing or duplicated")
        for node in document.iter():
            if node.tag in {"failure", "error", "skipped"} or any(
                node.get(field, "0") != "0" for field in ("failures", "errors", "skipped")
            ):
                raise SystemExit("Native device gate failed: failed, errored or skipped tests")
        print(f"Device report verified: {len(cases)} tests; no failures/errors/skips")


def environment(command=None):
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
    result = {key: value for key, value in os.environ.items() if key in allowed}
    if command == "device":
        # AGP 9.4.1 sends install options with a device suffix; engine 1.0.1
        # reads only the base key. Inject one constant into its forked JVM.
        # Ambient JAVA_TOOL_OPTIONS is deliberately never inherited.
        result["JAVA_TOOL_OPTIONS"] = "-Dandroid-test.apk-install-options=-r"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build", "device-build", "device", "wrapper"))
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
        "device-build": [":app:assembleDebug", ":app:assembleDebugAndroidTest", "-PdevelopmentOrigin=http://10.0.2.2:8001"],
        "device": [":app:connectedDebugAndroidTest", "-PdevelopmentOrigin=http://10.0.2.2:8001"],
    }
    if args.command == "device":
        # Gradle can return zero after APK installation fails. Old reports must
        # never authorize a new run, and every required native journey must run.
        if DEVICE_RESULTS.exists():
            shutil.rmtree(DEVICE_RESULTS)
    command = [str(ANDROID / "gradlew"), *jobs[args.command], "--no-daemon"]
    private = ROOT / ".cache/android-e2e/login.json"
    result = subprocess.run(command, cwd=ANDROID, env=environment(args.command), stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=1800)
    output = result.stdout.decode(errors="replace")
    if args.command == "device" and private.exists():
        for account in json.loads(private.read_text())["accounts"].values():
            for value in account.values():
                output = output.replace(value, "[synthetic credential redacted]")
    print(output, end="")
    if args.command == "device" and result.returncode == 0:
        verify_device_results(DEVICE_RESULTS)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
