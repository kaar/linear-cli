PROJECT_NAME = linear
VERSION = 1.2.0

pipx-install-editable:
	pipx install --editable .
.PHONY: pipx-install-editable

pipx-uninstall:
	pipx uninstall linear
.PHONY: pipx-uninstall

clean: pipx-uninstall
.PHONY: clean

install:
	uv sync --all-extras --dev
.PHONY: install

check:
	uv run ruff check --output-format=github .
.PHONY: check

format:
	uv run ruff format --diff
.PHONY: format
