"""Native tooling must not silently omit the buildscript security boundary."""

import os
import io
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
