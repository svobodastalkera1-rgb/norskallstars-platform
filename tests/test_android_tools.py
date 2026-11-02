"""Native tooling must not silently omit the buildscript security boundary."""

import os
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from android_audit import inventory
from android import environment
from android import REQUIRED_DEVICE_TESTS, verify_device_results, instrumentation_results
import android_jdk
import android


class AndroidAuditTests(unittest.TestCase):
    def test_device_options_are_constant_and_never_inherit_ambient_jvm_arguments(self):
        with patch.dict(os.environ, {
            "JAVA_TOOL_OPTIONS": "-Dsynthetic-secret=must-not-reach-tools",
            "GITHUB_TOKEN": "synthetic-marker",
        }, clear=True):
            self.assertEqual(environment(), {})
            self.assertEqual(environment("check"), {})
            self.assertEqual(environment("device"), {})

    @staticmethod
    def instrumentation_trace():
        output = []
        for cls, name in sorted(REQUIRED_DEVICE_TESTS):
            for code in (1, 0):
                output.extend((f"INSTRUMENTATION_STATUS: class={cls}",
                    f"INSTRUMENTATION_STATUS: test={name}",
                    f"INSTRUMENTATION_STATUS_CODE: {code}"))
        return "\n".join(output + ["INSTRUMENTATION_CODE: -1"])

    def test_instrumentation_requires_real_started_and_completed_journeys(self):
        trace = self.instrumentation_trace()
        self.assertEqual(instrumentation_results(trace), REQUIRED_DEVICE_TESTS)
        for bad in ("", "OK (3 tests)", trace.replace("INSTRUMENTATION_CODE: -1", ""),
                    trace.replace("INSTRUMENTATION_STATUS_CODE: 0", "INSTRUMENTATION_STATUS_CODE: -2", 1),
                    trace.replace("INSTRUMENTATION_STATUS_CODE: 0", "INSTRUMENTATION_STATUS_CODE: -3", 1),
                    trace.replace("INSTRUMENTATION_STATUS_CODE: 1", "INSTRUMENTATION_STATUS_CODE: 0", 1),
                    trace + "\nINSTRUMENTATION_ABORTED: synthetic crash",
                    trace + "\nINSTRUMENTATION_CODE: -1", trace + "\n" + trace):
            with self.subTest(trace=bad), self.assertRaises(SystemExit):
                instrumentation_results(bad)

    def test_instrumentation_rejects_incomplete_and_oversized_output(self):
        trace = self.instrumentation_trace()
        with self.assertRaises(SystemExit):
            instrumentation_results(trace.split("INSTRUMENTATION_STATUS_CODE: 0", 1)[1])
        with self.assertRaises(SystemExit):
            instrumentation_results("x" * 1048577)

    def test_diagnostics_preserve_success_and_classify_failures(self):
        trace = self.instrumentation_trace()
        diagnostics = {}
        self.assertEqual(instrumentation_results(trace, diagnostics), REQUIRED_DEVICE_TESTS)
        report = diagnostics["instrumentation"]
        self.assertEqual(report["classification"], "success")
        self.assertEqual(report["result_codes"], [-1])
        self.assertEqual([e["state"] for e in report["events"]], ["started", "completed"] * 3)
        for status, state in ((-1, "error"), (-2, "failed"), (-3, "skipped"), (-4, "assumption_failed")):
            with self.subTest(status=status):
                diagnostics = {}
                bad = trace.replace("INSTRUMENTATION_STATUS_CODE: 0", f"INSTRUMENTATION_STATUS_CODE: {status}", 1)
                with self.assertRaises(SystemExit):
                    instrumentation_results(bad, diagnostics)
                self.assertEqual(diagnostics["instrumentation"]["classification"], "instrumentation_" + state)
        for bad, classification in (
            ("INSTRUMENTATION_STATUS_CODE: 0", "missing_test_identity"),
            (trace.replace("INSTRUMENTATION_CODE: -1", ""), "incomplete_run"),
            (trace.replace("INSTRUMENTATION_STATUS_CODE: 1", "INSTRUMENTATION_STATUS_CODE: 0", 1), "incomplete_sequence"),
            ("INSTRUMENTATION_ABORTED: private", "instrumentation_aborted"),
            ("INSTRUMENTATION_STATUS: malformed", "malformed_event"),
        ):
            with self.subTest(classification=classification):
                diagnostics = {}
                with self.assertRaises(SystemExit):
                    instrumentation_results(bad, diagnostics)
                self.assertEqual(diagnostics["instrumentation"]["classification"], classification)

    def test_diagnostics_never_copy_private_runner_payloads(self):
        secret = "private-synthetic-token-answer-marker"
        trace = self.instrumentation_trace().replace("INSTRUMENTATION_STATUS_CODE: 0",
            "INSTRUMENTATION_STATUS: stack=java.lang.AssertionError: " + secret +
            "\n  at com.norskallstars.platform.NativeSecurityTest.synthetic(NativeSecurityTest.kt:24)" +
            "\nINSTRUMENTATION_STATUS: stream=" + secret + "\nINSTRUMENTATION_STATUS_CODE: -2", 1)
        diagnostics = {}
        with self.assertRaises(SystemExit):
            instrumentation_results(trace, diagnostics)
        encoded = json.dumps(diagnostics)
        self.assertNotIn(secret, encoded)
        self.assertNotIn("synthetic(", encoded)
        self.assertEqual(diagnostics["instrumentation"]["exception_types"], ["AssertionError"])
        self.assertEqual(diagnostics["instrumentation"]["test_frames"], [{"file": "NativeSecurityTest.kt", "line": 24}])
        for raw in (f"INSTRUMENTATION_STATUS: class={secret}\nINSTRUMENTATION_STATUS: test={secret}\nINSTRUMENTATION_STATUS_CODE: -2",
                    f"INSTRUMENTATION_STATUS_CODE: {secret}\nINSTRUMENTATION_CODE: {secret}"):
            report = android.instrumentation_diagnostics(raw)
            self.assertNotIn(secret, json.dumps(report))
        self.assertLess(len(json.dumps(android.instrumentation_diagnostics(trace * 500))), 32768)

    def test_failed_device_run_persists_only_sanitized_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk = root / "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
            apk.parent.mkdir(parents=True)
            apk.write_bytes(b"synthetic")
            artifact = root / "diagnostics/device.json"
            private = "private-device-input-token-marker"
            responses = [subprocess.CompletedProcess([], 0, b"List of devices attached\nemulator-5554\tdevice\n"),
                subprocess.CompletedProcess([], 0, b"Success"),
                subprocess.CompletedProcess([], 0, ("INSTRUMENTATION_STATUS_CODE: -2\n" + private).encode())]
            with patch.object(android, "ANDROID", root), patch.object(android, "DEVICE_RESULTS", root / "results"), \
                    patch.object(android, "DIAGNOSTICS", artifact), patch.object(android.subprocess, "run", side_effect=responses), \
                    patch("sys.stdout", new_callable=io.StringIO) as output:
                with self.assertRaisesRegex(SystemExit, "failed, errored or skipped instrumentation"):
                    android.run_device()
                report = json.loads(artifact.read_text())
                self.assertEqual(report["outcome"], "failed")
                self.assertEqual(report["processes"][-1], {"stage": "instrumentation", "outcome": "exited", "exit_code": 0})
                self.assertNotIn(private, output.getvalue() + artifact.read_text())
                self.assertFalse((root / "results").exists())
            for error, outcome in ((subprocess.TimeoutExpired(["adb"], 900, output=private), "timeout"),
                                   (OSError(private), "launch_error")):
                with patch.object(android, "DIAGNOSTICS", artifact), \
                        patch.object(android.subprocess, "run", side_effect=error), \
                        patch("sys.stdout", new_callable=io.StringIO) as output:
                    with self.assertRaises(SystemExit):
                        android.run_device()
                    self.assertEqual(json.loads(artifact.read_text())["processes"][0]["outcome"], outcome)
                    self.assertNotIn(private, output.getvalue() + artifact.read_text())

    def test_device_install_failure_cannot_pass_without_junit_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(SystemExit, "no fresh JUnit reports"):
                verify_device_results(Path(folder))

    def test_device_reports_require_all_journeys_and_no_skips_or_failures(self):
        cases = ''.join(f'<testcase classname="{cls}" name="{name}" />' for cls, name in REQUIRED_DEVICE_TESTS)
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "TEST-synthetic.xml"
            report.write_text(f'<testsuites tests="3">{cases}</testsuites>')
            verify_device_results(Path(folder))
            for bad in ('<testsuites tests="0" />',
                        f'<testsuites failures="1">{cases}</testsuites>',
                        f'<testsuites skipped="1">{cases}</testsuites>',
                        f'<testsuites>{cases}<skipped /></testsuites>',
                        f'<testsuites>{cases}{cases}</testsuites>'):
                with self.subTest(report=bad):
                    report.write_text(bad)
                    with self.assertRaises(SystemExit):
                        verify_device_results(Path(folder))

    def test_corrupt_jdk_is_not_installed_and_temporary_download_is_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / android_jdk.FILENAME
            with self.assertRaisesRegex(SystemExit, "checksum mismatch"):
                android_jdk.download(destination, lambda *args, **kwargs: io.BytesIO(b"corrupt archive"))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_oversized_jdk_is_not_installed(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(android_jdk, "MAX_BYTES", 4):
            destination = Path(folder) / android_jdk.FILENAME
            with self.assertRaisesRegex(SystemExit, "size limit"):
                android_jdk.download(destination, lambda *args, **kwargs: io.BytesIO(b"oversized"))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_build_environment_excludes_ambient_provider_credentials(self):
        with patch.dict(os.environ, {
            "JAVA_HOME": "/synthetic/jdk", "ANDROID_HOME": "/synthetic/sdk",
            "AWS_SECRET_ACCESS_KEY": "synthetic-marker", "FUTURE_PROVIDER_KEY": "synthetic-marker",
            "GITHUB_TOKEN": "synthetic-marker", "NORSKALLSTARS_IDENTITY_PEPPER": "synthetic-marker",
        }, clear=True):
            self.assertEqual(environment(), {"JAVA_HOME": "/synthetic/jdk", "ANDROID_HOME": "/synthetic/sdk"})

    def test_missing_buildscript_lock_cannot_pass_with_a_complete_app_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            app = root / "apps/android/app"
            app.mkdir(parents=True)
            (app / "gradle.lockfile").write_text("\n".join(
                f"synthetic:module{i}:1.0=runtimeClasspath" for i in range(20)
            ))
            with self.assertRaisesRegex(SystemExit, "buildscript"):
                inventory(root)

    def test_missing_app_lock_cannot_pass_with_buildscript_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / "apps/android"
            directory.mkdir(parents=True)
            (directory / "buildscript-gradle.lockfile").write_text("synthetic:module:1.0=classpath")
            with self.assertRaisesRegex(SystemExit, "app/buildscript"):
                inventory(root)

    def test_real_inventory_contains_runtime_tests_and_toolchain(self):
        coordinates = inventory()
        names = {f"{group}:{artifact}" for group, artifact, _ in coordinates}
        self.assertIn("com.squareup.okhttp3:okhttp", names)
        self.assertIn("com.squareup.okhttp3:mockwebserver3", names)
        self.assertIn("com.android.tools.build:gradle", names)
        self.assertIn("org.jetbrains.kotlin:kotlin-gradle-plugin", names)


if __name__ == "__main__":
    unittest.main()
