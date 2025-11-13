#!/bin/bash

# CypherVault Setup Script for DAWN Black Box
# This script automates the entire deployment process

set -e  # Exit on error

echo "🔒 DawnGuard - Privacy-First AI Assistant Setup"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check for docker compose (new syntax) or docker-compose (old syntax)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
echo -e "${GREEN}✓ Using: $DOCKER_COMPOSE${NC}"
echo ""

# Domain configuration
echo "🌐 Domain Configuration"
echo "======================="
read -p "Enter your DuckDNS domain (e.g., dawnguard.duckdns.org): " DOMAIN_NAME
read -p "Enter your email for SSL certificate: " SSL_EMAIL

if [ -z "$DOMAIN_NAME" ]; then
    echo -e "${RED}❌ Domain name is required!${NC}"
    exit 1
fi

if [ -z "$SSL_EMAIL" ]; then
    echo -e "${RED}❌ Email is required for SSL certificate!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Domain: $DOMAIN_NAME${NC}"
echo -e "${GREEN}✓ Email: $SSL_EMAIL${NC}"
echo ""

# Generate secure keys
echo "🔑 Generating secure encryption keys..."
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' 2>/dev/null || openssl rand -base64 50)
ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))' 2>/dev/null || openssl rand -base64 32)

# Create .env file
echo "📝 Creating environment configuration..."
cat > .env << EOF
# Django Configuration
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${DOMAIN_NAME},localhost,127.0.0.1

# Encryption
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Ollama
OLLAMA_HOST=http://ollama:11434
DEFAULT_MODEL=llama3.2:3b

# Domain & SSL
DOMAIN_NAME=${DOMAIN_NAME}
SSL_EMAIL=${SSL_EMAIL}
EOF

echo -e "${GREEN}✓ Environment file created${NC}"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs staticfiles media

# Build and start containers
echo "🐳 Building Docker containers..."
$DOCKER_COMPOSE build

echo ""
echo "🚀 Starting services (without SSL first)..."
$DOCKER_COMPOSE up -d web ollama ipfs

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Run migrations
echo "🗄️  Setting up database..."
$DOCKER_COMPOSE exec -T web python manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
$DOCKER_COMPOSE exec -T web python manage.py collectstatic --noinput

# Start Nginx without SSL initially
echo ""
echo "🌐 Starting Nginx (HTTP only for now)..."
$DOCKER_COMPOSE up -d nginx

# Obtain SSL certificate
echo ""
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
echo "   This may take a moment..."

# Wait a moment for nginx to be fully ready
sleep 5

# Check if certificate already exists
if [ ! -d "./certbot/conf/live/${DOMAIN_NAME}" ]; then
    echo "Attempting to obtain SSL certificate..."
    $DOCKER_COMPOSE run --rm --entrypoint certbot certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email ${SSL_EMAIL} \
        --agree-tos \
        --no-eff-email \
        -d ${DOMAIN_NAME}

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ SSL certificate obtained successfully!${NC}"
        # Restart Nginx to apply SSL
        echo "🔄 Restarting Nginx with SSL..."
        $DOCKER_COMPOSE restart nginx
    else
        echo -e "${YELLOW}⚠ SSL certificate failed. Running in HTTP mode.${NC}"
        echo -e "${YELLOW}   Make sure your domain points to this server's IP.${NC}"
        echo -e "${YELLOW}   Common issues:${NC}"
        echo -e "${YELLOW}   - Domain DNS not pointing to this server${NC}"
        echo -e "${YELLOW}   - Port 80 not accessible from internet${NC}"
        echo -e "${YELLOW}   - Firewall blocking certbot${NC}"
        echo ""
        echo -e "${YELLOW}   You can retry SSL later with:${NC}"
        echo -e "${YELLOW}   $DOCKER_COMPOSE run --rm --entrypoint certbot certbot certonly --webroot --webroot-path=/var/www/certbot --email ${SSL_EMAIL} --agree-tos -d ${DOMAIN_NAME}${NC}"
        echo -e "${YELLOW}   Then restart nginx: $DOCKER_COMPOSE restart nginx${NC}"
    fi
else
    echo -e "${GREEN}✓ SSL certificate already exists${NC}"
    # Restart Nginx to ensure it's using SSL
    echo "🔄 Restarting Nginx with SSL..."
    $DOCKER_COMPOSE restart nginx
fi

# Start certbot renewal service
echo "🤖 Starting SSL auto-renewal service..."
$DOCKER_COMPOSE up -d certbot

# Pull LLM model
echo ""
echo "🤖 Downloading AI model (this may take a few minutes)..."
echo "   Model: Llama 3.2 3B"
$DOCKER_COMPOSE exec ollama ollama pull llama3.2:3b

# Wait for IPFS to be ready
echo ""
echo "🌐 Setting up IPFS decentralized storage..."
sleep 5

# Test IPFS connection
echo "   Testing IPFS connection..."
if $DOCKER_COMPOSE exec -T web curl -s -o /dev/null -w "%{http_code}" http://ipfs:5001/api/v0/version | grep -q "200"; then
    echo -e "${GREEN}   ✓ IPFS is ready${NC}"
else
    echo -e "${YELLOW}   ⚠ IPFS may need a moment to start${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ DawnGuard TRUE DAPP is ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📍 Access your private AI assistant at:"
echo -e "   → ${BLUE}https://${DOMAIN_NAME}${NC}"
echo -e "   → ${BLUE}http://${DOMAIN_NAME}${NC} (redirects to HTTPS)"
echo ""
echo "🔐 Your encryption key has been saved to .env"
echo "   Keep this file secure!"
echo ""
echo "📊 View logs with:"
echo "   → $DOCKER_COMPOSE logs -f"
echo ""
echo "🛑 Stop services with:"
echo "   → $DOCKER_COMPOSE down"
echo ""
echo "🎯 Next steps:"
echo "   1. Open https://${DOMAIN_NAME} in your browser"
echo "   2. Create an account"
echo "   3. Start chatting with your private AI"
echo ""
echo "🚀 TRUE DAPP Features:"
echo "   → IPFS Vault: https://${DOMAIN_NAME}/vault/dapp/"
echo "   → P2P Knowledge: https://${DOMAIN_NAME}/p2p/dapp/"
echo "   → Gun.js P2P Database: Automatically syncing"
echo "   → Solana Blockchain: Connect Phantom wallet"
echo ""
echo -e "${YELLOW}⚠️  Remember: Your data never leaves this server!${NC}"
echo -e "${GREEN}✨ TRUE DECENTRALIZATION: IPFS + Gun.js + Solana${NC}"
echo -e "${GREEN}🔒 SSL Certificate: Auto-renewing every 12 hours${NC}"
echo ""