# 🚀 AgriTech Platform - Deployment & Setup Guide

## Overview
Complete guide for deploying and running the AgriTech Smart Bidding Platform in various environments.

## 📋 Prerequisites

### Required Software
- Docker Desktop (Recommended)
- Git 
- Python 3.11+
- Node.js 18+ (for frontend)
- PostgreSQL 14+ (for local setup)

### System Requirements
- RAM: Minimum 4GB, Recommended 8GB
- Storage: 2GB free space
- OS: Windows 10/11, macOS, or Linux
- Network: Internet connection

## 🐳 Docker Deployment (Recommended)

### 1. Production Deployment
```bash
# Clone repository
git clone https://github.com/Captain-Vikram/Live_Bidding.git
cd Live_Bidding/bidout-auction-v6

# Build and start production containers
docker-compose -f deployment/docker-compose.prod.yml up -d

# Verify deployment
docker-compose -f deployment/docker-compose.prod.yml ps
```

### 2. Development Setup
```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🛠️ Manual Deployment

### 1. Database Setup
```bash
# Create PostgreSQL database
createdb bidout_auction_db

# Run migrations
alembic upgrade head
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Start Services
```bash
# Start Redis (required for real-time features)
redis-server

# Start API server
python start_server.py
# Or
uvicorn app.main:app --reload
```

## 🔍 Health Checks

### API Health Check
- http://localhost:8000/api/v6/healthcheck
- http://localhost:8000/api/v6/redis-health

### Database Admin
- http://localhost:5050 (pgAdmin)
- Default credentials in `.env`

## 🔐 Initial Setup

### Default Credentials
```
Admin User:
- Email: admin@agritech.com
- Password: admin123

Test User:
- Email: farmer@agritech.com
- Password: farmer123
```

### Database Admin Access
```
pgAdmin:
- Email: pgadmin4@pgadmin.org
- Password: admin
```

## 📊 Monitoring

### Prometheus Metrics
- Available at `/metrics`
- Dashboard at http://localhost:9090

### Application Logs
- Location: `logs/app.log`
- Docker: `docker-compose logs -f app`

## 🔄 Common Operations

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose up -d --build
```

### Backup Database
```bash
# Export database
pg_dump -U postgres bidout_auction_db > backup.sql

# Restore if needed
psql -U postgres bidout_auction_db < backup.sql
```

## 🚨 Troubleshooting

### CORS Issues
If experiencing CORS errors:
1. Verify allowed origins in `app/core/config.py`
2. Check frontend URL matches CORS settings
3. Ensure proper headers in frontend requests

### Redis Connection
If Redis connection fails:
1. Check Redis service is running
2. Verify Redis URL in environment
3. Test with `redis-cli ping`

## 📚 Additional Resources

- [API Documentation](./API_DOCUMENTATION.md)
- [Frontend Integration](./FRONTEND_INTEGRATION.md)
- [Database Schema](./DATABASE_SCHEMA.md)
