.PHONY: help dev fmt lock pre-commit

.DEFAULT: help
help:
	@echo "make dev"
	@echo "	prepare development environment"
	@echo "make fmt"
	@echo "	run black code formatter"
	@echo "make lock"
	@echo "	lock requirements"
	@echo "make pre-commit"
	@echo "	run pre-commit hooks"

dev:
	pipenv install --dev
	pipenv run pre-commit install

fmt:
	pipenv run black .

lock:
	pipenv lock
	pipenv requirements > requirements.txt
	pipenv requirements --dev > requirements-dev.txt

pre-commit:
	pipenv run pre-commit
