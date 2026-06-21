.PHONY: help install dev clean build rebuild test lint format pre-commit run uninstall

UV ?= uv

help:
	@echo "qcp dev tasks:"
	@echo "  make install   - create venv, install qcp (editable)"
	@echo "  make dev       - create venv, install qcp + dev/test deps"
	@echo "  make build     - build sdist + wheel into dist/"
	@echo "  make clean     - remove venv, build artifacts, caches"
	@echo "  make rebuild   - clean, then dev install + build (clean build)"
	@echo "  make test      - run the test suite"
	@echo "  make lint      - run Ruff checks"
	@echo "  make format    - format Python with Ruff"
	@echo "  make pre-commit - run all pre-commit hooks"
	@echo "  make uninstall - pip-uninstall qcp from the active environment"

# --- clean install: fresh venv, fresh deps -----------------------------
install: clean
	$(UV) sync
	@echo "qcp installed in .venv. Run it with: uv run qcp"

dev: clean
	$(UV) sync --extra dev
	@echo "qcp + development dependencies installed in .venv."

# --- clean build: fresh dist/ from a clean tree -------------------------
build: clean
	$(UV) build
	@echo "Built sdist + wheel into dist/"

rebuild: dev build

test:
	$(UV) run pytest -v

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

pre-commit:
	$(UV) run pre-commit run --all-files

run:
	$(UV) run qcp $(ARGS)

uninstall:
	$(UV) pip uninstall qcp || true

# --- clean: wipe venv, build artifacts, caches ---------------------------
clean:
	rm -rf .venv build dist *.egg-info qcp.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	@echo "✔ Cleaned (venv, build/, dist/, caches)"
