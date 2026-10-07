"""Trusted operator learning-policy selection; no HTTP authorization is implied by assertions."""

import argparse
import asyncio
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from norskallstars_backend.config import load_settings
from norskallstars_backend.course_packages.archive import BoundaryError
from norskallstars_backend.course_packages.validation import parse_json
from norskallstars_backend.database import Database
from norskallstars_backend.learning.policy import LearningPolicy
from norskallstars_backend.learning.service import LearningError, select_learning_release


def read_policy(path: Path) -> LearningPolicy:
    with path.open("rb") as stream:
        raw = stream.read(2 * 1024 * 1024 + 1)
    return LearningPolicy.model_validate(parse_json(raw))


async def select(args: argparse.Namespace) -> None:
    policy = read_policy(args.policy)
    database = Database(load_settings())
    try:
        await select_learning_release(
            database, args.release_id, policy, actor=args.actor, approval=args.approval
        )
        print("Learning policy selected for new enrollments; existing progress unchanged")
    finally:
        await database.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("select")
    command.add_argument("release_id", type=UUID)
    command.add_argument("policy", type=Path)
    command.add_argument("--actor", required=True)
    command.add_argument("--approval", required=True)
    try:
        asyncio.run(select(parser.parse_args()))
    except (LearningError, BoundaryError, ValidationError, ValueError, OSError):
        raise SystemExit(
            "Learning selection rejected; check approved release/policy/configuration privately"
        ) from None


if __name__ == "__main__":
    main()
