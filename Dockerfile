# syntax=docker/dockerfile:1

# --- Build stage: resolve the agent's deps into a venv ---
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app

# Deps only (no project build, no dev tools). Cached on the lockfile, so code
# changes don't re-resolve. --group rag pulls langgraph/langchain/chroma/
# streamlit/databricks-sql-connector/azure-* — everything the agent imports.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --group rag

# --- Runtime stage: slim, no uv, non-root ---
FROM python:3.12-slim AS runtime
WORKDIR /app

COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1

# App code + the prebuilt vector store, baked in. CHROMA_DIR resolves to
# /app/.chroma (parents[3] of .../src/readmission_lakehouse/agent/config.py).
COPY src ./src
COPY .chroma ./.chroma

RUN useradd -m -u 1001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8501
# Container Apps ingress will target 8501. headless + 0.0.0.0 to serve in-container.
CMD ["streamlit", "run", "src/readmission_lakehouse/agent/app.py", \
        "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
