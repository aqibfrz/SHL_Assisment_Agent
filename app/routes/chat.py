from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.agents.controller import handle_chat

router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(..., description="conversation role, e.g. user or assistant")
    content: str = Field("", description="message text")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1)


@router.post("/chat")
def chat(body: ChatRequest):
    return handle_chat([m.model_dump() for m in body.messages])