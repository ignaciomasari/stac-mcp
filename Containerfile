# STAC MCP Server - Container image for VM / HTTP deployment
# Supports both stdio (default for MCP clients) and HTTP transport.
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files (include uv.lock for reproducible builds)
COPY pyproject.toml uv.lock* ./
COPY README.md ./
COPY LICENSE ./
COPY stac_mcp ./stac_mcp

# Install uv (Astral) for fast dependency resolution
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install dependencies and build the package
RUN uv sync --frozen
RUN uv build
RUN pip install dist/stac_mcp-*.whl

# Runtime: use stac_mcp CLI (python -m stac_mcp) which supports --transport, --host, --port
# Default: HTTP transport on 0.0.0.0:8000 for container/VM deployment
# Override CMD for stdio: CMD ["--transport", "stdio"]
EXPOSE 8000

ENTRYPOINT ["python", "-m", "stac_mcp"]
CMD ["--transport", "http", "--host", "0.0.0.0", "--port", "8000"]