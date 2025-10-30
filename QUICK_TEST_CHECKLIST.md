# ⚡ QUICK TEST CHECKLIST - Before Hackathon Demo

## 🔥 5-MINUTE PRE-DEMO TEST

### 1. Start Services (1 min)
```bash
cd /Users/macbookair/projects/DawnGuard

# Start Docker services
docker-compose up -d

# Wait 10 seconds for IPFS to initialize
sleep 10

# Check all containers running
docker ps
```

**Expected Output:**
- ✅ cyphervault_web (Django)
- ✅ dawnguard_ollama (AI)
- ✅ dawnguard_ipfs (Storage)

---

### 2. Test IPFS (30 sec)
```bash
# Check IPFS connectivity
docker exec dawnguard_ipfs ipfs swarm peers | wc -l

# Should show at least 5-10 peers
```

If peers < 5:
```bash
# Restart IPFS
docker-compose restart ipfs
sleep 5
docker exec dawnguard_ipfs ipfs swarm peers | wc -l
```

---

### 3. Test Ollama (30 sec)
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Should return JSON with models
```

If fails:
```bash
# Check models downloaded
docker exec dawnguard_ollama ollama list

# If no models, pull one (DO THIS NOW BEFORE DEMO!)
docker exec dawnguard_ollama ollama pull llama2
```

---

### 4. Start Django (30 sec)
```bash
# In a NEW terminal tab
cd /Users/macbookair/projects/DawnGuard
python3 manage.py runserver
```

**Expected:** `Starting development server at http://127.0.0.1:8000/`

---

### 5. Test Gun.js (1 min)

Open browser: http://localhost:8000/dapp/

**In Console (F12), run:**
```javascript
window.dawnguardGun.get('test').put({demo: 'ready', timestamp: Date.now()})
```

**Expected:** No errors, shows in console

---

### 6. Test Wallet Connection (30 sec)

1. Open http://localhost:8000/dapp/
2. Click "Connect Phantom Wallet"
3. Approve

**Expected:** Wallet address shown in header

**If fails:** Install Phantom from https://phantom.app

---

### 7. Test IPFS Upload (1 min)

1. Go to http://localhost:8000/dapp/vault/
2. Upload ANY small file (test.txt with "Hello")
3. Wait for success message

**Expected:**
- ✅ Success message with CID
- ✅ File appears in table
- ✅ Can click "View Local" and file loads

**If fails:**
```bash
# Check IPFS API
curl -X POST http://localhost:5001/api/v0/version

# Should return version info
```

---

### 8. Test Kids AI (30 sec)

1. Go to http://localhost:8000/dapp/kids-ai/
2. Type: "Say hello"
3. Click Send

**Expected:** AI responds within 5-10 seconds

**If fails:**
- Check Ollama: `curl http://localhost:11434/api/tags`
- Check Django logs for errors

---

## 🚨 Common Issues & Quick Fixes

### Issue: IPFS not connecting to peers
```bash
docker-compose down
docker-compose up -d ipfs
sleep 10
docker exec dawnguard_ipfs ipfs swarm peers
```

### Issue: Ollama not responding
```bash
# Restart Ollama
docker-compose restart ollama
sleep 5

# Test again
curl http://localhost:11434/api/tags
```

### Issue: Gun.js not loading
- Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
- Check browser console for errors
- Verify CDN loaded: Look for "✅ Gun.js P2P Database initialized"

### Issue: Phantom wallet not found
1. Install from https://phantom.app
2. Create or import wallet
3. Refresh page
4. Try connecting again

### Issue: Django migrations needed
```bash
python3 manage.py migrate
```

---

## ✅ All Systems GO Checklist

Before starting demo, verify:

- [ ] Docker containers running (3/3)
- [ ] IPFS has peers (count > 5)
- [ ] Ollama responds to curl
- [ ] Django server running on :8000
- [ ] Gun.js initializes in browser console
- [ ] Phantom wallet connected
- [ ] Test file uploaded to IPFS successfully
- [ ] Kids AI responds to test message
- [ ] DevTools open and ready

---

## 🎯 30-Second Smoke Test

Run this ONE command to test everything:
```bash
echo "Testing all services..." && \
docker ps --format "{{.Names}}: {{.Status}}" | grep -E "dawnguard|cyphervault" && \
echo "\nIPFS Peers:" && docker exec dawnguard_ipfs ipfs swarm peers | wc -l && \
echo "\nOllama:" && curl -s http://localhost:11434/api/tags | python3 -m json.tool | grep name && \
echo "\nDjango:" && curl -s http://localhost:8000 > /dev/null && echo "✅ Responding" || echo "❌ Not running"
```

**Expected Output:**
```
Testing all services...
cyphervault_web: Up 5 minutes
dawnguard_ollama: Up 5 minutes
dawnguard_ipfs: Up 5 minutes (healthy)

IPFS Peers:
9

Ollama:
      "name": "llama2"

Django:
✅ Responding
```

---

## 🚀 You're Ready!

If all checks pass:
1. Open http://localhost:8000/dapp/ in browser
2. Connect Phantom wallet
3. Open DevTools (F12)
4. You're ready to present!

**REMEMBER:** You've built something amazing. Now go show it! 🏆
