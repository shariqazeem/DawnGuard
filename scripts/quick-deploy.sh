#!/bin/bash

# Quick Deploy Script - HTTP Only (No SSL)
# Perfect for hackathons and quick demos

set -e

echo "🚀 DawnGuard Quick Deploy (HTTP Only)"
echo "======================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get server IP
SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')
echo -e "${GREEN}Server IP: ${SERVER_IP}${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is ready${NC}"
echo ""

# Generate keys
echo "🔑 Generating encryption keys..."
SECRET_KEY=$(openssl rand -base64 50)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Create .env
cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=*
ENCRYPTION_KEY=${ENCRYPTION_KEY}
DATABASE_URL=sqlite:///db.sqlite3
OLLAMA_HOST=http://ollama:11434
DEFAULT_MODEL=llama3.2:3b
EOF

echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Create directories
mkdir -p logs staticfiles media

# Stop any running containers
echo "🛑 Stopping old containers..."
docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
echo ""

# Build and start
echo "🐳 Building containers..."
docker-compose -f docker-compose.simple.yml build
echo ""

echo "🚀 Starting services..."
docker-compose -f docker-compose.simple.yml up -d
echo ""

# Wait for services
echo "⏳ Waiting for services..."
sleep 15

# Run migrations
echo "🗄️  Setting up database..."
docker-compose -f docker-compose.simple.yml exec -T web python manage.py migrate
echo ""

# Collect static files
echo "📦 Collecting static files..."
docker-compose -f docker-compose.simple.yml exec -T web python manage.py collectstatic --noinput
echo ""

# Pull LLM model
echo "🤖 Downloading AI model (Llama 3.2 3B)..."
docker-compose -f docker-compose.simple.yml exec -T ollama ollama pull llama3.2:3b || echo -e "${YELLOW}⚠ Model download failed, will retry on first use${NC}"
echo ""

# Test IPFS
echo "🌐 Testing IPFS..."
sleep 5
docker-compose -f docker-compose.simple.yml exec -T ipfs ipfs version || echo -e "${YELLOW}⚠ IPFS needs more time${NC}"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ DawnGuard is LIVE!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📍 Access your app at:"
echo -e "   ${BLUE}http://${SERVER_IP}${NC}"
echo ""
echo "🎯 Features:"
echo "   → Main App: http://${SERVER_IP}"
echo "   → IPFS Vault: http://${SERVER_IP}/vault/dapp/"
echo "   → P2P Knowledge: http://${SERVER_IP}/p2p/dapp/"
echo ""
echo "📊 Useful commands:"
echo "   → View logs: docker-compose -f docker-compose.simple.yml logs -f"
echo "   → Restart: docker-compose -f docker-compose.simple.yml restart"
echo "   → Stop: docker-compose -f docker-compose.simple.yml down"
echo ""
echo -e "${YELLOW}⚠️  Note: Using HTTP (not HTTPS) for quick deployment${NC}"
echo -e "${BLUE}💡 To add HTTPS later, see DEPLOYMENT.md${NC}"
echo ""
