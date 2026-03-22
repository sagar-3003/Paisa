import os
import smtplib
from email.message import EmailMessage
from datetime import date
from db.supabase_client import get_supabase

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


async def send_email_reminder(to: str, party: str, amount: float, invoice: str, overdue_days: int):
    if not (GMAIL_USER and GMAIL_APP_PASSWORD):
        print(f"SMTP not configured. Skipping email to {party} ({to}) for ₹{amount}")
        return

    msg = EmailMessage()
    msg.set_content(
        f"Dear {party},\n\n"
        f"This is a gentle reminder that your invoice {invoice} for the amount of ₹{amount:,.2f} "
        f"is overdue by {overdue_days} days.\n\n"
        f"Please arrange for payment at your earliest convenience.\n\n"
        f"Thank you,\n"
        f"Paisa AI Accounts"
    )
    msg['Subject'] = f"Payment Reminder: Invoice {invoice} Overdue"
    msg['From'] = GMAIL_USER
    msg['To'] = to

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
            print(f"Sent reminder email to {to}")
    except Exception as e:
        print(f"Failed to send email to {to}: {e}")


async def send_overdue_reminders():
    """Called by the cron endpoint daily at 9AM IST (3AM UTC)."""
    print("Running send_overdue_reminders")
    sb = await get_supabase()
    today = date.today()
    today_str = today.isoformat()

    result = await sb.table("creditor_dues").select("*").neq("status", "paid").not_.is_("due_date", "null").not_.is_("party_email", "null").execute()

    sent = 0
    for due in result.data:
        due_date_str = due.get("due_date")
        party_email = due.get("party_email")
        if not due_date_str or not party_email:
            continue

        due_date = date.fromisoformat(due_date_str)
        overdue_days = (today - due_date).days
        if overdue_days >= 7:
            pending_amount = (due.get("amount") or 0) - (due.get("paid_amount") or 0)
            await send_email_reminder(
                to=party_email,
                party=due["party_name"],
                amount=pending_amount,
                invoice=due.get("invoice_no", "N/A"),
                overdue_days=overdue_days,
            )
            await sb.table("creditor_dues").update({
                "reminder_count": (due.get("reminder_count") or 0) + 1,
                "last_reminder": today_str,
            }).eq("id", due["id"]).execute()
            sent += 1

    return {"sent": sent}
