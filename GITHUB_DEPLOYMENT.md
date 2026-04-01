# GitHub Deployment & Sharing Guide

## 📤 Push Changes to GitHub

### Step 1: Check Git Status

```bash
git status
```

You should see `.gitignore` is marked (credentials ARE protected):
```
modified:   .gitignore
new file:   SETUP_GUIDE.md
modified:   README.md
```

**Important**: You should NOT see:
- `token.json`
- `client_secrets.json`

(They're blocked by `.gitignore`)

### Step 2: Stage Changes

```bash
# Stage only safe files (credentials excluded automatically)
git add .
```

### Step 3: Commit

```bash
git commit -m "Add Google Drive integration and setup guides"
```

### Step 4: Push to GitHub

```bash
git push origin main
```

Or if you haven't set up GitHub yet:

```bash
# Initialize repository
git init

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/Uki-Smart-Attendance-System.git

# Push
git push -u origin main
```

---

## 👥 Sharing with Other Developers

### Option 1: Shared Test Credentials (Recommended for Teams)

**Project Owner Does:**
1. Creates OAuth credentials in Google Cloud
2. Adds all team members as **test users** in OAuth consent screen
3. Downloads `client_secrets.json`
4. Shares file **securely** (email/Slack, NOT GitHub)

**Each Developer Does:**
1. Clones repository from GitHub
2. Receives `client_secrets.json` from project owner
3. Places file in project root:
   ```bash
   # Place in project root
   ~/Uki-Smart-Attendance-System/client_secrets.json
   ```
4. Runs OAuth setup:
   ```bash
   source venv/bin/activate
   python setup_oauth.py
   ```
5. Authorizes with **shared test Gmail** account
6. Gets their own `token.json` (stays local)

### Option 2: Individual Credentials (For Independent Developers)

Each developer:
1. Creates their own OAuth credentials
2. Runs `python setup_oauth.py`
3. Gets their own `token.json`

---

## 🔒 Security Checklist Before Pushing

✅ Make sure these are NOT committed:
```bash
# Check .gitignore blocks these:
git check-ignore -v token.json
git check-ignore -v client_secrets.json

# Should output:
# .gitignore:1:             token.json
# .gitignore:2:             client_secrets.json
```

✅ Verify nothing sensitive in commit:
```bash
git diff --cached | grep -i "secret\|token\|password"
# Should return nothing
```

✅ Only safe files are staged:
```bash
git status

# Should show:
# modified:   .gitignore
# modified:   README.md
# new file:   SETUP_GUIDE.md
# google_drive_service.py (no secrets here, code is safe)
```

---

## 📋 Files Safe to Commit

✅ **These are OK to push:**
- `app.py` - Flask app code
- `google_drive_service.py` - Drive integration (no secrets in code)
- `attendance_service.py` - CSV logic
- `face_engine.py` - Face recognition
- `config.py` - Configuration (no actual credentials)
- `requirements.txt` - Dependencies
- `.gitignore` - Security rules
- `README.md` - Documentation
- `SETUP_GUIDE.md` - Setup instructions
- `templates/` - HTML/JS frontend
- `setup_oauth.py` - OAuth setup script

❌ **These are BLOCKED (won't commit):**
- `token.json` - Personal OAuth token
- `client_secrets.json` - OAuth credentials
- `.env` - Environment variables (if you add them)
- `venv/` - Virtual environment

---

## 🚀 New Developer Onboarding

Give new developers this one-liner:

```bash
# 1. Clone repo
git clone https://github.com/YourUsername/Uki-Smart-Attendance-System.git
cd Uki-Smart-Attendance-System

# 2. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Ask project lead for client_secrets.json
# (Or create your own OAuth credentials)

# 4. Place client_secrets.json in project root

# 5. Authorize
python setup_oauth.py

# 6. Run app
python app.py
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

---

## 📧 Sharing Credentials Safely

### For `client_secrets.json`:

❌ **NEVER:**
- Email as plain text
- Slack in public channels
- GitHub (will be rejected by .gitignore anyway)
- Google Drive shared publicly

✅ **DO:**
- Email with encryption
- Private Slack message
- Password-protected email
- Share link only with team members

### For Test Gmail Account:

✅ Share credentials in a **separate**, **secure** channel:
- Private password manager (1Password, LastPass)
- Encrypted email
- Secure note sharing (Apple Notes iCloud, Notion private)

**Example message:**
```
Test Gmail for OAuth testing:
Email: test.attendance@gmail.com
Password: [ENCRYPTED PASSWORD]
```

---

## 🔧 Troubleshooting GitHub Setup

**Issue: "push rejected because .gitignore"**
- Solution: This means secrets were blocked ✅ (Good!)

**Issue: "token.json is being tracked"**
```bash
# Remove it from tracking
git rm --cached token.json

# Commit removal
git commit -m "Remove token.json from tracking"

# Push
git push
```

**Issue: "I accidentally committed credentials"**
```bash
# Remove from history
git filter-branch --tree-filter 'rm -f token.json client_secrets.json' HEAD

# Force push (careful!)
git push -f origin main

# Regenerate credentials (they're now public!)
```

---

## ✅ Ready to Deploy!

Your project is now:
- ✅ Secured with `.gitignore`
- ✅ Ready for team sharing
- ✅ Well-documented for new developers
- ✅ Has safe OAuth integration

Push and share with your team! 🚀
