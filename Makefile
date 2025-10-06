.PHONY: install run lint test format check

install:
	poetry install

run:
	poetry run python main.py

lint:
	poetry run ruff check .

format:
	poetry run ruff check . --select I --fix
	poetry run ruff format .

check: lint test

test:
	poetry run pytest
