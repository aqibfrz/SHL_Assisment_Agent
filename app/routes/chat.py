import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agents.controller import handle_chat

router = APIRouter()
_log = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str = Field(..., description="conversation role, e.g. user or assistant")
    content: str = Field("", description="message text")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1)


@router.post("/chat")
def chat(body: ChatRequest):
    try:
        return handle_chat([m.model_dump() for m in body.messages])
    except Exception as e:
        _log.exception("POST /chat failed")
        raise HTTPException(
            status_code=502,
            detail=str(e) or "Chat handler failed",
        ) from e