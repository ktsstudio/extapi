.PHONY: mypy ruff style style-check test lint pytest

package?=extapi tests

style:
	python -m ruff format $(package)
	python -m ruff check --select I --fix $(package)

mypy:
	python -m mypy --enable-error-code ignore-without-code $(package)

ruff:
	python -m ruff check $(package)

style-check:
	python -m ruff format --check --diff $(package)

deptry:
	deptry . -e 'env|\.env|venv|\.venv|\..+'

lint: style-check ruff mypy deptry

pytest:
	python -m pytest .

test: lint pytest
