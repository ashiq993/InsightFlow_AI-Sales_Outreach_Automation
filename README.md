# InsightFlow AI - Sales Outreach Automation

### 👉 Dive into the full article: [**AI Agents + LangGraph: The Winning Formula for Sales Outreach Automation**](https://dev.to/kaymen99/how-ai-automation-can-transform-your-sales-outreach-strategy-aop)

![outreach-automation](https://github.com/user-attachments/assets/2685ef70-ab9f-4177-9b2a-71086f79726b)

**InsightFlow AI** is a comprehensive **AI-powered outreach system** designed to automate lead research, qualification, and engagement. It combines a powerful **FastAPI backend** with a modern **React frontend** to provide a seamless user experience.

The system analyzes **LinkedIn data**, company websites, and recent news to generate detailed **analysis reports** and **personalized outreach materials** (emails, interview scripts).

## 🚀 New Features (v2.0)

*   **Modern Frontend**: A sleek, responsive React application ("InsightFlow AI") with **Light/Dark mode** support.
*   **File Upload**: Drag & drop support for **CSV** and **Excel** files to bulk process leads.
*   **Real-Time Feedback**: Live **WebSocket-based console** showing the AI's thought process and progress in real-time.
*   **Google Drive Integration**: Automatically uploads processed reports and Excel files to your Google Drive.
*   **Dockerized**: Fully containerized with **Docker Compose** for easy deployment.

## ✨ Key Capabilities

### **Automated Lead Research**
- **LinkedIn Profile Scraping**: Collects details about leads and companies.
- **Digital Presence Analysis**: Evaluates websites, blogs, and social media (Facebook, Twitter, YouTube).
- **News Analysis**: Tracks recent company announcements.
- **Pain Point Identification**: Identifies challenges and matches them with your services.

### **Personalized Outreach**
- **Customized Reports**: Generates detailed audit reports for each lead.
- **Email Generation**: Crafts personalized emails referencing specific insights.
- **Interview Prep**: Creates tailored interview scripts with SPIN questions.

### **Efficient Workflow**
- **Cloud Storage**: All reports are saved to **Google Docs** and **Google Drive**.
- **Excel Export**: Download processed data with analysis results directly from the UI.

## 🛠️ Tech Stack

*   **Frontend**: React, Vite, CSS Variables (Theming)
*   **Backend**: Python, FastAPI, LangChain, LangGraph
*   **AI Models**: Google Gemini (Flash & Pro)
*   **Infrastructure**: Docker, Docker Compose

## 🔐 Google OAuth Setup (Important!)

**⚠️ REQUIRED FIRST STEP:** Before running the application with Docker, you need to generate a `token.json` file through Google OAuth authentication. This is because Docker containers cannot open a browser for interactive OAuth.

### Step 1: Get Google API Credentials

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project** (or select an existing one)
3. **Enable the following APIs:**
   - Gmail API
   - Google Drive API
   - Google Docs API
   - Google Sheets API
4. **Create OAuth 2.0 Credentials:**
   - Go to **APIs & Services** → **Credentials**
   - Click **"Create Credentials"** → **"OAuth client ID"**
   - Select **"Desktop app"** as application type
   - Download the credentials JSON file
   - **Rename it to `credentials.json`** and place it in the `backend/` directory

### Step 2: Generate `token.json` Locally

Since Docker can't open a browser for OAuth, you need to run the backend locally **once** to generate the authentication token.

#### Option A: Quick Token Generation (Recommended)

Create a simple script to generate the token:

```bash
# Navigate to backend directory
cd backend

# Create a Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install minimal dependencies
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Create token generation script
cat > generate_token.py << 'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

def generate_token():
    """Generate token.json through OAuth flow"""
    print("🔐 Starting OAuth authentication flow...")
    print("📌 Make sure credentials.json exists in the current directory!\n")
    
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save the credentials
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    
    print("\n✅ Success! token.json has been generated.")
    print("📂 You can now copy this file to your Docker container or use it locally.\n")

if __name__ == "__main__":
    generate_token()
EOF

# Run the token generation script
python generate_token.py
```

**What happens:**
1. A browser window will open automatically
2. Sign in with your Google account
3. Grant the requested permissions
4. The browser will show "The authentication flow has completed"
5. `token.json` will be created in the `backend/` directory ✅

#### Option B: Run Backend Locally (Alternative)

```bash
# Navigate to backend directory
cd backend

# Install all dependencies
pip install -r requirements.txt

# Run the backend server
python -c "from src.utils import get_google_credentials; get_google_credentials(); print('✅ token.json generated!')"
```

This will trigger the OAuth flow and generate `token.json`.

### Step 3: Verify Token Generation

Check that `token.json` exists:

```bash
ls -la backend/token.json
```

You should see the file with a size of ~1-2 KB.

### Step 4: Use with Docker

Now that you have `token.json`, your Docker container can use it without needing interactive authentication.

**Important:** The `token.json` file will be copied into the Docker container during build. If you need to update it (e.g., after token expiry), regenerate it locally and rebuild the container.

---

## 📦 Installation & Setup

### Option 1: Run with Docker (Recommended)

**Prerequisites:** Make sure you've completed the **🔐 Google OAuth Setup** section above and have `token.json` in the `backend/` directory.

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/ashiq993/InsightFlow_AI-Sales_Outreach_Automation.git
    cd InsightFlow_AI-Sales_Outreach_Automation
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the `backend/` directory based on `.env.example` and add your API keys.

3.  **Verify OAuth credentials:**
    ```sh
    # Make sure these files exist:
    ls backend/credentials.json  # Google OAuth credentials
    ls backend/token.json         # Generated authentication token
    ```

4.  **Run with Docker Compose:**
    ```sh
    docker-compose up --build
    ```
    *   Frontend: `http://localhost:5173`
    *   Backend: `http://localhost:8000`

### Option 2: Manual Setup

#### Backend
1.  Navigate to `backend/`:
    ```sh
    cd backend
    ```
2.  Create virtual environment and install dependencies:
    ```sh
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  Run the server:
    ```sh
    uvicorn server:app --reload
    ```

#### Frontend
1.  Navigate to `frontend/`:
    ```sh
    cd frontend
    ```
2.  Install dependencies:
    ```sh
    npm install
    ```
3.  Start the development server:
    ```sh
    npm run dev
    ```

## 📝 Usage

1.  Open the **InsightFlow AI** frontend (`http://localhost:5173`).
2.  **Upload a CSV/Excel file** containing lead information (Name, Email, Company, etc.).
3.  Click **"Start AI Analysis"**.
4.  Watch the **Live Console** as the AI researches each lead.
5.  Once complete, **Download** the processed file or view the reports in **Google Drive**.

---

## 🔧 Troubleshooting

### Issue: "Application stuck on loading screen"

**Symptom:** The backend starts but shows a URL like:
```
Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?...
```

**Cause:** OAuth authentication is trying to run inside Docker container, which cannot open a browser.

**Solution:** 
1. Stop Docker: `docker-compose down`
2. Follow the **🔐 Google OAuth Setup** section above to generate `token.json` locally
3. Verify the file exists: `ls backend/token.json`
4. Restart Docker: `docker-compose up --build`

---

### Issue: "Error: credentials.json not found"

**Cause:** Missing Google OAuth credentials file.

**Solution:**
1. Follow **Step 1** in the **🔐 Google OAuth Setup** section
2. Download OAuth credentials from Google Cloud Console
3. Rename to `credentials.json` and place in `backend/` directory
4. Generate `token.json` using the instructions

---

### Issue: "token.json expired" or "Invalid credentials"

**Symptom:** Application was working but now shows authentication errors.

**Cause:** The OAuth token has expired (tokens typically last 7 days to 6 months depending on settings).

**Solution:**
```bash
# Navigate to backend
cd backend

# Delete old token
rm token.json

# Regenerate token (using Option A from OAuth setup)
python generate_token.py

# Rebuild Docker
docker-compose down
docker-compose up --build
```

---

### Issue: "Chromium sandbox error"

**Error Message:**
```
ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:101] 
Running as root without --no-sandbox is not supported
```

**Cause:** This is a warning from Chrome/Chromium during OAuth flow.

**Impact:** This is safe to ignore. It's a security warning but doesn't affect functionality.

**Solution (Optional):** If it bothers you, you can suppress it by running as non-root user (advanced Docker configuration).

---

### Issue: "Pandas warnings in logs"

**Warnings like:**
- `SettingWithCopyWarning`
- `FutureWarning: Setting an item of incompatible dtype`

**Status:** These have been fixed in the latest version. Make sure you're using the updated code.

**Solution:** Pull the latest changes or rebuild:
```bash
git pull origin main
docker-compose down
docker-compose up --build
```

---

### Issue: "Cannot connect to backend"

**Symptom:** Frontend shows "Unable to connect to server"

**Diagnosis:**
1. Check if backend is running: `docker ps`
2. Check backend logs: `docker-compose logs backend`
3. Verify backend is accessible: `curl http://localhost:8000/health`

**Solution:**
- If backend isn't running, check for errors in `docker-compose logs backend`
- Verify port 8000 isn't being used by another application
- Check firewall settings

---

### Issue: "File upload fails"

**Symptom:** Upload button doesn't work or shows errors

**Common Causes:**
1. **File format:** Only CSV and XLSX files are supported
2. **Missing columns:** File must have columns like NAME, EMAIL, COMPANY
3. **File size:** Very large files (>100MB) may timeout

**Solution:**
- Use the provided sample CSV/Excel template
- Ensure required columns exist
- Break large files into smaller batches

---

### Getting More Help

If you encounter issues not covered here:

1. **Check logs:** `docker-compose logs backend` and `docker-compose logs frontend`
2. **Enable verbose logging:** Set `LOG_LEVEL=DEBUG` in your `.env` file
3. **Review the full error trace** in terminal output
4. **Check the Issue Analysis Report:** See `ISSUE_ANALYSIS_REPORT.md` for technical details

---

## 📄 License

This project is open-source and available under the MIT License.

## 🙏 Acknowledgments

Built with ❤️ using LangChain, LangGraph, and Google Gemini.

