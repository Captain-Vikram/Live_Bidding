#!/bin/bash
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
