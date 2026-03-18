# Clinical Audit AI - Frontend

This repository contains the dynamic Next.js React frontend for the Clinical Audit Intelligence Platform.

## Prerequisites

Before running the project, ensure you have the following installed on your machine:

1. **Node.js** (v18 or higher): Download from [nodejs.org](https://nodejs.org/)
2. **npm** (comes with Node.js)

## 1st Time Setup Guide

Follow these instructions to set up and run the frontend for the first time:

### 1. Install Dependencies
Open a terminal in this directory (`ai-audit-frontend`) and run:
```bash
npm install
```
*Depending on your internet speed, this may take a minute or two to download React, Next.js, and Tailwind CSS packages.*

### 2. Start the Development Server
Once dependencies are installed, start the local server by running:
```bash
npm run dev
```

### 3. Open in Browser
Open your browser and navigate to:
```text
http://localhost:3000
```

---

## Connecting to Backend
The frontend is currently fully decoupled and ready for a backend API. It attempts to communicate with `http://localhost:8000`.

- `/api/chat`: Main conversation API supporting filters.
- `/api/metrics`: Loads top statistics.
- `/api/conversations`: Fetches the History tab in the sidebar (falls back to mock UI gracefully if not found).
- `/api/user`: Loads the Auditor profile information.

If your backend is not yet started, the frontend will automatically use built-in dummy mock data to prevent visual crashing.
