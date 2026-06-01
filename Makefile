.PHONY: install lint format test test-dags clean tree

install:
	uv sync --all-groups
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src

format:
	uv run ruff format .
	uv run ruff check --fix .

test:
	uv run pytest

test-dags:
	ENV_FILE_PATH=/dev/null AIRFLOW_UID=50000 AIRFLOW__CORE__FERNET_KEY="" \
	docker compose -f airflow/docker-compose.yaml run --rm --entrypoint bash airflow-cli \
	-lc "pytest /opt/airflow/tests"

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov
	rm -f .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

tree:
	@if command -v tree >/dev/null 2>&1; then \
		tree -L 3 -I '.venv|node_modules|pycache'; \
	else \
		find . \( \
			-path './.git' -o \
			-name '.venv' -o -name 'node_modules' -o -name '__pycache__' -o \
			-name '.mypy_cache' -o -name '.pytest_cache' -o -name '.ruff_cache' \
		\) -prune -o -maxdepth 3 -print | LC_ALL=C sort; \
	fi
