import io
import json
import base64
from PIL import Image
import pdfplumber
from services.llm import call_llm, call_llm_vision

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB — resize above this

def _resize_image(image_bytes: bytes) -> bytes:
    """Resize large images to keep base64 payload under vision API limits."""
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((2000, 2000))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        text += " | ".join(str(c or "") for c in row) + "\n"
                text += (page.extract_text() or "") + "\n"
    except Exception as e:
        print(f"Error extracting text from pdf: {e}")
    return text

INVOICE_PARSE_PROMPT = """
You are an expert at reading Indian business invoices.
Given the following raw text (or image) from an invoice, extract all fields.
Return ONLY valid JSON. No explanation. No markdown.

{context}

Extract this JSON:
{{
  "intent": "purchase",
  "party_name": "string",
  "party_gstin": "string | null",
  "invoice_number": "string | null",
  "date": "YYYY-MM-DD",
  "items": [
    {{
      "description": "string",
      "hsn_sac": "string | null",
      "quantity": "number | null",
      "unit_price": "number | null",
      "amount": "number"
    }}
  ],
  "total_amount": "number",
  "payment_status": "pending",
  "confidence": "0.0-1.0"
}}

If any field is not found, use null.
"""

async def process_invoice_bytes(file_bytes: bytes, content_type: str) -> dict:
    response_text = ""

    if "pdf" in content_type:
        raw_text = extract_text_from_pdf(file_bytes)
        if not raw_text.strip():
            return {"error": "Could not extract text from the PDF"}
        prompt = INVOICE_PARSE_PROMPT.format(
            context=f"Raw text from invoice:\n---\n{raw_text[:3000]}\n---"
        )
        response_text = await call_llm(prompt)
    else:
        # Image — use vision LLM directly
        if len(file_bytes) > MAX_IMAGE_BYTES:
            file_bytes = _resize_image(file_bytes)

        image_b64 = base64.b64encode(file_bytes).decode("utf-8")
        mime_type = content_type if content_type.startswith("image/") else "image/jpeg"
        prompt = INVOICE_PARSE_PROMPT.format(
            context="Please read this invoice image and extract the fields listed below."
        )
        response_text = await call_llm_vision(prompt, image_b64, mime_type)

    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        return json.loads(response_text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse invoice JSON from LLM"}
