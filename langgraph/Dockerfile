FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

LABEL maintainer="Jerrico Gamis <jecklgamis@gmail.com>"

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "server_api.py"]
