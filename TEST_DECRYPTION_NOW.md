# 🔐 TEST ENCRYPTED FILE DOWNLOAD

## Quick Test (2 minutes)

### Step 1: Start Services
```bash
# Make sure everything is running
docker-compose ps

# Should see: ipfs, ollama - all "Up"
# Django should be running: python3 manage.py runserver
```

### Step 2: Clear Browser Cache & Navigate
```bash
# Open vault
open http://localhost:8000/vault/dapp/
```

**In browser:**
1. Press F12 (DevTools)
2. Go to Console tab
3. Keep it open to see logs

### Step 3: Upload a Test File
```bash
# Create a test file
echo "Hello from DawnGuard! This is a secret message. 🔐" > test_secret.txt
```

**In browser:**
1. Click "Choose File"
2. Select `test_secret.txt`
3. Click "Upload to IPFS"
4. Wait for success alert

**Expected:**
- ✅ Alert: "Success! File uploaded to IPFS!"
- ✅ Console shows: `💾 Saving to Gun.js`
- ✅ Console shows: `✅ Gun.js saved`
- ✅ File appears in table (2-3 seconds)

### Step 4: Test Decryption Download
**Click the "Download" button on your file**

**Expected:**
1. 🔄 Blue notification: "Downloading from IPFS and decrypting..."
2. ✅ Green notification: "File downloaded and decrypted!"
3. 📥 Browser downloads the file
4. Open the downloaded file
5. **Should show:** "Hello from DawnGuard! This is a secret message. 🔐"

**Console logs should show:**
```
📥 Downloading and decrypting: bafybei... test_secret.txt
✅ File decrypted successfully
```

### Step 5: Test Raw View (Optional)
**Click the "Raw" button**

**Expected:**
- Opens IPFS gateway: `http://127.0.0.1:8080/ipfs/bafybei...`
- Shows **encrypted gibberish** (base64 encrypted data)
- This PROVES the file is encrypted on IPFS!

---

## 🎯 DEMO FLOW

**For Judges:**

1. **Upload file:**
   "Let me upload a file to IPFS..."

2. **Show CID:**
   "See this CID? `bafybei...` - that's content-addressed storage."

3. **Click Raw:**
   "If I view it directly on IPFS, you see encrypted data."
   *(Show gibberish)*

4. **Click Download:**
   "But when I download through DawnGuard..."
   *(File downloads)*

5. **Open downloaded file:**
   "It's decrypted! End-to-end encryption with IPFS storage."

6. **Explain:**
   - File encrypted locally (AES-256)
   - Uploaded to IPFS (decentralized)
   - CID stored in Gun.js (P2P database)
   - Download decrypts on-demand
   - **NO Django database!**

---

## 🐛 TROUBLESHOOTING

### Issue: Download button does nothing
**Check Console:**
- Look for errors
- Make sure IPFS is running: `docker-compose ps ipfs`

**Fix:**
```bash
# Restart IPFS
docker-compose restart ipfs

# Check logs
docker-compose logs ipfs
```

### Issue: "Decryption failed"
**Cause:** File might not be encrypted properly

**Check:**
1. Is encryption working? Look at upload logs
2. Try uploading a new file

### Issue: "Cannot connect to IPFS"
**Fix:**
```bash
# Make sure IPFS API is accessible
curl http://localhost:5001/api/v0/version

# Should return IPFS version info
```

### Issue: File downloads but is gibberish
**Cause:** Decryption might be failing

**Check:**
1. Open browser console
2. Look for decryption errors
3. Check the downloaded file size - should match original

---

## ✅ SUCCESS CRITERIA

Before demo, verify:

- [x] File uploads successfully
- [x] File appears in table within 3 seconds
- [x] CID is displayed and copyable
- [x] "Download" button triggers download
- [x] Downloaded file is **decrypted and readable**
- [x] "Raw" button shows **encrypted data** on IPFS gateway
- [x] Console shows all logs correctly

**If all ✅ → YOU'RE READY TO BLOW JUDGES' MINDS!** 🚀

---

## 🎬 KILLER DEMO LINE

"This file is encrypted with AES-256, stored on IPFS with content addressing,
metadata in Gun.js P2P database, and it's all running on YOUR Black Box.

No central server. No cloud subscription. No privacy risk.

That's TRUE decentralization."

**🎤⬇️ BOOM.**
