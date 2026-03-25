from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.repository import create_chat, delete_chat, get_chats
from app.services.llm_service import LLMService
from app.services.query_service import handle_query

router = APIRouter()
_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = LLMService()
    return _llm


def _error_response(message):
    return {
        "answer": message,
        "sql": None,
        "data": [],
        "chart": None,
        "chartType": None,
        "xKey": None,
        "yKey": None,
        "visualizations": [],
    }


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
    question = payload.question.strip()
    if not question:
        return _error_response("Please enter a question before sending the request.")

    try:
        return handle_query(chat_id, question, payload.preFilters, get_llm())
    except Exception as error:
        return _error_response(
            str(error)
            or "The assistant is temporarily unavailable. Please verify the model configuration and try again."
        )


@router.get("/chats/{chat_id}")
def get_chat_messages(chat_id: str):
    from app.db.repository import get_messages

    return get_messages(chat_id)
