# SSL Certificate Troubleshooting Guide

This guide helps you troubleshoot SSL certificate issues with DawnGuard.

## Common Issue: "No renewals attempted"

This message from certbot usually means one of two things:
1. **Wrong entrypoint**: The certbot container's entrypoint is set to run `certbot renew` instead of `certbot certonly`
2. **No certificates to renew**: Certificates don't exist yet or aren't close to expiration

**Root Cause**: The docker-compose.yml certbot service has a custom entrypoint for auto-renewal. When running certbot manually, this entrypoint must be overridden with `--entrypoint certbot`.

**Solution**: Use the fixed scripts that properly override the entrypoint:
```bash
./scripts/get-ssl.sh
```

**Manual Fix**: If running certbot directly, always include `--entrypoint certbot`:
```bash
docker compose run --rm --entrypoint certbot certbot certonly \
    --webroot --webroot-path=/var/www/certbot \
    --email your@email.com --agree-tos -d your-domain.com
```

## Common Issues and Solutions

### 1. Setup Script Fails at SSL Certificate Step

**Symptoms:**
- Setup stops with SSL certificate errors
- Can't access the app after setup
- Nginx fails to start

**Causes:**
- Domain DNS not pointing to server
- Port 80 blocked by firewall
- Nginx started with SSL config before certificates exist

**Solutions:**

#### Option A: Use the manual SSL script
```bash
# First, make sure the app is running
docker compose ps

# Then obtain SSL certificates manually
./scripts/get-ssl.sh
```

#### Option B: Access app via HTTP first
If SSL fails, the app should still be accessible via HTTP:
```bash
# Check if nginx is running in HTTP mode
docker compose logs nginx

# Access your app at:
http://your-domain.duckdns.org
```

### 2. Domain DNS Issues

**Check DNS resolution:**
```bash
# Verify your domain points to this server
dig your-domain.duckdns.org +short

# Should return your server's public IP
curl ifconfig.me
```

**For DuckDNS domains:**
- Visit https://www.duckdns.org
- Ensure your domain is active
- Update the IP if needed

### 3. Firewall Blocking Port 80

**Check if port 80 is open:**
```bash
# Check firewall status
sudo ufw status

# Open port 80 if needed
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Test from another machine
curl -I http://your-domain.duckdns.org
```

### 4. Nginx Configuration Issues

**Check current nginx config:**
```bash
# View active configuration
docker compose exec nginx cat /etc/nginx/conf.d/default.conf

# Check for errors
docker compose exec nginx nginx -t

# View nginx logs
docker compose logs nginx
```

**Manual nginx restart:**
```bash
# Restart nginx
docker compose restart nginx

# Or rebuild and restart
docker compose up -d --build nginx
```

### 5. Certificate Verification Fails

**Check certbot logs:**
```bash
# View detailed certbot logs
docker compose logs certbot

# Check certificate status
docker compose run --rm certbot certificates
```

**Test ACME challenge accessibility:**
```bash
# Create test file
docker compose exec nginx sh -c 'echo "test" > /var/www/certbot/test.txt'

# Try to access it
curl http://your-domain.duckdns.org/.well-known/acme-challenge/test.txt
```

## Manual Certificate Management

### Obtain New Certificate
```bash
./scripts/get-ssl.sh
```

### Renew Existing Certificate
```bash
./scripts/renew-ssl.sh
```

### Test Renewal (dry-run)
```bash
./scripts/renew-ssl.sh --dry-run
```

### Force Certificate Renewal
```bash
docker compose run --rm --entrypoint certbot certbot renew --force-renewal
docker compose restart nginx
```

### View Certificate Details
```bash
docker compose run --rm --entrypoint certbot certbot certificates
```

## Emergency: Running Without SSL

If you need to access your app immediately without SSL:

1. **Ensure nginx is running:**
```bash
docker compose up -d nginx
```

2. **Access via HTTP:**
```bash
http://your-domain.duckdns.org
```

3. **Fix SSL later:**
Once your DNS and firewall are configured correctly, run:
```bash
./scripts/get-ssl.sh
```

## Setting Up Auto-Renewal

The certbot container automatically attempts renewal every 12 hours. To ensure nginx picks up renewed certificates:

1. **Check certbot service is running:**
```bash
docker compose ps certbot
```

2. **Add cron job for nginx reload (optional):**
```bash
# Edit crontab
crontab -e

# Add this line to reload nginx daily
0 0 * * * cd /path/to/DawnGuard && docker compose exec nginx nginx -s reload
```

Or use the renewal script with cron:
```bash
# Add to crontab
0 0 * * * cd /path/to/DawnGuard && ./scripts/renew-ssl.sh >> logs/ssl-renewal.log 2>&1
```

## Complete Reset

If everything else fails, reset the SSL setup:

```bash
# Stop all services
docker compose down

# Remove old certificates
sudo rm -rf certbot/conf/live/*
sudo rm -rf certbot/conf/archive/*
sudo rm -rf certbot/conf/renewal/*

# Restart setup
./scripts/setup.sh
```

## Getting Help

If you're still having issues:

1. Check logs:
```bash
docker compose logs nginx
docker compose logs certbot
docker compose logs web
```

2. Verify all services are running:
```bash
docker compose ps
```

3. Test basic connectivity:
```bash
curl http://localhost
curl http://your-domain.duckdns.org
```

## Understanding the SSL Flow

1. **Setup starts** → nginx runs with HTTP-only config
2. **ACME challenge** → certbot requests certificate via port 80
3. **Certificate obtained** → stored in `/etc/letsencrypt/`
4. **Nginx restarts** → loads HTTPS config with certificates
5. **Auto-renewal** → certbot checks every 12 hours, renews 30 days before expiry

The key is ensuring step 2 works: port 80 must be accessible and the domain must resolve correctly.
