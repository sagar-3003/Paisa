import io
import json
from PIL import Image
import pdfplumber
import easyocr
from services.llm import call_llm

reader = easyocr.Reader(['en'], gpu=False)  # CPU mode for cloud

def extract_text_from_image(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        results = reader.readtext(image, detail=0)
        return "\n".join(results)
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                # Try table extraction first (more structured)
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        text += " | ".join(str(c or "") for c in row) + "\n"
                # Then plain text
                text += (page.extract_text() or "") + "\n"
    except Exception as e:
        print(f"Error extracting text from pdf: {e}")
    return text

INVOICE_PARSE_PROMPT = """
You are an expert at reading Indian business invoices.
Given the following raw OCR text from an invoice, extract all fields.
Return ONLY valid JSON. No explanation. No markdown.

Raw OCR text:
---
{ocr_text}
---

Extract this JSON:
{{
  "intent": "purchase", // assume purchase or expense from OCR
  "party_name": "string",
  "party_gstin": "string | null",          // 15-digit GSTIN if present
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

If any field is not found in the text, use null.
"""

async def process_invoice_bytes(file_bytes: bytes, content_type: str) -> dict:
    if "pdf" in content_type:
        raw_text = extract_text_from_pdf(file_bytes)
    else:
        raw_text = extract_text_from_image(file_bytes)
        
    if not raw_text.strip():
        return {"error": "Could not extract text from the file"}
        
    prompt = INVOICE_PARSE_PROMPT.format(ocr_text=raw_text[:3000])
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
        return {"error": "Failed to parse invoice JSON from LLM"}
