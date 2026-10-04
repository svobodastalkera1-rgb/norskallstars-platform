import hashlib
import json
import shutil
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from tools.course_package import PackageError, build_package, validate_package

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures/course-package-v1"
STAMP = "2026-10-02T00:00:00Z"


class CoursePackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def clone_fixture(self, name="package"):
        dest = self.base / name
        shutil.copytree(FIXTURE, dest)
        return dest

    @staticmethod
    def reseal(root):
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        files = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and p.name != "manifest.json"}
        manifest["checksums"] = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
        manifest["components"] = sorted(name for name in files if name.endswith(".json"))
        manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")

    def test_checked_in_synthetic_fixture_is_valid(self):
        result = validate_package(FIXTURE)
        self.assertTrue(result["valid"], result["errors"])
        self.assertFalse(result["release_eligible"])

    def test_contract_schemas_use_stable_public_safe_identifiers(self):
        schema_files = sorted((ROOT / "specification/platform-contract/v1").glob("*.schema.json"))
        self.assertGreater(len(schema_files), 0)
        for path in schema_files:
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                schema["$id"],
                f"https://schemas.invalid/course-package/v1/{path.name}",
            )
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_invalid_schema_is_reported(self):
        root = self.clone_fixture()
        p = root / "course.json"
        course = json.loads(p.read_text())
        del course["title"]
        p.write_text(json.dumps(course))
        self.reseal(root)
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("title" in error for error in result["errors"]))

    def test_missing_asset_is_reported(self):
        root = self.clone_fixture()
        (root / "assets/images/fixture-garden.png").unlink()
        self.reseal(root)
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("missing asset" in error for error in result["errors"]))

    def test_broken_activity_reference_is_reported(self):
        root = self.clone_fixture()
        p = root / "lessons/fixture.lesson.signal.json"
        lesson = json.loads(p.read_text())
        lesson["activity_refs"] = ["missing.activity"]
        p.write_text(json.dumps(lesson))
        self.reseal(root)
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("broken activity" in error for error in result["errors"]))

    def test_duplicate_global_id_is_reported(self):
        root = self.clone_fixture()
        p = root / "activities/fixture.activity.describe.json"
        activity = json.loads(p.read_text())
        activity["activity_id"] = "fixture.activity.choose"
        p.write_text(json.dumps(activity))
        self.reseal(root)
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("duplicate global ID" in error for error in result["errors"]))

    def test_checksum_mismatch_is_reported(self):
        root = self.clone_fixture()
        p = root / "assets/images/fixture-garden.png"
        p.write_bytes(p.read_bytes() + b"x")
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("checksum mismatch" in error for error in result["errors"]))

    def test_malformed_manifest_is_reported(self):
        root = self.clone_fixture()
        (root / "manifest.json").write_text("{")
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("malformed" in error for error in result["errors"]))

    def test_unsupported_schema_major_is_reported(self):
        root = self.clone_fixture()
        p = root / "manifest.json"
        manifest = json.loads(p.read_text())
        manifest["schema_version"] = "2.0.0"
        p.write_text(json.dumps(manifest))
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unsupported schema" in error for error in result["errors"]))

    def test_unsupported_schema_minor_is_reported(self):
        root = self.clone_fixture()
        p = root / "manifest.json"
        manifest = json.loads(p.read_text())
        manifest["schema_version"] = "1.1.0"
        p.write_text(json.dumps(manifest))
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unsupported schema minor" in error for error in result["errors"]))

    def test_invalid_block_type_is_reported_by_schema(self):
        root = self.clone_fixture()
        p = root / "lessons/fixture.lesson.signal.json"
        lesson = json.loads(p.read_text())
        lesson["blocks"][0]["type"] = "platform_widget"
        p.write_text(json.dumps(lesson))
        self.reseal(root)
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("platform_widget" in error for error in result["errors"]))

    def test_release_flag_requires_human_and_asset_approval(self):
        root = self.clone_fixture()
        p = root / "manifest.json"
        manifest = json.loads(p.read_text())
        manifest["release_eligible"] = True
        manifest["build_kind"] = "release"
        p.write_text(json.dumps(manifest))
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("requires approved source" in error for error in result["errors"]))

    def test_zip_traversal_is_rejected_without_extraction(self):
        root = self.clone_fixture()
        zpath = self.base / "unsafe.zip"
        with zipfile.ZipFile(zpath, "w") as zf:
            for p in root.rglob("*"):
                if p.is_file(): zf.write(p, p.relative_to(root).as_posix())
            zf.writestr("../escape.json", "{}")
        result = validate_package(zpath)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unsafe package path" in error for error in result["errors"]))

    def test_unsafe_filename_is_rejected(self):
        root = self.clone_fixture()
        (root / "assets/images/fixture-garden.png").rename(root / "assets/images/fixture garden.png")
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unsupported package path" in error for error in result["errors"]))

    def test_duplicate_zip_entries_are_rejected(self):
        zpath = self.base / "duplicate.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(zpath, "w") as zf:
                zf.writestr("manifest.json", "{}")
                zf.writestr("manifest.json", "{}")
        result = validate_package(zpath)
        self.assertFalse(result["valid"])
        self.assertTrue(any("duplicate ZIP path" in error for error in result["errors"]))

    def test_zip_bomb_ratio_is_rejected(self):
        zpath = self.base / "ratio.zip"
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("assets/images/synthetic.png", b"0" * 500_000)
        result = validate_package(zpath)
        self.assertFalse(result["valid"])
        self.assertTrue(any("expansion ratio" in error for error in result["errors"]))

    def test_symlink_in_directory_is_rejected(self):
        root = self.clone_fixture()
        link = root / "assets/images/outside.png"
        link.symlink_to(root / "course.json")
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("symlink" in error for error in result["errors"]))

    def test_directory_limits_reject_oversized_file(self):
        root = self.clone_fixture()
        p = root / "assets/audio/oversized.wav"
        with p.open("wb") as f: f.truncate(32 * 1024 * 1024 + 1)
        result = validate_package(root)
        self.assertFalse(result["valid"])
        self.assertIn("exceeds", result["errors"][0])

    def test_builder_is_deterministic_with_fixed_timestamp_and_immutable(self):
        staging = self.base / "staging"
        staging.mkdir()
        for name in ("course.json", "chapters", "lessons", "activities", "assets"):
            src = FIXTURE / name
            dest = staging / name
            if src.is_dir(): shutil.copytree(src, dest)
            elif src.exists(): shutil.copy2(src, dest)
        one, two = self.base / "one", self.base / "two"
        r1 = build_package(staging, one, "fixture.course", "1.0.0", STAMP)
        r2 = build_package(staging, two, "fixture.course", "1.0.0", STAMP)
        self.assertTrue(r1["valid"] and r2["valid"])
        bytes_one = {p.relative_to(one).as_posix(): p.read_bytes() for p in one.rglob("*") if p.is_file()}
        bytes_two = {p.relative_to(two).as_posix(): p.read_bytes() for p in two.rglob("*") if p.is_file()}
        self.assertEqual(bytes_one, bytes_two)
        with self.assertRaisesRegex(PackageError, "immutable"):
            build_package(staging, one, "fixture.course", "1.0.0", STAMP)


if __name__ == "__main__":
    unittest.main()
