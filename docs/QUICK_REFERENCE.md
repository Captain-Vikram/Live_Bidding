# ⚡ Quick Reference Guide

## 🚀 **Essential Commands**

### **Start Server**
```bash
# Docker (Recommended - with Redis)
docker-compose up -d

# Development (without Redis)
python start_server.py

# Direct (without Redis)
uvicorn app.main:app --reload
```

### **Stop Server**
```bash
# Docker
docker-compose down

# Direct
Ctrl+C
```

---

## 🌐 **Key URLs**

| Service | URL |
|---------|-----|
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/api/v6/healthcheck |
| Database Admin | http://localhost:5050 |
| Redis Health | http://localhost:8000/api/v6/redis-health |

---

## 🔑 **Default Credentials**

**pgAdmin (Database)**:
- Email: `pgadmin4@pgadmin.org`
- Password: `admin`

**Test User**:
- Email: `farmer@agritech.com`  
- Password: `farmer123`

---

## 📊 **Database Quick Access**

```bash
# Connect to database
docker exec -it postgres psql -U agritech_user -d agritech_db

# Common queries
\dt                    # List tables
\d users              # Describe users table
SELECT COUNT(*) FROM listings;  # Count listings
```

---

## 🔧 **Common Issues & Solutions**

### **Port 8000 in use**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### **Database not starting**
```bash
docker-compose restart postgres
docker-compose logs postgres
```

### **Redis connection error**
```bash
docker-compose restart redis
```

### **Permission errors**
```bash
# Run as administrator
# Or check Docker Desktop is running
```

---

## 📦 **Quick Commands**

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest --disable-warnings -vv

# Database migration
alembic upgrade heads

# Create new migration
alembic revision --autogenerate -m "description"

# Check API health
curl http://localhost:8000/api/v6/healthcheck

# View logs
docker-compose logs -f
```

---

## 🎯 **API Testing**

### **Authentication**
```bash
# Register user
curl -X POST "http://localhost:8000/api/v6/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","first_name":"Test","last_name":"User","role":"FARMER","terms_agreement":true}'

# Login
curl -X POST "http://localhost:8000/api/v6/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### **Listings**
```bash
# Get listings
curl "http://localhost:8000/api/v6/listings"

# Create listing (requires auth token)
curl -X POST "http://localhost:8000/api/v6/listings" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Wheat","description":"Premium wheat","category_id":"CATEGORY_UUID","price":100,"quantity":50,"unit":"TONNES","closing_date":"2025-08-01T18:00:00Z"}'
```

---

## 📱 **Development Workflow**

1. **Start Services**: `docker-compose up -d`
2. **Check Health**: Visit health check URL
3. **View Docs**: Open interactive API docs
4. **Test APIs**: Use Swagger UI or curl
5. **Check Logs**: `docker-compose logs -f`
6. **Stop Services**: `docker-compose down`

---

## 🆘 **Emergency Commands**

```bash
# Nuclear option - reset everything
docker-compose down -v
docker system prune -f
docker-compose up -d --build

# Reset database only
docker-compose down
docker volume rm bidout-auction-v6_postgres_data
docker-compose up -d

# View all containers
docker ps -a

# Clean up
docker system prune -f
```

---

## 📞 **Support Resources**

- **Full Documentation**: [docs/README.md](./README.md)
- **Database Schema**: [docs/DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)  
- **API Documentation**: [docs/API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Frontend Guide**: [docs/FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md)

**Quick Help**: Check health endpoints first, then logs, then restart services.
