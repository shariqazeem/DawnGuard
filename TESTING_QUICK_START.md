# ⚡ TESTING QUICK START - AI GUARDIAN

## 🚀 **3-MINUTE TEST**

### Step 1: Restart (30 seconds)
```bash
docker-compose restart
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Step 2: Create Test File (30 seconds)

Create `test_risky.txt` with this exact content:

```
My SSN: 123-45-6789
Credit card: 4532-1234-5678-9010
Password: secret123
Home address: 123 Main St
```

**IMPORTANT:** Make sure to use dashes in SSN: `123-45-6789` (not `123456789`)

### Step 3: Upload (1 minute)

1. Go to `http://localhost:8000/vault/`
2. Click "Upload File"
3. Select `test_risky.txt`
4. Wait for success message

### Step 4: Check Results (1 minute)

1. Click "**AI Guardian**" in navbar (orange link)
2. You should see:
   - ⚠️ **Big alert box** at top
   - 🔴 **Severity: High**
   - 🔐 **Detected: Personal Data**
   - 📝 **Keywords: ssn, credit card, password, address**

---

## ✅ **WHAT YOU SHOULD SEE**

### Guardian Dashboard (`/guardian/`)

**Safety Score:** ~0-50% (depends on how many safe files)

**Active Alert Box:**
```
⚠️ New Alert Detected

File: test_risky.txt
Uploaded by: [Your Name] (Admin)

🔐 Personal Data  📍 Privacy Concern

AI Analysis:
- Pattern detected: Personal Data
- Keyword: ssn
- Keyword: credit card
- Keyword: password
- Keyword: address

🚨 Recommendations:
⚠️ This file contains sensitive information
💡 Remove or redact personal data before uploading
```

**Stats Grid:**
- Files Scanned: 1
- Active Alerts: 1
- Safe Scans: 0

**Recent Scans Table:**
| File | Uploaded By | Scan Result | Severity |
|------|-------------|-------------|----------|
| test_risky.txt | You (Admin) | Personal Data, Privacy | High 🔴 |

---

## 🐛 **IF IT SHOWS "SAFE"**

### Check 1: SSN Format
Your file must have: `123-45-6789` (with dashes!)

### Check 2: File Content
Open your `test_risky.txt` and verify it contains:
- SSN with dashes
- Keywords: password, address

### Check 3: Verify Upload Location
- ✅ Upload to `/vault/`
- ❌ NOT `/dashboard/`

### Check 4: Check Logs
```bash
docker-compose logs web | tail -50
```

Look for:
- `AI Guardian scan`
- Any error messages

### Check 5: Verify Database
```bash
docker-compose exec web python manage.py shell
```

```python
from core.models import AIGuardianScan
scans = AIGuardianScan.objects.all()
print(f"Total scans: {scans.count()}")

if scans.exists():
    scan = scans.last()
    print(f"\nFile: {scan.file.name}")
    print(f"Severity: {scan.severity}")
    print(f"Risk Score: {scan.risk_score}")
    print(f"Patterns: {scan.detected_patterns}")
    print(f"Keywords: {scan.detected_keywords}")
    print(f"Categories: {scan.risk_categories}")
```

---

## 📋 **PATTERNS THAT WORK**

Copy these into your test file:

### SSN (High Risk)
```
SSN: 123-45-6789
Social Security Number: 987-65-4321
```

### Credit Card (High Risk)
```
Credit card: 4532 1234 5678 9010
Card: 1234-5678-9012-3456
```

### Phone (Medium Risk - via personal_data pattern)
```
Phone: 555-123-4567
Call: (555) 987-6543
```

### Email (via personal_data pattern)
```
Email: test@example.com
Contact: user@domain.org
```

### Keywords (Various Risk Levels)
```
password: mypass123
home address: 123 Main St
prescription: Amoxicillin
private information
confidential document
```

---

## 🎯 **BEST TEST FILE FOR DEMO**

**Filename:** `demo.txt`

```
CONFIDENTIAL FAMILY DATA

Emergency Contact:
Name: Emma Thompson
SSN: 123-45-6789
Credit Card: 4532-1234-5678-9010
Phone: (555) 123-4567
Email: emma@example.com
Home Address: 789 Oak Street
Password: Family2025!
Medical: Diabetes medication - Metformin 500mg

PRIVATE - DO NOT SHARE
```

**This file will trigger:**
- 🔴 High/Critical severity
- 🔴 Multiple patterns (SSN, credit card, phone, email)
- 🔴 Multiple keywords (password, address, medical, private)
- 🔴 3+ risk categories
- 🔴 Risk score 85+

---

## 🎬 **30-SECOND DEMO**

1. **Open `/vault/`** - "This is our family vault"
2. **Upload demo.txt** - "Let me upload a family document"
3. **Open `/guardian/`** - "Watch what happens..."
4. **Point to alert** - "AI Guardian caught SSN, credit card, medical info!"
5. **Point to stats** - "All scanned locally in milliseconds"
6. **Emphasize** - "Zero data left the Black Box!"

---

## 🏆 **SUCCESS CRITERIA**

Your AI Guardian is working if:

- ✅ Alert appears when uploading file with SSN `123-45-6789`
- ✅ Severity shows "High" or "Critical"
- ✅ Detected patterns list appears
- ✅ Keywords show up
- ✅ Recommendations appear
- ✅ Recent scans table shows the file
- ✅ Safety score calculates correctly

**If all checked ✅ → You're ready to win! 🏆**

---

**Good luck!** 🚀
