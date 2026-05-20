# ── Build stage ──────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# ── Runtime ──────────────────────────────────────────────────────────
# Default entrypoint — can be overridden with docker run args
ENTRYPOINT ["python", "-m", "bot.cli.main"]
CMD ["--help"]
