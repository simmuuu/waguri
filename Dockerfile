FROM ghcr.io/astral-sh/uv:python3.14-bookworm

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

ARG COMMIT_SHA=unknown
ENV COMMIT_SHA=${COMMIT_SHA}

COPY . .

CMD ["uv", "run", "python", "main.py"]
