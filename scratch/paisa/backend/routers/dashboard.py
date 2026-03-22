from fastapi import APIRouter
from datetime import date, timedelta
from db.supabase_client import get_supabase

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard():
    sb = await get_supabase()
    today = date.today()
    month_start = today.replace(day=1)
    today_str = today.isoformat()
    month_start_str = month_start.isoformat()

    # 1. Today's sales
    sales_res = await sb.table("transactions").select("net_amount").eq("intent", "sales").eq("date", today_str).execute()
    today_sales = sum(r["net_amount"] or 0 for r in sales_res.data)

    # 2. GST Payable (Sales GST - Purchase GST) for this month
    gst_sales_res = await sb.table("transactions").select("gst_amount").eq("intent", "sales").gte("date", month_start_str).execute()
    gst_sales = sum(r["gst_amount"] or 0 for r in gst_sales_res.data)

    gst_purch_res = await sb.table("transactions").select("gst_amount").eq("intent", "purchase").gte("date", month_start_str).execute()
    gst_purch = sum(r["gst_amount"] or 0 for r in gst_purch_res.data)
    gst_payable = gst_sales - gst_purch

    # 3. Pending dues total and count
    dues_res = await sb.table("creditor_dues").select("amount,paid_amount").neq("status", "paid").execute()
    pending_dues_amt = sum((r["amount"] or 0) - (r["paid_amount"] or 0) for r in dues_res.data)
    pending_dues_count = len(dues_res.data)

    # 4. Overdue count
    overdue_res = await sb.table("creditor_dues").select("id").neq("status", "paid").lt("due_date", today_str).execute()
    overdue_count = len(overdue_res.data)

    # 5. TDS Deducted this month
    tds_res = await sb.table("transactions").select("tds_amount").gte("date", month_start_str).execute()
    tds_deducted = sum(r["tds_amount"] or 0 for r in tds_res.data)

    # 6. Low stock items
    inv_res = await sb.table("inventory").select("item_name,quantity,reorder_level").execute()
    low_stock_items = [r["item_name"] for r in inv_res.data if (r["quantity"] or 0) <= (r["reorder_level"] or 0)]

    return {
        "today_sales": round(today_sales, 2),
        "gst_payable": round(gst_payable, 2),
        "gst_due_date": (month_start + timedelta(days=50)).replace(day=20).isoformat(),
        "pending_dues": round(pending_dues_amt, 2),
        "pending_dues_parties": pending_dues_count,
        "overdue_count": overdue_count,
        "tds_deducted": round(tds_deducted, 2),
        "low_stock_items": low_stock_items,
    }
