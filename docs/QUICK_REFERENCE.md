# ⚡ AgriTech Platform - Quick Reference

## 🚀 **Start Server (Choose One)**

### **🐳 Docker Desktop (Recommended)**
```
1. Open Docker Desktop
2. Find "bidout-auction-v6"
3. Click "Start"
4. Wait for "Healthy" status
```

### **💻 Command Line**
```powershell
cd "C:\Users\konth\Desktop\project\Idea\Live_Bidding\bidout-auction-v6"
docker-compose up -d
```

### **🔧 Development Script**
```powershell
python start_server.py
```

### **🔍 Debug Mode**
```powershell
python start_server.py --debug
```

---

## 🌐 **Essential URLs**

| Service | URL | Purpose |
|---------|-----|---------|
| **Welcome Page** | http://localhost:8000/ | Platform info |
| **API Docs** | http://localhost:8000/docs | Interactive API |
| **Health Check** | http://localhost:8000/api/v6/healthcheck | Status |
| **Database Admin** | http://localhost:5050/ | pgAdmin |

### **pgAdmin Login**
- **Email**: pgadmin4@pgadmin.org
- **Password**: admin

---

## 🔧 **Common Commands**

### **Container Management**
```powershell
# Check status
docker ps

# View logs
docker-compose logs api

# Stop all
docker-compose down

# Restart
docker-compose restart
```

### **Health Checks**
```powershell
# Test API
curl http://localhost:8000/api/v6/healthcheck

# Check containers
docker-compose ps
```

---

## ⚠️ **Quick Troubleshooting**

### **Port 8000 Already in Use**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID [PID] /F
```

### **Docker Not Starting**
```
1. Restart Docker Desktop
2. Check system resources (RAM/CPU)
3. Try: docker-compose up --build
```

### **API Not Responding**
```
1. Check: docker-compose ps
2. View logs: docker logs bidout-auction-v6-api-1
3. Try health check: http://localhost:8000/api/v6/healthcheck
```

---

## 📚 **Documentation Files**

- **[SERVER_STARTUP_GUIDE.md](./SERVER_STARTUP_GUIDE.md)** - Complete startup guide
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - API reference
- **[DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)** - Docker deployment
- **[ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md)** - System design
- **[PHASE_7_COMPLETION_REPORT.md](./PHASE_7_COMPLETION_REPORT.md)** - Project status

---

## ✅ **Success Checklist**

After starting, verify these work:

- [ ] http://localhost:8000/ shows welcome message
- [ ] http://localhost:8000/docs loads API documentation
- [ ] http://localhost:8000/api/v6/healthcheck returns `{"success":"pong!"}`
- [ ] http://localhost:5050/ loads pgAdmin
- [ ] `docker ps` shows 4 healthy containers

---

**🎯 Need Help?** Check the [SERVER_STARTUP_GUIDE.md](./SERVER_STARTUP_GUIDE.md) for detailed instructions!
