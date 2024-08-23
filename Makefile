PROJECT_NAME = linear
VERSION = 1.2.0

pipx-install-editable:
	pipx install --editable .
.PHONY: pipx-install-editable

pipx-uninstall:
	pipx uninstall linear
.PHONY: pipx-uninstall

test:
	poetry run pytest linear
.PHONY: test

clean: pipx-uninstall
.PHONY: clean

build: clean
	poetry build

release: build test
	gh release create v$(VERSION) --generate-notes
