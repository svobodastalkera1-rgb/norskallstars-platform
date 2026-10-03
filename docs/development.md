# Reproducible bootstrap environment

Phase 0 checks need Git and Python 3.14.2. The repository has no third-party Python
packages or application dependency graph. .python-version pins bootstrap tooling;
it does not select the backend runtime before compatibility review. Make is a
convenience only. Use a Python 3.14.2 installation from python.org or your reviewed
version manager. Linux/macOS/Windows are supported; WSL is suitable for Make.

## Setup

Linux/macOS, from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python scripts/install_security_tool.py
.venv/bin/python scripts/install_hooks.py
.venv/bin/python scripts/check_repository.py
.venv/bin/python scripts/confidentiality_guard.py --history main
.venv/bin/python scripts/scan_secrets.py --history main
```

Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python.exe scripts/install_security_tool.py
.venv\Scripts\python.exe scripts/install_hooks.py
.venv\Scripts\python.exe scripts/check_repository.py
.venv\Scripts\python.exe scripts/confidentiality_guard.py --history main
.venv\Scripts\python.exe scripts/scan_secrets.py --history main
```

Hooks use the .venv Python interpreter and execute a Git-compatible shell hook.
The installer refuses to replace an existing unrelated hook or custom hooksPath.
A missing tool causes commit/check failure with setup instructions, not a skip.

The Gitleaks installer supports pinned Linux x64/arm64, macOS x64/arm64 and
Windows x64 archives. It verifies archive SHA-256 against committed upstream
release checksums before extracting just the executable. Network access is only
to the upstream public release, not the corpus repository. Cached binaries are
verified using a locally recorded executable checksum on each scan. For offline
setup, supply the matching archive with --archive /path/to/archive; the same
committed checksum applies. Never use unverified executables to bypass a check.

## Working and checking

Inspect git status, work on a focused branch, and read AGENTS.md before changes.
Stage public-safe files, review git diff --cached, and run the checks again.
make check validates docs/tooling and scans index paths/content plus main trees.
make security-check scans secrets in the exact index and main history. CI scans
HEAD as well as main when available. Tests for new application behavior arrive
with the actual implementation; no product tests run in bootstrap.

.env.example contains only future non-secret environment labels. A local .env
may be copied when Phase 1 implements settings, but is unnecessary now. Docker,
PostgreSQL, Node and Android SDK installation is deferred until needed and pinned
with real manifests/locks. There is no demo application command yet; synthetic
handoff availability is a prerequisite for the future demo environment.

## Limitations

Local hooks are bypassable and scanners cannot prove arbitrary content public.
Current-main checks exclude old dangling objects/reflogs; do not recover private
inputs from them. Use current clean history. Tool downloads/runner images are
third-party inputs; review pins and security updates. Hosted Actions execution
must be verified after an authorized push; local success is not hosted CI evidence.
