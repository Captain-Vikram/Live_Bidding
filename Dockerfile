FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /build

# Copy requirements first for better caching
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app
COPY ./initials ./initials
COPY ./.env .
COPY ./alembic.ini .

# Copy and make scripts executable
COPY ./initials/initial_fixed.sh /docker-entrypoint.d/initial.sh
RUN chmod +x /docker-entrypoint.d/initial.sh
RUN chmod +x ./initials/initial_fixed.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v6/healthcheck || exit 1

# Start the application
CMD ["bash", "./initials/initial_fixed.sh"]

ENV PYTHONPATH=/build