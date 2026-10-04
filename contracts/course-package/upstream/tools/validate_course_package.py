#!/usr/bin/env python3
"""Validate an untrusted Course Package directory or ZIP without extraction."""
import argparse
import json
import sys
from pathlib import Path

from course_package import PackageError, validate_package

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    try:
        report = validate_package(args.package)
    except PackageError as exc:
        report = {"valid": False, "errors": [str(exc)]}
    if args.json: print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print("VALID" if report["valid"] else "INVALID")
        for error in report["errors"]: print(f"- {error}")
        if report["valid"]: print(f"Course {report['course_id']} {report['course_version']}: {report['files']} files; release_eligible={report['release_eligible']}")
    return 0 if report["valid"] else 1

if __name__ == "__main__":
    sys.exit(main())
