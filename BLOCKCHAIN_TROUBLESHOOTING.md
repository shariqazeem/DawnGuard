# 🔧 Blockchain Transaction Troubleshooting Guide

## Error: "Transaction cancelled. Blockchain verification is REQUIRED"

This error means the Solana transaction failed. Here's how to fix it:

---

## ✅ Step 1: Check Wallet Connection

**Open browser console** (F12 or Cmd+Option+I) and check:

```javascript
// Check if Phantom wallet is connected
console.log('Wallet connected:', window.solana?.isConnected);
console.log('Wallet address:', window.solana?.publicKey?.toString());
```

**Expected**:
- `Wallet connected: true`
- `Wallet address: <your-solana-address>`

**If not connected**:
1. Install Phantom wallet: https://phantom.app/
2. Create/import wallet
3. Click "Connect Wallet" on DawnGuard P2P page

---

## ✅ Step 2: Get Devnet SOL (Transaction Fees)

**Most common issue**: No devnet SOL for transaction fees!

### Check your balance:
```javascript
const connection = new solanaWeb3.Connection('https://api.devnet.solana.com');
const balance = await connection.getBalance(window.solana.publicKey);
console.log('Balance:', balance / 1e9, 'SOL');
```

**If balance is 0**:

1. **Go to Solana Faucet**: https://faucet.solana.com/
2. **Paste your wallet address**
3. **Select "Devnet"**
4. **Request airdrop** (gives you 2 devnet SOL)
5. **Wait 30 seconds** for confirmation
6. **Try sharing knowledge again**

**Alternative faucet**:
- https://solfaucet.com/ (if main faucet is down)

---

## ✅ Step 3: Check Solana Web3 Library

**In browser console**:
```javascript
console.log('Solana Web3 loaded:', !!window.solanaWeb3);
console.log('Version:', window.solanaWeb3?.version);
```

**Expected**: `Solana Web3 loaded: true`

**If undefined**:
1. Hard refresh page: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Clear browser cache
3. Check that `base.html` has:
   ```html
   <script src="https://unpkg.com/@solana/web3.js@latest/lib/index.iife.min.js"></script>
   ```

---

## ✅ Step 4: Check Network Connection

DawnGuard uses **Solana Devnet** (not mainnet).

**Test connection**:
```bash
curl -X POST https://api.devnet.solana.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
```

**Expected**: `{"jsonrpc":"2.0","result":"ok","id":1}`

**If fails**:
- Check your internet connection
- Try alternative RPC: `https://api.devnet.solana.com`

---

## ✅ Step 5: Check Browser Console for Errors

**Open console** and look for errors when clicking "Share Knowledge":

### Common Errors:

#### Error: "User rejected the request"
**Cause**: You clicked "Cancel" in Phantom popup
**Fix**: Click "Approve" when Phantom asks to sign transaction

#### Error: "Insufficient funds"
**Cause**: Not enough SOL for transaction fee (~0.000005 SOL)
**Fix**: Get devnet SOL from faucet (Step 2)

#### Error: "Blockhash not found"
**Cause**: Network congestion or slow connection
**Fix**: Wait 10 seconds and try again

#### Error: "Transaction simulation failed"
**Cause**: Invalid transaction or network issue
**Fix**:
1. Check console for detailed error
2. Try refreshing page
3. Reconnect wallet

---

## 🔍 Debug Mode

**Enable detailed logging**:

Open browser console and run:
```javascript
// Enable debug mode
localStorage.setItem('DEBUG_P2P', 'true');
location.reload();
```

Now when you try to share knowledge, you'll see detailed logs:
- Wallet connection status
- Balance check
- Transaction creation
- Signing attempt
- Verification response

**Disable debug mode**:
```javascript
localStorage.removeItem('DEBUG_P2P');
```

---

## 📋 Full Checklist

Before sharing knowledge, verify:

- [ ] Phantom wallet installed
- [ ] Wallet connected to DawnGuard
- [ ] Wallet set to **Devnet** (not mainnet)
- [ ] Balance > 0 SOL (get from faucet if needed)
- [ ] Internet connection working
- [ ] Browser console shows no errors
- [ ] Page fully loaded (Solana Web3 loaded)

---

## 🚀 Quick Test

**Test if everything works**:

```javascript
// Run this in browser console
async function testBlockchain() {
    console.log('1. Checking wallet...');
    if (!window.solana?.isConnected) {
        console.error('❌ Wallet not connected');
        return;
    }
    console.log('✅ Wallet connected:', window.solana.publicKey.toString());

    console.log('2. Checking Solana Web3...');
    if (!window.solanaWeb3) {
        console.error('❌ Solana Web3 not loaded');
        return;
    }
    console.log('✅ Solana Web3 loaded');

    console.log('3. Checking balance...');
    const connection = new window.solanaWeb3.Connection('https://api.devnet.solana.com');
    const balance = await connection.getBalance(window.solana.publicKey);
    console.log('✅ Balance:', balance / 1e9, 'SOL');

    if (balance === 0) {
        console.error('❌ No SOL! Get devnet SOL from https://faucet.solana.com/');
        return;
    }

    console.log('4. Testing transaction creation...');
    const tx = new window.solanaWeb3.Transaction();
    console.log('✅ Transaction created');

    console.log('🎉 All checks passed! You can share knowledge.');
}

testBlockchain();
```

---

## 🆘 Still Not Working?

### Get Help:

1. **Copy console output**:
   - Open console
   - Try sharing knowledge
   - Copy all error messages
   - Screenshot if needed

2. **Share details**:
   - Browser: Chrome/Firefox/Edge?
   - Wallet address: (first 8 characters)
   - Balance: X SOL
   - Error message: "..."

3. **Check GitHub Issues**:
   - https://github.com/shariqazeem/DawnGuard/issues

---

## 💡 Pro Tips

### Faster Transactions:
- Keep wallet connected (don't disconnect between shares)
- Maintain balance > 0.01 SOL (for multiple transactions)

### Save Transaction Fees:
- Batch multiple knowledge shares (coming soon)
- Use compression for large data

### Verify on Blockchain:
- After successful share, you'll see Solana Explorer link
- Click to view transaction on blockchain
- Example: `https://explorer.solana.com/tx/<signature>?cluster=devnet`

---

## 📚 References

- **Phantom Wallet**: https://phantom.app/
- **Solana Faucet**: https://faucet.solana.com/
- **Solana Devnet Explorer**: https://explorer.solana.com/?cluster=devnet
- **Solana Status**: https://status.solana.com/

---

**Last Updated**: 2025-01-XX
**Status**: Active troubleshooting guide
