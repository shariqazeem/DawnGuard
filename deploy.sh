#!/bin/bash

# CypherVault Deployment Script for Ubuntu Server
# Usage: ./deploy.sh

set -e  # Exit on error

echo "🚀 Starting CypherVault Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}⚠️  Please don't run as root. Use a regular user with docker permissions.${NC}"
   exit 1
fi

# Step 1: Check dependencies
echo -e "${YELLOW}📋 Checking dependencies...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}❌ Docker is not installed${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}❌ Docker Compose is not installed${NC}"; exit 1; }
echo -e "${GREEN}✅ Dependencies OK${NC}"

# Step 2: Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p staticfiles
mkdir -p media
echo -e "${GREEN}✅ Directories created${NC}"

# Step 3: Generate secure keys if .env doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}🔐 Generating .env file...${NC}"
    SECRET_KEY=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-50)
    ENCRYPTION_KEY=$(openssl rand -base64 32)
    
    cat > .env << EOF
# Django Configuration
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=*

# Encryption
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Ollama
OLLAMA_HOST=http://ollama:11434
DEFAULT_MODEL=llama3.2:3b
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Step 4: Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✅ Containers stopped${NC}"

# Step 5: Build and start containers
echo -e "${YELLOW}🏗️  Building Docker images...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✅ Images built${NC}"

echo -e "${YELLOW}🚀 Starting containers...${NC}"
docker-compose up -d
echo -e "${GREEN}✅ Containers started${NC}"

# Step 6: Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Step 7: Pull Ollama model
echo -e "${YELLOW}🤖 Pulling Ollama model (this may take a few minutes)...${NC}"
docker-compose exec -T ollama ollama pull llama3.2:3b || {
    echo -e "${YELLOW}⚠️  Failed to pull model. You can do this manually later:${NC}"
    echo -e "${YELLOW}   docker-compose exec ollama ollama pull llama3.2:3b${NC}"
}
echo -e "${GREEN}✅ Ollama model ready${NC}"

# Step 8: Run migrations
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
docker-compose exec -T web python manage.py migrate --noinput
echo -e "${GREEN}✅ Migrations complete${NC}"

# Step 9: Collect static files
echo -e "${YELLOW}📦 Collecting static files...${NC}"
docker-compose exec -T web python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Static files collected${NC}"

# Step 10: Create superuser (optional)
echo -e "${YELLOW}👤 Create superuser? (y/n)${NC}"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    docker-compose exec web python manage.py createsuperuser
fi

# Step 11: Get server IP
SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

# Step 12: Setup firewall
echo -e "${YELLOW}🔥 Configure firewall? (y/n)${NC}"
read -r setup_firewall
if [ "$setup_firewall" = "y" ]; then
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 80/tcp    # HTTP
    sudo ufw allow 443/tcp   # HTTPS
    sudo ufw --force enable
    echo -e "${GREEN}✅ Firewall configured${NC}"
fi

# Final output
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║           🎉 CypherVault Deployed Successfully! 🎉         ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}📍 Access your app at:${NC}"
echo -e "   ${YELLOW}http://${SERVER_IP}${NC}"
echo -e "   ${YELLOW}http://localhost${NC} (if on server)"
echo ""
echo -e "${GREEN}🔧 Useful commands:${NC}"
echo -e "   ${YELLOW}docker-compose logs -f${NC}          # View logs"
echo -e "   ${YELLOW}docker-compose restart${NC}          # Restart services"
echo -e "   ${YELLOW}docker-compose down${NC}             # Stop services"
echo -e "   ${YELLOW}docker-compose exec web python manage.py createsuperuser${NC}"
echo ""
echo -e "${GREEN}🤖 Ollama commands:${NC}"
echo -e "   ${YELLOW}docker-compose exec ollama ollama list${NC}    # List models"
echo -e "   ${YELLOW}docker-compose exec ollama ollama pull llama3.2:3b${NC}"
echo ""
echo -e "${GREEN}🔐 Important:${NC}"
echo -e "   - Your SECRET_KEY and ENCRYPTION_KEY are in .env"
echo -e "   - Keep .env file secure and never commit it to git"
echo -e "   - Backup your database regularly: db.sqlite3"
echo ""
echo -e "${YELLOW}⚠️  Note: Solana wallet will work, but you may need to:${NC}"
echo -e "   1. Use http://${SERVER_IP} (not https) in Phantom wallet"
echo -e "   2. Add this URL to Phantom's approved sites"
echo ""