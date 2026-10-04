import asyncio
import hashlib
import io
import json
import stat
import warnings
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import func, select, text

from norskallstars_backend.course_packages.archive import BoundaryError, read_archive
from norskallstars_backend.course_packages.models import CourseRelease, ReleaseAsset, ReleaseEvent
from norskallstars_backend.course_packages.service import import_package, publish_release
from norskallstars_backend.course_packages.validation import contract_root, validate_archive
from norskallstars_backend.storage import LocalObjectStorage

FIXTURE = contract_root() / "fixtures/course-package-v1"
# Installed wheel contains schemas/validator only; fixture remains public-test-only.
if not FIXTURE.exists():
    FIXTURE = (
        Path(__file__).resolve().parents[3]
        / "contracts/course-package/upstream/fixtures/course-package-v1"
    )


def payload():
    return {
        p.relative_to(FIXTURE).as_posix(): p.read_bytes() for p in FIXTURE.rglob("*") if p.is_file()
    }


def zipped(files, compression=zipfile.ZIP_STORED):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)
    return output.getvalue()


def mutate(files, name, change):
    value = json.loads(files[name])
    change(value)
    files[name] = json.dumps(value).encode()
    if name != "manifest.json":
        manifest = json.loads(files["manifest.json"])
        manifest["checksums"][name] = hashlib.sha256(files[name]).hexdigest()
        files["manifest.json"] = json.dumps(manifest).encode()


def test_fixture_and_zip_repacking_identity():
    data = payload()
    first = validate_archive(zipped(data))
    second = validate_archive(zipped(dict(reversed(list(data.items()))), zipfile.ZIP_DEFLATED))
    assert first.digest == second.digest
    assert first.manifest["release_eligible"] is False


@pytest.mark.parametrize(
    "path",
    [
        "../escape",
        "/absolute",
        "a/../b",
        "a\\b",
        "a//b",
        "a/./b",
        "CON",
        "a:stream",
        "a\nsecret",
        "a/.hidden",
        "LPT1.txt",
    ],
)
def test_unsafe_archive_paths(path):
    with pytest.raises(BoundaryError):
        read_archive(zipped({path: b"x"}))


def test_duplicate_and_case_conflicting_paths():
    with pytest.raises(BoundaryError):
        read_archive(zipped({"a.json": b"x", "A.json": b"y"}))
    output = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(output, "w") as z:
            z.writestr("a.json", "x")
            z.writestr("a.json", "x")
    with pytest.raises(BoundaryError):
        read_archive(output.getvalue())


@pytest.mark.parametrize(
    "mode", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFSOCK, stat.S_IFDIR]
)
def test_special_archive_entries(mode):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        info = zipfile.ZipInfo("special")
        info.external_attr = (mode | 0o600) << 16
        z.writestr(info, b"target")
    with pytest.raises(BoundaryError):
        read_archive(stream.getvalue())


def test_archive_resource_limits():
    for raw, limits in [
        (zipped({"a": b"x", "b": b"x"}), {"entries": 1}),
        (zipped({"a": b"xx"}), {"file_limit": 1}),
        (zipped({"a": b"xx"}), {"total_limit": 1}),
        (zipped({"a": b"x"}), {"archive_limit": 1}),
        (zipped({"a": b"0" * 100_000}, zipfile.ZIP_DEFLATED), {}),
    ]:
        with pytest.raises(BoundaryError):
            read_archive(raw, **limits)


@pytest.mark.parametrize(
    "case",
    [
        "checksum",
        "unsupported",
        "importer",
        "duplicate_json",
        "missing",
        "undeclared",
        "media",
        "duplicate_id",
        "broken_reference",
        "schema",
        "oversize_string",
        "synthetic_release",
    ],
)
def test_invalid_packages(case):
    data = payload()
    if case == "checksum":
        data["course.json"] += b" "
    elif case == "unsupported":
        mutate(data, "manifest.json", lambda d: d.update(schema_version="1.1.0"))
    elif case == "importer":
        mutate(
            data,
            "manifest.json",
            lambda d: d["compatibility"].update(minimum_importer_version="9.0.0"),
        )
    elif case == "duplicate_json":
        data["course.json"] = b'{"course_id":"one","course_id":"two"}'
    elif case == "missing":
        del data["course.json"]
    elif case == "undeclared":
        data["assets/images/extra.png"] = b"not media"
    elif case == "media":
        data["assets/images/fixture-garden.png"] = b"broken"
    elif case == "duplicate_id":
        mutate(
            data,
            "activities/fixture.activity.describe.json",
            lambda d: d.update(activity_id="fixture.activity.choose"),
        )
    elif case == "broken_reference":
        mutate(
            data,
            "lessons/fixture.lesson.signal.json",
            lambda d: d.update(activity_refs=["missing.activity"]),
        )
    elif case == "schema":
        mutate(data, "course.json", lambda d: d.pop("title"))
    elif case == "oversize_string":
        mutate(data, "course.json", lambda d: d.update(title="x" * 16385))
    elif case == "synthetic_release":
        mutate(
            data, "manifest.json", lambda d: d.update(release_eligible=True, build_kind="release")
        )
        mutate(
            data,
            "course.json",
            lambda d: d["metadata"].update(
                source_status="approved",
                human_g2="passed",
                illustrations="all_approved",
                release_approval="simulated-test",
            ),
        )
    with pytest.raises(BoundaryError):
        validate_archive(zipped(data))


