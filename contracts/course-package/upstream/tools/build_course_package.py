#!/usr/bin/env python3
"""Create an immutable Course Package v1 from a prepared component directory."""
import argparse
import json
import sys
from pathlib import Path

from course_package import PackageError, build_package

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("staging", type=Path, help="directory containing course/chapter/lesson/activity JSON and assets")
    parser.add_argument("output", type=Path, help="new output directory; existing output is never overwritten")
    parser.add_argument("--course-id", required=True)
    parser.add_argument("--course-version", required=True)
    parser.add_argument("--build-timestamp", help="fixed UTC timestamp for reproducible builds")
    parser.add_argument("--release-eligible", action="store_true", help="mark only after owner/QA release approval")
    args = parser.parse_args()
    try:
        report = build_package(args.staging, args.output, args.course_id, args.course_version, args.build_timestamp, args.release_eligible)
    except (PackageError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    sys.exit(main())
