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

.PHONY: web-check web-test web-e2e storage-cleanup
web-check:
	cd apps/web && npm run format && npm run lint && npm run build
web-test:
	cd apps/web && npm test
web-e2e:
	$(PYTHON) scripts/web_e2e.py run
storage-cleanup:
	$(PYTHON) scripts/phase1.py storage-cleanup

.PHONY: android-check android-build android-audit
android-check:
	$(PYTHON) scripts/android_contract.py --check
	$(PYTHON) scripts/android.py wrapper
	$(PYTHON) scripts/android.py check
android-build:
	$(PYTHON) scripts/android.py build
android-audit:
	$(PYTHON) scripts/android_audit.py
