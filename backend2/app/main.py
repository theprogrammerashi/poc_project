import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.api.chat_routes import router
from app.db.db import ANALYTICS_VIEW, ensure_audits_table, get_connection
from app.db.repository import init_tables
from app.services.sql_service import build_filter_conditions

app = FastAPI(title="AI Data Analyst API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("charts", exist_ok=True)
app.mount("/charts", StaticFiles(directory="charts"), name="charts")


@app.on_event("startup")
def startup():
    ensure_audits_table()
    init_tables()


app.include_router(router, prefix="/chat", tags=["Chat"])


class MetricsRequest(BaseModel):
    preFilters: Optional[dict] = None


@app.post("/api/metrics")
def get_metrics(req: MetricsRequest = MetricsRequest()):
    try:
        conditions, params = build_filter_conditions(req.preFilters)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with get_connection() as con:
            total = con.execute(
                f"SELECT COUNT(*) FROM {ANALYTICS_VIEW} {where_clause}",
                params,
            ).fetchone()[0]

            avg_result = con.execute(
                f'SELECT AVG("quality_score_overall") FROM {ANALYTICS_VIEW} {where_clause}',
                params,
            ).fetchone()
            avg_score = round(avg_result[0], 1) if avg_result[0] else 0.0

            needs_result = con.execute(
                f'SELECT COUNT(*) FROM {ANALYTICS_VIEW} {where_clause} {"AND" if conditions else "WHERE"} "quality_score_overall" < 75',
                params,
            ).fetchone()
            needs_attention = needs_result[0] if needs_result else 0

            strong_result = con.execute(
                f'SELECT COUNT(*) FROM {ANALYTICS_VIEW} {where_clause} {"AND" if conditions else "WHERE"} "quality_score_overall" >= 85',
                params,
            ).fetchone()
            strong = strong_result[0] if strong_result else 0

            emp_result = con.execute(
                f'SELECT COUNT(DISTINCT "employee_name") FROM {ANALYTICS_VIEW} {where_clause}',
                params,
            ).fetchone()
            employees = emp_result[0] if emp_result else 0

        return {
            "success": True,
            "data": {
                "totalRecords": total,
                "avgQualityScore": avg_score,
                "needsAttention": needs_attention,
                "strongPerformers": strong,
                "employees": employees,
            },
        }
    except Exception as error:
        print(f"Metrics error: {error}")
        return {
            "success": False,
            "data": {
                "totalRecords": 0,
                "avgQualityScore": 0.0,
                "needsAttention": 0,
                "strongPerformers": 0,
                "employees": 0,
            },
        }
