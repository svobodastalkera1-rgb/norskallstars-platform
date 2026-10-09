"""Native tooling must not silently omit the buildscript security boundary."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from android_audit import inventory
from android import environment


class AndroidAuditTests(unittest.TestCase):
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
