"""Run pinned native checks without inherited provider/application secrets."""

import argparse
import hashlib
import os
import re
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
    return result


def instrumentation_results(output):
    """Accept completed AndroidJUnitRunner events, never adb's exit status alone."""
    if len(output.encode()) > 1048576:
        raise SystemExit("Native device gate failed: oversized instrumentation output")
    bundle = {}
    started = None
    completed = set()
    final = []
    for line in output.splitlines():
        if line.startswith(("INSTRUMENTATION_FAILED:", "INSTRUMENTATION_ABORTED:")):
            raise SystemExit("Native device gate failed: instrumentation aborted")
        if line.startswith("INSTRUMENTATION_STATUS: "):
            key, separator, value = line[len("INSTRUMENTATION_STATUS: "):].partition("=")
            if not separator or key in bundle:
                raise SystemExit("Native device gate failed: malformed instrumentation event")
            bundle[key] = value
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            code = line[len("INSTRUMENTATION_STATUS_CODE: "):]
            case = (bundle.get("class"), bundle.get("test"))
            if code not in {"1", "0"} or not all(case):
                raise SystemExit("Native device gate failed: failed, errored or skipped instrumentation")
            if code == "1":
                if started is not None or case in completed:
                    raise SystemExit("Native device gate failed: duplicate or overlapping test")
                started = case
            else:
                if started != case:
                    raise SystemExit("Native device gate failed: incomplete test event sequence")
                completed.add(case)
                started = None
            bundle = {}
        elif line.startswith("INSTRUMENTATION_CODE: "):
            final.append(line[len("INSTRUMENTATION_CODE: "):])
    if final != ["-1"] or started is not None or bundle or not REQUIRED_DEVICE_TESTS <= completed:
        raise SystemExit("Native device gate failed: missing final result or required journeys")
    return completed


def run_device():
    # Use the documented AndroidJUnitRunner/adb interface. The pinned AGP's
    # engine can silently skip tests after reinstalling the preprovisioned app.
    if DEVICE_RESULTS.exists():
        shutil.rmtree(DEVICE_RESULTS)
    def adb(*args, timeout=120):
        result = subprocess.run(["adb", *args], env=environment("device"),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        if result.returncode:
            raise SystemExit("Native device gate failed: adb operation failed; private output omitted")
        return result.stdout.decode(errors="replace")
    devices = [line.split() for line in adb("devices").splitlines()[1:] if line.strip()]
    if len(devices) != 1 or len(devices[0]) != 2 or devices[0][1] != "device" or not re.fullmatch(r"emulator-\d+", devices[0][0]):
        raise SystemExit("Native device gate requires exactly one isolated online emulator")
    serial = devices[0][0]
    apk = ANDROID / "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
    if not apk.is_file():
        raise SystemExit("Native device gate failed: build the instrumentation APK first")
    adb("-s", serial, "install", "-r", str(apk))
    output = adb("-s", serial, "shell", "am", "instrument", "-w", "-r",
        "com.norskallstars.platform.dev.test/androidx.test.runner.AndroidJUnitRunner", timeout=900)
    completed = instrumentation_results(output)
    # Persist only case identities/results, never raw stacks, responses or credentials.
    suite = ET.Element("testsuite", tests=str(len(completed)), failures="0", errors="0", skipped="0")
    for cls, name in sorted(completed):
        ET.SubElement(suite, "testcase", classname=cls, name=name)
    DEVICE_RESULTS.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(suite).write(DEVICE_RESULTS / "TEST-instrumentation.xml", encoding="utf-8")
    verify_device_results(DEVICE_RESULTS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build", "device-build", "device", "wrapper"))
    args = parser.parse_args()
    if args.command == "device":
        run_device()
        return
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
    }
    command = [str(ANDROID / "gradlew"), *jobs[args.command], "--no-daemon"]
    result = subprocess.run(command, cwd=ANDROID, env=environment(args.command), stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=1800)
    output = result.stdout.decode(errors="replace")
    print(output, end="")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
