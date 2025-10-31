#!/bin/bash

# Restart web container properly to reload Django settings

echo "🔄 Restarting web container..."

# Stop web container
docker-compose -f docker-compose.simple.yml stop web

# Remove web container (to clear any cached settings)
docker-compose -f docker-compose.simple.yml rm -f web

# Start web container fresh
docker-compose -f docker-compose.simple.yml up -d web

# Wait for it to be ready
echo "⏳ Waiting for web container to start..."
sleep 5

# Check status
docker-compose -f docker-compose.simple.yml ps web

echo "✅ Web container restarted!"
echo ""
echo "Test kids-ai chat now at: https://YOUR_SERVER_IP/kids-ai/"
