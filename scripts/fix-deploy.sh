#!/bin/bash

# Fix current broken deployment and switch to HTTP-only mode

echo "🔧 Fixing DawnGuard Deployment..."
echo ""

# Stop all containers
echo "🛑 Stopping all containers..."
docker-compose down 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true

# Remove old containers
echo "🧹 Cleaning up..."
docker-compose rm -f 2>/dev/null || true

# Switch to simple deployment
echo "🚀 Starting simple HTTP deployment..."
./scripts/quick-deploy.sh
