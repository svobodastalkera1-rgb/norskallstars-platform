"""Adversarial coverage for public artifact boundaries, not product placeholder tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from confidentiality_guard import MANIFEST, forbidden_path, validate
from repository import index_files


def files(manifest=None, **extra):
    value = {'status': 'pending', 'approval': None, 'artifacts': []} if manifest is None else manifest
    return {MANIFEST: ('100644', json.dumps(value).encode()),
            **{name: ('100644', content) for name, content in extra.items()}}


class BoundaryTests(unittest.TestCase):
    def test_confidential_paths_even_when_force_added(self):
        for path in ['docs/Master Technical Specification.md', 'ТЗ №2.md',
                     'private-pilot.json', 'private/fixture.json',
                     'norwegian-course/schema.json', 'backups/data.sql',
                     '.env.production', 'apps/backend/.env', 'signing/release.jks',
                     'exports/users.csv', 'production-assets/image.png', '.cache/prod.env',
                     '.venv/credentials.json', 'mail/verification.eml', 'learning-policies/answers.json', 'course.learning-policy.json']:
            with self.subTest(path=path):
                self.assertTrue(forbidden_path(path))
                self.assertTrue(validate(files(**{path: b'content'}), 'test'))

    def test_safe_env_template_and_engineering_docs(self):
        self.assertFalse(validate(files(**{'.env.example': b'ENV=local\n',
                                          'docs/security/confidentiality.md': b'Public instructions'}), 'test'))

    def test_renamed_specification_header(self):
        marker = b'MASTER ' + b'TECHNICAL ' + b'SPECIFICATION\n'
        self.assertTrue(validate(files(**{'misc/notes.md': marker}), 'test'))

    def test_pending_handoff_does_not_authorize_artifacts(self):
        self.assertTrue(validate(files(**{'contracts/course-package/schema.json': b'{}'}), 'test'))
        self.assertTrue(validate(files(**{'fixtures/course-package/synthetic.json': b'{}'}), 'test'))

    def approved(self):
        path = 'fixtures/course-package/synthetic.json'
        content = b'{"synthetic-test": true}'
        manifest = {'status': 'received', 'approval': 'test-only approval', 'artifacts': [
            {'path': path, 'sha256': hashlib.sha256(content).hexdigest(), 'role': 'synthetic fixture'}]}
        return path, content, manifest

    def test_exact_approved_artifact(self):
        path, content, manifest = self.approved()
        self.assertFalse(validate(files(manifest, **{path: content}), 'test'))

    def test_approved_artifact_tamper_and_missing(self):
        path, _, manifest = self.approved()
        self.assertTrue(validate(files(manifest, **{path: b'changed'}), 'test'))
        self.assertTrue(validate(files(manifest), 'test'))

    def test_inventory_cannot_approve_private_or_external_path(self):
        for path in ['private/pilot.json', '../outside.json', 'apps/backend/data.json']:
            _, content, manifest = self.approved()
            manifest['artifacts'][0]['path'] = path
            self.assertTrue(validate(files(manifest, **{path: content}), 'test'))

    def test_invalid_and_duplicate_inventory(self):
        path, content, manifest = self.approved()
        manifest['artifacts'].append(dict(manifest['artifacts'][0]))
        self.assertTrue(validate(files(manifest, **{path: content}), 'test'))
        self.assertTrue(validate(files({'status': 'received', 'approval': None, 'artifacts': []}), 'test'))

    def test_unapproved_archive_and_media(self):
        for path in ['misc/course.zip', 'misc/recording.wav']:
            self.assertTrue(validate(files(**{path: b'bytes'}), 'test'))

    def test_scanner_suppression_file_is_forbidden(self):
        self.assertTrue(forbidden_path('.gitleaksignore'))


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)

    def test_index_does_not_trust_clean_working_copy(self):
        path = self.root / 'innocent.md'
        marker = b'MASTER ' + b'TECHNICAL ' + b'SPECIFICATION\n'
        path.write_bytes(marker)
        subprocess.run(['git', '-C', str(self.root), 'add', 'innocent.md'], check=True)
        path.write_bytes(b'clean working file')
        indexed = index_files(self.root)
        self.assertEqual(indexed['innocent.md'][1], marker)
        self.assertTrue(validate(indexed, 'test'))

    def test_private_mail_is_rejected_from_real_index(self):
        (self.root / '.gitignore').write_text('*.eml\n')
        (self.root / 'verification.eml').write_bytes(b'Synthetic private mail')
        subprocess.run(['git', '-C', str(self.root), 'add', '-f', 'verification.eml'], check=True)
        self.assertTrue(validate(index_files(self.root), 'test'))

    def test_runtime_learning_policy_rejected_even_when_force_indexed(self):
        (self.root / '.gitignore').write_text('*.learning-policy.json\n')
        (self.root / 'course.learning-policy.json').write_bytes(b'{"synthetic": true}')
        subprocess.run(['git', '-C', str(self.root), 'add', '-f', 'course.learning-policy.json'], check=True)
        self.assertTrue(validate(index_files(self.root), 'test'))

    def test_symlink_rejected_before_materialization(self):
        # Force an index symlink without depending on platform symlink privileges.
        oid = subprocess.check_output(['git', '-C', str(self.root), 'hash-object', '-w', '--stdin'],
                                      input=b'../outside').decode().strip()
        subprocess.run(['git', '-C', str(self.root), 'update-index', '--add',
                        '--cacheinfo', f'120000,{oid},link'], check=True)
        with self.assertRaises(ValueError):
            index_files(self.root)


if __name__ == '__main__':
    unittest.main()


class LocalStagingBoundaryTests(unittest.TestCase):
    def test_force_added_local_staging_is_forbidden(self):
        from confidentiality_guard import forbidden_path
        self.assertTrue(forbidden_path('.local/handoff/candidate.zip'))
