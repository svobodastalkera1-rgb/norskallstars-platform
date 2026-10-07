"""Generate/check the public policy schema without any real policy/content instance."""

import argparse
import json
from pathlib import Path

from norskallstars_backend.learning.policy import LearningPolicy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = (
        json.dumps(LearningPolicy.model_json_schema(), sort_keys=True, indent=2) + "\n"
    ).encode()
    if args.check:
        if not args.path.is_file() or args.path.read_bytes() != data:
            raise SystemExit("Learning policy schema differs; regenerate and review")
        print("PASS: generated platform policy schema matches reviewed contract")
    else:
        args.path.parent.mkdir(parents=True, exist_ok=True)
        args.path.write_bytes(data)


if __name__ == "__main__":
    main()
