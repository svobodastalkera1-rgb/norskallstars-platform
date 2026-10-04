"""Receiver regression tests use constructed synthetic bytes, never inbound archives."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from receive_handoff import (
    BoundaryError,
    FIXED,
    confidentiality,
    inventory,
    json_object,
)


def bundle():
    files = {
        n: b"public synthetic"
        for n in FIXED
        if n not in {"HANDOFF_MANIFEST.json", "SHA256SUMS"}
    }
    files["fixtures/course-package-v1/manifest.json"] = b'{"release_eligible":false}'
    files["fixtures/course-package-v1/course.json"] = (
        b'{"metadata":{"fixture":true,"public_safe":true}}'
    )
    records = [
        {"path": n, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}
        for n, raw in files.items()
    ]
    files["HANDOFF_MANIFEST.json"] = json.dumps(
        {
            "artifact_status": "candidate",
            "contract_version": "1.0.0",
            "file_count": len(records),
            "files": records,
            "format": "course-package-public-handoff-v1",
            "generated_at": "2026-10-04T00:00:00Z",
        }
    ).encode()
    seal(files)
    return files


def seal(files):
    files["SHA256SUMS"] = "".join(
        hashlib.sha256(raw).hexdigest() + "  " + n + "\n"
        for n, raw in files.items()
        if n != "SHA256SUMS"
    ).encode()


class ReceivingTests(unittest.TestCase):
    def test_inventory_complete(self):
        inventory(bundle())

    def test_undeclared(self):
        f = bundle()
        f["fixtures/course-package-v1/extra.json"] = b"{}"
        seal(f)
        with self.assertRaises(BoundaryError):
            inventory(f)

    def test_missing(self):
        f = bundle()
        del f["tools/course_package.py"]
        seal(f)
        with self.assertRaises(BoundaryError):
            inventory(f)

    def test_checksum_tampering(self):
        f = bundle()
        f["README.md"] = b"tampered"
        seal(f)
        with self.assertRaises(BoundaryError):
            inventory(f)

    def test_duplicate_inventory(self):
        f = bundle()
        m = json.loads(f["HANDOFF_MANIFEST.json"])
        m["files"].append(m["files"][0])
        m["file_count"] += 1
        f["HANDOFF_MANIFEST.json"] = json.dumps(m).encode()
        seal(f)
        with self.assertRaises(BoundaryError):
            inventory(f)

    def test_checksum_index_tampering(self):
        f = bundle()
        f["SHA256SUMS"] += f["SHA256SUMS"].splitlines()[0] + b"\n"
        with self.assertRaises(BoundaryError):
            inventory(f)

    def test_synthetic_release_flag(self):
        f = bundle()
        f["fixtures/course-package-v1/manifest.json"] = b'{"release_eligible":true}'
        with self.assertRaises(BoundaryError):
            inventory(f)

    def test_duplicates_and_constants_in_json(self):
        for raw in [b'{"a":1,"a":2}', b'{"a":NaN}']:
            with self.assertRaises(BoundaryError):
                json_object(raw)

    def test_unresolved_confidentiality(self):
        with self.assertRaises(BoundaryError):
            confidentiality({"unknown.md": b"/home/internal/data"})

    def test_public_synthetic(self):
        confidentiality({"fixture.json": b'{"synthetic":true}'})
