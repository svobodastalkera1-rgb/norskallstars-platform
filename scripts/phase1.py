"""Local-only orchestration with generated ignored credentials, never production inputs."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".cache" / "phase1.env"
BACKEND = ROOT / "apps" / "backend"


def local_values() -> dict[str, str]:
    if not ENV_FILE.is_file():
        raise SystemExit("Run python scripts/phase1.py init first")
    values = dict(line.split("=", 1) for line in ENV_FILE.read_text().splitlines() if line)
    if len(values.get("NORSKALLSTARS_DATABASE_PASSWORD", "")) < 24:
        raise SystemExit("Invalid local configuration; remove only the local env and reinitialize")
    return values


def environment(test: bool = False) -> dict[str, str]:
    # Never inherit accidental production connection settings from a developer shell.
    env = {key: value for key, value in os.environ.items() if not key.startswith("NORSKALLSTARS_")}
    env.update(local_values())
    env.update(NORSKALLSTARS_ENV="test" if test else "local",
               NORSKALLSTARS_DATABASE_HOST="127.0.0.1", NORSKALLSTARS_DATABASE_PORT="5433",
               NORSKALLSTARS_DATABASE_NAME="norskallstars_test" if test else "norskallstars_local",
               NORSKALLSTARS_DATABASE_USER="norskallstars_dev")
    return env


def run(command: list[str], **kwargs: object) -> None:
    subprocess.run(command, check=True, cwd=ROOT, **kwargs)


def compose(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["docker", "compose", "--env-file", str(ENV_FILE), "-f",
                           "infra/development/compose.yaml", *args], cwd=ROOT,
                          env=environment(), check=True, text=True,
                          stdout=subprocess.PIPE if capture else None)


def uv_executable() -> str:
    executable = shutil.which("uv")
    local = ROOT / ".venv" / ("Scripts/uv.exe" if os.name == "nt" else "bin/uv")
    if executable is None and local.is_file():
        executable = str(local)
    if executable is None:
        raise SystemExit("Install uv 0.12.23; see docs/development.md")
    return executable


def uv(*args: str) -> list[str]:
    return [uv_executable(), "run", "--locked", "--project", str(BACKEND), *args]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "up", "down", "test", "migrate", "smoke", "audit"))
    args = parser.parse_args()
    if args.command == "init":
        ENV_FILE.parent.mkdir(exist_ok=True)
        if not ENV_FILE.exists():
            descriptor = os.open(ENV_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w") as stream:
                stream.write("NORSKALLSTARS_DATABASE_PASSWORD=" + secrets.token_urlsafe(36) + "\n")
        print("Local credentials ready in ignored .cache/phase1.env (values not printed)")
    elif args.command == "up":
        compose("up", "-d", "--wait", "database")
        compose("build", "backend")
        compose("run", "--rm", "migrate")
        compose("up", "-d", "--wait", "backend")
    elif args.command == "down":
        compose("down")  # Preserve developer volumes; never implicitly delete data.
    elif args.command == "migrate":
        compose("run", "--rm", "migrate")
    elif args.command == "test":
        compose("up", "-d", "--wait", "database")
        databases = compose("exec", "-T", "database", "psql", "-U", "norskallstars_dev", "-d",
                            "postgres", "-Atc", "SELECT datname FROM pg_database", capture=True).stdout
        if "norskallstars_test" not in databases.splitlines():
            compose("exec", "-T", "database", "psql", "-U", "norskallstars_dev", "-d", "postgres",
                    "-c", "CREATE DATABASE norskallstars_test")
        run(uv("alembic", "-c", "apps/backend/alembic.ini", "upgrade", "head"), env=environment(True))
        run(uv("pytest", "-c", "apps/backend/pyproject.toml", "apps/backend/tests"), env=environment(True))
        subprocess.run(uv("python", "-m", "unittest", "discover", "-s", "qa/automated", "-p", "test_course_package.py", "-v"), cwd=ROOT / "contracts/course-package/upstream", env=environment(True), check=True)
    elif args.command == "audit":
        requirements = ROOT / ".cache" / "backend-audit.txt"
        requirements.parent.mkdir(exist_ok=True)
        run([uv_executable(), "export", "--locked", "--project", str(BACKEND), "--no-emit-project",
             "--no-hashes", "--output-file", str(requirements)], stdout=subprocess.DEVNULL)
        run(uv("pip-audit", "--strict", "--disable-pip", "--no-deps", "--progress-spinner", "off",
               "-r", str(requirements)))
    elif args.command == "smoke":
        for endpoint, expected in [("live", "alive"), ("ready", "ready")]:
            with urllib.request.urlopen("http://127.0.0.1:8000/health/" + endpoint, timeout=5) as response:
                assert response.status == 200 and json.load(response) == {"status": expected}
                assert response.headers.get("X-Request-ID")
        runtime = json.loads(compose("config", "--format", "json", capture=True).stdout)["services"]["backend"]
        assert runtime["read_only"] and runtime["cap_drop"] == ["ALL"]
        uid = compose("exec", "-T", "backend", "id", "-u", capture=True).stdout.strip()
        assert uid == "10001"
        compose("exec", "-T", "backend", "python", "-c", "from norskallstars_backend.course_packages.validation import schema_registry; assert len(schema_registry()[0]) == 7")
        print("PASS: real container liveness/readiness, correlation ID, non-root/read-only runtime and packaged contract schemas")


if __name__ == "__main__":
    main()
