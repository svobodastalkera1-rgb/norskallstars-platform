"""Trusted operator CLI: OS/runtime access plus database/storage privileges required."""

import argparse
import asyncio
import logging
import os
import stat
import uuid
from pathlib import Path

from norskallstars_backend.config import load_settings
from norskallstars_backend.course_packages.archive import BoundaryError
from norskallstars_backend.course_packages.service import import_package, publish_release
from norskallstars_backend.database import Database
from norskallstars_backend.logging import configure_logging, exception_fields
from norskallstars_backend.storage import LocalObjectStorage


async def operate(args: argparse.Namespace) -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    if settings.storage_backend != "local" or settings.storage_root is None:
        raise BoundaryError("storage_adapter_required")
    storage = LocalObjectStorage(settings.storage_root, settings.storage_max_bytes)
    database = Database(settings)
    try:
        if args.command == "import":
            fd = os.open(args.package, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > 64 << 20:
                    raise BoundaryError("input_file")
                data = stream.read((64 << 20) + 1)
            await import_package(database, storage, data, actor=args.actor, approval=args.approval)
        else:
            if not args.confirm_publication:
                raise BoundaryError("publication_confirmation_required")
            await publish_release(
                database,
                uuid.UUID(args.release_id),
                actor=args.actor,
                approval=args.approval,
                storage=storage,
            )
        print("Completed operator transition; inspect authorized release inventory privately")
    finally:
        await database.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    importer = sub.add_parser("import")
    importer.add_argument("package", type=Path)
    publisher = sub.add_parser("publish")
    publisher.add_argument("release_id")
    publisher.add_argument("--confirm-publication", action="store_true")
    for child in (importer, publisher):
        child.add_argument("--actor", required=True)
        child.add_argument("--approval", required=True)
    args = parser.parse_args()
    try:
        asyncio.run(operate(args))
        return 0
    except Exception as exc:
        logging.getLogger("norskallstars.importer").error(
            "unexpected_error", extra=exception_fields(exc)
        )
        print("Rejected operator transition; review private diagnostics")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
