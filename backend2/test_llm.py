import sys, os
sys.path.insert(0, os.path.abspath('.'))

from app.services.llm_service import LLMService
from app.services.sql_service import generate_sql

llm = LLMService()

print("--- RAW SQL GENERATION TEST ---")
try:
    sql1 = generate_sql(llm, "What are the top 3 lines of business by average quality score?")
    print("SQL 1:", sql1)
except Exception as e:
    print("Error 1:", e)

print("\n--- QUESTION 2 ---")
try:
    sql2 = generate_sql(llm, "How many employees are there in total?")
    print("SQL 2:", sql2)
except Exception as e:
    print("Error 2:", e)