@pytest.fixture
async def release_db(database):
    async with database.transaction() as s:
        await s.execute(text("DELETE FROM release_events"))
        await s.execute(text("DELETE FROM release_assets"))
        await s.execute(text("DELETE FROM course_releases"))
    return database


@pytest.mark.integration
async def test_import_persistence_idempotency_and_conflict(release_db, tmp_path):
    storage = LocalObjectStorage(tmp_path, 32 << 20)
    data = payload()
    raw = zipped(data)
    rid = await import_package(
        release_db, storage, raw, actor="test-operator", approval="synthetic-test"
    )
    assert (
        await import_package(
            release_db,
            storage,
            zipped(data, zipfile.ZIP_DEFLATED),
            actor="test-operator",
            approval="synthetic-test",
        )
        == rid
    )
    async with release_db.transaction() as s:
        row = await s.get(CourseRelease, rid)
        assert row.state == "staged" and not row.release_eligible
        assert row.documents["course.json"]["course_id"] == row.course_id
        assets = (await s.scalars(select(ReleaseAsset))).all()
        for asset in assets:
            assert hashlib.sha256(await storage.get(asset.object_key)).hexdigest() == asset.checksum
        assert await s.scalar(select(func.count()).select_from(ReleaseEvent)) == 1
    mutate(data, "course.json", lambda d: d.update(title="A different synthetic title"))
    with pytest.raises(BoundaryError, match="version_conflict"):
        await import_package(
            release_db, storage, zipped(data), actor="test-operator", approval="synthetic-test"
        )
    with pytest.raises(BoundaryError, match="release_ineligible"):
        await publish_release(
            release_db, rid, actor="test-operator", approval="synthetic-test", storage=storage
        )


@pytest.mark.integration
async def test_failed_storage_rolls_back_all_course_state(release_db, tmp_path):
    class FailingStorage(LocalObjectStorage):
        calls = 0

        async def put(self, key, data):
            self.calls += 1
            if self.calls == 2:
                raise OSError("simulated failure")
            await super().put(key, data)

    with pytest.raises(OSError):
        await import_package(
            release_db,
            FailingStorage(tmp_path, 32 << 20),
            zipped(payload()),
            actor="test-operator",
            approval="synthetic-test",
        )
    async with release_db.transaction() as s:
        for model in (CourseRelease, ReleaseAsset, ReleaseEvent):
            assert await s.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.integration
async def test_concurrent_import_has_one_release_and_audit(release_db, tmp_path):
    storage = LocalObjectStorage(tmp_path, 32 << 20)
    data = zipped(payload())
    ids = await asyncio.gather(
        *(
            import_package(
                release_db, storage, data, actor="test-operator", approval="synthetic-test"
            )
            for _ in range(2)
        )
    )
    assert ids[0] == ids[1]
    async with release_db.transaction() as s:
        assert await s.scalar(select(func.count()).select_from(CourseRelease)) == 1
        assert await s.scalar(select(func.count()).select_from(ReleaseEvent)) == 1


