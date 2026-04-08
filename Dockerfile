# ---- Stage 1: Build dependencies ----
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir poetry==2.1.3

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock ./

# Configure poetry: no virtualenv in container, no interaction
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-root --no-interaction --no-ansi

# ---- Stage 2: Runtime ----
FROM python:3.12-slim

# Install minimal runtime deps for compiled wheels (zmq, gevent, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
        libegl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY apps/ ./apps/
COPY lib/ ./lib/
COPY meta/ ./meta/
COPY assets/ ./assets/

# Note: png_config.json is NOT baked into the image.
# Mount your own config at runtime via:
#   -v /path/to/png_config.json:/app/png_config.json:ro

# Save Data Viewer
EXPOSE 4769/tcp
# Web UI
EXPOSE 4768/tcp
# F1 telemetry UDP receiver
EXPOSE 20777/udp

# Run as non-root user for security (CIS Docker Benchmark 4.1)
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4768/')" || exit 1

ENTRYPOINT ["python", "-m", "apps.backend"]
