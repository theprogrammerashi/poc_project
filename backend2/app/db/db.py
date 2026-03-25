import os

import duckdb

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "audit.duckdb")
CSV_PATH = os.path.join(DATA_DIR, "UM_Clinical_Audit_2025_Synthetic.csv")

RAW_TABLE = "audits"
ANALYTICS_VIEW = "audits_analytics"


def get_connection():
    return duckdb.connect(DB_PATH)


def ensure_audits_table():
    if not os.path.exists(CSV_PATH):
        return False

    csv_path = CSV_PATH.replace(os.sep, "/")

    with get_connection() as con:
        table_exists = con.execute(
            f"""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{RAW_TABLE}'
            """
        ).fetchone()[0]

        if not table_exists:
            con.execute(
                f"""
                CREATE TABLE {RAW_TABLE} AS
                SELECT *
                FROM read_csv_auto('{csv_path}', HEADER=TRUE)
                """
            )

        con.execute(
            f"""
            CREATE OR REPLACE VIEW {ANALYTICS_VIEW} AS
            SELECT
                raw.*,
                raw."employee_mananger" AS "manager_name",
                raw."emloyee_director" AS "director_name",
                raw."employee_supervisor_name" AS "supervisor_name",
                raw."employee_supervisor_email" AS "supervisor_email",
                raw."month_audited" AS "audit_month",
                raw."quality_review_status" AS "review_status",
                raw."quality_score_overall" AS "overall_quality_score",
                raw."line_of_business" AS "line_of_business_name",
                raw."business_program" AS "program_name"
            FROM {RAW_TABLE} AS raw
            """
        )

        row_count = con.execute(f"SELECT COUNT(*) FROM {RAW_TABLE}").fetchone()[0]

    return row_count > 0
