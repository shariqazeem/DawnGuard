# 📁 TEST FILES FOR AI GUARDIAN

Create these files on your computer and upload them to test AI Guardian!

---

## ✅ **TEST 1: Safe File** (Should show GREEN "Safe")

**Filename:** `homework.txt`

**Content:**
```
My Homework Assignment

Today I learned about Python programming.
I created a simple calculator that can add and subtract numbers.
Here is the code:

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

This was a fun project!
```

**Expected Result:**
- ✅ Severity: **Safe**
- ✅ Risk Score: **0**
- ✅ No alerts created

---

## 🚨 **TEST 2: High Risk - SSN Only** (Should show RED "High")

**Filename:** `test_ssn.txt`

**Content:**
```
Employee Records

John Doe
SSN: 123-45-6789
Department: Sales

Jane Smith
Social Security Number: 987-65-4321
Department: Marketing
```

**Expected Result:**
- 🚨 Severity: **High**
- 🚨 Risk Score: **75+**
- 🚨 Patterns Detected: **Personal Data**
- 🚨 Keywords: **ssn, social security**
- 🚨 Alert Created: **YES**

---

## 🔴 **TEST 3: Critical Risk - Multiple Issues** (Should show RED "Critical/High")

**Filename:** `sensitive_data.txt`

**Content:**
```
CONFIDENTIAL FAMILY INFORMATION

Personal Details:
Name: Emma Thompson
SSN: 456-78-9123
Credit Card: 4532 1234 5678 9010
Phone: 555-123-4567
Email: emma@example.com

Home Information:
Address: 123 Oak Street, Los Angeles, CA 90001
Password: MySecret123!

Medical:
Prescription: Amoxicillin 500mg
Diagnosis: Type 2 Diabetes
```

**Expected Result:**
- 🔴 Severity: **High** (personal_data has highest severity)
- 🔴 Risk Score: **85-95**
- 🔴 Patterns Detected: **Personal Data, Privacy Concern**
- 🔴 Keywords: **ssn, credit card, password, address, prescription, medical**
- 🔴 Categories: **personal_data, privacy_concern, medical**
- 🔴 Alert Created: **YES** (Big red alert!)

---

## ⚠️ **TEST 4: Medium Risk - Privacy** (Should show YELLOW "Medium")

**Filename:** `contact_info.txt`

**Content:**
```
Family Contact List

Mom: (555) 111-2222
Address: 456 Maple Drive

Dad: (555) 333-4444
Location: Same as above

School: (555) 555-6666
Private notes about pickup
```

**Expected Result:**
- ⚠️ Severity: **Medium**
- ⚠️ Risk Score: **50-60**
- ⚠️ Patterns Detected: **Privacy Concern**
- ⚠️ Keywords: **address, location, phone number, private**
- ⚠️ Alert Created: **YES**

---

## 🔴 **TEST 5: Critical - Explicit Content** (Should show RED "Critical")

**Filename:** `flagged_content.txt`

**Content:**
```
This file contains explicit adult content.
NSFW material.
Pornography warning.
```

**Expected Result:**
- 🔴 Severity: **Critical**
- 🔴 Risk Score: **95**
- 🔴 Keywords: **explicit, nsfw, adult, pornography**
- 🔴 Alert Created: **YES** (Immediate alert!)

---

## ⚠️ **TEST 6: Violence Warning** (Should show RED "High")

**Filename:** `story.txt`

**Content:**
```
Action Story

The hero grabbed the weapon.
There was a threat of violence.
Someone shouted about guns and harm.
The villain wanted to kill the hero.
```

**Expected Result:**
- 🚨 Severity: **High**
- 🚨 Risk Score: **75**
- 🚨 Keywords: **weapon, violence, threat, gun, harm, kill**
- 🚨 Alert Created: **YES**

---

## 📊 **TESTING CHECKLIST**

Upload files in this order and verify results:

### 1. Upload `homework.txt`
- [ ] Shows "Safe" in Guardian dashboard
- [ ] Green badge in recent scans
- [ ] No alert created
- [ ] Safety score = 100%

