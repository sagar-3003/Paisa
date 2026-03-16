from fastapi import APIRouter, UploadFile, File
from services.ocr_service import process_invoice_bytes
from services.gst_engine import lookup_hsn
from services.storage import upload_to_r2

router = APIRouter()

@router.post("/scan-invoice")
async def scan_invoice(file: UploadFile = File(...)):
    content = await file.read()
    
    invoice_data = await process_invoice_bytes(content, file.content_type)
    
    if "error" in invoice_data:
        return invoice_data
        
    # Apply GST engine validation fallback
    for item in invoice_data.get("items", []):
        if item.get("description") and not item.get("hsn_sac"):
            hsn, rate = lookup_hsn(item["description"])
            item["hsn_sac"] = hsn
            
    # Upload to Cloudflare R2 for storage
    file_url = await upload_to_r2(content, file.filename)
    if file_url:
        invoice_data["source_file_url"] = file_url
        
    return invoice_data
