# DawnGuard Deployment Guide - DuckDNS + HTTPS

This guide will help you deploy DawnGuard on your Oracle Cloud Ubuntu server with a free DuckDNS domain and automatic HTTPS.

## Prerequisites

- Ubuntu server with Docker & Docker Compose installed
- Public IP address from Oracle Cloud
- Port 80 and 443 open in firewall

## Step 1: Setup DuckDNS (Do this FIRST - 2 minutes)

### 1.1 Create DuckDNS Account
1. Go to https://www.duckdns.org
2. Login with GitHub, Google, or Reddit
3. Create a subdomain (e.g., `dawnguard`) - You'll get: `dawnguard.duckdns.org`

### 1.2 Point Domain to Your Server
1. Copy your **Oracle Cloud server public IP** (e.g., `132.145.xxx.xxx`)
2. In DuckDNS dashboard, paste your IP in the "current ip" field
3. Click "update ip"
4. Test: `ping dawnguard.duckdns.org` (should show your server IP)

### 1.3 Optional: Auto-update IP (if IP changes)
On your server, add to crontab:
```bash
# Update DuckDNS IP every 5 minutes
echo "*/5 * * * * curl 'https://www.duckdns.org/update?domains=YOUR_SUBDOMAIN&token=YOUR_TOKEN&ip=' >/dev/null 2>&1" | crontab -
```

Get your token from DuckDNS dashboard.

## Step 2: Open Firewall Ports on Oracle Cloud

### 2.1 Oracle Cloud Console
1. Go to: Instance Details → Virtual Cloud Network → Subnet → Security List
2. Add Ingress Rules:
   - **Port 80** (HTTP) - Source: 0.0.0.0/0
   - **Port 443** (HTTPS) - Source: 0.0.0.0/0
   - **Port 4001** (IPFS) - Source: 0.0.0.0/0

### 2.2 Ubuntu Firewall (UFW)
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 4001/tcp
sudo ufw reload
```

Or if using iptables:
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 4001 -j ACCEPT
sudo netfilter-persistent save
```

## Step 3: Deploy DawnGuard

### 3.1 On Your Local Machine (macOS)
```bash
# Commit and push your changes
git add .
git commit -m "Add HTTPS deployment with DuckDNS"
git push origin main
```

### 3.2 On Ubuntu Server
```bash
# Clone or pull latest code
cd ~
git clone https://github.com/YOUR_USERNAME/DawnGuard.git
# OR if already cloned:
cd ~/DawnGuard
git pull origin main

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3.3 During Setup
The script will ask for:
1. **Domain name**: `dawnguard.duckdns.org` (your DuckDNS domain)
2. **Email**: `your-email@example.com` (for SSL certificate notifications)

The script will automatically:
- Generate encryption keys
- Build Docker containers
- Obtain SSL certificate from Let's Encrypt
- Start all services with HTTPS

## Step 4: Access Your App

Visit: **https://dawnguard.duckdns.org**

The first time may take a moment for the SSL certificate to be issued.

## Troubleshooting

### SSL Certificate Failed?
**Most common issue**: Domain not pointing to server yet

```bash
# 1. Check DNS is working
ping dawnguard.duckdns.org
# Should show your server IP

# 2. Check if port 80 is reachable
curl http://dawnguard.duckdns.org
# Should show "301 Moved Permanently"

# 3. Retry SSL certificate
docker-compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  -d dawnguard.duckdns.org

# 4. Restart Nginx
docker-compose restart nginx
```

### Check Service Status
```bash
# View all containers
docker-compose ps

# View logs
docker-compose logs -f nginx
docker-compose logs -f certbot
docker-compose logs -f web

# Check SSL certificate
docker-compose exec nginx ls -la /etc/letsencrypt/live/
```

### HTTP Works But HTTPS Doesn't?
```bash
# Check Nginx configuration
docker-compose exec nginx nginx -t

# Check certificate files exist
docker-compose exec nginx ls /etc/letsencrypt/live/dawnguard.duckdns.org/

# Restart Nginx
docker-compose restart nginx
```

### Firewall Issues?
```bash
# Test if ports are open from outside
# (Run from your local machine)
telnet YOUR_SERVER_IP 80
telnet YOUR_SERVER_IP 443

# Check iptables rules
sudo iptables -L -n | grep -E '80|443'
```

## Maintenance

### View Logs
```bash
docker-compose logs -f
```

### Restart Services
```bash
docker-compose restart
```

### Stop Everything
```bash
docker-compose down
```

### Update Application
```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

### SSL Auto-Renewal
Certbot automatically renews certificates every 12 hours. No action needed!

Check renewal logs:
```bash
docker-compose logs certbot
```

## Production Tips

1. **Backup your .env file** - Contains encryption keys
2. **Monitor SSL expiry**: Certificates auto-renew 30 days before expiry
3. **Update DuckDNS token**: Save it somewhere safe
4. **Check logs regularly**: `docker-compose logs -f`

## Quick Reference

| Service | URL |
|---------|-----|
| Main App | https://dawnguard.duckdns.org |
| IPFS Vault | https://dawnguard.duckdns.org/vault/dapp/ |
| P2P Knowledge | https://dawnguard.duckdns.org/p2p/dapp/ |

| Command | Purpose |
|---------|---------|
| `docker-compose ps` | Check status |
| `docker-compose logs -f` | View logs |
| `docker-compose restart` | Restart all |
| `docker-compose down` | Stop all |

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify DNS: `ping your-domain.duckdns.org`
3. Check ports: `sudo netstat -tlnp | grep -E '80|443'`

Good luck with your hackathon! 🚀
