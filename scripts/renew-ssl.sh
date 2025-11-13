#!/bin/bash

# SSL Certificate Renewal Helper Script
# This script helps renew SSL certificates and reload nginx

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔐 SSL Certificate Renewal"
echo "=========================="
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

# Load domain from .env file
if [ -f ".env" ]; then
    export $(grep DOMAIN_NAME .env | xargs)
else
    echo -e "${RED}❌ .env file not found. Please run setup.sh first.${NC}"
    exit 1
fi

if [ -z "$DOMAIN_NAME" ]; then
    read -p "Enter your domain name: " DOMAIN_NAME
fi

echo -e "Domain: ${BLUE}${DOMAIN_NAME}${NC}"
echo ""

# Check if running in dry-run mode
if [ "$1" == "--dry-run" ]; then
    echo -e "${YELLOW}Running in dry-run mode (test only)${NC}"
    DRY_RUN="--dry-run"
else
    DRY_RUN=""
fi

# Run certbot renewal
echo "Attempting to renew SSL certificate..."
$DOCKER_COMPOSE run --rm --entrypoint certbot certbot renew $DRY_RUN

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Certificate renewal successful (or not needed yet)${NC}"

    # Reload nginx to pick up new certificates
    echo "Reloading nginx..."
    $DOCKER_COMPOSE exec nginx nginx -s reload

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Nginx reloaded successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Nginx reload failed, trying restart...${NC}"
        $DOCKER_COMPOSE restart nginx
    fi
else
    echo -e "${RED}❌ Certificate renewal failed${NC}"
    echo -e "${YELLOW}Check the logs with: $DOCKER_COMPOSE logs certbot${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ SSL renewal process complete${NC}"
echo ""
echo "Certificate details:"
$DOCKER_COMPOSE run --rm --entrypoint certbot certbot certificates

echo ""
echo -e "${BLUE}Tip: Add this to cron for automatic renewal:${NC}"
echo "0 0 * * * cd $(pwd) && ./scripts/renew-ssl.sh >> logs/ssl-renewal.log 2>&1"
