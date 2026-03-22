import os
from fastapi import APIRouter, HTTPException, Request
from services.reminder_service import send_overdue_reminders

router = APIRouter()

CRON_SECRET = os.getenv("CRON_SECRET", "")

@router.post("/cron/reminders")
async def run_reminders(request: Request):
    """
    Called by Vercel Cron daily at 0 3 * * * (9AM IST).
    Protected by Authorization: Bearer <CRON_SECRET>.
    """
    auth = request.headers.get("Authorization", "")
    if CRON_SECRET and auth != f"Bearer {CRON_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await send_overdue_reminders()
    return {"ok": True, **result}
