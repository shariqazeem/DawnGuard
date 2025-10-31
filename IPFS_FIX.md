# IPFS Gateway URL Fix

## ✅ Issue Fixed

**Problem**: IPFS gateway URLs were hardcoded to `http://127.0.0.1:8080/ipfs/...`
- Raw button redirected to localhost instead of server IP
- Downloads failed with 403 errors
- Files couldn't be accessed from external browsers

**Solution**: Dynamic gateway URLs based on request host + Nginx proxy

## 🔧 Changes Made

### 1. Updated `core/vault_views_ipfs.py`
**Before**:
```python
IPFS_PUBLIC_GATEWAY = 'http://localhost:8080'
gateway_url = f"{IPFS_PUBLIC_GATEWAY}/ipfs/{cid}"
```

**After**:
```python
request_host = request.get_host()
protocol = 'https' if request.is_secure() else 'http'
gateway_url = f"{protocol}://{request_host}/ipfs/{cid}"
```

### 2. Updated `nginx/nginx-http.conf`
Added IPFS proxy routes to both HTTP and HTTPS servers:
```nginx
# IPFS Gateway Proxy
location /ipfs/ {
    proxy_pass http://ipfs:8080;
    proxy_set_header Host $host;
    proxy_read_timeout 300s;
    proxy_buffering off;
}
```

### 3. Updated `core/utils/ipfs_handler.py`
- Added support for dynamic gateway URLs
- Uses environment variable or container name

## 🚀 How It Works Now

### Upload Flow:
1. User uploads file to IPFS
2. Server returns gateway URL: `https://YOUR_SERVER_IP/ipfs/bafkrei...`
3. URL works from any browser/location

### Access Flow:
1. User clicks "Raw" button or downloads file
2. Browser requests: `https://YOUR_SERVER_IP/ipfs/bafkrei...`
3. Nginx proxies request to `ipfs:8080` container
4. IPFS returns file content
5. File displays/downloads correctly

## ✅ What's Fixed

| Feature | Before | After |
|---------|--------|-------|
| **Raw Button** | ❌ Opens `127.0.0.1:8080` (fails) | ✅ Opens `https://YOUR_IP/ipfs/CID` |
| **Downloads** | ❌ 403 error | ✅ Works correctly |
| **External Access** | ❌ Localhost only | ✅ Works from any IP |
| **HTTPS Support** | ❌ N/A | ✅ Full HTTPS support |

## 📋 Testing

### Test Upload & View:
1. Go to IPFS Vault: `https://YOUR_IP/vault/dapp/`
2. Upload an image
3. Click "Raw" button
4. Should open: `https://YOUR_IP/ipfs/bafkrei...` ✅
5. Image should display

### Test Download:
1. Upload a file
2. Click download icon
3. File should download correctly ✅
4. No 403 errors

## 🔄 Deployment

On your Ubuntu server:
```bash
cd ~/DawnGuard
git pull origin main

# Restart to apply Nginx changes
docker-compose -f docker-compose.simple.yml restart nginx

# Or full restart
docker-compose -f docker-compose.simple.yml down
./scripts/quick-deploy.sh
```

## 🎯 Technical Details

### URL Generation:
- **Old**: Hardcoded `http://localhost:8080/ipfs/CID`
- **New**: Dynamic `{protocol}://{request.get_host()}/ipfs/CID`

### Examples:
- Local: `http://localhost/ipfs/bafkrei...`
- Server: `https://144.24.xxx.xxx/ipfs/bafkrei...`
- Domain: `https://dawnguard.duckdns.org/ipfs/bafkrei...`

### Nginx Proxy:
- Receives: `https://YOUR_IP/ipfs/bafkrei...`
- Forwards to: `http://ipfs:8080/ipfs/bafkrei...`
- Returns: File content from IPFS

## 🐛 Troubleshooting

### Still getting localhost URLs?
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)
- Upload a new file (old files have old URLs in Gun.js)

### 403 Errors?
```bash
# Check IPFS is running
docker-compose ps | grep ipfs

# Check Nginx config
docker-compose exec nginx nginx -t

# Restart services
docker-compose restart ipfs nginx
```

### IPFS not accessible?
```bash
# Check IPFS logs
docker-compose logs ipfs

# Test IPFS directly
curl http://localhost:8080/ipfs/bafkrei...
```

---

**All IPFS gateway issues fixed!** Files now accessible via your actual server IP/domain. 🎉
