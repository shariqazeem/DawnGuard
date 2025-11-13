#!/bin/bash

# Manual SSL Certificate Obtainer Script
# Use this if the initial setup.sh failed to obtain certificates

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔐 Manual SSL Certificate Setup"
echo "==============================="
echo ""

# Check for docker compose (new syntax) or docker-compose (old syntax)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}❌ Docker Compose is not installed.${NC}"
    exit 1
fi

# Load from .env file
if [ -f ".env" ]; then
    export $(grep DOMAIN_NAME .env | xargs)
    export $(grep SSL_EMAIL .env | xargs)
else
    echo -e "${YELLOW}⚠ .env file not found.${NC}"
fi

# Prompt for domain and email if not set
if [ -z "$DOMAIN_NAME" ]; then
    read -p "Enter your domain name: " DOMAIN_NAME
fi

if [ -z "$SSL_EMAIL" ]; then
    read -p "Enter your email for SSL certificate: " SSL_EMAIL
fi

echo -e "Domain: ${BLUE}${DOMAIN_NAME}${NC}"
echo -e "Email: ${BLUE}${SSL_EMAIL}${NC}"
echo ""

# Pre-flight checks
echo "Running pre-flight checks..."

# 1. Check if nginx is running
if ! $DOCKER_COMPOSE ps nginx | grep -q "Up"; then
    echo -e "${RED}❌ Nginx is not running. Starting it now...${NC}"
    $DOCKER_COMPOSE up -d nginx
    sleep 5
fi

# 2. Check if port 80 is accessible
echo "Checking nginx accessibility..."
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:80 | grep -qE "200|301|302"; then
    echo -e "${YELLOW}⚠ Warning: nginx might not be accessible on port 80${NC}"
    echo -e "${YELLOW}  Make sure your firewall allows traffic on port 80${NC}"
fi

# 3. Display current nginx config
echo ""
echo -e "${BLUE}Current nginx configuration:${NC}"
$DOCKER_COMPOSE exec nginx cat /etc/nginx/conf.d/default.conf | head -20

echo ""
echo -e "${YELLOW}IMPORTANT: Before proceeding, ensure:${NC}"
echo -e "  1. Your domain ${DOMAIN_NAME} points to this server's IP address"
echo -e "  2. Port 80 is open and accessible from the internet"
echo -e "  3. No firewall is blocking Let's Encrypt servers"
echo ""
read -p "Ready to proceed? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborting."
    exit 1
fi

# Obtain SSL certificate
echo ""
echo "Obtaining SSL certificate from Let's Encrypt..."
$DOCKER_COMPOSE run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email ${SSL_EMAIL} \
    --agree-tos \
    --no-eff-email \
    -d ${DOMAIN_NAME} \
    --verbose

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ SSL certificate obtained successfully!${NC}"

    # Restart nginx to apply SSL
    echo "Restarting nginx to apply SSL..."
    $DOCKER_COMPOSE restart nginx

    echo ""
    echo -e "${GREEN}✓ Setup complete!${NC}"
    echo -e "Your site should now be accessible at: ${BLUE}https://${DOMAIN_NAME}${NC}"

    # Start certbot auto-renewal if not running
    if ! $DOCKER_COMPOSE ps certbot | grep -q "Up"; then
        echo "Starting auto-renewal service..."
        $DOCKER_COMPOSE up -d certbot
    fi
else
    echo -e "${RED}❌ Failed to obtain SSL certificate${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting tips:${NC}"
    echo "1. Verify DNS: dig ${DOMAIN_NAME} +short"
    echo "2. Check nginx logs: $DOCKER_COMPOSE logs nginx"
    echo "3. Check certbot logs: $DOCKER_COMPOSE logs certbot"
    echo "4. Test port 80: curl -I http://${DOMAIN_NAME}/.well-known/acme-challenge/test"
    echo "5. Check firewall: sudo ufw status"
    exit 1
fi
