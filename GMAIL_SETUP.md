# 🔥 1-MINUTE FRESH EMAIL SETUP GUIDE

## Getting Gmail API Credentials (REQUIRED)

### Step 1: Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search "Gmail API"
   - Click "Enable"

### Step 2: Create Desktop Application Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. **IMPORTANT**: Select "Desktop application" (NOT Service Account!)
4. Name it (e.g., "Email Assistant")
5. Download the JSON file

### Step 3: Setup in Project
1. Rename downloaded file to `credentials.json`
2. Move it to `backend/` folder
3. Structure should be:
   ```
   backend/
   ├── credentials.json  ← Your downloaded file here
   ├── app/
   └── requirements.txt
   ```

## 🔥 1-MINUTE FRESH FILTERING

Your system is now configured for **EXACTLY 1 MINUTE** fresh emails:
- ✅ Only emails from last 60 seconds
- ✅ Real-time timestamp checking  
- ✅ Clear logging of email age
- ✅ Precise filtering as you demanded

## Testing
1. Start backend: `uvicorn app.main:app --reload`
2. Start dashboard: `streamlit run dashboard/app.py`
3. Select category filter
4. Watch for 1-MINUTE FRESH emails only!

## Note
Without real credentials.json, the system will show the error message.
This is normal - just follow the setup steps above.
