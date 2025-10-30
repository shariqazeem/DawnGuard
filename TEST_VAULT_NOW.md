# 🧪 TEST VAULT RIGHT NOW

## ⚡ Quick Test (3 minutes)

### Step 1: Start Services
```bash
# Make sure everything is running
docker-compose ps

# Should see: ipfs, ollama, web - all "Up"
```

### Step 2: Clear Browser Storage (IMPORTANT!)
```
1. Open: http://localhost:8000/dapp/vault/
2. Press F12 (open DevTools)
3. Go to "Application" tab (Chrome) or "Storage" tab (Firefox)
4. Click "Local Storage" → "http://localhost:8000"
5. Click "Clear All" or delete these keys:
   - dawnguard_wallet
   - dawnguard_demo_wallet
6. Refresh page (F5)
```

**Why?** This ensures you start fresh with a stable wallet address.

### Step 3: Upload a Test File
```
1. Create test file:
   echo "Hello from DawnGuard TRUE dApp!" > test_upload.txt

2. On the vault page:
   - Click "Choose File"
   - Select test_upload.txt
   - Click "Upload to IPFS"

3. Wait for alert: "✅ Success! File uploaded to IPFS!"
```

### Step 4: Watch Console Logs
```
In DevTools Console, you should see:

🔑 Vault using wallet: demo_user_XXXXXXXXX
📂 Loading files for wallet: demo_user_XXXXXXXXX
💾 Saving to Gun.js: {name: "test_upload.txt", cid: "bafybei...", ...}
✅ Gun.js saved: {ok: 1}
⏳ Waiting for Gun.js to sync and display file...
📄 Gun.js file event: XXXXXXXXX {name: "test_upload.txt", ...}
✅ Adding file to UI: test_upload.txt CID: bafybei...
```

### Step 5: Verify File Appears
```
File should appear in the table within 2-3 seconds.

If it doesn't:
- Check console for errors
- Make sure Gun.js logs show "✅ Gun.js saved"
```

### Step 6: Test File Viewing
```
1. Click "View Local" button
2. Should open: http://127.0.0.1:8080/ipfs/bafybei...
3. Should show your file content or download it

If shows metadata instead:
- The file is encrypted, so you see the encrypted bytes
- This is CORRECT behavior!
- For demo, upload a plain text file without encryption
```

### Step 7: Test Persistence
```
1. Note the CID of your file
2. Navigate away: http://localhost:8000/dapp/
3. Come back: http://localhost:8000/dapp/vault/
4. File should STILL BE THERE! ✅

If file disappeared:
- Check console: what wallet address is being used?
- Should be SAME as before
```

---

## 🐛 TROUBLESHOOTING

### Issue: File disappears after upload
**Check Console:**
```javascript
// Should see SAME wallet address on upload and reload
🔑 Vault using wallet: demo_user_1234567890
💾 Saving to Gun.js: ...
🔑 Vault using wallet: demo_user_1234567890  // ← SAME!
```

**If wallet address CHANGES, that's the problem!**

**Solution:**
```
The fix we just applied should prevent this.
Clear localStorage and try again (Step 2 above).
```

### Issue: IPFS gateway shows metadata
**This means:**
- File is encrypted (correct!)
- You're seeing the encrypted bytes

**For demo, use unencrypted upload:**
We can add an "unencrypted demo" button if needed, OR just explain:
*"This file is encrypted with AES-256. The CID proves it's on IPFS. Let me show you the decryption..."*

**Better for demo:**
Upload an image file - IPFS gateway will try to render it even if encrypted.

### Issue: Gun.js not syncing
**Check console for:**
```
✅ Gun.js P2P Database initialized - TRUE DAPP MODE
```

**If missing:**
- Refresh page
- Check base.html has Gun.js CDN loaded

---

## 🎯 WHAT SUCCESS LOOKS LIKE

### Upload Flow:
```
1. Click upload ✅
2. Alert: "Success! File uploaded!" ✅
3. Console: "💾 Saving to Gun.js" ✅
4. Console: "✅ Gun.js saved" ✅
5. Console: "📄 Gun.js file event" ✅
6. Console: "✅ Adding file to UI" ✅
7. File appears in table (2-3 seconds) ✅
```

### Persistence Flow:
```
1. Upload file ✅
2. File appears ✅
3. Navigate away ✅
4. Come back ✅
5. File STILL THERE ✅
```

### IPFS Flow:
```
1. Click "View Local" ✅
2. Opens: http://127.0.0.1:8080/ipfs/bafybei... ✅
3. File downloads or shows content ✅
```

---

## 🔥 FOR DEMO

### Best Files to Upload:
1. **Small text file** - Quick, shows CID clearly
2. **Image (JPG/PNG)** - Looks good in gateway
3. **PDF** - Shows it works with any file type

### Demo Script:
```
"Let me upload a file to IPFS...

[Upload]

See the CID? bafybei... That's the content-addressed hash.

This file is now on IPFS - MY local node.

[Click View Local]

See? File loads from IPFS gateway. No central server.

And the metadata? Stored in Gun.js P2P database.

[Show console]

Here's the Gun.js sync in real-time.

Now watch - I'll navigate away and come back...

[Navigate away, come back]

File still here! Because it's in Gun.js, not Django database.

That's TRUE decentralization."
```

---

## ✅ SUCCESS CRITERIA

Before you move forward, verify:

- [ ] File uploads successfully
- [ ] File appears in table (within 3 seconds)
- [ ] File persists after navigating away
- [ ] "View Local" opens IPFS gateway
- [ ] Console shows all Gun.js logs
- [ ] Same wallet address on upload and reload

**If all ✅ → YOU'RE READY TO DEMO!** 🎉

---

## 🚀 NEXT STEPS

Once vault works:

1. Test family members: `/dapp/`
2. Test AI chat: `/dapp/kids-ai/`
3. Test P2P knowledge: `/p2p/dapp/`

Then:
4. Practice full demo
5. WIN HACKATHON! 🏆