### 2. Upload `test_ssn.txt`
- [ ] Shows "High" severity
- [ ] Red badge in recent scans
- [ ] Alert appears at top of Guardian page
- [ ] Safety score drops to ~50%
- [ ] Alert shows detected SSN pattern

### 3. Upload `sensitive_data.txt`
- [ ] Shows "High" or "Critical" severity
- [ ] Multiple badges (Personal Data, Privacy, Medical)
- [ ] Big alert with multiple detected issues
- [ ] Shows SSN, credit card, password keywords
- [ ] Recommendations appear

### 4. View Guardian Dashboard (`/guardian/`)
- [ ] Safety Score: ~25-33% (1 safe, 2 risky)
- [ ] Total Scans: 3
- [ ] Active Alerts: 2
- [ ] Recent Scans table shows all 3 files
- [ ] Alert details show actual detected patterns

---

## 🎯 **DEMO FILE** (Best for judges)

**Filename:** `family_documents.txt`

**Content:**
```
FAMILY INFORMATION - CONFIDENTIAL

Emergency Contact Information:

Dad: John Smith
SSN: 123-45-6789
Phone: (555) 987-6543
Email: john@email.com

Mom: Sarah Smith
Social Security: 987-65-4321
Credit Card: 4532-8765-1234-9876

Kids:
Emma (Age 10) - Prescription: Adderall 10mg
Jake (Age 8) - Medical: ADHD diagnosis

Home Address: 789 Pine Street, Austin, TX 78701
Security Password: FamilyHome2025!

PRIVATE - DO NOT SHARE
```

**Why this is perfect for demo:**
- ✅ Contains **multiple** risk types
- ✅ Looks like **real family data**
- ✅ Will trigger **HIGH/CRITICAL** alert
- ✅ Shows **all detection capabilities**:
  - SSN patterns (2)
  - Credit card pattern (1)
  - Email pattern (2)
  - Phone pattern (1)
  - Keywords: ssn, social security, credit card, password, address, prescription, medical, private

**Expected in Guardian Dashboard:**
- 🚨 Huge red/yellow alert box
- 🚨 Title: "🚨 family_documents.txt - HIGH Risk"
- 🚨 Detected Patterns: Personal Data
- 🚨 Detected Keywords: ssn, credit card, password, address, prescription, medical, private
- 🚨 Risk Categories: personal_data, privacy_concern, medical
- 🚨 Recommendations appear with action buttons

---

## 🐛 **TROUBLESHOOTING**

### Problem: All files show "Safe"

**Check:**
1. Did you restart Docker after adding migration?
   ```bash
   docker-compose restart
   docker-compose exec web python manage.py migrate
   ```

2. Is the file content actually text?
   - Make sure you created `.txt` files
   - Content should be plain text

3. Check if scanning is running:
   ```bash
   docker-compose logs web | grep "Guardian"
   ```

### Problem: No patterns detected even with SSN

**Verify SSN format:**
- ✅ Correct: `123-45-6789` (dashes required)
- ❌ Wrong: `123456789` (no dashes)
- ❌ Wrong: `123 45 6789` (spaces)

### Problem: Scans not appearing in dashboard

**Check:**
1. Are you uploading to `/vault/` (not `/dashboard/`)?
2. Is FamilyMember profile created?
3. Check database:
   ```bash
   docker-compose exec web python manage.py shell
   >>> from core.models import AIGuardianScan
   >>> AIGuardianScan.objects.all()
   ```

---

## 🎬 **DEMO SCRIPT** (30 seconds)

1. **"Let me show you AI Guardian protecting our family..."**

2. *Upload `family_documents.txt`*
   - "I'm uploading what looks like a normal family file..."

3. *Navigate to `/guardian/`*
   - "AI Guardian scanned it in milliseconds..."
   - *Point to alert*
   - "And immediately detected 2 SSNs, a credit card, medical info, and passwords!"

4. **"All of this happened locally on the Black Box. Zero data left the device."**

5. *Point to recommendations*
   - "It even tells me exactly what to do - restrict access, remove sensitive data."

6. **"This is how HomeGuardian AI protects families with local AI."**

---

**Now create these files and test!** 🚀
