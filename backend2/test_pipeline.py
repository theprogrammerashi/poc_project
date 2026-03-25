import sys, os
sys.path.insert(0, os.path.abspath('.'))

from app.services.llm_service import LLMService
from app.services.query_service import handle_query
from app.db.repository import create_chat

llm = LLMService()

chat_id = create_chat()

print("--- TEST CONVERSATION ROUTER ---")
try:
    res = handle_query(chat_id, "Hi! How are you?", None, llm)
    print("FINAL ANSWER:", res["answer"])
    print("SQL:", res["sql"])
except Exception as e:
    print("Pipeline Error:", e)

print("\n--- TEST DATABASE ROUTER ---")
try:
    res = handle_query(chat_id, "How many records are in the database?", None, llm)
    print("FINAL ANSWER:", res["answer"])
    print("SQL:", res["sql"])
except Exception as e:
    print("Pipeline Error:", e)
