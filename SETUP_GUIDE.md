# Setup Guide for Developers

This guide explains how to set up the Uki Smart Attendance System locally.

## 🚀 Quick Start (5 Minutes)

### For Team Developers Using Shared Credentials

Since the project is already set up with shared OAuth credentials, new developers **do NOT need to create their own project**. Just follow these simple steps:

#### Step 1: Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/Uki-Smart-Attendance-System.git
cd Uki-Smart-Attendance-System
```

#### Step 2: Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Step 3: Get Shared Credentials from Project Lead
Contact the project owner and get:
- **`client_secrets.json`** file (via email/Slack)
- **Test Gmail credentials** (email & password)

#### Step 4: Place client_secrets.json
```bash
# Place the file in the project root
# Should look like:
# ~/Uki-Smart-Attendance-System/
# ├── client_secrets.json  ← Place it here
# ├── app.py
# ├── config.py
# └── ...
```

#### Step 5: Authorize with Test Gmail
```bash
source venv/bin/activate
python setup_oauth.py
```

A browser will open. **Sign in with the test Gmail credentials** provided by project lead.
- ✅ Click "Allow" to authorize
- ✅ Your **own `token.json`** will be created automatically
- ✅ This is machine-specific and stays local

#### Step 6: Run the Application
```bash
python app.py
```

Access at: **http://127.0.0.1:5050**

---

## 📝 What You Get vs. What's Shared

| Item | Status | Notes |
|------|--------|-------|
| `client_secrets.json` | 📤 Shared | OAuth project credential (same for all developers) |
| `token.json` | 👤 Personal | Each developer gets their own (machine-specific) |
| Test Gmail Account | 📤 Shared | Everyone uses same test account for OAuth |
| Code (`app.py`, etc.) | 📤 Shared | Git repository |

---

## ✅ What's Next?

✅ You can now:
- Start the app: `python app.py`
- Check in/check out with face recognition
- Upload attendance to shared Google Drive
- Collaborate with team!

❌ Never commit:
- `token.json` (blocked by `.gitignore`)
- Your own credentials
- Sensitive files

---

## 🔒 Important Security Notes

### Your token.json
- ✅ Automatically created when you run `setup_oauth.py`
- ✅ Unique to your machine
- ✅ Safe to keep locally
- ❌ Never share or commit it

### Test Gmail Account
- ✅ Shared among team
- ✅ Used for OAuth authorization
- ❌ Keep password secure
- ❌ Don't change account settings

### client_secrets.json
- ✅ Shared among team
- ✅ Safe to share (it's the project credential)
- ❌ Don't lose it - keep a backup

---

## 🐛 Troubleshooting

### Error: "Access blocked: Uki Attendance System has not completed Google verification"
**Solution**: This shouldn't happen if you sign in with the correct test Gmail. Contact project lead.

### Error: "No OAuth token found"
**Solution**: Run `python setup_oauth.py` and complete browser authorization with test Gmail.

### Multiple sheets being created in Google Drive
**Solution**: Restart the app (`python app.py`).

### Can't find client_secrets.json
**Solution**: Make sure it's in the project root directory (same folder as `app.py`).

---

## 👥 Setting Up Individual OAuth (Optional)

If you want your own OAuth project instead of using shared credentials:

1. Follow the detailed Google Drive Setup section below
2. Create your own `client_secrets.json`
3. Run `python setup_oauth.py` with your own account
4. Get your own `token.json`

This is NOT required for team development with shared credentials.

---

## 🌐 Google Drive Setup (Individual - Optional)

If you're setting up your own OAuth project:

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Create New Project**
3. Name it: `Uki Attendance System - [Your Name]`
4. Click **Create**

### Step 2: Enable Google Drive API

1. Search for **Google Drive API**
2. Click on it and press **Enable**

### Step 3: Create OAuth 2.0 Credentials

1. Go to **Credentials** (left sidebar)
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, click **Configure OAuth consent screen**:
   - Choose **External**
   - Add app name: `Uki Attendance System`
   - Add your email as a test user
   - Save
4. Back to Credentials, click **Create Credentials** → **OAuth client ID**
5. Select **Desktop application**
6. Click **Create**
7. Click **Download** button (arrow icon)
8. Rename file to `client_secrets.json`
9. Place in project root

### Step 4: First-Time Authorization

```bash
source venv/bin/activate
python setup_oauth.py
```

Sign in with your Google account and click **Allow**.
- ✅ `token.json` will be created automatically
- ✅ You won't need to authorize again

---

## 📊 Development Workflow

```bash
# Make changes
git add .
git commit -m "Feature: Add new functionality"

# Push to GitHub
git push origin main
```

**Note:** Git will automatically skip credentials (`.gitignore` blocks them).

---

## 🆘 Need Help?

- See [GITHUB_DEPLOYMENT.md](GITHUB_DEPLOYMENT.md) for sharing guide
- See [README.md](README.md) for feature documentation
- Contact project lead for credential issues

---

**Happy coding! 🚀**
