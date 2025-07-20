# 🌾 AgriTech Platform - Server Startup Guide

## 🎯 **Complete Guide to Starting Your AgriTech Platform**

This guide provides step-by-step instructions for starting the AgriTech Smart Bidding Platform using the recommended methods.

---

## 📋 **Prerequisites**

### **Required Software**
- ✅ **Docker Desktop** (Recommended)
- ✅ **Git** (for cloning repository)
- ✅ **Python 3.11+** (for local development)
- ✅ **PowerShell/Command Prompt** (Windows)

### **System Requirements**
- **RAM**: Minimum 4GB, Recommended 8GB
- **Storage**: 2GB free space
- **OS**: Windows 10/11, macOS, or Linux
- **Network**: Internet connection for initial setup

---

## 🚀 **Method 1: Docker Desktop (Recommended)**

This is the **simplest and most reliable** method for running the AgriTech Platform.

### **Step 1: Open Docker Desktop**
```
1. Launch Docker Desktop application
2. Wait for Docker to fully start (green status)
3. Ensure Docker engine is running
```

### **Step 2: Navigate to Project**
```
1. Open Docker Desktop
2. Go to "Containers" tab
3. Look for "bidout-auction-v6" project
```

### **Step 3: Start Services**
```
1. Click the "Start" button next to bidout-auction-v6
2. Wait for all containers to show "Running" status
3. Verify health status shows "Healthy"
```

### **Step 4: Access the Platform**
Once all containers are running:

```
✅ API Server: http://localhost:8000
✅ API Documentation: http://localhost:8000/docs
✅ Interactive API Explorer: http://localhost:8000/redoc
✅ Database Admin: http://localhost:5050
   └─ Email: pgadmin4@pgadmin.org
   └─ Password: admin
✅ Health Check: http://localhost:8000/api/v6/healthcheck
```

### **Step 5: Verify Everything is Working**
```bash
# Open browser and test these URLs:
http://localhost:8000/                    # Welcome message
http://localhost:8000/docs               # API documentation
http://localhost:8000/api/v6/healthcheck # Health check
```

---

## ⚡ **Method 2: Command Line (Docker)**

For users who prefer command-line interface.

### **Step 1: Open Terminal**
```powershell
# Open PowerShell as Administrator
# Navigate to project directory
cd "C:\Users\konth\Desktop\project\Idea\Live_Bidding\bidout-auction-v6"
```

### **Step 2: Start All Services**
```powershell
# Start all services in background
docker-compose up -d

# OR start with logs visible
docker-compose up
```

### **Step 3: Monitor Status**
```powershell
# Check container status
docker-compose ps

# View logs
docker-compose logs api
docker-compose logs db
```

### **Step 4: Stop Services (when done)**
```powershell
# Stop all services
docker-compose down

# Stop and remove volumes (full cleanup)
docker-compose down -v
```

---

## 🔧 **Method 3: Using start_server.py (Hybrid)**

This method starts Docker services and runs the API locally for development.

### **Step 1: Run Startup Script**
```powershell
# Navigate to project directory
cd "C:\Users\konth\Desktop\project\Idea\Live_Bidding\bidout-auction-v6"

# Run the startup script
python start_server.py
```

### **Step 2: What Happens Automatically**
```
1. 🐳 Checks Docker availability
2. 🗄️ Starts PostgreSQL database
3. ⚡ Starts Redis cache
4. 🔧 Starts pgAdmin interface
5. ⏳ Waits 10 seconds for initialization
6. 🚀 Starts FastAPI application locally
```

### **Step 3: Access Points**
```
✅ API Server: http://localhost:8000
✅ Database Admin: http://localhost:5050
✅ Redis Cache: localhost:6379
```

---

## 🔍 **Method 4: Debug Mode (Development Only)**

For troubleshooting and local development without Docker dependencies.

### **Step 1: Start Debug Server**
```powershell
# Start minimal server for debugging
python start_server.py --debug

# OR
python start_server.py --minimal
```

### **Step 2: What This Does**
```
- Runs minimal FastAPI server
- No Docker dependencies
- Limited functionality
- Port 8000 (or 8001 to avoid conflicts)
- Useful for testing imports and basic functionality
```

---

## 🎯 **Recommended Startup Sequence**

### **For Daily Development:**
```
1. Open Docker Desktop
2. Start "bidout-auction-v6" project
3. Open http://localhost:8000/docs
4. Begin development work
```

### **For Testing/Debugging:**
```
1. Use Method 3 (start_server.py)
2. Make code changes
3. Server auto-reloads
4. Test in browser
```

### **For Production:**
```
1. Use Method 2 (docker-compose)
2. Add -d flag for background
3. Monitor with docker logs
4. Use health checks
```

---

## 🔄 **Service Management**

### **Starting Services**
```powershell
# Docker Desktop: Click "Start" button
# Command Line: 
docker-compose up -d

# Script:
python start_server.py
```

### **Stopping Services**
```powershell
# Docker Desktop: Click "Stop" button
# Command Line:
docker-compose down

# Script: Ctrl+C (then auto-cleanup)
```

