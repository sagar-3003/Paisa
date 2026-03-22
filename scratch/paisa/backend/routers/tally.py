from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from db.database import get_db
from db.models import TallyQueue, Transaction
from services.tally_xml import build_sales_voucher
import uuid

router = APIRouter()


# ─── Existing bridge endpoints (kept for future Windows Tally sync) ──────────

@router.get("/pending-tally-posts")
async def get_pending_posts(db: AsyncSession = Depends(get_db)):
    """Used by the local Tally bridge to fetch pending vouchers."""
    result = await db.execute(
        select(TallyQueue).where(TallyQueue.status == 'pending').limit(50)
    )
    vouchers = result.scalars().all()
    return [{"id": v.id, "xml_payload": v.xml_payload} for v in vouchers]

@router.post("/mark-posted/{voucher_id}")
async def mark_posted(voucher_id: str, db: AsyncSession = Depends(get_db)):
    """Used by the local Tally bridge to mark a voucher as posted."""
    result = await db.execute(select(TallyQueue).where(TallyQueue.id == voucher_id))
    voucher = result.scalars().first()
    if voucher:
        voucher.status = 'posted'
        await db.commit()
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
async def save_transaction(req: SaveTransactionRequest, db: AsyncSession = Depends(get_db)):
    """Persist a parsed chat/OCR transaction to the database."""
    txn_id = str(uuid.uuid4())
    txn_date = None
    if req.date:
        try:
            from datetime import datetime
            txn_date = datetime.strptime(req.date, "%Y-%m-%d").date()
        except ValueError:
            txn_date = date.today()
    else:
        txn_date = date.today()

    txn = Transaction(
        id=txn_id,
        intent=req.intent,
        party_name=req.party_name,
        party_gstin=req.party_gstin,
        party_state=req.party_state,
        total_amount=req.total_amount,
        gst_amount=req.gst_amount,
        tds_amount=req.tds_amount or 0.0,
        net_amount=req.net_amount or req.total_amount,
        payment_status=req.payment_status or "pending",
        source_type=req.source_type or "chat",
        raw_input=req.raw_input,
        date=txn_date,
    )
    db.add(txn)
    await db.commit()
    return {"transaction_id": txn_id}


# ─── Download Tally XML for a transaction ─────────────────────────────────────

@router.get("/tally/download/{transaction_id}")
async def download_tally_xml(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and return a downloadable Tally XML voucher file."""
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    txn = result.scalars().first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    entry = {
        "intent": txn.intent,
        "party_name": txn.party_name or "Cash",
        "party_gstin": txn.party_gstin,
        "party_state": txn.party_state,
        "total_amount": txn.total_amount or 0,
        "date": txn.date.strftime("%Y-%m-%d") if txn.date else "",
        "notes": f"Paisa AI - {txn.intent} entry",
    }

    gst_data = {}
    if txn.gst_amount:
        gst_data = {
            "total_amount": txn.total_amount,
            "taxes": {
                "CGST": round(txn.gst_amount / 2, 2),
                "SGST": round(txn.gst_amount / 2, 2),
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
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a Day Book-style ledger of all transactions.
    Sales/payment_received → Credit; Purchase/expense/payment_made → Debit.
    Filterable by date range and voucher type.
    """
    from datetime import datetime
    query = select(Transaction).order_by(Transaction.date.desc())

    if from_date:
        try:
            fd = datetime.strptime(from_date, "%Y-%m-%d").date()
            query = query.where(Transaction.date >= fd)
        except ValueError:
            pass

    if to_date:
        try:
            td = datetime.strptime(to_date, "%Y-%m-%d").date()
            query = query.where(Transaction.date <= td)
        except ValueError:
            pass

    if type and type != "all":
        query = query.where(Transaction.intent == type)

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    transactions = result.scalars().all()

    # Count query for pagination
    from sqlalchemy import func
    count_query = select(func.count(Transaction.id))
    if from_date:
        try:
            count_query = count_query.where(Transaction.date >= datetime.strptime(from_date, "%Y-%m-%d").date())
        except ValueError:
            pass
    if to_date:
        try:
            count_query = count_query.where(Transaction.date <= datetime.strptime(to_date, "%Y-%m-%d").date())
        except ValueError:
            pass
    if type and type != "all":
        count_query = count_query.where(Transaction.intent == type)
    total_count = (await db.execute(count_query)).scalar() or 0

    CREDIT_INTENTS = {"sales", "payment_received"}

    rows = []
    total_debit = 0.0
    total_credit = 0.0

    for txn in transactions:
        is_credit = txn.intent in CREDIT_INTENTS
        amount = txn.net_amount or txn.total_amount or 0.0

        debit = 0.0 if is_credit else amount
        credit = amount if is_credit else 0.0
        total_debit += debit
        total_credit += credit

        rows.append({
            "id": txn.id,
            "date": txn.date.isoformat() if txn.date else None,
            "voucher_type": txn.intent,
            "party_name": txn.party_name or "Cash",
            "debit": round(debit, 2),
            "credit": round(credit, 2),
            "gst_amount": round(txn.gst_amount or 0.0, 2),
            "tds_amount": round(txn.tds_amount or 0.0, 2),
            "net_amount": round(amount, 2),
            "payment_status": txn.payment_status,
            "source_type": txn.source_type,
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
