# Clinical Audit AI — Project Documentation

> **EXL Audit Intelligence Platform** — A full-stack AI-powered clinical audit analysis tool.  
> Built with **Next.js 16** (Frontend) + **FastAPI** + **DuckDB** + **Groq LLM** (Backend).

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Backend — File-by-File Breakdown](#backend--file-by-file-breakdown)
4. [Frontend — File-by-File Breakdown](#frontend--file-by-file-breakdown)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Environment Variables](#environment-variables)
8. [How the Query Pipeline Works](#how-the-query-pipeline-works)

---

## Quick Start

### Prerequisites

- **Python 3.10+** (for the backend)
- **Node.js 18+** & **npm** (for the frontend)
- A **Groq API Key** (free at [console.groq.com](https://console.groq.com))

### 1. Start the Backend

```bash
cd backend

# Create a virtual environment (first time only)
python -m venv venv

# Activate it
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Set up your API key — create/edit the .env file:
# GROQ_API_KEY=gsk_your_key_here

# Load data into DuckDB (first time only)
python scripts/load_data.py

# Start the server
uvicorn app.main:app --port 8000 --reload
```

The backend will be live at **http://localhost:8000**.

### 2. Start the Frontend

```bash
cd ai-audit-frontend

# Install dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

The frontend will be live at **http://localhost:3000**.

### 3. Open the App

Navigate to **http://localhost:3000** in your browser. You should see the Clinical Audit AI welcome screen with live metrics.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 16)                │
│                  http://localhost:3000                   │
│                                                         │
│  page.tsx ─── Sidebar.tsx ─── SuggestedPrompts.tsx      │
│      │                             │                    │
│      │        ChatMessage.tsx      │                    │
│      │         (Markdown +         │                    │
│      │          Charts +           │                    │
│      │          Follow-ups)        │                    │
│      │                             │                    │
│      ▼                             ▼                    │
│  POST /chat/chats/{id}/ask    POST /api/metrics         │
└──────────────┬─────────────────────┬────────────────────┘
               │                     │
               ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                     │
│                  http://localhost:8000                   │
│                                                         │
│  main.py ──── chat_routes.py ──── query_service.py      │
│                                       │                 │
│                              ┌────────┼────────┐        │
│                              ▼        ▼        ▼        │
│                         sql_service  llm_service  chart  │
│                              │       (Groq API)  service│
│                              ▼                          │
│                          DuckDB                         │
│                   (clinical_audit.db)                    │
│                    20,000 audit records                  │
└─────────────────────────────────────────────────────────┘
```

### Data Flow (User Asks a Question)

1. User types a question in the frontend input bar
2. Frontend sends `POST /chat/chats/{chatId}/ask` with the question
3. Backend generates a SQL query using Groq LLM (LLaMA 3.3 70B)
4. SQL is executed against DuckDB to get real data
5. Data is sent back to the LLM to generate a formatted Markdown answer
6. A Plotly chart is generated and saved as an HTML file
7. Backend returns: `{ answer, sql, data, chartPath, chartType, xKey, yKey }`
8. Frontend renders the Markdown answer, chart iframe, and clickable follow-up suggestions

---

## Backend — File-by-File Breakdown

```
backend/
├── .env                          # Environment variables (GROQ_API_KEY)
├── requirements.txt              # Python dependencies
├── scripts/
│   └── load_data.py              # One-time script to load Excel → DuckDB
└── app/
    ├── __init__.py               # Python package marker
    ├── main.py                   # FastAPI app entry point
    ├── api/
    │   ├── __init__.py
    │   └── chat_routes.py        # API route handlers
    ├── core/
    │   ├── __init__.py
    │   └── prompts.py            # LLM system prompts
    ├── db/
    │   ├── __init__.py
    │   ├── db.py                 # DuckDB connection manager
    │   └── repository.py         # Database CRUD operations
    ├── services/
    │   ├── __init__.py
    │   ├── llm_service.py        # Groq API client wrapper
    │   ├── sql_service.py        # SQL generation from natural language
    │   ├── query_service.py      # Main query orchestrator
    │   └── chart_service.py      # Plotly chart generation
    └── utils/
        ├── __init__.py
        └── context_builder.py    # Chat history context formatter
```

### `app/main.py` — FastAPI Application Entry Point

- Creates the FastAPI app instance with CORS middleware (allows frontend at `localhost:3000`)
- Mounts `/charts` as a static file directory so generated Plotly HTML charts can be served
- Registers all chat routes under the `/chat` prefix
- Defines the `POST /api/metrics` endpoint that returns live dashboard metrics from DuckDB
- The metrics endpoint accepts `preFilters` (quarter, lineOfBusiness, program) and builds SQL `WHERE` clauses to filter the data dynamically

### `app/api/chat_routes.py` — API Route Handlers

- `POST /chat/chats` — Creates a new conversation session (returns a UUID `chat_id`)
- `GET /chat/chats` — Lists all conversations with their titles and timestamps
- `DELETE /chat/chats/{chat_id}` — Deletes a conversation and all its messages
- `POST /chat/chats/{chat_id}/ask` — The main query endpoint. Accepts `{ question, preFilters }` and delegates to `query_service.handle_query()`
- `GET /chat/chats/{chat_id}` — Returns all messages for a conversation (for loading chat history)

### `app/core/prompts.py` — LLM System Prompts

Contains three prompt templates:
- **`SQL_PROMPT`** — Instructs the LLM to generate a valid DuckDB SQL query from a natural language question. Includes schema information and strict formatting rules (no markdown wrapping, no row limits, etc.)
- **`TITLE_PROMPT`** — Instructs the LLM to generate a short conversation title (5 words max) from the user's first question
- **`INSIGHT_PROMPT`** — Instructs the LLM to format the final answer as clean Markdown with sections: Answer, Key Insights, and Suggested Follow-ups. Explicitly prohibits Data Summary, SQL queries, and hallucinated data in the response

### `app/db/db.py` — DuckDB Connection Manager

- Provides `get_connection()` which returns a DuckDB connection to `clinical_audit.db`
- The database file path is resolved relative to the script's location (not the working directory) to avoid path issues

### `app/db/repository.py` — Database CRUD Operations

- `init_tables()` — Creates the `chats` and `messages` tables if they don't exist
- `create_chat()` — Inserts a new chat with a UUID and returns the ID
- `get_chats()` — Returns all chats ordered by creation time (newest first)
- `delete_chat(chat_id)` — Deletes a chat and all its associated messages
- `update_chat_title(chat_id, title)` — Updates the title of a chat (called after the LLM generates a title from the first message)
- `save_message(chat_id, role, content, sql, chart_path)` — Saves a message to the database
- `get_messages(chat_id)` — Returns all messages for a chat as JSON-serializable dicts

### `app/services/llm_service.py` — Groq API Client

- Wraps the **Groq Python SDK** to provide a simple `generate(messages)` interface
- Uses the `llama-3.3-70b-versatile` model (fast, high-quality, large context window)
- Reads `GROQ_API_KEY` from the `.env` file
- Accepts OpenAI-compatible message format: `[{"role": "system", "content": "..."}, ...]`

### `app/services/sql_service.py` — SQL Generation

- `get_schema()` — Reads the `audits` table schema from DuckDB and formats it as a string
- `generate_sql(llm, question, context, error)` — Sends the question + schema to the LLM and asks it to generate a SQL query. If a previous SQL attempt failed, the error message is included for the LLM to self-correct
- Strips markdown code fences (` ```sql ... ``` `) that the LLM sometimes wraps around SQL
- Validates that the output contains a `SELECT` statement

### `app/services/query_service.py` — Main Query Orchestrator

This is the **brain** of the backend. When a user asks a question, this service:

1. Saves the user's message to the database
2. If it's the first message, generates a conversation title via the LLM
3. Builds conversation context from chat history
4. Calls `sql_service.generate_sql()` to create a SQL query
5. Executes the SQL against DuckDB (with retry on failure)
6. If SQL completely fails, returns a graceful error message instead of crashing
7. Asks the LLM whether a chart should be generated (and if so, what type/columns)
8. Calls `chart_service.generate_chart()` to create a Plotly HTML chart
9. Generates the final formatted answer using the `INSIGHT_PROMPT`
10. Saves the assistant's response and returns everything to the frontend

### `app/services/chart_service.py` — Plotly Chart Generation

- `generate_chart(df, chart_type, x_col, y_col)` — Creates a Plotly chart from a DataFrame
- Supports `bar`, `line`, and `pie` chart types
- Saves charts as standalone HTML files in the `charts/` directory
- Returns the URL path (e.g., `/charts/abc123.html`) for the frontend to embed as an iframe

### `app/utils/context_builder.py` — Chat History Formatter

- `build_context(messages)` — Converts the raw message list into OpenAI-compatible message format (`[{"role": "user", "content": "..."}, ...]`)
- Handles both dict format (new messages) and tuple format (legacy messages) for backwards compatibility

### `scripts/load_data.py` — Data Loader

- One-time script that reads `UM_Clinical_Audit_2025_Synthetic.xlsx` and loads it into the DuckDB `audits` table
- Resolves file paths relative to its own location

---

## Frontend — File-by-File Breakdown

```
ai-audit-frontend/
├── app/
│   ├── globals.css               # Global styles + Tailwind v4 config
│   ├── layout.tsx                # Root HTML layout wrapper
│   └── page.tsx                  # Main application page
├── components/
│   ├── ChatMessage.tsx           # AI/User message renderer
│   ├── Sidebar.tsx               # Sidebar with history + filters
│   ├── SuggestedPrompts.tsx      # Welcome dashboard with metrics
│   ├── DynamicChart.tsx          # React chart component (legacy)
│   └── DeleteConfirmationModal.tsx # Conversation delete modal
├── lib/
│   └── utils.ts                  # Shared utility functions
├── package.json                  # npm dependencies
├── tailwind.config.ts            # Tailwind configuration
└── next.config.ts                # Next.js configuration
```

### `app/page.tsx` — Main Application Page (Home)

The central orchestrator of the entire frontend. Manages:

- **State Management**: `input`, `messages`, `activeChatId`, `appliedFilters`, sidebar filter dropdowns
- **Chat Session Lifecycle**: Creating new conversations, loading existing ones, sending messages
- **Filter Coordination**: Sidebar dropdowns update staged filter state → "Apply Changes" pushes them to `appliedFilters` → `SuggestedPrompts` re-fetches metrics → "Clear Selections" resets to "All"
- **API Communication**: All `fetch()` calls to the backend happen here
- **Layout**: Renders a 2-column layout with the Sidebar on the left and the main chat area on the right

Key functions:
- `processUserMessage(text)` — Sends the question to the backend, receives the AI response, and updates the message list
- `handleApplyChanges()` — Copies the staged dropdown values into `appliedFilters`, triggering a metrics refresh
- `handleClearSelections()` — Resets all filters to "All" and refreshes metrics to show full dataset
- `handleNewConversation()` — Clears active chat and resets to the welcome screen
- `handleLoadConversation(chatId)` — Fetches and displays messages from a previous conversation

### `components/ChatMessage.tsx` — Message Renderer

Renders each message in the chat feed:

- **User messages** — Dark rounded bubble, right-aligned with "AS" avatar
- **AI messages** — White card with orange bot avatar, left-aligned
- **Markdown rendering** — Uses `react-markdown` with Tailwind Typography for beautiful formatting (headers, bold, lists, tables)
- **Chart display** — Embeds backend-generated Plotly HTML charts via `<iframe>` below the answer
- **Clickable follow-ups** — Extracts "Suggested Follow-ups" from the AI's markdown, strips them from the rendered text, and displays them as styled chip buttons. Clicking a chip populates the input bar with that question
- **SQL toggle** — Collapsible `<details>` element showing the generated SQL query
- **Legacy cleanup** — Regex patterns strip old prompt artifacts from database-stored messages

### `components/Sidebar.tsx` — Sidebar Panel

The left navigation panel containing:

- **EXL branding** — Logo and "Audit Intelligence Platform" header
- **"+ New Conversation" button** — Creates a fresh chat session
- **Conversation history** — List of past conversations loaded from the backend, with:
  - Click to load → `onLoadConversation(chatId)`
  - Hover to reveal trash icon → Opens delete confirmation modal
  - Active conversation highlighted with orange border
- **Pre-Filter Panel** (expandable via "Show generated SQL" toggle):
  - **Quarter** dropdown — All, Q1, Q2, Q3, Q4
  - **Line of Business** dropdown — All, Commercial, DSNP, IFP, Medicare
  - **Program** dropdown — All, AIA, CCS, CCSO, UM
  - **Active Records** indicator
  - **"Apply Changes"** button — Commits filter selections
  - **"Clear Selections"** button — Resets all filters to "All"
- **User profile** — Name, title, and initials at the bottom

### `components/SuggestedPrompts.tsx` — Welcome Dashboard

Displayed when no conversation is active. Contains:

- **Welcome header** — "Welcome to Clinical Audit AI" with record count
- **5 Metric Tiles** — Total Records, Avg Quality Score, Needs Attention, Strong Performers, Employees
  - Fetches live data from `POST /api/metrics` on mount and whenever `appliedFilters` change
  - Displays real aggregated data from DuckDB based on active sidebar filters
- **Capabilities Card** — Lists what the AI assistant can analyze (quality scores, failing elements, root causes, trends, coaching opportunities)

### `components/DeleteConfirmationModal.tsx` — Delete Confirmation

A modal dialog that appears when the user clicks the trash icon on a conversation. Asks "Remove this conversation?" with Cancel/Delete buttons.

### `components/DynamicChart.tsx` — Legacy Chart Component

A React-based chart component using Recharts. Currently not actively used (charts are rendered via backend-generated Plotly HTML iframes instead), but kept for potential future use.

### `app/globals.css` — Global Styles

Contains:
- `@plugin "@tailwindcss/typography"` — Enables the `prose` classes for markdown rendering
- `@theme` block — Custom CSS variables for the design system:
  - `--color-exl-orange: #E8400C` (primary brand)
  - `--color-orange-deep: #C43508` (hover state)
  - `--color-sidebar: #1A1D23` (dark sidebar)
  - `--color-chat-bg: #F0F2F5` (light chat background)
  - `--color-surface: #FFFFFF` (card backgrounds)
  - `--color-text-primary`, `--color-text-secondary`, `--color-active-green`

### `app/layout.tsx` — Root Layout

Standard Next.js root layout. Sets the HTML `<lang>`, applies the global CSS, and wraps the app in a `<body>` tag.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/chats` | Create a new conversation → `{ chat_id }` |
| `GET` | `/chat/chats` | List all conversations |
| `DELETE` | `/chat/chats/{id}` | Delete a conversation |
| `POST` | `/chat/chats/{id}/ask` | Ask a question → `{ answer, sql, data, chartPath, chartType, xKey, yKey }` |
| `GET` | `/chat/chats/{id}` | Get all messages for a conversation |
| `POST` | `/api/metrics` | Get dashboard metrics (accepts `preFilters`) |

---

## Database Schema

The `audits` table in DuckDB contains **20,000 rows** with these key columns:

| Column | Type | Description |
|--------|------|-------------|
| `employee_name` | VARCHAR | Name of the audited employee |
| `employee_aetna_id` | VARCHAR | Employee ID |
| `employee_supervisor_name` | VARCHAR | Supervisor's name |
| `quarter` | VARCHAR | Q1, Q2, Q3, Q4 |
| `line_of_business` | VARCHAR | Commercial, DSNP, IFP, Medicare |
| `business_program` | VARCHAR | AIA, CCS, CCSO, UM |
| `quality_score_overall` | DOUBLE | Overall quality score (0–100) |
| `element_*` | DOUBLE | Individual quality element scores (60 elements) |
| `root_case_*` | VARCHAR | Root cause analysis per element |
| `recommendations_*` | VARCHAR | Recommendations per element |

---

## Environment Variables

### Backend (`backend/.env`)

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

Get your free API key at [console.groq.com](https://console.groq.com).

---

## How the Query Pipeline Works

```
User Question: "Which top 5 employees have the highest quality scores?"
         │
         ▼
┌─────────────────────────────┐
│  1. Save message to DB      │
│  2. Generate chat title     │
│     (if first message)      │
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│  3. Build conversation      │
│     context from history    │
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│  4. Send to Groq LLM with   │
│     SQL_PROMPT + schema     │
│                             │
│  → Generated SQL:           │
│  SELECT employee_name,      │
│    AVG(quality_score_overall)│
│  FROM audits                │
│  GROUP BY employee_name     │
│  ORDER BY 2 DESC LIMIT 5   │
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│  5. Execute SQL on DuckDB   │
│     (retry once on failure) │
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│  6. Ask LLM: "Should I      │
│     chart this? What type?" │
│  → Response: bar chart,     │
│     x=employee_name,        │
│     y=avg_score             │
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│  7. Generate Plotly chart   │
│     → Save as HTML file     │
│     → /charts/abc123.html   │
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│  8. Send data + question    │
│     to LLM with             │
│     INSIGHT_PROMPT          │
│  → Formatted Markdown       │
│     answer with insights    │
│     and follow-ups          │
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│  9. Save response to DB     │
│ 10. Return to frontend      │
└─────────────────────────────┘
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `GROQ_API_KEY` error on startup | Make sure `backend/.env` has your Groq key |
| Backend won't start (port in use) | Kill existing process: `taskkill /F /IM python.exe` |
| Frontend shows "Failed to fetch" | Make sure backend is running on port 8000 |
| Metrics show 0 everywhere | Run `python scripts/load_data.py` to load data |
| Charts not displaying | Ensure `backend/charts/` directory exists |
| "Model decommissioned" error | Update model name in `llm_service.py` |

---

*Documentation generated on 18 March 2026*
