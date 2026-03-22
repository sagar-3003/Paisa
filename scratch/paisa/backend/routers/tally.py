from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from db.supabase_client import get_supabase
from services.tally_xml import build_sales_voucher
import uuid

router = APIRouter()


# ─── Existing bridge endpoints (kept for future Windows Tally sync) ──────────

@router.get("/pending-tally-posts")
async def get_pending_posts():
    sb = await get_supabase()
    result = await sb.table("tally_queue").select("id,xml_payload").eq("status", "pending").limit(50).execute()
    return [{"id": v["id"], "xml_payload": v["xml_payload"]} for v in result.data]


@router.post("/mark-posted/{voucher_id}")
async def mark_posted(voucher_id: str):
    sb = await get_supabase()
    result = await sb.table("tally_queue").update({"status": "posted"}).eq("id", voucher_id).execute()
    if result.data:
        return {"success": True}
    return {"success": False, "error": "Voucher not found"}


# ─── Save parsed transaction to DB ────────────────────────────────────────────

class SaveTransactionRequest(BaseModel):
    intent: str
    party_name: Optional[str] = None
    party_gstin: Optional[str] = None
    party_state: Optional[str] = None
    total_amount: Optional[float] = None
    gst_amount: Optional[float] = None
    tds_amount: Optional[float] = 0.0
    net_amount: Optional[float] = None
    payment_status: Optional[str] = "pending"
    source_type: Optional[str] = "chat"
    raw_input: Optional[str] = None
    date: Optional[str] = None


@router.post("/transactions/save")
async def save_transaction(req: SaveTransactionRequest):
    sb = await get_supabase()
    txn_id = str(uuid.uuid4())
    txn_date = date.today().isoformat()
    if req.date:
        try:
            txn_date = datetime.strptime(req.date, "%Y-%m-%d").date().isoformat()
        except ValueError:
            pass

    await sb.table("transactions").insert({
        "id": txn_id,
        "intent": req.intent,
        "party_name": req.party_name,
        "party_gstin": req.party_gstin,
        "party_state": req.party_state,
        "total_amount": req.total_amount,
        "gst_amount": req.gst_amount,
        "tds_amount": req.tds_amount or 0.0,
        "net_amount": req.net_amount or req.total_amount,
        "payment_status": req.payment_status or "pending",
        "source_type": req.source_type or "chat",
        "raw_input": req.raw_input,
        "date": txn_date,
    }).execute()

    return {"transaction_id": txn_id}


# ─── Download Tally XML for a transaction ─────────────────────────────────────

@router.get("/tally/download/{transaction_id}")
async def download_tally_xml(transaction_id: str):
    sb = await get_supabase()
    result = await sb.table("transactions").select("*").eq("id", transaction_id).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn = result.data[0]
    entry = {
        "intent": txn["intent"],
        "party_name": txn["party_name"] or "Cash",
        "party_gstin": txn["party_gstin"],
        "party_state": txn["party_state"],
        "total_amount": txn["total_amount"] or 0,
        "date": txn["date"] or "",
        "notes": f"Paisa AI - {txn['intent']} entry",
    }

    gst_data = {}
    if txn.get("gst_amount"):
        gst_data = {
            "total_amount": txn["total_amount"],
            "taxes": {
                "CGST": round(txn["gst_amount"] / 2, 2),
                "SGST": round(txn["gst_amount"] / 2, 2),
            },
        }

    xml_content = build_sales_voucher(entry, gst_data)
    filename = f"paisa_voucher_{transaction_id[:8]}.xml"

    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ─── Tally Ledger (Day Book view) ─────────────────────────────────────────────

@router.get("/tally/ledger")
async def get_ledger(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    type: Optional[str] = "all",
    page: int = 1,
    page_size: int = 50,
):
    sb = await get_supabase()

    query = sb.table("transactions").select("*").order("date", desc=True)

    if from_date:
        try:
            datetime.strptime(from_date, "%Y-%m-%d")
            query = query.gte("date", from_date)
        except ValueError:
            pass

    if to_date:
        try:
            datetime.strptime(to_date, "%Y-%m-%d")
            query = query.lte("date", to_date)
        except ValueError:
            pass

    if type and type != "all":
        query = query.eq("intent", type)

    offset = (page - 1) * page_size
    result = await query.range(offset, offset + page_size - 1).execute()
    transactions = result.data

    # Total count via separate query
    count_query = sb.table("transactions").select("id", count="exact")
    if from_date:
        try:
            datetime.strptime(from_date, "%Y-%m-%d")
            count_query = count_query.gte("date", from_date)
        except ValueError:
            pass
    if to_date:
        try:
            datetime.strptime(to_date, "%Y-%m-%d")
            count_query = count_query.lte("date", to_date)
        except ValueError:
            pass
    if type and type != "all":
        count_query = count_query.eq("intent", type)
    count_result = await count_query.execute()
    total_count = count_result.count or 0

    CREDIT_INTENTS = {"sales", "payment_received"}
    rows = []
    total_debit = 0.0
    total_credit = 0.0

    for txn in transactions:
        is_credit = txn["intent"] in CREDIT_INTENTS
        amount = txn.get("net_amount") or txn.get("total_amount") or 0.0

        debit = 0.0 if is_credit else amount
        credit = amount if is_credit else 0.0
        total_debit += debit
        total_credit += credit

        rows.append({
            "id": txn["id"],
            "date": txn.get("date"),
            "voucher_type": txn["intent"],
            "party_name": txn.get("party_name") or "Cash",
            "debit": round(debit, 2),
            "credit": round(credit, 2),
            "gst_amount": round(txn.get("gst_amount") or 0.0, 2),
            "tds_amount": round(txn.get("tds_amount") or 0.0, 2),
            "net_amount": round(amount, 2),
            "payment_status": txn.get("payment_status"),
            "source_type": txn.get("source_type"),
        })

    return {
        "rows": rows,
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "balance": round(total_credit - total_debit, 2),
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
    }