### **Restarting Services**
```powershell
# Full restart
docker-compose restart

# Rebuild and restart
docker-compose up --build -d
```

### **Viewing Logs**
```powershell
# All services
docker-compose logs

# Specific service
docker logs bidout-auction-v6-api-1
docker logs bidout-auction-v6-db-1
```

---

## 🌐 **Access Points & URLs**

### **Main Platform**
| Service | URL | Description |
|---------|-----|-------------|
| **API Root** | http://localhost:8000/ | Welcome page & basic info |
| **Health Check** | http://localhost:8000/api/v6/healthcheck | System status |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **ReDoc** | http://localhost:8000/redoc | Alternative documentation |

### **Admin Interfaces**
| Service | URL | Credentials |
|---------|-----|------------|
| **pgAdmin** | http://localhost:5050/ | pgadmin4@pgadmin.org / admin |
| **Redis** | localhost:6379 | Direct connection |

### **API Endpoints**
| Endpoint | Purpose |
|----------|---------|
| `/api/v6/general/site-detail` | Site information |
| `/api/v6/auth/register` | User registration |
| `/api/v6/auth/login` | User authentication |
| `/api/v6/commodities/` | Commodity listings |
| `/api/v6/recommendations/market-overview` | ML recommendations |

---

## ⚠️ **Troubleshooting**

### **Common Issues**

#### **Docker Desktop Not Starting**
```
1. Check Docker Desktop is installed
2. Restart Docker Desktop
3. Check system resources (RAM/CPU)
4. Try: docker-compose up --build
```

#### **Port Already in Use**
```
Error: Port 8000 is already in use

Solutions:
1. Stop other services using port 8000
2. Use different port: docker-compose -p alt up
3. Kill process: netstat -ano | findstr :8000
```

#### **Database Connection Error**
```
1. Wait longer for database startup (30 seconds)
2. Check database container: docker logs bidout-auction-v6-db-1
3. Restart database: docker-compose restart db
```

#### **API Not Responding**
```
1. Check container status: docker-compose ps
2. View API logs: docker logs bidout-auction-v6-api-1
3. Verify health: http://localhost:8000/api/v6/healthcheck
```

### **Debug Commands**
```powershell
# Check all containers
docker ps

# Check specific container health
docker inspect bidout-auction-v6-api-1

# View real-time logs
docker-compose logs -f api

# Access container shell
docker exec -it bidout-auction-v6-api-1 bash
```

---

## 📊 **Verification Checklist**

After starting the server, verify these work:

- [ ] **Welcome Page**: http://localhost:8000/ shows AgriTech welcome
- [ ] **Health Check**: http://localhost:8000/api/v6/healthcheck returns `{"success":"pong!"}`
- [ ] **API Docs**: http://localhost:8000/docs loads Swagger UI
- [ ] **Database**: pgAdmin at http://localhost:5050/ is accessible
- [ ] **Site Details**: http://localhost:8000/api/v6/general/site-detail returns data
- [ ] **All Containers**: `docker ps` shows 4 healthy containers

---

## 💡 **Pro Tips**

### **For Development**
```
✅ Use Docker Desktop for simplicity
✅ Keep containers running between sessions
✅ Use /docs for API testing
✅ Monitor logs for errors
✅ Use health check endpoint regularly
```

### **For Performance**
```
✅ Allocate sufficient RAM to Docker (4GB+)
✅ Use SSD storage for better performance
✅ Close unnecessary applications
✅ Monitor container resource usage
```

### **For Debugging**
```
✅ Use --debug mode for import issues
✅ Check container logs first
✅ Verify network connectivity
✅ Test endpoints individually
✅ Use curl or Postman for API testing
```

---

## 🎯 **Quick Start Commands**

### **Fastest Way (Docker Desktop)**
```
1. Open Docker Desktop
2. Click "Start" on bidout-auction-v6
3. Open http://localhost:8000/docs
```

### **Command Line Quick Start**
```powershell
cd "C:\Users\konth\Desktop\project\Idea\Live_Bidding\bidout-auction-v6"
docker-compose up -d
start http://localhost:8000/docs
```

### **Development Quick Start**
```powershell
cd "C:\Users\konth\Desktop\project\Idea\Live_Bidding\bidout-auction-v6"
python start_server.py
# Server starts automatically, opens browser
```

---

## 📞 **Support**

### **If You Need Help**
1. Check the troubleshooting section above
2. View container logs: `docker-compose logs`
3. Verify system requirements
4. Try debug mode: `python start_server.py --debug`
5. Restart Docker Desktop and try again

### **Additional Resources**
- **API Documentation**: Available at `/docs` when server is running
- **Architecture Diagrams**: See `docs/ARCHITECTURE_DIAGRAMS.md`
- **Deployment Guide**: See `docs/DEPLOYMENT_SUMMARY.md`
- **Phase 7 Report**: See `docs/PHASE_7_COMPLETION_REPORT.md`

---

**🌾 Happy Development with AgriTech Platform!**

**Last Updated**: July 20, 2025  
**Platform Version**: 6.0.0  
**Recommended Method**: Docker Desktop
