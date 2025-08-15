FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

WORKDIR /app

# Copy dependency file(s) first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies in a separate layer
RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "flutter-setup"]
