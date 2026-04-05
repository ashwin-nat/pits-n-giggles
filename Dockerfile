FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev libgl1 libxkbcommon-x11-0 libdbus-1-3 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
    libxcb-render-util0 libxcb-xinerama0 libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --without dev --no-interaction --no-ansi
COPY src/ .
RUN mkdir -p /app/data/sessions /app/data/config

ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app QT_QPA_PLATFORM=offscreen PNG_HEADLESS=1
EXPOSE 4768/tcp 4769/tcp 20777/udp
CMD ["python", "-m", "apps.backend"]
