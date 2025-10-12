#!/bin/bash

# CypherVault Setup Script for DAWN Black Box
# This script automates the entire deployment process

set -e  # Exit on error

echo "🔒 CypherVault - Privacy-First AI Assistant Setup"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
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
ALLOWED_HOSTS=*

# Encryption
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Ollama
OLLAMA_HOST=http://ollama:11434
DEFAULT_MODEL=llama3.2:3b
EOF

echo -e "${GREEN}✓ Environment file created${NC}"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs staticfiles media

# Build and start containers
echo "🐳 Building Docker containers..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Run migrations
echo "🗄️  Setting up database..."
docker-compose exec -T web python manage.py migrate

# Collect static files
echo "📦 Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

# Pull LLM model
echo ""
echo "🤖 Downloading AI model (this may take a few minutes)..."
echo "   Model: Llama 3.2 3B"
docker-compose exec ollama ollama pull llama3.2:3b

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ CypherVault is ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📍 Access your private AI assistant at:"
echo "   → http://localhost:8000"
echo ""
echo "🔐 Your encryption key has been saved to .env"
echo "   Keep this file secure!"
echo ""
echo "📊 View logs with:"
echo "   → docker-compose logs -f"
echo ""
echo "🛑 Stop services with:"
echo "   → docker-compose down"
echo ""
echo "🎯 Next steps:"
echo "   1. Open http://localhost:8000 in your browser"
echo "   2. Create an account"
echo "   3. Start chatting with your private AI"
echo ""
echo -e "${YELLOW}⚠️  Remember: Your data never leaves this device!${NC}"
echo ""