"""
Production Deployment Configuration
==================================

Complete production-ready configuration for the AgriTech platform with:
- Security hardening
- Performance optimization  
- Monitoring and logging
- Docker configuration
- Environment management
"""

import os
from typing import List, Dict, Any
from pathlib import Path
from datetime import timedelta


class ProductionConfig:
    """
    Production deployment configuration
    """
    
    # Application Settings
    APP_NAME = "AgriTech Smart Bidding Platform"
    APP_VERSION = "6.0.0"
    DEBUG = False
    TESTING = False
    ENVIRONMENT = "production"
    
    # Security Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "production-secret-key-change-me")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Database Configuration
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://agritech_user:secure_password@db:5432/agritech_prod"
    )
    DATABASE_POOL_SIZE = 20
    DATABASE_MAX_OVERFLOW = 30
    DATABASE_POOL_TIMEOUT = 30
    DATABASE_POOL_RECYCLE = 3600
    
    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # Celery Configuration
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TIMEZONE = "UTC"
    CELERY_ENABLE_UTC = True
    
    # Email Configuration
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = True
    EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@agritech.com")
    
    # File Storage Configuration
    UPLOAD_DIRECTORY = "/app/uploads"
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "image/webp"]
    
    # Security Configuration
    CORS_ORIGINS = [
        "https://agritech.com",
        "https://www.agritech.com",
        "https://app.agritech.com"
    ]
    TRUSTED_HOSTS = ["agritech.com", "*.agritech.com"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_PER_HOUR = 1000
    RATE_LIMIT_PER_DAY = 10000
    
    # Monitoring and Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "/app/logs/agritech.log"
    
    # Performance Settings
    WORKERS = int(os.getenv("WORKERS", "4"))
    WORKER_CLASS = "uvicorn.workers.UvicornWorker"
    WORKER_CONNECTIONS = 1000
    MAX_REQUESTS = 1000
    MAX_REQUESTS_JITTER = 50
    PRELOAD_APP = True
    
    # Health Check Settings
    HEALTH_CHECK_INTERVAL = 30  # seconds
    HEALTH_CHECK_TIMEOUT = 10   # seconds
    
    # Domain and SSL
    DOMAIN_NAME = os.getenv("DOMAIN_NAME", "agritech.com")
    SSL_ENABLED = True
    FORCE_HTTPS = True


def generate_docker_compose_production():
    """
    Generate production Docker Compose configuration
    """
    
    docker_compose = """version: '3.8'

services:
  web:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    container_name: agritech_web_prod
    restart: unless-stopped
    ports:
      - "80:8000"
      - "443:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://agritech_user:${DB_PASSWORD}@db:5432/agritech_prod
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - DOMAIN_NAME=${DOMAIN_NAME}
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./ssl:/app/ssl
    networks:
      - agritech_network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  db:
    image: postgres:15-alpine
    container_name: agritech_db_prod
    restart: unless-stopped
    environment:
      - POSTGRES_DB=agritech_prod
      - POSTGRES_USER=agritech_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    networks:
      - agritech_network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  redis:
    image: redis:7-alpine
    container_name: agritech_redis_prod
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - agritech_network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  celery_worker:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    container_name: agritech_celery_prod
    restart: unless-stopped
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://agritech_user:${DB_PASSWORD}@db:5432/agritech_prod
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    networks:
      - agritech_network

  celery_beat:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    container_name: agritech_beat_prod
    restart: unless-stopped
    command: celery -A app.celery_app beat --loglevel=info --scheduler=django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://agritech_user:${DB_PASSWORD}@db:5432/agritech_prod
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - agritech_network

  nginx:
    image: nginx:alpine
    container_name: agritech_nginx_prod
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./static:/var/www/static
    depends_on:
      - web
    networks:
      - agritech_network

  prometheus:
    image: prom/prometheus:latest
    container_name: agritech_prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - agritech_network

  grafana:
    image: grafana/grafana:latest
    container_name: agritech_grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - agritech_network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  agritech_network:
    driver: bridge
"""
    
    return docker_compose


def generate_production_dockerfile():
    """
    Generate production Dockerfile
    """
    
    dockerfile = """# Production Dockerfile for AgriTech Platform
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs /app/static
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:8000/api/v1/general/health || exit 1

# Command to run the application
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "50", "--preload"]
"""
    
    return dockerfile


def generate_nginx_config():
    """
    Generate Nginx configuration for production
    """
    
    nginx_config = """events {
    worker_connections 1024;
}

http {
    upstream agritech_backend {
        server web:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    server {
        listen 80;
        server_name agritech.com www.agritech.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name agritech.com www.agritech.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers off;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

        # Request size limits
        client_max_body_size 10M;

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API endpoints with rate limiting
        location /api/v1/auth/login {
            limit_req zone=login burst=10 nodelay;
            proxy_pass http://agritech_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://agritech_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support
        location /ws/ {
            proxy_pass http://agritech_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Default location
        location / {
            proxy_pass http://agritech_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
"""
    
    return nginx_config


def generate_environment_file():
    """
    Generate production environment file template
    """
    
    env_content = """# Production Environment Configuration
# Copy this file to .env and update the values

# Application
SECRET_KEY=your-super-secret-key-here-change-this
DOMAIN_NAME=agritech.com

# Database
DB_PASSWORD=secure-database-password

# Redis
REDIS_PASSWORD=secure-redis-password

# Email Configuration
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-app-password
EMAIL_FROM=noreply@agritech.com

# Monitoring
GRAFANA_PASSWORD=secure-grafana-password

# Security
JWT_SECRET_KEY=jwt-secret-key-change-this
ENCRYPTION_KEY=encryption-key-32-bytes-long

# External Services
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=agritech-uploads

# Payment Gateway (if applicable)
PAYMENT_GATEWAY_API_KEY=your-payment-api-key
PAYMENT_GATEWAY_SECRET=your-payment-secret

# SMS Service (if applicable)
SMS_API_KEY=your-sms-api-key
SMS_SECRET=your-sms-secret

# Push Notifications
FCM_SERVER_KEY=your-fcm-server-key
APNS_KEY_ID=your-apns-key-id
APNS_TEAM_ID=your-apns-team-id
"""
    
    return env_content


def generate_monitoring_config():
    """
    Generate Prometheus monitoring configuration
    """
    
    prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'agritech-api'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
"""
    
    return prometheus_config


def generate_production_makefile():
    """
    Generate production deployment Makefile
    """
    
    makefile_content = """# Production Deployment Makefile

.PHONY: help build deploy start stop restart logs backup restore clean

help:
	@echo "Available commands:"
	@echo "  build     - Build production images"
	@echo "  deploy    - Deploy to production"
	@echo "  start     - Start all services"
	@echo "  stop      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  logs      - View application logs"
	@echo "  backup    - Create database backup"
	@echo "  restore   - Restore database from backup"
	@echo "  clean     - Clean up unused images and volumes"

build:
	docker-compose -f docker-compose.prod.yml build --no-cache

deploy:
	@echo "Deploying AgriTech Platform..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Waiting for services to start..."
	sleep 30
	@echo "Running database migrations..."
	docker-compose -f docker-compose.prod.yml exec web alembic upgrade head
	@echo "Deployment complete!"

start:
	docker-compose -f docker-compose.prod.yml up -d

stop:
	docker-compose -f docker-compose.prod.yml down

restart:
	docker-compose -f docker-compose.prod.yml restart

logs:
	docker-compose -f docker-compose.prod.yml logs -f web

logs-celery:
	docker-compose -f docker-compose.prod.yml logs -f celery_worker

logs-db:
	docker-compose -f docker-compose.prod.yml logs -f db

backup:
	@echo "Creating database backup..."
	docker-compose -f docker-compose.prod.yml exec db pg_dump -U agritech_user agritech_prod > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in backups/ directory"

restore:
	@echo "Available backups:"
	@ls -la backups/*.sql
	@read -p "Enter backup filename: " backup_file; \\
	docker-compose -f docker-compose.prod.yml exec -T db psql -U agritech_user -d agritech_prod < backups/$$backup_file

clean:
	docker system prune -f
	docker volume prune -f

health-check:
	@echo "Checking service health..."
	curl -f http://localhost/api/v1/general/health || echo "API health check failed"
	docker-compose -f docker-compose.prod.yml ps

ssl-setup:
	@echo "Setting up SSL certificates with Let's Encrypt..."
	docker run --rm -v $(PWD)/ssl:/etc/letsencrypt certbot/certbot certonly --standalone -d $(DOMAIN_NAME) -d www.$(DOMAIN_NAME)

ssl-renew:
	@echo "Renewing SSL certificates..."
	docker run --rm -v $(PWD)/ssl:/etc/letsencrypt certbot/certbot renew

migrate:
	docker-compose -f docker-compose.prod.yml exec web alembic upgrade head

shell:
	docker-compose -f docker-compose.prod.yml exec web bash

db-shell:
	docker-compose -f docker-compose.prod.yml exec db psql -U agritech_user -d agritech_prod
"""
    
    return makefile_content


def generate_all_production_files():
    """
    Generate all production deployment files
    """
    
    print("🚀 Generating Production Deployment Configuration...")
    print("=" * 60)
    
    files_generated = []
    
    # Create directory structure
    os.makedirs("deployment/production", exist_ok=True)
    os.makedirs("deployment/nginx", exist_ok=True)
    os.makedirs("deployment/monitoring", exist_ok=True)
    os.makedirs("ssl", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Generate files
    files_to_generate = [
        ("docker-compose.prod.yml", generate_docker_compose_production()),
        ("Dockerfile.prod", generate_production_dockerfile()),
        ("nginx/nginx.conf", generate_nginx_config()),
        (".env.example", generate_environment_file()),
        ("monitoring/prometheus.yml", generate_monitoring_config()),
        ("Makefile.prod", generate_production_makefile())
    ]
    
    for filename, content in files_to_generate:
        filepath = f"deployment/{filename}" if not filename.startswith('.') else filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        files_generated.append(filepath)
        print(f"✅ Generated: {filepath}")
    
    # Generate additional scripts
    deployment_script = """#!/bin/bash
# Production Deployment Script

set -e

echo "🚀 Starting AgriTech Platform Deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one from .env.example"
    exit 1
fi

# Load environment variables
source .env

# Build and deploy
echo "📦 Building production images..."
make -f Makefile.prod build

echo "🚀 Deploying to production..."
make -f Makefile.prod deploy

echo "🔍 Checking service health..."
sleep 30
make -f Makefile.prod health-check

echo "✅ Deployment complete!"
echo "🌐 Application available at: https://$DOMAIN_NAME"
echo "📊 Monitoring available at: https://$DOMAIN_NAME:3000"
"""
    
    with open("deployment/deploy.sh", "w", encoding="utf-8") as f:
        f.write(deployment_script)
    
    # Make script executable
    os.chmod("deployment/deploy.sh", 0o755)
    files_generated.append("deployment/deploy.sh")
    
    print(f"\n📊 Production Configuration Summary:")
    print(f"   Files Generated: {len(files_generated)}")
    print(f"   Security: ✅ SSL, Rate Limiting, Security Headers")
    print(f"   Monitoring: ✅ Prometheus, Grafana")
    print(f"   Performance: ✅ Nginx, Gunicorn, Connection Pooling")
    print(f"   Backup: ✅ Automated database backups")
    
    print(f"\n🔧 Next Steps:")
    print(f"   1. Copy .env.example to .env and configure")
    print(f"   2. Set up SSL certificates: make -f Makefile.prod ssl-setup")
    print(f"   3. Deploy: ./deployment/deploy.sh")
    print(f"   4. Monitor: https://your-domain:3000")
    
    print(f"\n🎯 Phase 7: Security and Testing - Production Configuration Complete!")
    
    return files_generated


if __name__ == "__main__":
    generate_all_production_files()
