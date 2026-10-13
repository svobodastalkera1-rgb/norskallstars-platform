"""Regression gates for normative public-document identity; no private inputs."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import experience_bible as bible


class ExperienceBibleTests(unittest.TestCase):
    def setUp(self):
        self.document = (bible.ROOT / bible.DOCUMENT).read_bytes()
        self.record = (bible.ROOT / bible.RECORD).read_bytes()

    def record_for(self, data, **changes):
        metadata = json.loads(self.record)
        metadata.update(sha256=hashlib.sha256(data).hexdigest(), **changes)
        return json.dumps(metadata).encode()

    def test_canonical_public_document_is_complete_and_versioned(self):
        self.assertEqual(bible.validate(self.document, self.record)['version'], '1.0')

    def test_changed_or_crlf_public_copy_is_rejected_without_import(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / 'public-export.md'
            record = Path(directory) / 'version-record'; record.write_bytes(self.record)
            candidate.write_bytes(self.document)
            bible.check(candidate=candidate, candidate_record=record)
            for data in (self.document + b'altered\n', self.document.replace(b'\n', b'\r\n')):
                candidate.write_bytes(data)
                with self.assertRaises(ValueError):
                    bible.check(candidate=candidate, candidate_record=record)
            self.assertEqual((bible.ROOT / bible.DOCUMENT).read_bytes(), self.document)

    def test_invalid_duplicate_or_redirecting_metadata_fails_closed(self):
        for record in (b'{}', b'[]', b'{"version":"1.0","version":"1.1"}',
                       self.record_for(self.document, document='../../other.md'),
                       self.record_for(self.document, version='2.0'),
                       self.record_for(self.document, extra='unsupported')):
            with self.subTest(record_type=len(record)), self.assertRaises(ValueError):
                bible.validate(self.document, record)

    def test_byte_corruption_header_and_section_drift_are_rejected(self):
        with self.assertRaises(ValueError):
            bible.validate(self.document + b'x', self.record)
        for data in (self.document.replace(b'Version: 1.0', b'Version: 1.1'),
                     self.document.replace(b'## 24. ', b'## 23. '),
                     self.document.replace(b'\n', b'\r\n'),
                     self.document + b'\xff'):
            with self.assertRaises(ValueError):
                bible.validate(data, self.record_for(data))

    def test_symlink_oversized_and_non_file_exports_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'public.md'; source.write_bytes(self.document)
            link = root / 'link.md'; link.symlink_to(source)
            large = root / 'large.md'; large.write_bytes(b'x' * (bible.MAX_DOCUMENT + 1))
            record = root / 'version-record'; record.write_bytes(self.record)
            for candidate in (link, large, root, root / 'missing.md'):
                with self.assertRaises(ValueError):
                    bible.check(candidate=candidate, candidate_record=record)

    def test_incomplete_export_or_mismatched_record_is_not_synchronization(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / 'public.md'; candidate.write_bytes(self.document)
            record = Path(directory) / 'record'; record.write_bytes(b'{}')
            for arguments in ({'candidate': candidate}, {'candidate_record': record},
                              {'candidate': candidate, 'candidate_record': record}):
                with self.assertRaises(ValueError):
                    bible.check(**arguments)

    def test_working_copy_cannot_mask_valid_but_different_staged_version(self):
        staged = self.document.replace(b'v1.0\n', b'v1.1\n').replace(b'Version: 1.0', b'Version: 1.1')
        record = self.record_for(staged, version='1.1')
        with patch.object(bible, 'indexed', side_effect=[staged, record]):
            with self.assertRaises(ValueError):
                bible.check(index=True)


if __name__ == '__main__':
    unittest.main()
