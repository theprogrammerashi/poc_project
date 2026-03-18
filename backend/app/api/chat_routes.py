from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.db.repository import create_chat, get_chats, delete_chat
from app.services.query_service import handle_query
from app.services.llm_service import LLMService

router = APIRouter()
llm = LLMService()

class QueryRequest(BaseModel):
    question: str
    preFilters: Optional[dict] = None

@router.post("/chats")
def new_chat():
    return {"chat_id": create_chat()}

@router.get("/chats")
def list_chats():
    return get_chats()

@router.delete("/chats/{chat_id}")
def remove_chat(chat_id: str):
    success = delete_chat(chat_id)
    return {"status": "deleted" if success else "not found"}

@router.post("/chats/{chat_id}/ask")
def ask(chat_id: str, payload: QueryRequest):
    return handle_query(chat_id, payload.question, payload.preFilters, llm)

@router.get("/chats/{chat_id}")
def get_chat_messages(chat_id: str):
    from app.db.repository import get_messages
    return get_messages(chat_id)