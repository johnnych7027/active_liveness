.PHONY: install-pre-commit-fmt
install-pre-commit-fmt:
	cat pre-commit-hook.sh > .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit