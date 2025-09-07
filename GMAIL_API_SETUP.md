# Gmail API Setup Instructions

## ⚠️ IMPORTANT: Current Issue & Solution

**The current `credentials.json` file is a placeholder and needs to be replaced with real OAuth2 Desktop Application credentials.**

## 🚀 Quick Solution Options

### Option 1: Create Real Gmail API Credentials (Recommended)

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create/Select Project**
3. **Enable Gmail API**: APIs & Services → Library → Search "Gmail API" → Enable
4. **Create OAuth2 Credentials**:
   - APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client IDs
   - Application Type: **Desktop Application**
   - Name: "AI Support Assistant"
   - Download the JSON file
5. **Replace `credentials.json`** in the root directory with the downloaded file

### Option 2: Use CSV Mode (Immediate Testing)

For immediate testing without Gmail API setup:
1. Click "� Load CSV" instead of "�📧 Load Inbox"
2. This loads sample emails from the CSV file
3. All features work the same way (analysis, drafts, sending via SMTP)

## 🔧 Current Error Explanation

**Error**: `"Client secrets must be for a web or installed app"`
**Cause**: The current `credentials.json` is a placeholder with Desktop Application structure, but needs real values from Google Cloud Console.

## 📧 Your Email Configuration (Already Set)

```env
# SMTP for sending replies (WORKING)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587  
SMTP_USER=........@gmail.com
SMTP_PASSWORD=.......

# Gmail API for reading emails (NEEDS SETUP)
GMAIL_USER=........
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
```

## 🎯 Testing Right Now

**Dashboard**: http://localhost:8501

**Options**:
1. **"� Load CSV"** - Works immediately with sample data
2. **"📧 Load Inbox"** - Requires real Gmail API credentials setup

## ⚡ Recommendation

Since you want to test the complete system quickly:
1. Use **"📁 Load CSV"** for immediate testing
2. Set up real Gmail API credentials when you're ready for production

Both options support the full AI pipeline:
- ✅ Email filtering & analysis
- ✅ Sentiment & priority scoring  
- ✅ Empathetic draft generation
- ✅ SMTP reply sending
- ✅ Analytics dashboard

The only difference is the data source (CSV vs live Gmail inbox).
