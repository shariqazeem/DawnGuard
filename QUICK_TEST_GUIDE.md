# ⚡ QUICK TEST GUIDE - AI GUARDIAN REAL-TIME

## 🚀 Step-by-Step Testing

### 1️⃣ **Restart & Migrate** (2 minutes)

```bash
# In your terminal:
docker-compose restart
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

**Expected output:**
```
Creating migration core/0008_aiguardianscan_aiguardianalert...
Running migrations:
  Applying core.0008_aiguardianscan_aiguardianalert... OK
```

---

### 2️⃣ **Create Test Files** (1 minute)

Create these files on your computer:

#### **test_safe.txt**
```
This is my homework for school.
I learned about Python programming today.
It was fun and educational!
```

#### **test_risky.txt**
```
Personal Information:
Name: Emma Smith
SSN: 123-45-6789
Credit Card: 4532-1234-5678-9010
Home Address: 456 Oak Street, Anytown
Password: mySecretPass123
Medical: diabetes medication
```

---

### 3️⃣ **Upload & Test** (3 minutes)

1. **Login to your app** at `http://localhost:8000`

2. **Go to Family Vault**
   - Click "Vault" in navbar
   - Or navigate to `/vault/`

3. **Upload test_safe.txt**
   - Click upload button
   - Select `test_safe.txt`
   - Wait for upload confirmation

4. **Upload test_risky.txt**
   - Click upload button
   - Select `test_risky.txt`
   - Wait for upload confirmation

5. **Go to AI Guardian**
   - Click "AI Guardian" in navbar (orange link)
   - Or navigate to `/guardian/`

---

### 4️⃣ **Verify Results**

You should see:

#### **Safety Score**
- Should be around **50%** (1 safe file, 1 risky file)

#### **Stats Grid**
- **Files Scanned:** 2
- **Active Alerts:** 1
- **Safe Scans:** 1

#### **Active Alert** (Big yellow/red box)
- **File:** test_risky.txt
- **Severity:** High or Critical
- **Detected Patterns:**
  - ✅ SSN format
  - ✅ Credit Card
- **Detected Keywords:**
  - ✅ password
  - ✅ address
  - ✅ medical

#### **Recent Scans Table**
- **Row 1:** test_risky.txt - High/Critical severity
- **Row 2:** test_safe.txt - Safe severity

---

### 5️⃣ **Verify in Database** (Optional)

```bash
docker-compose exec web python manage.py shell
```

```python
from core.models import AIGuardianScan, AIGuardianAlert

# Check scans
scans = AIGuardianScan.objects.all()
print(f"Total scans: {scans.count()}")

for scan in scans:
    print(f"\nFile: {scan.file.name}")
    print(f"Severity: {scan.severity}")
    print(f"Risk Score: {scan.risk_score}")
    print(f"Patterns: {scan.detected_patterns}")
    print(f"Keywords: {scan.detected_keywords}")

# Check alerts
alerts = AIGuardianAlert.objects.all()
print(f"\nTotal alerts: {alerts.count()}")

for alert in alerts:
    print(f"\nAlert: {alert.title}")
    print(f"Type: {alert.alert_type}")
    print(f"Status: {alert.status}")
```

---

## ✅ SUCCESS CHECKLIST

- [ ] Migration created successfully
- [ ] Can access `/guardian/` page
- [ ] Can upload files to `/vault/`
- [ ] Safe file shows green "Safe" badge
- [ ] Risky file shows red "High/Critical" badge
- [ ] Active alert appears at top of Guardian page
- [ ] Stats grid shows real numbers (2 scans, 1 alert)
- [ ] Recent scans table shows both files
- [ ] Safety score calculates correctly (~50%)

---

## 🐛 TROUBLESHOOTING

### **Problem:** Migration fails
**Solution:**
```bash
docker-compose down
docker-compose up -d
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### **Problem:** Guardian page is blank
**Check:**
1. Is family member profile created? (should auto-create)
2. Are files uploaded to vault? (not just documents)
3. Check Docker logs: `docker-compose logs web`

### **Problem:** Files not showing in scans
**Check:**
1. Upload via `/vault/` not `/dashboard/`
2. Make sure files are text-based (.txt, .pdf, .doc)
3. Check vault_views.py is importing ai_guardian

### **Problem:** No alerts appearing
**Verify:**
1. Upload file with actual patterns: SSN (123-45-6789)
2. Check severity is medium/high/critical
3. Verify you're logged in as admin

---

## 📸 SCREENSHOT CHECKLIST FOR DEMO

Take screenshots of:

1. **Vault upload** - Uploading test_risky.txt
2. **Guardian dashboard** - Showing active alert
3. **Stats grid** - Real numbers
4. **Recent scans table** - Both files listed
5. **Alert detail** - Showing detected patterns

---

## 🎬 DEMO SCRIPT (30 seconds)

> "Let me show you AI Guardian in action. I'm going to upload a file that contains personal data..."
>
> *Upload test_risky.txt to vault*
>
> "Now watch what happens when I go to the Guardian dashboard..."
>
> *Navigate to /guardian/*
>
> "AI Guardian has already scanned the file and detected an SSN, credit card number, and password. It immediately flagged this as high risk and notified me as the admin."
>
> *Point to alert box*
>
> "All of this scanning happened locally on the Black Box in milliseconds. No data was sent to the cloud. This is true privacy protection for families."

---

## 🏆 YOU'RE READY!

If all checks pass, your AI Guardian is **production-ready** and will blow judges' minds! 🎉

*Now go practice that demo and win the hackathon!* 🚀
