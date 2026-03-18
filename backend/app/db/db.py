import duckdb
import os

# Use relative path from the backend working directory
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "audit.duckdb")

def get_connection():
    return duckdb.connect(DB_PATH)