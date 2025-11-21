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

## 📦 Installation & Setup

### Option 1: Run with Docker (Recommended)

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/ashiq993/InsightFlow_AI-Sales_Outreach_Automation.git
    cd InsightFlow_AI-Sales_Outreach_Automation
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the `backend/` directory based on `.env.example` and add your API keys.

3.  **Run with Docker Compose:**
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

