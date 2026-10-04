"""Safe, local Course Package v1 construction and validation helpers."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, RefResolver

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "specification/platform-contract/v1"
MAX_PACKAGE = 64 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_FILE = 32 * 1024 * 1024
MAX_ENTRIES = 2000
MAX_RATIO = 100
MIME_BY_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg"}
EXPECTED_TOP = {"manifest.json", "course.json", "chapters", "lessons", "activities", "assets"}
PATH_RE = re.compile(r"^(?:course\.json|chapters/[A-Za-z0-9._-]+\.json|lessons/[A-Za-z0-9._-]+\.json|activities/[A-Za-z0-9._-]+\.json|assets/(?:images/[A-Za-z0-9._-]+\.(?:png|jpg|jpeg|webp)|audio/[A-Za-z0-9._-]+\.(?:mp3|wav|ogg)))$")


class PackageError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relpath(raw: str) -> str:
    if not isinstance(raw, str) or "\\" in raw or "\x00" in raw or any(ord(c) < 32 for c in raw):
        raise PackageError(f"unsafe package path: {raw!r}")
    p = PurePosixPath(raw)
    if p.is_absolute() or not p.parts or any(part in ("", ".", "..") or part.startswith(".") for part in p.parts):
        raise PackageError(f"unsafe package path: {raw!r}")
    if not PATH_RE.fullmatch(raw):
        raise PackageError(f"unsupported package path: {raw!r}")
    return raw


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _schema_store() -> dict[str, Any]:
    store = {}
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        store[schema["$id"]] = schema
    return store


def schema_errors(name: str, value: Any) -> list[str]:
    schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    resolver = RefResolver.from_schema(schema, store=_schema_store())
    validator = Draft202012Validator(schema, resolver=resolver, format_checker=FormatChecker())
    return [f"{name} {list(e.absolute_path)}: {e.message}" for e in validator.iter_errors(value)]


def _read_directory(path: Path) -> dict[str, bytes]:
    if path.is_symlink() or not path.is_dir():
        raise PackageError("package directory must be a real directory, not a symlink")
    result: dict[str, bytes] = {}
    total = 0
    for base, dirs, files in os.walk(path, followlinks=False):
        base_path = Path(base)
        for name in list(dirs):
            p = base_path / name
            if p.is_symlink():
                raise PackageError(f"symlink is not allowed: {p}")
        for name in files:
            p = base_path / name
            rel = p.relative_to(path).as_posix()
            if rel == "manifest.json":
                if p.is_symlink():
                    raise PackageError("manifest symlink is not allowed")
            else:
                safe_relpath(rel)
            st = p.lstat()
            if stat.S_ISLNK(st.st_mode):
                raise PackageError(f"symlink is not allowed: {rel}")
            if not stat.S_ISREG(st.st_mode):
                raise PackageError(f"non-regular file is not allowed: {rel}")
            if st.st_size > MAX_FILE:
                raise PackageError(f"file exceeds {MAX_FILE} bytes: {rel}")
            total += st.st_size
            if total > MAX_TOTAL:
                raise PackageError("package exceeds total uncompressed size limit")
            result[rel] = p.read_bytes()
            if len(result) > MAX_ENTRIES:
                raise PackageError("package exceeds file count limit")
    return result


def _read_zip(path: Path) -> dict[str, bytes]:
    if path.stat().st_size > MAX_PACKAGE:
        raise PackageError("ZIP exceeds compressed package size limit")
    result: dict[str, bytes] = {}
    seen = set()
    total = 0
    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
            if len(infos) > MAX_ENTRIES:
                raise PackageError("ZIP exceeds entry count limit")
            for info in infos:
                raw = info.filename.rstrip("/")
                if info.is_dir():
                    if raw and ("\\" in raw or raw.startswith("/") or ".." in PurePosixPath(raw).parts):
                        raise PackageError(f"unsafe ZIP directory entry: {info.filename!r}")
                    continue
                rel = "manifest.json" if raw == "manifest.json" else safe_relpath(raw)
                if rel in seen:
                    raise PackageError(f"duplicate ZIP path: {rel}")
                seen.add(rel)
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise PackageError(f"ZIP symlink is not allowed: {rel}")
                if info.flag_bits & 0x1:
                    raise PackageError(f"encrypted ZIP entry is not allowed: {rel}")
                if info.file_size > MAX_FILE:
                    raise PackageError(f"ZIP entry exceeds {MAX_FILE} bytes: {rel}")
                if info.file_size and info.compress_size == 0:
                    raise PackageError(f"invalid ZIP compressed size: {rel}")
                if info.compress_size and info.file_size / info.compress_size > MAX_RATIO:
                    raise PackageError(f"ZIP expansion ratio exceeds {MAX_RATIO}:1: {rel}")
                total += info.file_size
                if total > MAX_TOTAL:
                    raise PackageError("ZIP exceeds total uncompressed size limit")
                result[rel] = zf.read(info)
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        raise PackageError(f"invalid ZIP package: {exc}") from exc
    return result


def _parse_json(files: dict[str, bytes], path: str) -> dict[str, Any]:
    try:
        value = json.loads(files[path].decode("utf-8"))
    except KeyError as exc:
        raise PackageError(f"missing required file: {path}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PackageError(f"malformed UTF-8 JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PackageError(f"top-level JSON value must be an object: {path}")
    return value


def _media_ok(asset: dict[str, Any], data: bytes) -> bool:
    mime = asset["mime_type"]
    if mime == "image/png": return data.startswith(b"\x89PNG\r\n\x1a\n")
    if mime == "image/jpeg": return data.startswith(b"\xff\xd8\xff")
    if mime == "image/webp": return len(data) > 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    if mime == "audio/wav": return len(data) > 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"
    if mime == "audio/ogg": return data.startswith(b"OggS")
    if mime == "audio/mpeg": return data.startswith(b"ID3") or (len(data) > 1 and data[0] == 0xff and data[1] & 0xe0 == 0xe0)
    return False


def _png_size(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        import struct
        return struct.unpack("!II", data[16:24])
    return None


def validate_package(path: Path) -> dict[str, Any]:
    path = Path(path)
    try:
        files = _read_zip(path) if path.is_file() and zipfile.is_zipfile(path) else _read_directory(path)
    except (PackageError, OSError) as exc:
        return {"valid": False, "errors": [str(exc)]}
    errors: list[str] = []
    unexpected_roots = {name.split("/", 1)[0] for name in files} - EXPECTED_TOP
    if unexpected_roots:
        errors.append(f"unexpected top-level paths: {sorted(unexpected_roots)}")
    try:
        manifest = _parse_json(files, "manifest.json")
        course = _parse_json(files, "course.json")
    except PackageError as exc:
        return {"valid": False, "errors": [str(exc)]}
    errors += schema_errors("manifest.schema.json", manifest)
    errors += schema_errors("course.schema.json", course)
    schema_version = manifest.get("schema_version")
    if not isinstance(schema_version, str) or schema_version.split(".", 1)[0] != "1":
        errors.append(f"unsupported schema version: {schema_version!r}")
    elif schema_version.split(".")[1:2] != ["0"]:
        errors.append(f"unsupported schema minor version: {schema_version!r}")
    if errors:
        return {"valid": False, "errors": errors, "course_id": course.get("course_id"), "course_version": course.get("version")}
    if manifest.get("course_id") != course.get("course_id") or manifest.get("course_version") != course.get("version"):
        errors.append("manifest and course identity/version do not match")
    if manifest.get("release_eligible"):
        metadata = course.get("metadata", {})
        if metadata.get("source_status") != "approved" or metadata.get("human_g2") != "passed" or metadata.get("illustrations") != "all_approved" or not metadata.get("release_approval"):
            errors.append("release_eligible requires approved source status, passed G2, all approved illustrations and a recorded release approval")
    content_paths = sorted(p for p in files if p != "manifest.json")
    checksums = manifest.get("checksums", {})
    if set(checksums) != set(content_paths):
        errors.append("manifest checksums do not enumerate exactly all non-manifest package files")
    for name in content_paths:
        if checksums.get(name) != sha256(files[name]):
            errors.append(f"checksum mismatch: {name}")
    component_paths = sorted(p for p in content_paths if p.endswith(".json"))
    if sorted(manifest.get("components", [])) != component_paths:
        errors.append("manifest components do not enumerate exactly all JSON package components")

    chapters = {}
    lessons = {}
    activities = {}
    assets = {}
    global_ids: dict[str, str] = {}
    def register(key: str, value: dict[str, Any], dest: dict[str, Any], schema_name: str) -> None:
        errors.extend(schema_errors(schema_name, value))
        oid = value.get(key)
        if isinstance(oid, str):
            if oid in global_ids: errors.append(f"duplicate global ID {oid!r}: {global_ids[oid]} and {schema_name}")
            global_ids[oid] = schema_name
            dest[oid] = value

    for name, data in files.items():
        if name.startswith("chapters/") and name.endswith(".json"):
            try:
                value = json.loads(data.decode("utf-8"))
                if not isinstance(value, dict): errors.append(f"top-level JSON value must be an object: {name}")
                else: register("chapter_id", value, chapters, "chapter.schema.json")
            except (UnicodeDecodeError, json.JSONDecodeError) as exc: errors.append(f"malformed JSON in {name}: {exc}")
        elif name.startswith("lessons/") and name.endswith(".json"):
            try:
                value = json.loads(data.decode("utf-8"))
                if not isinstance(value, dict): errors.append(f"top-level JSON value must be an object: {name}")
                else: register("lesson_id", value, lessons, "lesson.schema.json")
            except (UnicodeDecodeError, json.JSONDecodeError) as exc: errors.append(f"malformed JSON in {name}: {exc}")
        elif name.startswith("activities/") and name.endswith(".json"):
            try:
                value = json.loads(data.decode("utf-8"))
                if not isinstance(value, dict): errors.append(f"top-level JSON value must be an object: {name}")
                else: register("activity_id", value, activities, "activity.schema.json")
            except (UnicodeDecodeError, json.JSONDecodeError) as exc: errors.append(f"malformed JSON in {name}: {exc}")
    asset_paths: set[str] = set()
    for asset in course.get("assets", []):
        if not isinstance(asset, dict): continue
        register("asset_id", asset, assets, "asset.schema.json")
        apath = asset.get("path", "")
        if apath in asset_paths: errors.append(f"duplicate asset path: {apath}")
        asset_paths.add(apath)
        if apath not in files: errors.append(f"missing asset file: {apath}")
        else:
            raw = files[apath]
            if asset.get("checksum") != sha256(raw): errors.append(f"asset checksum mismatch: {apath}")
            if MIME_BY_EXT.get(Path(apath).suffix.lower()) != asset.get("mime_type") or not _media_ok(asset, raw): errors.append(f"asset MIME/signature mismatch: {apath}")
            if asset.get("mime_type") == "image/png" and asset.get("width") and asset.get("height"):
                if _png_size(raw) != (asset["width"], asset["height"]): errors.append(f"image dimensions do not match metadata: {apath}")
            if asset.get("mime_type") == "audio/wav" and asset.get("duration_ms"):
                import io, wave
                try:
                    with wave.open(io.BytesIO(raw), "rb") as wav:
                        actual_ms = round(wav.getnframes() * 1000 / wav.getframerate())
                    if actual_ms != asset["duration_ms"]: errors.append(f"audio duration does not match metadata: {apath}")
                except (wave.Error, EOFError): errors.append(f"invalid WAV media file: {apath}")
    if course.get("chapters", []) != sorted(chapters, key=lambda cid: chapters[cid].get("order", 0)): errors.append("course chapter references do not match ordered chapter components")
    concept_ids = [concept.get("concept_id") for concept in course.get("concepts", []) if isinstance(concept, dict)]
    if len(concept_ids) != len(set(concept_ids)): errors.append("duplicate concept ID")
    for chapter in chapters.values():
        refs = chapter.get("lesson_refs", [])
        if len(refs) != len(set(refs)): errors.append(f"duplicate lesson ref in chapter {chapter.get('chapter_id')}")
        ordered = [lessons.get(ref) for ref in refs]
        for ref, lesson in zip(refs, ordered):
            if lesson is None: errors.append(f"broken lesson reference {ref!r} in chapter {chapter.get('chapter_id')}")
            elif lesson.get("chapter_id") != chapter.get("chapter_id"): errors.append(f"lesson {ref} has wrong chapter_id")
        nums = [x.get("order") for x in ordered if x]
        if nums != sorted(nums) or len(nums) != len(set(nums)): errors.append(f"lesson order mismatch in chapter {chapter.get('chapter_id')}")
        if nums and nums != list(range(1, len(nums) + 1)): errors.append(f"lesson order is not contiguous in chapter {chapter.get('chapter_id')}")
        for prereq in chapter.get("prerequisites", []):
            if prereq not in chapters: errors.append(f"broken chapter prerequisite {prereq!r}")
        review = chapter.get("review")
        if isinstance(review, dict) and review.get("lesson_ref") and review["lesson_ref"] not in lessons:
            errors.append(f"broken chapter review reference {review['lesson_ref']!r}")
    chapter_graph = {cid: list(chapter.get("prerequisites", [])) for cid, chapter in chapters.items()}
    chapter_visiting: set[str] = set(); chapter_visited: set[str] = set()
    def visit_chapter(node: str) -> bool:
        if node in chapter_visiting: return False
        if node in chapter_visited: return True
        chapter_visiting.add(node)
        if any(child in chapter_graph and not visit_chapter(child) for child in chapter_graph[node]): return False
        chapter_visiting.remove(node); chapter_visited.add(node); return True
    for node in chapter_graph:
        if not visit_chapter(node): errors.append(f"chapter prerequisite cycle involving {node}"); break
    graph = {lid: list(lesson.get("prerequisites", [])) for lid, lesson in lessons.items()}
    for lid, lesson in lessons.items():
        if lesson.get("chapter_id") not in chapters: errors.append(f"lesson {lid} references missing chapter")
        for prereq in graph[lid]:
            if prereq not in lessons: errors.append(f"broken lesson prerequisite {prereq!r} in {lid}")
        for aid in lesson.get("activity_refs", []):
            if aid not in activities: errors.append(f"broken activity reference {aid!r} in {lid}")
        for block in lesson.get("blocks", []):
            if block.get("block_id") in global_ids: errors.append(f"duplicate global ID {block.get('block_id')!r}: content block and existing object")
            global_ids[block.get("block_id")] = f"content block in {lid}"
            if block.get("type") == "image" and block.get("asset_ref") not in assets: errors.append(f"broken asset ref {block.get('asset_ref')!r} in {lid}")
            if block.get("type") == "audio" and block.get("asset_ref") and block.get("asset_ref") not in assets: errors.append(f"broken audio asset ref {block.get('asset_ref')!r} in {lid}")
            if block.get("type") == "activity" and block.get("activity_ref") not in activities: errors.append(f"broken activity block ref {block.get('activity_ref')!r} in {lid}")
        block_orders = [block.get("order") for block in lesson.get("blocks", [])]
        if block_orders != list(range(1, len(block_orders) + 1)): errors.append(f"content block order is missing, duplicated or non-contiguous in {lid}")
        for concept in lesson.get("concepts", []):
            if concept.get("id") not in concept_ids: errors.append(f"broken concept reference {concept.get('id')!r} in {lid}")
    for activity in activities.values():
        for ref in activity.get("stimulus_refs", []):
            if ref not in global_ids and ref not in lessons and ref not in assets: errors.append(f"broken activity stimulus reference {ref!r} in {activity.get('activity_id')}")
    for asset in assets.values():
        for ref in asset.get("related_to", []):
            if ref not in global_ids and ref not in lessons and ref not in activities: errors.append(f"broken asset relation {ref!r} in {asset.get('asset_id')}")
    visiting: set[str] = set(); visited: set[str] = set()
    def visit(node: str) -> bool:
        if node in visiting: return False
        if node in visited: return True
        visiting.add(node)
        if any(child in graph and not visit(child) for child in graph[node]): return False
        visiting.remove(node); visited.add(node); return True
    for node in graph:
        if not visit(node): errors.append(f"prerequisite cycle involving {node}"); break
    for label, objects, directory, key in (("chapter", chapters, "chapters", "chapter_id"), ("lesson", lessons, "lessons", "lesson_id"), ("activity", activities, "activities", "activity_id")):
        for oid in objects:
            if f"{directory}/{oid}.json" not in files: errors.append(f"missing {label} component file for {oid}")
    return {"valid": not errors, "errors": errors, "course_id": course.get("course_id"), "course_version": course.get("version"), "files": len(files), "release_eligible": manifest.get("release_eligible", False)}


def build_package(staging: Path, output: Path, course_id: str, course_version: str, build_timestamp: str | None = None, release_eligible: bool = False) -> dict[str, Any]:
    staging, output = Path(staging), Path(output)
    if output.exists(): raise PackageError(f"output already exists (packages are immutable): {output}")
    files = _read_directory(staging)
    if "manifest.json" in files: raise PackageError("staging directory must not contain manifest.json")
    for required in ("course.json",):
        if required not in files: raise PackageError(f"staging directory is missing {required}")
    parsed_course = _parse_json(files, "course.json")
    if parsed_course.get("course_id") != course_id or parsed_course.get("version") != course_version:
        raise PackageError("course ID/version arguments do not match course.json")
    timestamp = build_timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    checksums = {name: sha256(data) for name, data in sorted(files.items())}
    components = sorted(name for name in files if name.endswith(".json"))
    manifest = {"schema_version": "1.0.0", "course_id": course_id, "course_version": course_version, "build_timestamp": timestamp, "content_version": course_version, "components": components, "checksums": checksums, "compatibility": {"minimum_importer_version": "1.0.0", "schema_major": 1}, "release_eligible": release_eligible, "build_kind": "release" if release_eligible else "internal_validation"}
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".course-package-", dir=output.parent))
    try:
        for name, data in files.items():
            target = tmp / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (tmp / "manifest.json").write_bytes(_json_bytes(manifest))
        report = validate_package(tmp)
        if not report["valid"]: raise PackageError("built package failed validation: " + "; ".join(report["errors"]))
        os.rename(tmp, output)
        return report
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
