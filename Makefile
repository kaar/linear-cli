PROJECT_NAME = $(shell poetry version | cut -d' ' -f1)
VERSION = $(shell poetry version | cut -d' ' -f2)
SRC = src

pipx-install-editable:
	pipx install --editable .
.PHONY: pipx-install-editable

pipx-uninstall:
	pipx uninstall $(PROJECT_NAME)
.PHONY: pipx-uninstall

test:
	poetry run pytest $(SRC)
.PHONY: test

clean: pipx-uninstall
.PHONY: clean
