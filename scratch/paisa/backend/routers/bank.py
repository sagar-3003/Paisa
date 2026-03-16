from fastapi import APIRouter, UploadFile, File
from services.bank_statement import parse_bank_statement_pdf, parse_bank_statement_excel, categorize_transactions

router = APIRouter()

@router.post("/scan-bank")
async def scan_bank_statement(file: UploadFile = File(...)):
    content = await file.read()
    
    # 1. Parse lines from PDF/Excel
    if "pdf" in file.content_type:
        transactions = parse_bank_statement_pdf(content)
    elif "spreadsheet" in file.content_type or "excel" in file.content_type:
        transactions = parse_bank_statement_excel(content)
    else:
         return {"error": "Unsupported file format. Please upload PDF or Excel."}
        
    if not transactions:
        return {"error": "No transactions found in this file"}
        
    # 2. Add LLM Categorization
    categorized = await categorize_transactions(transactions)
    
    return {
        "success": True,
        "total_extracted": len(categorized),
        "transactions": categorized
    }
