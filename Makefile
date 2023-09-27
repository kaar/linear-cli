pipx-install-editable:
	pipx install --editable .
.PHONY: pipx-install-editable

pipx-uninstall:
	pipx uninstall linear-cli
.PHONY: pipx-uninstall

clean: pipx-uninstall
.PHONY: clean
