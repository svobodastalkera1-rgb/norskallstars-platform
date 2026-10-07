"""Reproducible synthetic browser backend; no inherited production configuration."""

import argparse
from pathlib import Path
import subprocess
import sys

import phase1

ROOT = Path(__file__).resolve().parents[1]


def environment():
    env = phase1.environment(True)
    env.update(
        NORSKALLSTARS_DATABASE_NAME="norskallstars_web_test",
        NORSKALLSTARS_IDENTITY_PUBLIC_ORIGIN="http://127.0.0.1:8000",
        NORSKALLSTARS_WEB_ROOT=str(ROOT / "apps/web/dist"),
        NORSKALLSTARS_STORAGE_BACKEND="local",
        NORSKALLSTARS_STORAGE_ROOT=str(ROOT / ".cache/web-e2e/objects"),
    )
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "serve", "run"))
    args = parser.parse_args()
    env = environment()
    if args.command == "run":
        # Independent browser projects must not share learner/rate-bucket state.
        # Reset only the guarded synthetic web_test DB; never bypass runtime limits.
        for browser in ("chromium", "firefox", "webkit"):
            phase1.run([sys.executable, str(Path(__file__).resolve()), "prepare"])
            subprocess.run(
                ["npm", "run", "e2e", "--", "--project", browser],
                cwd=ROOT / "apps/web",
                check=True,
            )
        print("PASS: all three isolated browser projects completed")
    elif args.command == "prepare":
        (ROOT / ".cache/web-e2e/objects").mkdir(parents=True, exist_ok=True)
        phase1.compose("up", "-d", "--wait", "database")
        databases = phase1.compose(
            "exec",
            "-T",
            "database",
            "psql",
            "-U",
            "norskallstars_dev",
            "-d",
            "postgres",
            "-Atc",
            "SELECT datname FROM pg_database",
            capture=True,
        ).stdout
        if "norskallstars_web_test" not in databases.splitlines():
            phase1.compose(
                "exec",
                "-T",
                "database",
                "psql",
                "-U",
                "norskallstars_dev",
                "-d",
                "postgres",
                "-c",
                "CREATE DATABASE norskallstars_web_test",
            )
        phase1.run(
            phase1.uv("alembic", "-c", "apps/backend/alembic.ini", "upgrade", "head"),
            env=env,
        )
        phase1.run(phase1.uv("python", "apps/backend/tests/browser_seed.py"), env=env)
    else:
        phase1.run(
            phase1.uv(
                "uvicorn",
                "norskallstars_backend.app:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--no-access-log",
                "--no-proxy-headers",
            ),
            env=env,
        )


if __name__ == "__main__":
    main()
