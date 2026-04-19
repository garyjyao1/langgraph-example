FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

LABEL maintainer="Jerrico Gamis <jecklgamis@gmail.com>"

WORKDIR /app

# Install workspace deps (build context = repo root)
COPY pyproject.toml ./
COPY shared/ ./shared/
COPY pydantic-ai/pyproject.toml pydantic-ai/uv.lock* ./pydantic-ai/
RUN uv sync --frozen --no-dev --package pydantic-ai-example

# Copy framework-specific source
COPY pydantic-ai/ ./pydantic-ai/

# Copy shared operational assets
COPY static/ ./static/
COPY templates/ ./templates/

WORKDIR /app/pydantic-ai

EXPOSE 8000

CMD ["uv", "run", "server_api.py"]
