.PHONY: help install dev clean build rebuild test lint run uninstall

PYTHON ?= python3
VENV   ?= .venv
BIN    := $(VENV)/bin

help:
	@echo "qcp dev tasks:"
	@echo "  make install   - create venv, install qcp (editable)"
	@echo "  make dev       - create venv, install qcp + dev/test deps"
	@echo "  make build     - build sdist + wheel into dist/"
	@echo "  make clean     - remove venv, build artifacts, caches"
	@echo "  make rebuild   - clean, then dev install + build (clean build)"
	@echo "  make test      - run the test suite"
	@echo "  make uninstall - pip-uninstall qcp from the active environment"

# --- clean install: fresh venv, fresh deps -----------------------------
install: clean
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip --quiet
	$(BIN)/pip install -e . --quiet
	@echo "✔ qcp installed in $(VENV). Activate with: source $(VENV)/bin/activate"

dev: clean
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip --quiet
	$(BIN)/pip install -e ".[dev,postgres]" --quiet
	@echo "✔ qcp + dev/test deps installed in $(VENV)."

# --- clean build: fresh dist/ from a clean tree -------------------------
build: clean
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip build --quiet
	$(BIN)/python -m build
	@echo "✔ Built sdist + wheel into dist/"

rebuild: dev build

test:
	$(BIN)/pytest -v

lint:
	$(BIN)/python -m py_compile qcp/*.py tests/*.py
	@echo "✔ All files compile"

run:
	$(BIN)/qcp $(ARGS)

uninstall:
	$(BIN)/pip uninstall -y qcp || true

# --- clean: wipe venv, build artifacts, caches ---------------------------
clean:
	rm -rf $(VENV) build dist *.egg-info qcp.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	@echo "✔ Cleaned (venv, build/, dist/, caches)"
