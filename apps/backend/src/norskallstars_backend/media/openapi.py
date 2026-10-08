"""Generate/check stable public media endpoints with synthetic configuration."""

from norskallstars_backend.identity.openapi import main as generate

if __name__ == "__main__":
    generate(prefix="/api/v1/media/", label="Media")
