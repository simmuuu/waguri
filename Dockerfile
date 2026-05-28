FROM ghcr.io/astral-sh/uv:python3.14-bookworm

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY . .

CMD ["uv", "run", "python", "main.py"]
