# 🧪 Test the Setup Wizard - Quick Guide

## 🚀 How to Test

### Step 1: Reset Database (Force Setup)

```bash
# Option A: Delete all users via Django shell
python3 manage.py shell

# In Python shell:
from django.contrib.auth.models import User
User.objects.all().delete()
exit()

# Option B: Fresh database (nuclear option)
rm db.sqlite3
python3 manage.py migrate
```

### Step 2: Start Server

```bash
python3 manage.py runserver
```

### Step 3: Open Browser

```
http://localhost:8000
```

**What should happen:**
- ✅ Automatically redirects to `/setup/`
- ✅ Shows beautiful setup wizard

---

## 📝 Test Checklist

### ✅ Step 1: Welcome Screen
- [ ] See animated background with particles
- [ ] See glowing house icon
- [ ] Read feature highlights
- [ ] Click "Let's Get Started"
- [ ] Progress bar advances to step 2

### ✅ Step 2: Admin Setup
- [ ] See 3 auth method cards
- [ ] Wallet card is pre-selected
- [ ] Click each card - see selection change
- [ ] Fill in display name (e.g., "Dad")
- [ ] Try all auth methods:

#### Test Wallet Auth
- [ ] Select "Solana Wallet"
- [ ] Enter display name
- [ ] Click "Continue"
- [ ] Advances to step 3

#### Test Password Auth
- [ ] Go back to step 2
- [ ] Select "Username & Password"
- [ ] Enter display name
- [ ] Enter username
- [ ] Enter password
- [ ] Click "Continue"

#### Test ZKP Auth
- [ ] Go back to step 2
- [ ] Select "Zero-Knowledge"
- [ ] Enter display name
- [ ] Enter secret phrase
- [ ] Click "Continue"

### ✅ Step 3: Family Members
- [ ] Click "+ Add Family Member"
- [ ] Modal opens
- [ ] Enter name: "Emma"
- [ ] Select role: "Child"
- [ ] Click "Add Member"
- [ ] See Emma card with:
  - [ ] Random avatar color
  - [ ] Auto-generated username (e.g., emma472)
  - [ ] Auto-generated password (e.g., Xy4jK9mN)
  - [ ] Child badge
- [ ] Add another member: "Jake"
- [ ] See Jake with different credentials
- [ ] Try deleting Jake
- [ ] Jake removed from list
- [ ] Add Jake back
- [ ] Click "Complete Setup"

### ✅ Step 4: Success Screen
- [ ] See animated checkmark
- [ ] See "🎉 All Set!" message
- [ ] Confetti animation plays
- [ ] See 3 feature cards
- [ ] Click "Open My Dashboard"
- [ ] Redirects to `/family/`
- [ ] Admin is logged in
- [ ] See family members on dashboard

### ✅ Post-Setup Tests
- [ ] Logout
- [ ] Try accessing `/setup/`
- [ ] Should redirect to login (setup not accessible)
- [ ] Login with admin credentials
- [ ] Try adding more family members from dashboard

---

## 🐛 Common Issues & Fixes

### Issue: "Page not found" when accessing /setup/
**Fix:**
```bash
# Make sure routes are added
grep "setup_views" core/urls.py

# Should see:
# from . import setup_views
# path('setup/', setup_views.setup_wizard, name='setup_wizard'),
```

### Issue: Doesn't redirect to setup automatically
**Fix:**
```bash
# Check middleware is added
grep "SetupRequiredMiddleware" cyphervault/settings.py

# Should see it in MIDDLEWARE list
```

### Issue: "module 'core.middleware' has no attribute 'SetupRequiredMiddleware'"
**Fix:**
```bash
# Make sure middleware.py exists
ls core/middleware.py

# Restart server
python3 manage.py runserver
```

### Issue: Family members not showing on dashboard
**Fix:**
```bash
# Check models exist
python3 manage.py shell
>>> from core.models import FamilyMember
>>> FamilyMember.objects.all()
# Should see created members
```

---

## 📱 Mobile Testing

### On Phone
1. Get your computer's local IP:
   ```bash
   # Mac
   ifconfig | grep "inet "

   # Should see something like: 192.168.1.100
   ```

2. Update settings to allow connections:
   ```python
   # cyphervault/settings.py
   ALLOWED_HOSTS = ['*']  # Already set for demo
   ```

3. On phone browser:
   ```
   http://192.168.1.100:8000
   ```

4. Test:
   - [ ] Wizard loads on phone
   - [ ] All buttons clickable
   - [ ] Forms work
   - [ ] Layout responsive
   - [ ] Animations smooth

---

## 🎥 Demo Video Checklist

Record these parts:

1. **Fresh Open** (5 sec)
   - Show app auto-redirects to setup
   - Emphasize "automatic"

2. **Welcome Screen** (10 sec)
   - Show animated background
   - Highlight features
   - Click "Let's Get Started"

3. **Auth Selection** (15 sec)
   - Show 3 methods
   - Click each one
   - Fill wallet auth form
   - Continue

4. **Add Family** (20 sec)
   - Click "Add Family Member"
   - Add "Emma" (Child)
   - Show auto-generated credentials
   - Add "Jake" (Child)
   - Show warning to save credentials

5. **Complete** (15 sec)
   - Click "Complete Setup"
   - Show success screen
   - Confetti animation
   - Click "Open Dashboard"

6. **Dashboard** (10 sec)
   - Show logged in as admin
   - Show family members
   - Show features ready

**Total: ~75 seconds for impressive demo clip**

---

## 💡 Testing Pro Tips

### Quick Reset for Multiple Tests
```bash
# Create a script: reset_setup.sh
python3 manage.py shell -c "from django.contrib.auth.models import User; User.objects.all().delete()"
echo "✅ Setup reset! Users deleted."

# Make executable
chmod +x reset_setup.sh

# Run anytime
./reset_setup.sh
```

### Save Test Credentials
```bash
# Create test_credentials.txt to remember what you created
echo "Admin: dad_admin / MyPass123" > test_credentials.txt
echo "Emma: emma472 / Xy4jK9mN" >> test_credentials.txt
echo "Jake: jake234 / Bh7nP2wQ" >> test_credentials.txt
```

### Browser Dev Tools
```javascript
// Check setup status via API
fetch('/setup/status/')
  .then(r => r.json())
  .then(data => console.log(data))

// Should see:
// { setup_required: false, user_count: 3 }
```

---

## ✅ Success Criteria

Setup wizard is working if:
- ✅ Auto-redirects when no users exist
- ✅ All 4 steps are navigable
- ✅ Admin account is created
- ✅ Family members are created with auto-credentials
- ✅ Confetti plays on success
- ✅ Redirects to dashboard after completion
- ✅ Admin is logged in
- ✅ Setup is not accessible after completion

---

## 🎉 You're Ready!

Once all tests pass, your setup wizard is **DEMO-READY**! 🚀

This is going to blow judges away! 💥
