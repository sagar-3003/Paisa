from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.database import get_db
from db.models import Transaction, CreditorDues, Inventory
from datetime import date, datetime, timedelta

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    today = date.today()
    month_start = today.replace(day=1)
    
    # 1. Today's sales
    sales_result = await db.execute(
        select(func.sum(Transaction.net_amount))
        .where(Transaction.intent == 'sales', Transaction.date == today)
    )
    today_sales = sales_result.scalar() or 0.0

    # 2. GST Payable (Sales GST - Purchase GST) for this month
    gst_sales_res = await db.execute(
        select(func.sum(Transaction.gst_amount))
        .where(Transaction.intent == 'sales', Transaction.date >= month_start)
    )
    gst_sales = gst_sales_res.scalar() or 0.0
    
    gst_purch_res = await db.execute(
        select(func.sum(Transaction.gst_amount))
        .where(Transaction.intent == 'purchase', Transaction.date >= month_start)
    )
    gst_purch = gst_purch_res.scalar() or 0.0
    gst_payable = gst_sales - gst_purch

    # 3. Pending dues total and count
    dues_res = await db.execute(
        select(func.sum(CreditorDues.amount - CreditorDues.paid_amount), func.count(CreditorDues.id))
        .where(CreditorDues.status != 'paid')
    )
    pending_dues_amt, pending_dues_count = dues_res.first()
    pending_dues_amt = pending_dues_amt or 0.0
    pending_dues_count = pending_dues_count or 0

    # 4. Overdue count
    overdue_res = await db.execute(
        select(func.count(CreditorDues.id))
        .where(CreditorDues.status != 'paid', CreditorDues.due_date < today)
    )
    overdue_count = overdue_res.scalar() or 0

    # 5. TDS Deducted
    tds_res = await db.execute(
        select(func.sum(Transaction.tds_amount))
        .where(Transaction.date >= month_start)
    )
    tds_deducted = tds_res.scalar() or 0.0

    # 6. Low stock items
    low_stock_res = await db.execute(
        select(Inventory.item_name)
        .where(Inventory.quantity <= Inventory.reorder_level)
    )
    low_stock_items = [row for row in low_stock_res.scalars().all()]

    return {
        "today_sales": round(today_sales, 2),
        "gst_payable": round(gst_payable, 2),
        "gst_due_date": (month_start + timedelta(days=50)).replace(day=20).isoformat(), # 20th of next month
        "pending_dues": round(pending_dues_amt, 2),
        "pending_dues_parties": pending_dues_count,
        "overdue_count": overdue_count,
        "tds_deducted": round(tds_deducted, 2),
        "low_stock_items": low_stock_items,
    }
