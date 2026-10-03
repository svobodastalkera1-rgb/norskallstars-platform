PYTHON ?= python3

.PHONY: bootstrap check security-check hooks
bootstrap:
	$(PYTHON) -m venv .venv
	.venv/bin/python scripts/install_security_tool.py

check:
	$(PYTHON) scripts/check_repository.py
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/confidentiality_guard.py --history main

security-check:
	$(PYTHON) scripts/scan_secrets.py --history main

hooks:
	$(PYTHON) scripts/install_hooks.py
