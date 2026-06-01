# --- Build stage: resolve the agent's deps into a venv ---
    FROM python:3.12-slim AS build
    COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/
    ENV UV_COMPILE_BYTECODE=1 \
        UV_LINK_MODE=copy
    WORKDIR /app

    # Plain COPY + RUN (no BuildKit cache/bind mounts) so the image builds the same
    # with local Docker AND ACR Tasks' classic builder (BuildKit is preview-only in ACR).
    COPY pyproject.toml uv.lock ./
    RUN uv sync --frozen --no-install-project --no-dev --group rag

    # --- Runtime stage: slim, no uv, non-root ---
    FROM python:3.12-slim AS runtime
    WORKDIR /app

    COPY --from=build /app/.venv /app/.venv
    ENV PATH="/app/.venv/bin:$PATH" \
        PYTHONPATH="/app/src" \
        PYTHONUNBUFFERED=1

    COPY src ./src
    COPY .chroma ./.chroma

    RUN useradd -m -u 1001 appuser && chown -R appuser /app
    USER appuser

    EXPOSE 8501
    CMD ["streamlit", "run", "src/readmission_lakehouse/agent/app.py", \
         "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
