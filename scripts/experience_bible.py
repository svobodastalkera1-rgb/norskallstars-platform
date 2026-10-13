"""Verify the Owner-approved public Bible and an optional explicitly supplied public copy.

No repository discovery, network access, content import or automatic checksum update.
The version record is documentation provenance, not a Course Package schema.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from repository import ROOT, git

DOCUMENT = 'docs/product-world/world-experience-bible-v1.md'
RECORD = 'docs/product-world/EXPERIENCE_BIBLE_VERSION'
MAX_DOCUMENT = 128 * 1024
MAX_RECORD = 4096


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate version-record key')
        result[key] = value
    return result


def validate(document: bytes, record: bytes) -> dict:
    if not document or len(document) > MAX_DOCUMENT or len(record) > MAX_RECORD:
        raise ValueError('Bible/version record size rejected')
    try:
        metadata = json.loads(record.decode('utf-8'), object_pairs_hook=unique_object)
        text = document.decode('utf-8')
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Invalid UTF-8 or version record') from exc
    if not isinstance(metadata, dict) or set(metadata) != {'version', 'document', 'sha256'}:
        raise ValueError('Invalid version-record fields')
    version, digest = metadata['version'], metadata['sha256']
    if not isinstance(version, str) or not re.fullmatch(r'1\.\d+', version):
        raise ValueError('Unsupported Bible version; major changes require reviewed tooling')
    if metadata['document'] != Path(DOCUMENT).name:
        raise ValueError('Unexpected Bible document identity')
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('Invalid Bible SHA-256')
    if hashlib.sha256(document).hexdigest() != digest:
        raise ValueError('Bible checksum mismatch; never auto-update an unreviewed copy')
    if '\r' in text or '\x00' in text or not text.endswith('\n'):
        raise ValueError('Bible must use UTF-8/LF with a final newline')
    if not text.startswith(f'# NorskAllstars — World & Experience Bible v{version}\n\nVersion: {version}\n'):
        raise ValueError('Bible header/version mismatch')
    if re.findall(r'^## (\d+)\. ', text, re.MULTILINE) != [str(n) for n in range(1, 25)]:
        raise ValueError('Bible section inventory is incomplete or duplicated')
    return metadata


def read_public_file(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('Expected a bounded regular public document, not a symlink')
    with path.open('rb') as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Public document exceeds size limit')
    return data


def indexed(name: str, limit: int) -> bytes:
    if int(git('cat-file', '-s', ':' + name)) > limit:
        raise ValueError('Indexed Bible/version record exceeds size limit')
    return git('show', ':' + name)


def check(*, index: bool = False, candidate: Path | None = None,
          candidate_record: Path | None = None) -> dict:
    document = read_public_file(ROOT / DOCUMENT, MAX_DOCUMENT)
    record = read_public_file(ROOT / RECORD, MAX_RECORD)
    metadata = validate(document, record)
    if index:
        staged_document = indexed(DOCUMENT, MAX_DOCUMENT)
        staged_record = indexed(RECORD, MAX_RECORD)
        validate(staged_document, staged_record)
        if (staged_document, staged_record) != (document, record):
            raise ValueError('Working Bible and exact index differ; review/stage deliberately')
    if (candidate is None) != (candidate_record is None):
        raise ValueError('Supply the complete public document/version-record pair')
    if candidate is not None and candidate_record is not None:
        exported = read_public_file(candidate, MAX_DOCUMENT)
        exported_record = read_public_file(candidate_record, MAX_RECORD)
        validate(exported, exported_record)
        if (exported, exported_record) != (document, record):
            raise ValueError('Supplied public copy is not byte-identical; synchronization unverified')
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', action='store_true', help='Also verify exact staged bytes')
    parser.add_argument('--candidate-file', type=Path,
                        help='Explicitly authorized public export only; never discover/read a private repo')
    parser.add_argument('--candidate-record', type=Path,
                        help='Explicit public version-record export, required with --candidate-file')
    args = parser.parse_args()
    try:
        metadata = check(index=args.index, candidate=args.candidate_file,
                         candidate_record=args.candidate_record)
    except (ValueError, OSError, subprocess.SubprocessError):
        print('Bible verification failed closed; review version, checksum, file boundary and index.')
        return 1
    print(f"World & Experience Bible {metadata['version']} verified: SHA-256 {metadata['sha256']}")
    if args.candidate_file:
        print('Explicit public document/version-record pair is byte-identical; no files changed.')
    else:
        print('Other repository synchronization not verified; no other repository was accessed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
