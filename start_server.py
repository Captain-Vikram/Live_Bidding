#!/usr/bin/env python3
"""
AgriTech Platform Startup Script
================================

Complete startup script for the AgriTech platform including:
- FastAPI application
- Celery workers for background tasks
- pgAdmin web interface
- Docker containers management
"""

import uvicorn
import os
import subprocess
import time
import threading
import signal
import sys
from pathlib import Path

def check_docker_compose():
    """Check if docker-compose is available"""
    try:
        subprocess.run(["docker-compose", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def start_docker_services():
    """Start Docker services including database, Redis, and pgAdmin"""
    print("🐳 Starting Docker services...")
    
    if not check_docker_compose():
        print("❌ Error: docker-compose not found. Please install Docker Desktop.")
        return False
    
    try:
        # Start all Docker services
        result = subprocess.run(
            ["docker-compose", "up", "-d", "db", "redis", "pgadmin"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ Docker services started successfully!")
            print("   - PostgreSQL Database: Running")
            print("   - Redis Cache: Running") 
            print("   - pgAdmin: http://localhost:5050")
            return True
        else:
            print(f"❌ Error starting Docker services: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Docker services: {e}")
        return False

def wait_for_services():
    """Wait for services to be ready"""
    print("⏳ Waiting for services to initialize...")
    time.sleep(10)  # Give services time to start up
    print("✅ Services should be ready!")

def start_celery_worker():
    """Start Celery worker in background"""
    def run_worker():
        print("🔧 Starting Celery worker...")
        try:
            subprocess.run([
                "celery", "-A", "app.core.celery_app", "worker", 
                "--loglevel=info", "--concurrency=2"
            ], cwd=Path(__file__).parent)
        except Exception as e:
            print(f"❌ Celery worker error: {e}")
    
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    time.sleep(3)  # Give worker time to start
    print("✅ Celery worker started!")

def start_celery_beat():
    """Start Celery beat scheduler in background"""
    def run_beat():
        print("⏰ Starting Celery beat scheduler...")
        try:
            subprocess.run([
                "celery", "-A", "app.core.celery_app", "beat", 
                "--loglevel=info"
            ], cwd=Path(__file__).parent)
        except Exception as e:
            print(f"❌ Celery beat error: {e}")
    
    beat_thread = threading.Thread(target=run_beat, daemon=True)
    beat_thread.start()
    time.sleep(2)  # Give beat time to start
    print("✅ Celery beat scheduler started!")

def start_minimal_server():
    """Start minimal FastAPI server without Docker dependencies"""
    print("🔍 Starting minimal server (no Docker dependencies)...")
    try:
        uvicorn.run(
            "app.minimal_main:app",  # Use minimal app
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="debug"
        )
    except Exception as e:
        print(f"❌ Minimal server error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Start the complete AgriTech platform"""
    
    # Set the working directory to the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check for debug mode
    debug_mode = "--debug" in sys.argv or "--minimal" in sys.argv
    
    if debug_mode:
        print("🔍 DEBUG MODE - Starting minimal server without Docker...")
        start_minimal_server()
        return
    
    print("🌾 Starting AgriTech Platform...")
    print("=" * 60)
    print("📍 Project root:", project_root)
    print()
    
    # Start Docker services first
    if not start_docker_services():
        print("❌ Failed to start Docker services.")
        print("🔍 Try minimal mode: python start_server.py --minimal")
        return
    
    # Wait for services to be ready
    wait_for_services()
    
    # Skip Celery for now to get basic server running
    print("\n⚠️  Celery temporarily disabled - starting basic server")
    # Start Celery background task system
    # print("\n🔧 Starting Background Task System...")
    # start_celery_worker()
    # start_celery_beat()
    
    print()
    print("🚀 Starting FastAPI Application...")
    print("🌐 API Server: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔧 Alternative docs: http://localhost:8000/redoc")
    print("🗄️ pgAdmin Interface: http://localhost:5050")
    print("   - Email: pgadmin4@pgadmin.org")
    print("   - Password: admin")
    print("⚠️  Background Tasks: Temporarily disabled")
    print("📊 Price Tracking: Available via API")
    print("🤖 ML Recommendations: Available via API")
    print("📧 Notifications: Manual trigger available")
    print()
    print("=" * 60)
    print("🌾 AgriTech Platform Ready!")
    print("=" * 60)
    
    # Start the FastAPI server
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",  # Changed from 0.0.0.0 to localhost
            port=8000,
            reload=True,  # Auto-reload on code changes
            log_level="debug",  # Changed to debug for more info
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down AgriTech Platform...")
        print("🐳 Stopping Docker services...")
        subprocess.run(["docker-compose", "down"], cwd=project_root)
        print("✅ AgriTech Platform stopped successfully!")

if __name__ == "__main__":
    main()
