"""Generate/check the Learning API using synthetic configuration only."""

from norskallstars_backend.identity.openapi import main as generate


def main() -> None:
    generate(prefix="/api/v1/learning/", label="Learning")


if __name__ == "__main__":
    main()
