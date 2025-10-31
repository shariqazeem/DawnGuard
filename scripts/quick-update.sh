#!/bin/bash

# Quick Update Script - Pull latest changes and restart
# Run this on your Ubuntu server to deploy updates

set -e

echo "🔄 DawnGuard Quick Update"
echo "========================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Pull latest code
echo -e "${BLUE}📥 Pulling latest code from GitHub...${NC}"
git pull origin main
echo -e "${GREEN}✓ Code updated${NC}"
echo ""

# Rebuild containers with updated code
echo -e "${BLUE}🐳 Rebuilding containers...${NC}"
docker-compose -f docker-compose.simple.yml build web
echo -e "${GREEN}✓ Containers rebuilt${NC}"
echo ""

# Restart services
echo -e "${BLUE}🔄 Restarting services...${NC}"
docker-compose -f docker-compose.simple.yml restart web
echo -e "${GREEN}✓ Services restarted${NC}"
echo ""

# Wait for web to be ready
echo -e "${YELLOW}⏳ Waiting for web service to start...${NC}"
sleep 5

# Show status
echo -e "${BLUE}📊 Service Status:${NC}"
docker-compose -f docker-compose.simple.yml ps
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Update Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}💡 Your app should now have the latest fixes${NC}"
echo ""
echo "📝 Useful commands:"
echo "   → View logs: docker-compose -f docker-compose.simple.yml logs -f web"
echo "   → View all logs: docker-compose -f docker-compose.simple.yml logs -f"
echo "   → Restart all: docker-compose -f docker-compose.simple.yml restart"
echo ""
