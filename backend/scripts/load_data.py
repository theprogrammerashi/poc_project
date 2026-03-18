import duckdb
import os

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # backend/
DATA_DIR = os.path.join(BASE_DIR, "data")

FILE_PATH = os.path.join(DATA_DIR, "UM_Clinical_Audit_2025_Synthetic.csv")
DB_PATH = os.path.join(DATA_DIR, "audit.duckdb")

if not os.path.exists(FILE_PATH):
    raise FileNotFoundError(f"Dataset not found at: {FILE_PATH}")

con = duckdb.connect(DB_PATH)

con.execute(f"""
CREATE OR REPLACE TABLE audits AS
SELECT * FROM read_csv_auto('{FILE_PATH.replace(os.sep, '/')}')
""")

print("✅ Data loaded into DuckDB")
con.close()