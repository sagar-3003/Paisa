import os
import smtplib
from email.message import EmailMessage
from datetime import date
from sqlalchemy import select
from db.database import AsyncSessionLocal
from db.models import CreditorDues

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
    today = date.today()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CreditorDues).where(
                CreditorDues.status != 'paid',
                CreditorDues.due_date != None,
                CreditorDues.party_email != None
            )
        )
        overdue_records = result.scalars().all()

        for due in overdue_records:
            if due.due_date and due.party_email:
                overdue_days = (today - due.due_date).days
                if overdue_days >= 7:
                    pending_amount = due.amount - (due.paid_amount or 0)
                    await send_email_reminder(
                        to=due.party_email,
                        party=due.party_name,
                        amount=pending_amount,
                        invoice=due.invoice_no,
                        overdue_days=overdue_days
                    )
                    due.reminder_count = (due.reminder_count or 0) + 1
                    due.last_reminder = today

        await db.commit()
    return {"sent": len(overdue_records)}
