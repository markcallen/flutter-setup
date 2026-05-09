FROM python:3.12-slim

# Install uv.
RUN apt-get update && apt-get install -y curl ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

WORKDIR /app

# Copy dependency file(s) first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies in a separate layer
RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "flutter-setup"]
