# Backend Integration Guide

This document outlines the exact API contracts and endpoints the Frontend React application expects from the Backend API.

## Base Configuration
The frontend is currently configured to send all HTTP requests to:
`http://localhost:8000`

If your backend is hosted elsewhere, you must update the `fetch` URLs inside `app/page.tsx`, `components/Sidebar.tsx`, and `components/SuggestedPrompts.tsx`.

---

## 1. Chat & Query Processing
**Endpoint:** `POST /api/chat`
**Description:** Handles the main conversational AI query, incorporates filters, and returns text, SQL, tables, or charts.

**Expected Request Payload:**
```json
{
  "message": "What is the average quality score?",
  "preFilters": {
    "quarter": "Q1",
    "lineOfBusiness": "Commercial",
    "program": "UM"
  }
}
```

**Expected Response Payload:**
```json
{
  "success": true,
  "message": "The average quality score is 99.9%.",
  "sql_query": "SELECT AVG(score) FROM audit_table WHERE quarter='Q1'",
  "chartData": [
     {"name": "Jan", "score": 98},
     {"name": "Feb", "score": 99}
  ],
  "chartType": "bar",
  "xKey": "name",
  "yKey": "score",
  "tableData": [
     {"Employee": "John", "Score": 95},
     {"Employee": "Jane", "Score": 98}
  ]
}
```
*Note: `sql_query`, `chartData`, `chartType`, `xKey`, `yKey`, and `tableData` are completely optional. If provided, the UI will automatically render the SQL code block, the interactive Recharts visual, or the HTML Table respectively.*

---

## 2. Dashboard Metrics
**Endpoint:** `POST /api/metrics`
**Description:** Populates the 4 dashboard KPI cards at the top of the interface. Triggered on load and whenever "Apply Changes" is clicked.

**Expected Request Payload:**
```json
{
  "preFilters": {
    "quarter": "Q1",
    "lineOfBusiness": "Commercial",
    "program": "UM"
  }
}
```

**Expected Response Payload:**
```json
{
  "success": true,
  "data": {
    "totalRecords": 1224,
    "avgQualityScore": 99.9,
    "needsAttention": 7,
    "strongPerformers": 1217,
    "employees": 200
  }
}
```

---

## 3. Sidebar Conversation History
**Endpoint:** `GET /api/conversations`
**Description:** Loads the user's past chat history in the left Sidebar.

**Expected Request Payload:** None

**Expected Response Payload:**
```json
{
  "success": true,
  "conversations": [
    {
      "id": "1",
      "title": "Q3 Performance Overview",
      "time": "Currently open",
      "isActive": true,
      "icon": "activity"
    },
    {
      "id": "2",
      "title": "Employee Score Summary",
      "time": "1 hour ago",
      "isActive": false,
      "icon": "user"
    }
  ]
}
```
*Note: Valid icon strings are `activity`, `user`, `layers`, and `trend`.*

---

## 4. Delete Conversation
**Endpoint:** `DELETE /api/conversations/{id}`
**Description:** Deletes a specific conversation from the history. Triggered when the user clicks the red Trash icon on a sidebar chat.

**Expected Request Payload:** None

**Expected Response Payload:**
```json
{
  "success": true
}
```

---

## 5. User Profile
**Endpoint:** `GET /api/user`
**Description:** Loads the active user's details for the bottom-left profile card.

**Expected Request Payload:** None

**Expected Response Payload:**
```json
{
  "success": true,
  "user": {
    "name": "Ayush Singh",
    "title": "Senior Auditor",
    "initials": "AS"
  }
}
```
