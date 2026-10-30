from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
import backend.data_service as ds
from src.ai_assistant import ask_sales_assistant, build_analytical_context

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("")
def chat(req: ChatRequest):
    df = ds.get_df()
    context = build_analytical_context(df)
    result = ask_sales_assistant(req.message, context)
    
    answer = result.get("answer") or result.get("response") or "I could not analyze this request."
    mode = result.get("mode", "deterministic")
    
    return {"response": answer, "mode": mode}
