# [START dockerfile]
# Use the official Python 3.9 image as a parent image
FROM python:3.9-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.2.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -


# Set the working directory
WORKDIR /app

# Copy only the requirements files first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
RUN pip install --no-cache-dir -r requirements.txt

# ========================================
# Production stage
# ========================================
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    GUNICORN_CMD_ARGS="--timeout 180 --workers 4 --worker-class gthread --threads 2"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and switch to it
RUN addgroup --system appuser && \
    adduser --system --no-create-home --group appuser

# Set the working directory
WORKDIR /app

# Copy only the installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY . .

# Set file permissions
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["gunicorn", "--bind", ":8080", "--worker-class", "gthread", "--threads", "2", "main:app"]
# [END dockerfile]
