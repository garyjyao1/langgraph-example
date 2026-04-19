FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

LABEL maintainer="Jerrico Gamis <jecklgamis@gmail.com>"

WORKDIR /app

# Install workspace deps (build context = repo root)
COPY pyproject.toml ./
COPY shared/ ./shared/
COPY langgraph/pyproject.toml langgraph/uv.lock* ./langgraph/
RUN uv sync --frozen --no-dev --package langgraph-example

# Copy framework-specific source
COPY langgraph/ ./langgraph/

# Copy shared operational assets
COPY static/ ./static/
COPY templates/ ./templates/

WORKDIR /app/langgraph

EXPOSE 8000

CMD ["uv", "run", "server_api.py"]
