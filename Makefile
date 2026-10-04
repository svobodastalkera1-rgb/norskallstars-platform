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

.PHONY: backend-test backend-audit local-up local-down
backend-test:
	$(PYTHON) scripts/phase1.py test

backend-audit:
	$(PYTHON) scripts/phase1.py audit

local-up:
	$(PYTHON) scripts/phase1.py init
	$(PYTHON) scripts/phase1.py up

local-down:
	$(PYTHON) scripts/phase1.py down
