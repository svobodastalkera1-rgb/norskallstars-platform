"""Private operator mail/credential maintenance; no public HTTP job runner."""

import argparse
import asyncio
import json
from pathlib import Path

from norskallstars_backend.config import Environment, load_settings
from norskallstars_backend.database import Database
from norskallstars_backend.identity.google import GoogleVerifier
from norskallstars_backend.identity.mail import (
    LocalMailTransport,
    MailTransport,
    MailWorker,
    SMTPTransport,
    cleanup,
)
from norskallstars_backend.identity.service import Identity
from norskallstars_backend.storage import LocalObjectStorage


async def run(command: str, directory: Path | None, limit: int) -> None:
    settings = load_settings()
    database = Database(settings)
    try:
        identity = Identity(settings, database, GoogleVerifier())
        if command == "cleanup":
            result = await cleanup(identity)
        else:
            if settings.mail_transport == "outbox":
                if (
                    directory is None
                    or not directory.is_absolute()
                    or settings.env not in (Environment.LOCAL, Environment.TEST)
                ):
                    raise RuntimeError("Local mail requires an explicit private absolute directory")
                transport: MailTransport = LocalMailTransport(
                    identity, LocalObjectStorage(directory, 65536)
                )
            else:
                if directory is not None:
                    raise RuntimeError("Local mailbox cannot override SMTP configuration")
                transport = SMTPTransport(identity)
            result = await MailWorker(identity, transport).drain(limit)
        print(json.dumps(result))  # Counts only; never recipient/payload/connection information.
    finally:
        await database.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["mail", "cleanup"])
    parser.add_argument("--private-directory", type=Path)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    try:
        asyncio.run(run(args.command, args.private_directory, args.limit))
    except Exception:
        raise SystemExit("Identity maintenance failed; inspect private diagnostics") from None


if __name__ == "__main__":
    main()
