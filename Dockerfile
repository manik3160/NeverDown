FROM python:3.11-slim

WORKDIR /app

# Install git and curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /tmp/neverdown/clones /tmp/neverdown/sanitized

# Run as non-root user
RUN useradd -m -u 1000 neverdown && \
    chown -R neverdown:neverdown /app /tmp/neverdown
USER neverdown

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