@pytest.mark.integration
async def test_publication_is_explicit_audited_idempotent_and_checks_assets(release_db, tmp_path):
    # In-memory simulated approved package; no real content or release fixture persisted.
    data = payload()
    mutate(
        data,
        "course.json",
        lambda d: d["metadata"].update(
            fixture=False,
            source_status="approved",
            human_g2="passed",
            illustrations="all_approved",
            release_approval="simulated-test",
        ),
    )
    mutate(data, "manifest.json", lambda d: d.update(release_eligible=True, build_kind="release"))
    storage = LocalObjectStorage(tmp_path, 32 << 20)
    rid = await import_package(
        release_db, storage, zipped(data), actor="test-operator", approval="synthetic-test"
    )
    async with release_db.transaction() as s:
        asset = await s.scalar(select(ReleaseAsset))
    await storage.put(asset.object_key, b"tampered")
    with pytest.raises(BoundaryError, match="storage_integrity"):
        await publish_release(
            release_db, rid, actor="test-operator", approval="synthetic-test", storage=storage
        )
    async with release_db.transaction() as s:
        assert (await s.get(CourseRelease, rid)).state == "staged"
    await storage.put(asset.object_key, data[asset.metadata_json["path"]])
    await publish_release(
        release_db, rid, actor="test-operator", approval="synthetic-test", storage=storage
    )
    await publish_release(
        release_db, rid, actor="test-operator", approval="synthetic-test", storage=storage
    )
    async with release_db.transaction() as s:
        assert (await s.get(CourseRelease, rid)).state == "published"
        assert await s.scalar(select(func.count()).select_from(ReleaseEvent)) == 2


@pytest.mark.integration
async def test_invalid_package_and_audit_identity_leave_no_state(release_db, tmp_path):
    storage = LocalObjectStorage(tmp_path, 32 << 20)
    with pytest.raises(BoundaryError):
        await import_package(release_db, storage, b"bad", actor="test", approval="test")
    with pytest.raises(BoundaryError):
        await import_package(release_db, storage, zipped(payload()), actor="", approval="test")
    async with release_db.transaction() as s:
        assert await s.scalar(select(func.count()).select_from(CourseRelease)) == 0


def test_generic_structure_does_not_assume_fixture_identity_or_counts():
    data = payload()
    mutate(data, "course.json", lambda d: d.update(course_id="another.course", version="2.3.4"))
    mutate(
        data,
        "manifest.json",
        lambda d: d.update(
            course_id="another.course", course_version="2.3.4", content_version="revision-any"
        ),
    )
    chapter = json.loads(data["chapters/fixture.chapter.garden.json"])
    chapter["lesson_refs"].append("another.lesson")
    mutate(data, "chapters/fixture.chapter.garden.json", lambda d: d.update(chapter))
    lesson = json.loads(data["lessons/fixture.lesson.pattern.json"])
    lesson.update(
        lesson_id="another.lesson",
        order=3,
        prerequisites=[],
        activity_refs=[],
        blocks=[
            {"block_id": "another.block", "type": "text", "text": "Synthetic variant", "order": 1}
        ],
    )
    data["lessons/another.lesson.json"] = json.dumps(lesson).encode()
    manifest = json.loads(data["manifest.json"])
    manifest["checksums"] = {
        n: hashlib.sha256(raw).hexdigest() for n, raw in data.items() if n != "manifest.json"
    }
    manifest["components"] = sorted(n for n in data if n.endswith(".json") and n != "manifest.json")
    data["manifest.json"] = json.dumps(manifest).encode()
    parsed = validate_archive(zipped(data))
    assert parsed.manifest["course_id"] == "another.course"
    assert len([n for n in parsed.documents if n.startswith("lessons/")]) == 3


def test_parser_complexity_nonfinite_and_invalid_encoding():
    from norskallstars_backend.course_packages.validation import parse_json

    for raw in [
        b'{"v":NaN}',
        b'{"v":1e999}',
        b'{"v":Infinity}',
        b'{"v":"\xff"}',
        b'{"v":' + b"[" * 40 + b"0" + b"]" * 40 + b"}",
        b"[]",
        b"x" * (2 << 20 | 1),
    ]:
        with pytest.raises(BoundaryError):
            parse_json(raw)


def test_archive_compression_crc_and_invalid_container():
    for raw in [
        b"not a zip",
        zipped({"a": b"x"}, zipfile.ZIP_BZIP2),
        zipped({"a": b"payload"})[:-20],
    ]:
        with pytest.raises(BoundaryError):
            read_archive(raw)


def test_central_directory_lie_rejected_before_zip_allocation():
    import struct

    raw = bytearray(zipped({"a": b"x", "b": b"x"}))
    end = raw.rfind(b"PK\x05\x06")
    struct.pack_into("<HH", raw, end + 8, 1, 1)
    with pytest.raises(BoundaryError, match="entry_count"):
        read_archive(bytes(raw))
