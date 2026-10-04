"""Platform limits and compatibility around immutable upstream Contract v1."""

import hashlib
import importlib.util
import json
import math
import tempfile
from dataclasses import dataclass
from importlib.resources import files as resource_files
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from norskallstars_backend.course_packages.archive import BoundaryError, read_archive


def contract_root() -> Path:
    bundled = Path(str(resource_files("norskallstars_backend") / "_contract"))
    if bundled.is_dir():
        return bundled
    # Editable checkout: no access to private upstream repository.
    return Path(__file__).resolve().parents[5] / "contracts/course-package/upstream"


def parse_json(raw: bytes) -> dict[str, Any]:
    if len(raw) > 2 << 20:
        raise BoundaryError("json_size")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise BoundaryError("json_duplicate_key")
            result[key] = value
        return result

    def constant(_: str) -> None:
        raise BoundaryError("json_constant")

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
        if not isinstance(value, dict):
            raise BoundaryError("json_object")
        stack = [(value, 0)]
        nodes = 0
        while stack:
            item, depth = stack.pop()
            nodes += 1
            if depth > 32 or nodes > 100_000:
                raise BoundaryError("json_complexity")
            if isinstance(item, float) and not math.isfinite(item):
                raise BoundaryError("json_number")
            if isinstance(item, str) and (len(item) > 16384 or "\x00" in item):
                raise BoundaryError("json_string")
            if isinstance(item, dict):
                stack.extend((k, depth + 1) for k in item)
                stack.extend((v, depth + 1) for v in item.values())
            elif isinstance(item, list):
                stack.extend((v, depth + 1) for v in item)
        return cast(dict[str, Any], value)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise BoundaryError("invalid_json") from exc


@dataclass(frozen=True)
class ValidatedPackage:
    files: dict[str, bytes]
    documents: dict[str, dict[str, Any]]
    manifest: dict[str, Any]
    digest: str


def schema_registry() -> tuple[dict[str, Any], Registry[Any]]:
    schemas = {
        p.name: parse_json(p.read_bytes())
        for p in (contract_root() / "specification/platform-contract/v1").glob("*.schema.json")
    }
    registry = Registry().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in schemas.values()
    )
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    return schemas, registry


def validate_archive(data: bytes) -> ValidatedPackage:
    payload = read_archive(data)
    try:
        documents = {n: parse_json(b) for n, b in payload.items() if n.endswith(".json")}
        manifest = documents["manifest.json"]
        schemas, registry = schema_registry()
        for name, document in documents.items():
            kind = (
                "manifest"
                if name == "manifest.json"
                else "course"
                if name == "course.json"
                else {"chapters": "chapter", "lessons": "lesson", "activities": "activity"}.get(
                    name.split("/", 1)[0]
                )
            )
            if kind is None:
                raise BoundaryError("component_path")
            validator = Draft202012Validator(
                schemas[kind + ".schema.json"], registry=registry, format_checker=FormatChecker()
            )
            if not validator.is_valid(document):
                raise BoundaryError("component_schema")
        if manifest["schema_version"].split(".")[:2] != ["1", "0"]:
            raise BoundaryError("unsupported_schema")
        if any(len(manifest[name]) > 64 for name in ("schema_version", "course_version")):
            raise BoundaryError("version_size")
        minimum = tuple(
            int(x) for x in manifest["compatibility"]["minimum_importer_version"].split(".")
        )
        if minimum > (1, 0, 0):
            raise BoundaryError("unsupported_importer")
        # Execute only checked-in, byte-inventoried generic reference implementation.
        spec = importlib.util.spec_from_file_location(
            "norskallstars_reference_validator", contract_root() / "tools/course_package.py"
        )
        if spec is None or spec.loader is None:
            raise BoundaryError("contract_unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix="norskallstars-validation-") as root:
            base = Path(root)
            for name, raw in payload.items():
                target = base / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            report = module.validate_package(base)
        if not report["valid"]:
            raise BoundaryError("contract_semantics")
        if manifest["release_eligible"] and (
            manifest.get("build_kind") != "release"
            or documents["course.json"]["metadata"].get("fixture")
        ):
            raise BoundaryError("synthetic_release")
        # Logical identity does not depend on ZIP member order/compression.
        h = hashlib.sha256()
        for name, raw in sorted(payload.items()):
            h.update(name.encode() + b"\0" + hashlib.sha256(raw).digest())
        return ValidatedPackage(payload, documents, manifest, h.hexdigest())
    except BoundaryError:
        raise
    except Exception as exc:
        # Parser/reference failure must fail closed without sensitive diagnostics.
        raise BoundaryError("invalid_package") from exc
