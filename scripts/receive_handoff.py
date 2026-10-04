"""Fail-closed local handoff inspection. Never imports or executes inbound code."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/backend/src"))
from norskallstars_backend.course_packages.archive import BoundaryError, read_archive

STAGING = ROOT / ".local/handoff"
SCHEMAS = {
    "manifest",
    "course",
    "chapter",
    "lesson",
    "activity",
    "asset",
    "content-block",
}
FIXED = {
    "README.md",
    "RECEIVING_INSTRUCTIONS.md",
    "HANDOFF_MANIFEST.json",
    "SHA256SUMS",
    "fixtures/README.md",
    "qa/automated/test_course_package.py",
    "specification/platform-contract/PUBLIC_HANDOFF.md",
    "specification/platform-contract/CHANGELOG.md",
    "specification/platform-contract/v1/README.md",
    "tools/course_package.py",
    "tools/build_course_package.py",
    "tools/validate_course_package.py",
}
FIXED |= {"specification/platform-contract/v1/" + x + ".schema.json" for x in SCHEMAS}


def json_object(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise BoundaryError("duplicate_json_key")
            result[key] = value
        return result

    try:
        value = json.loads(
            raw,
            object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(
                BoundaryError("json_constant")
            ),
        )
        if not isinstance(value, dict):
            raise BoundaryError("json_object")
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise BoundaryError("invalid_json") from exc


def inventory(files):
    if not FIXED.issubset(files):
        raise BoundaryError("handoff_structure")
    for name in files:
        if name not in FIXED and not (
            name.startswith("fixtures/course-package-v1/")
            and name.endswith(
                (".json", ".png", ".wav", ".jpg", ".jpeg", ".webp", ".mp3", ".ogg")
            )
        ):
            raise BoundaryError("unexpected_artifact")
    m = json_object(files["HANDOFF_MANIFEST.json"])
    if (
        set(m)
        != {
            "artifact_status",
            "contract_version",
            "file_count",
            "files",
            "format",
            "generated_at",
        }
        or m["format"] != "course-package-public-handoff-v1"
        or m["contract_version"] != "1.0.0"
        or m["artifact_status"] != "candidate"
        or not isinstance(m["files"], list)
        or m["file_count"] != len(m["files"])
    ):
        raise BoundaryError("handoff_manifest")
    declared = {}
    for item in m["files"]:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "size_bytes"}:
            raise BoundaryError("inventory_record")
        name = item["path"]
        if not isinstance(name, str) or name in declared or name not in files:
            raise BoundaryError("inventory_path")
        raw = files[name]
        if (
            type(item["size_bytes"]) is not int
            or len(raw) != item["size_bytes"]
            or hashlib.sha256(raw).hexdigest() != item["sha256"]
        ):
            raise BoundaryError("inventory_checksum")
        declared[name] = item["sha256"]
    if set(declared) != set(files) - {"HANDOFF_MANIFEST.json", "SHA256SUMS"}:
        raise BoundaryError("inventory_completeness")
    sums = {}
    for line in files["SHA256SUMS"].decode("ascii").splitlines():
        match = re.fullmatch(r"([a-f0-9]{64})  ([A-Za-z0-9_./-]+)", line)
        if not match or match[2] in sums:
            raise BoundaryError("checksum_index")
        sums[match[2]] = match[1]
    if set(sums) != set(files) - {"SHA256SUMS"} or any(
        hashlib.sha256(files[n]).hexdigest() != digest for n, digest in sums.items()
    ):
        raise BoundaryError("checksum_index_mismatch")
    manifest = json_object(files["fixtures/course-package-v1/manifest.json"])
    course = json_object(files["fixtures/course-package-v1/course.json"])
    if (
        manifest.get("release_eligible") is not False
        or course.get("metadata", {}).get("fixture") is not True
        or course.get("metadata", {}).get("public_safe") is not True
    ):
        raise BoundaryError("synthetic_boundary")
    return m


def confidentiality(files):
    patterns = [
        rb"(?i)BEGIN.{0,30}PRIVATE KEY",
        rb"gh[pousr]_[A-Za-z0-9]{20,}",
        rb"(?i)(/home/|/Users/|/workspaces/|[A-Z]:\\Users\\)",
        rb"(?i)(norwegian-course|source.to.pilot|github\.com/|private[-_ ]pilot)",
        rb'(?i)(https?://[^\s"<>]*@|(?:password|token|secret)\s*[:=]\s*["\'][A-Za-z0-9+/]{16,})',
    ]
    findings = []
    for name, raw in files.items():
        if name.endswith((".json", ".py", ".md")):
            raw.decode("utf-8")
            if any(re.search(pattern, raw) for pattern in patterns):
                findings.append(name)
    if findings:
        raise BoundaryError("confidentiality_finding")


def candidate():
    if any(p.is_symlink() for p in (ROOT / ".local", STAGING)) or not STAGING.is_dir():
        raise BoundaryError("staging_directory")
    candidates = list(STAGING.iterdir())
    if len(candidates) != 1 or candidates[0].suffix != ".zip":
        raise BoundaryError("exactly_one_zip_required")
    p = candidates[0]
    if not stat.S_ISREG(p.lstat().st_mode) or p.stat().st_size > 20 << 20:
        raise BoundaryError("staging_file")
    subprocess.run(
        ["git", "check-ignore", "-q", "--", str(p.relative_to(ROOT))],
        cwd=ROOT,
        check=True,
    )
    if subprocess.check_output(["git", "ls-files", "--", ".local"], cwd=ROOT).strip():
        raise BoundaryError("staging_tracked")
    # Search current refs only: never reflogs, dangling objects or removed private history.
    refs = (
        subprocess.check_output(
            [
                "git",
                "for-each-ref",
                "--format=%(refname)",
                "refs/heads",
                "refs/remotes",
                "refs/tags",
            ],
            cwd=ROOT,
        )
        .decode()
        .splitlines()
    )
    refs.append("HEAD")
    names = subprocess.check_output(
        ["git", "log", *refs, "--name-only", "--format=", "--", ".local"], cwd=ROOT
    )
    if names.strip():
        raise BoundaryError("staging_history")
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        raw = stream.read((20 << 20) + 1)
    sha = hashlib.sha256(raw).hexdigest()
    # Also compare inbound bytes to reachable blobs, even if renamed.
    oid = subprocess.check_output(
        ["git", "hash-object", "--stdin"], input=raw, cwd=ROOT
    ).strip()
    objects = subprocess.check_output(["git", "rev-list", "--objects", *refs], cwd=ROOT)
    if any(line.split(b" ", 1)[0] == oid for line in objects.splitlines()):
        raise BoundaryError("archive_in_reachable_history")
    return p, raw, sha


def contract_gate(files):
    # Only called after independent text/media/code review, never upon inspection alone.
    from install_security_tool import verified_binary

    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="receiving-", dir=cache) as folder:
        root = Path(folder)
        for name, raw in files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        subprocess.run(
            [
                str(verified_binary()),
                "dir",
                "--redact",
                "--no-banner",
                "--ignore-gitleaks-allow",
                "--config",
                str(ROOT / ".gitleaks.toml"),
                str(root),
            ],
            check=True,
            timeout=45,
            capture_output=True,
        )
        # Validate every schema/reference locally BEFORE running supplied reviewed tooling.
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource

        schemas = [
            json_object(raw)
            for name, raw in files.items()
            if name.endswith(".schema.json")
        ]
        if len(schemas) != 7:
            raise BoundaryError("schema_count")
        registry = Registry().with_resources(
            (v["$id"], Resource.from_contents(v)) for v in schemas
        )
        for schema in schemas:
            if schema["$schema"] != "https://json-schema.org/draft/2020-12/schema":
                raise BoundaryError("schema_dialect")
            Draft202012Validator.check_schema(schema)
            stack = [schema]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    if "$ref" in node:
                        registry.resolver(schema["$id"]).lookup(node["$ref"])
                    stack.extend(node.values())
                elif isinstance(node, list):
                    stack.extend(node)
        environment = {
            k: v for k, v in os.environ.items() if not k.startswith("NORSKALLSTARS_")
        }
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        root.chmod(0o755)
        image = subprocess.check_output(
            [
                "docker",
                "image",
                "inspect",
                "norskallstars-backend:local",
                "--format",
                "{{.Id}}",
            ],
            text=True,
        ).strip()
        sandbox = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            "64",
            "--memory",
            "512m",
            "--cpus",
            "1",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=128m",
            "--mount",
            "type=bind,source=" + str(root.resolve()) + ",target=/handoff,readonly",
            "--workdir",
            "/handoff",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            image,
        ]
        commands = [
            sandbox
            + [
                "python",
                "tools/validate_course_package.py",
                "fixtures/course-package-v1",
                "--json",
            ],
            sandbox
            + [
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "qa/automated",
                "-p",
                "test_course_package.py",
            ],
        ]
        for index, command in enumerate(commands):
            result = subprocess.run(
                command,
                cwd=root,
                env=environment,
                capture_output=True,
                timeout=45,
                check=True,
            )
            if index == 0:
                report = json_object(result.stdout)
                if (
                    report.get("valid") is not True
                    or report.get("release_eligible") is not False
                ):
                    raise BoundaryError("fixture_contract")
        print(
            "PASS: redacted secret scan, offline schemas/refs, synthetic validator and supplied tests"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-gate", action="store_true")
    parser.add_argument(
        "--reviewed-sha",
        help="Exact identity independently reviewed by operator; does not replace audit",
    )
    args = parser.parse_args()
    try:
        path, raw, sha = candidate()
        print(
            json.dumps({"filename": path.name, "size_bytes": len(raw), "sha256": sha})
        )
        files = read_archive(
            raw,
            entries=500,
            total_limit=20 << 20,
            file_limit=10 << 20,
            archive_limit=20 << 20,
        )
        inventory(files)
        confidentiality(files)
        print(
            "PASS: Git boundary, archive, inventory/checksums, heuristic confidentiality and synthetic flags"
        )
        if args.reviewed_sha != sha:
            raise BoundaryError("independent_review_required_for_this_sha")
        # Never trust inbound automation/metadata as approval. No copy/execution here.
        if args.contract_gate:
            contract_gate(files)
        else:
            raise BoundaryError("contract_gate_required_before_acceptance")
        current = json_object(
            (ROOT / "contracts/course-package/handoff-manifest.json").read_bytes()
        )
        known = {
            a["path"].removeprefix("contracts/course-package/upstream/"): a["sha256"]
            for a in current["artifacts"]
        }
        proposed = {
            n: hashlib.sha256(b).hexdigest()
            for n, b in files.items()
            if n
            not in {
                "README.md",
                "RECEIVING_INSTRUCTIONS.md",
                "HANDOFF_MANIFEST.json",
                "SHA256SUMS",
            }
        }
        changes = sorted(
            n for n in set(known) | set(proposed) if known.get(n) != proposed.get(n)
        )
        print(json.dumps({"changed_public_artifacts": changes}))
        print(
            "PASS: receiving complete for this SHA; destination/compatibility review required, no automatic copy"
        )
        return 0
    except (
        BoundaryError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        UnicodeError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(
            "STOP: receiving gate "
            + (str(exc) if isinstance(exc, BoundaryError) else type(exc).__name__),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
