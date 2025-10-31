#!/bin/bash

# Generate Self-Signed SSL Certificate for Local Development
# Allows Phantom wallet to work on local/IP deployments

echo "🔐 Generating Self-Signed SSL Certificate..."
echo ""

# Create SSL directory
mkdir -p ssl

# Get server IP or use localhost
read -p "Enter your server IP or domain (or press Enter for localhost): " DOMAIN
DOMAIN=${DOMAIN:-localhost}

echo ""
echo "Generating certificate for: $DOMAIN"
echo ""

# Generate private key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/privkey.pem \
  -out ssl/fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=DawnGuard/CN=$DOMAIN" \
  -addext "subjectAltName=DNS:$DOMAIN,DNS:localhost,IP:127.0.0.1"

echo ""
echo "✅ SSL Certificate generated!"
echo ""
echo "📁 Files created:"
echo "   - ssl/privkey.pem (private key)"
echo "   - ssl/fullchain.pem (certificate)"
echo ""
echo "⚠️  IMPORTANT: Self-signed certificates will show a browser warning"
echo "   Click 'Advanced' → 'Proceed anyway' to access your site"
echo ""
echo "💡 For production, use Let's Encrypt instead:"
echo "   ./scripts/setup.sh (with DuckDNS domain)"
echo ""
