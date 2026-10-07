"""Generate/check the public API contract without reading external configuration or secrets."""

import argparse
import asyncio
import json
import secrets
from pathlib import Path

from cryptography.fernet import Fernet
from pydantic import SecretStr

from norskallstars_backend.api_contract import domain_schema
from norskallstars_backend.app import create_app
from norskallstars_backend.config import Environment, Settings


def schema_bytes(prefix: str = "/api/v1/identity/") -> bytes:
    settings = Settings(
        env=Environment.TEST,
        database_host="127.0.0.1",
        database_name="schema_test",
        database_user="schema_user",
        database_password=SecretStr(secrets.token_urlsafe(36)),
        identity_pepper=SecretStr(secrets.token_urlsafe(36)),
        identity_mail_key=SecretStr(Fernet.generate_key().decode()),
    )
    app = create_app(settings)
    try:
        return (
            json.dumps(domain_schema(app.openapi(), prefix), sort_keys=True, indent=2) + "\n"
        ).encode()
    finally:
        asyncio.run(app.state.database.close())


def main(prefix: str = "/api/v1/identity/", label: str = "Identity") -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = schema_bytes(prefix)
    if args.check:
        if not args.path.is_file() or args.path.read_bytes() != data:
            raise SystemExit(f"{label} OpenAPI differs; regenerate and review compatibility")
        print(f"PASS: generated {label} OpenAPI matches reviewed public contract")
    else:
        args.path.parent.mkdir(parents=True, exist_ok=True)
        args.path.write_bytes(data)


if __name__ == "__main__":
    main()
