"""Isolated synthetic Android backend and private device test-input provisioning."""

import argparse
import json
import subprocess
from pathlib import Path

import phase1

ROOT = Path(__file__).resolve().parents[1]


def environment():
    env = phase1.environment(True)
    env.update(
        NORSKALLSTARS_DATABASE_NAME="norskallstars_android_test",
        NORSKALLSTARS_IDENTITY_PUBLIC_ORIGIN="http://127.0.0.1:8001",
        NORSKALLSTARS_ALLOWED_HOSTS='["127.0.0.1","localhost","testserver","10.0.2.2"]',
        NORSKALLSTARS_STORAGE_BACKEND="local",
        NORSKALLSTARS_STORAGE_ROOT=str(ROOT / ".cache/android-e2e/objects"),
    )
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "serve", "device-input"))
    args = parser.parse_args()
    env = environment()
    if args.command == "prepare":
        directory = ROOT / ".cache/android-e2e/objects"
        directory.mkdir(parents=True, exist_ok=True)
        phase1.compose("up", "-d", "--wait", "database")
        names = phase1.compose("exec", "-T", "database", "psql", "-U", "norskallstars_dev",
            "-d", "postgres", "-Atc", "SELECT datname FROM pg_database", capture=True).stdout
        if "norskallstars_android_test" not in names.splitlines():
            phase1.compose("exec", "-T", "database", "psql", "-U", "norskallstars_dev",
                "-d", "postgres", "-c", "CREATE DATABASE norskallstars_android_test")
        phase1.run(phase1.uv("alembic", "-c", "apps/backend/alembic.ini", "upgrade", "head"), env=env)
        phase1.run(phase1.uv("python", "apps/backend/tests/android_seed.py"), env=env)
    elif args.command == "serve":
        phase1.run(phase1.uv("uvicorn", "norskallstars_backend.app:create_app", "--factory",
            "--host", "127.0.0.1", "--port", "8001", "--no-access-log", "--no-proxy-headers"), env=env)
    else:
        raw = json.loads((ROOT / ".cache/android-e2e/login.json").read_text())
        payload = json.dumps({"account": raw["accounts"]["android:learning"], "scenario": raw["scenario"]}).encode()
        # Only the debuggable app can receive this input. No args/logs/artifact contain credentials.
        # The documented isolated test device must not carry a prior account/session.
        subprocess.run(["adb", "shell", "pm", "clear", "com.norskallstars.platform.dev"], check=True)
        subprocess.run(["adb", "shell", "run-as", "com.norskallstars.platform.dev", "mkdir", "-p", "files"], check=True)
        subprocess.run(["adb", "shell", "run-as", "com.norskallstars.platform.dev", "sh", "-c",
            "'umask 077; cat > files/synthetic-test-input.json'"], input=payload, check=True)
        print("Private synthetic device input provisioned; values omitted")


if __name__ == "__main__":
    main()
