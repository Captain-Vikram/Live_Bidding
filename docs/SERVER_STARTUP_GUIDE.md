# 🚀 Server Startup Guide

## 🎯 **Quick Start Options**

Choose your preferred method to start the AgriTech Platform:

### **⚡ Method 1: Docker Desktop (Recommended)**
1. Open Docker Desktop
2. Navigate to "Containers/Apps"
3. Find "bidout-auction-v6"
4. Click "Start"
5. Access: http://localhost:8000/docs

### **💻 Method 2: Command Line**
```bash
# Navigate to project directory
cd C:\Users\konth\Desktop\project\Idea\Live_Bidding\bidout-auction-v6

# Start all services
docker-compose up -d

# Access the platform
open http://localhost:8000/docs
```

### **🔧 Method 3: Development Mode**
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade heads

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **🐛 Method 4: Debug Mode**
```bash
# Use the startup script
python start_server.py

# Or use the Makefile
make dev
```

---

## 🌐 **Access Points**

| Service | URL | Credentials |
|---------|-----|-------------|
| **API Documentation** | http://localhost:8000/docs | - |
| **API Alternative** | http://localhost:8000/redoc | - |
| **Health Check** | http://localhost:8000/api/v6/healthcheck | - |
| **Database Admin** | http://localhost:5050 | pgadmin4@pgadmin.org / admin |
| **Redis Admin** | http://localhost:8001 | - |

---

## ✅ **Verification Checklist**

After startup, verify these endpoints:

- [ ] ✅ **API Health**: http://localhost:8000/api/v6/healthcheck
- [ ] ✅ **Redis Health**: http://localhost:8000/api/v6/redis-health  
- [ ] ✅ **Database**: http://localhost:5050 (pgAdmin)
- [ ] ✅ **Documentation**: http://localhost:8000/docs
- [ ] ✅ **Welcome Page**: http://localhost:8000/

---

## 🔧 **Troubleshooting**

### **Port Already in Use**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID_NUMBER> /F

# Or use different port
uvicorn app.main:app --port 8001
```

### **Database Connection Issues**
```bash
# Check PostgreSQL status
docker-compose ps

# Restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### **Redis Connection Issues**
```bash
# Restart Redis
docker-compose restart redis

# Check Redis logs
docker-compose logs redis
```

---

## 📋 **Environment Configuration**

Essential environment variables in `.env`:

```bash
# Database
POSTGRES_USER=agritech_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=agritech_db

# Security
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Email (for notifications)
MAIL_SENDER_EMAIL=your-email@gmail.com
MAIL_SENDER_PASSWORD=your-app-password

# External Services (optional)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
```

---

## 🎯 **Next Steps**

1. **Test API**: Visit http://localhost:8000/docs
2. **Create Admin**: Use the interactive docs to register
3. **Add Sample Data**: Run `python initials/initial_data.py`
4. **Frontend Development**: See [Frontend Integration Guide](./FRONTEND_INTEGRATION.md)
5. **Mobile Setup**: See [Mobile Integration Guide](./MOBILE_INTEGRATION.md)

**Need help?** Check the [complete documentation](./README.md) or [troubleshooting guide](./TROUBLESHOOTING.md).
