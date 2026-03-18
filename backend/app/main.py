import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.chat_routes import router
from app.db.repository import init_tables
from app.db.db import get_connection

app = FastAPI(title="AI Data Analyst API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure charts directory exists
os.makedirs("charts", exist_ok=True)
app.mount("/charts", StaticFiles(directory="charts"), name="charts")

@app.on_event("startup")
def startup():
    init_tables()

app.include_router(router, prefix="/chat", tags=["Chat"])

# --- Metrics endpoint for the Welcome Dashboard ---
from pydantic import BaseModel
from typing import Optional

class MetricsRequest(BaseModel):
    preFilters: Optional[dict] = None

@app.post("/api/metrics")
def get_metrics(req: MetricsRequest = MetricsRequest()):
    try:
        # Build WHERE clause from preFilters
        # Frontend keys map to DB columns:
        # quarter -> quarter, lineOfBusiness -> line_of_business, program -> business_program
        filter_map = {
            "quarter": "quarter",
            "lineOfBusiness": "line_of_business",
            "program": "business_program"
        }

        conditions = []
        params = []
        if req.preFilters:
            for fe_key, db_col in filter_map.items():
                val = req.preFilters.get(fe_key)
                if val and val != "All":
                    conditions.append(f'"{db_col}" = ?')
                    params.append(val)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with get_connection() as con:
            total = con.execute(f"SELECT COUNT(*) FROM audits {where_clause}", params).fetchone()[0]

            avg_result = con.execute(f'SELECT AVG(quality_score_overall) FROM audits {where_clause}', params).fetchone()
            avg_score = round(avg_result[0], 1) if avg_result[0] else 0.0

            needs_result = con.execute(f'SELECT COUNT(*) FROM audits {where_clause} {"AND" if conditions else "WHERE"} quality_score_overall < 75', params).fetchone()
            needs_attention = needs_result[0] if needs_result else 0

            strong_result = con.execute(f'SELECT COUNT(*) FROM audits {where_clause} {"AND" if conditions else "WHERE"} quality_score_overall >= 85', params).fetchone()
            strong = strong_result[0] if strong_result else 0

            emp_result = con.execute(f'SELECT COUNT(DISTINCT employee_name) FROM audits {where_clause}', params).fetchone()
            employees = emp_result[0] if emp_result else 0

        return {
            "success": True,
            "data": {
                "totalRecords": total,
                "avgQualityScore": avg_score,
                "needsAttention": needs_attention,
                "strongPerformers": strong,
                "employees": employees
            }
        }
    except Exception as e:
        print(f"Metrics error: {e}")
        return {
            "success": False,
            "data": {
                "totalRecords": 0,
                "avgQualityScore": 0.0,
                "needsAttention": 0,
                "strongPerformers": 0,
                "employees": 0
            }
        }