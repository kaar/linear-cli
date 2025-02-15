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
