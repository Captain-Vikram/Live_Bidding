# 🌾 AgriTech Smart Bidding Platform v1.0.0

![FastAPI Platform](https://github.com/kayprogrammer/bidout-auction-v6/blob/main/display/fastapi.png?raw=true)

## 🎯 **Project Overview**

**AgriTech Smart Bidding Platform** is a comprehensive auction and commodity trading platform designed specifically for agricultural markets. It features real-time bidding, ML-powered recommendations, advanced security, and mobile integration.

### **✅ Current Status: Phase 7 Complete - Production Ready**

- **🔐 Security Framework**: Rate limiting, audit logging, input sanitization
- **🧪 Testing Suite**: 100% endpoint coverage with comprehensive tests
- **📚 Documentation**: Complete API documentation with interactive UI
- **🐳 Docker Deployment**: Fully containerized production setup
- **📱 Mobile Ready**: Push notifications and device management

---

## 🚀 **Quick Start**

### **⚡ Fastest Way (Docker Desktop)**

```
1. Open Docker Desktop
2. Find "bidout-auction-v6" project
3. Click "Start"
4. Open http://localhost:8000/docs
```

### **💻 Command Line**

```bash
# Clone repository
git clone git@github.com:kayprogrammer/bidout-auction-v6.git
cd bidout-auction-v6

# Start with Docker
docker-compose up -d

# Access platform
open http://localhost:8000/docs
```

### **📚 Complete Documentation**

**👉 [Full Documentation in /docs folder](./docs/README.md)**

- **[🚀 Server Startup Guide](./docs/SERVER_STARTUP_GUIDE.md)** - Step-by-step startup instructions
- **[⚡ Quick Reference](./docs/QUICK_REFERENCE.md)** - Essential commands and URLs
- **[📡 API Documentation](./docs/API_DOCUMENTATION.md)** - Complete API reference
- **[🏗️ Architecture](./docs/ARCHITECTURE_DIAGRAMS.md)** - System design and diagrams
- **[🐳 Deployment Guide](./docs/DEPLOYMENT_SUMMARY.md)** - Docker deployment details

---

## 🌐 **Access Points**

| Service               | URL                                      | Description            |
| --------------------- | ---------------------------------------- | ---------------------- |
| **API Documentation** | http://localhost:8000/docs               | Interactive Swagger UI |
| **Health Check**      | http://localhost:8000/api/v6/healthcheck | System status          |
| **Database Admin**    | http://localhost:5050                    | pgAdmin interface      |
| **Welcome Page**      | http://localhost:8000/                   | Platform information   |

### **pgAdmin Credentials**

- **Email**: pgadmin4@pgadmin.org
- **Password**: admin

---

## 🏗️ **Architecture & Features**

### **🎯 Core Features**

- **🏃‍♂️ Real-time Bidding**: WebSocket-powered live auctions
- **🤖 ML Recommendations**: Smart commodity suggestions
- **🔐 Enterprise Security**: Rate limiting, audit logs, input sanitization
- **📱 Mobile Integration**: Push notifications and device management
- **💼 Multi-role System**: Farmer, trader, and admin roles
- **📊 Analytics Dashboard**: Performance metrics and reporting

### **🛠️ Tech Stack**

- **Backend**: FastAPI, Python 3.13
- **Database**: PostgreSQL with Alembic migrations
- **Authentication**: JWT with refresh tokens
- **Real-time**: WebSocket connections
- **Deployment**: Docker containerization
- **Testing**: Pytest with 100% endpoint coverage
- **Documentation**: Swagger/OpenAPI

### **📁 Project Structure**

```
bidout-auction-v6/
├── app/                 # Main application code
│   ├── api/            # API routes and schemas
│   ├── core/           # Configuration and security
│   ├── db/             # Database models and managers
│   └── templates/      # Email templates
├── docs/               # 📚 Complete documentation suite
├── initials/           # Database initialization
├── display/            # Platform screenshots
└── Docker files        # Containerization setup
```

---

## 🧪 **Development & Testing**

### **Local Development Setup**

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env  # Configure your settings

# Run database migrations
alembic upgrade heads

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Testing Suite**

```bash
# Run all tests
pytest --disable-warnings -vv

# Test coverage report
pytest --cov=app tests/

# Quick test (using Makefile)
make test
```

---

## 🚀 **Deployment Options**

### **Production Docker (Recommended)**

```bash
# Build and start all services
docker-compose up -d

# View running containers
docker ps

# View logs
docker-compose logs -f
```

### **Alternative Commands**

```bash
# Using Makefile
make build    # Build and start
make test     # Run tests
make clean    # Clean containers
```

---

## 📚 **Documentation Links**

### **External References**

- **[FastAPI Documentation](https://fastapi.tiangolo.com/)** - Framework docs
- **[pgAdmin Documentation](https://pgadmin.org)** - Database admin
- **[Swagger Documentation](https://swagger.io/docs/)** - API documentation

### **Live Demo**

- **[Live API Demo](https://bidout-fastapi.vercel.app/)** - Deployed platform

---

## 📞 **Support & Contributing**

### **Getting Help**

1. **Check Documentation**: Start with `/docs` folder
2. **Review Issues**: Check GitHub issues for known problems
3. **Health Check**: Visit http://localhost:8000/api/v6/healthcheck
4. **Logs**: Use `docker-compose logs -f` for troubleshooting

### **Project Status**

- **✅ Phase 7 Complete**: Security, testing, and documentation
- **🐳 Production Ready**: Full Docker deployment
- **📱 Mobile Ready**: Push notification system implemented
- **🔐 Security Hardened**: Rate limiting and audit logging active

**Need help?** Check the **[Complete Documentation](./docs/README.md)** or **[Quick Reference Guide](./docs/QUICK_REFERENCE.md)**
