from fastapi import APIRouter
from pydantic import BaseModel
import json
from datetime import date
from services.llm import call_llm

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

SYSTEM_PROMPT = """
You are Paisa, an expert Indian accountant AI assistant.
Your job is to extract structured accounting data from user messages.

When the user describes a transaction, return ONLY a valid JSON object.
No explanation. No markdown. Just JSON.

Schema:
{{
  "intent": "sales" | "purchase" | "expense" | "payment_received" | "payment_made" | "bank_statement" | "query",
  "party_name": "string",
  "party_state": "string | null",       // e.g. "Rajasthan", "Maharashtra"
  "party_gstin": "string | null",
  "items": [
    {{
      "description": "string",
      "quantity": "number | null",
      "unit_price": "number | null",
      "amount": "number"
    }}
  ],
  "total_amount": "number",
  "date": "YYYY-MM-DD",               // today if not mentioned
  "payment_status": "paid" | "pending" | "partial",
  "payment_mode": "cash" | "bank" | "upi" | "cheque" | null,
  "notes": "string | null",
  "confidence": "0.0-1.0"               // your confidence in this extraction
}}

If intent is "query", return:
{{
  "intent": "query",
  "question": "string",
  "answer": "string"    // answer using your Indian accounting knowledge
}}

Today's date: {today}
User's business state: {user_state}
"""

@router.post("/chat")
async def process_chat(request: ChatRequest):
    # Retrieve user state from env or DB (hardcoded for now as per prompt)
    user_state = "Rajasthan" 
    today_str = date.today().isoformat()
    
    prompt = f"{SYSTEM_PROMPT.format(today=today_str, user_state=user_state)}\n\nUser Message: {request.message}"
    
    response_text = await call_llm(prompt)
    
    try:
        # Strip potential markdown formatting from LLM response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(response_text)
        return data
    except json.JSONDecodeError:
        return {"intent": "query", "question": request.message, "answer": "I had trouble parsing that. Could you provide the specific transaction details?", "raw_error": response_text}
