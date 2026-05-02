# The Civic Navigator 🗺️🗳️

**The Civic Navigator** is an interactive, privacy-first election assistant built to help users seamlessly navigate the voting process. 

Powered by **Gemini 3.1** via the `google-genai` SDK, it utilizes intelligent agent routing to automatically determine user intent and fetch real-time polling locations, add election deadlines to Google Calendar, generate digital "Add to Google Wallet" passes, and translate complex civic jargon—all without persistently storing any Personally Identifiable Information (PII).

## 🏗 Architecture
This project uses a decoupled, microservice-friendly architecture optimized for Google Cloud Run:

1. **Frontend (`/frontend`)**: A **Next.js (App Router)** application that serves the accessible UI and acts as a secure **Backend-For-Frontend (BFF)**. It handles Google OAuth 2.0 securely, ensuring tokens never leak to the client.
2. **Backend (`/backend`)**: A **Python FastAPI** application containing the AI Orchestration layer. It intercepts user queries, evaluates intent, and utilizes function calling to trigger the correct Google Service API.

## 🚀 Features
* **Google Civic Information Integration**: Finds local polling places and representatives.
* **Google Calendar Integration**: Automatically adds registration/voting deadlines with 24-hour reminders directly to the user's calendar.
* **Google Wallet Integration**: Generates a cryptographically signed JWT to provision a Digital Voter Readiness Pass.
* **Google Cloud Translation**: Uses an `@lru_cache` optimized pipeline to accurately translate complex voting jargon into the user's preferred language.

---

## 🛠️ Local Development Setup

### Prerequisites
- Node.js (v18+)
- Python 3.11+ (Conda recommended)
- A Google Cloud Project with the following APIs enabled:
  - Generative Language API
  - Google Civic Information API
  - Google Calendar API
  - Google Wallet API

### 1. Backend Setup (FastAPI + Gemini)
Navigate to the backend directory and set up the Python environment:
```bash
cd backend

# Create and activate environment (using conda)
conda create -n promptWars2-py311 python=3.11 -y
conda activate promptWars2-py311

# Install dependencies
pip install -r requirements.txt
```

**Environment Variables (`backend/.env`)**
Copy `.env.example` to `.env` and fill in your keys:
```env
GEMINI_API_KEY="your_gemini_api_key"
CIVIC_INFO_API_KEY="your_google_civic_api_key_here"
GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"
WALLET_ISSUER_ID="your_wallet_issuer_id"
```

**Run the Backend Server**:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup (Next.js)
In a new terminal, navigate to the frontend directory:
```bash
cd frontend

# Install dependencies
npm install
```

**Environment Variables (`frontend/.env.local`)**
```env
GOOGLE_CLIENT_ID="your_google_oauth_client_id"
GOOGLE_CLIENT_SECRET="your_google_oauth_client_secret"
NEXTAUTH_SECRET="your_random_secret_string"
NEXTAUTH_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8000"
```

**Run the Frontend**:
```bash
npm run dev
```

Visit `http://localhost:3000` to interact with The Civic Navigator!

## 🔒 Privacy & Security Note
**No PII Storage**: The backend strictly ensures that user email addresses and physical locations (addresses/zip codes) are used solely as ephemeral context parameters. They are scrubbed from logs and wiped immediately after the HTTP response is completed. 
