"""Generate/check the public API contract without reading external configuration or secrets."""

import argparse
import asyncio
import json
import secrets
from pathlib import Path

from cryptography.fernet import Fernet

from norskallstars_backend.app import create_app
from norskallstars_backend.config import Settings


def schema_bytes() -> bytes:
    settings = Settings(
        env="test",
        database_host="127.0.0.1",
        database_name="schema_test",
        database_user="schema_user",
        database_password=secrets.token_urlsafe(36),
        identity_pepper=secrets.token_urlsafe(36),
        identity_mail_key=Fernet.generate_key().decode(),
    )
    app = create_app(settings)
    try:
        return (json.dumps(app.openapi(), sort_keys=True, indent=2) + "\n").encode()
    finally:
        asyncio.run(app.state.database.close())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = schema_bytes()
    if args.check:
        if not args.path.is_file() or args.path.read_bytes() != data:
            raise SystemExit("Identity OpenAPI differs; regenerate and review compatibility")
        print("PASS: generated identity OpenAPI matches reviewed public contract")
    else:
        args.path.parent.mkdir(parents=True, exist_ok=True)
        args.path.write_bytes(data)


if __name__ == "__main__":
    main()
