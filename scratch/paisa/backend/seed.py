import os
import asyncio
from datetime import date, timedelta
import random

# Ensure we're running from the backend directory to find the db path
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./paisa.db"

from db.database import engine, Base, AsyncSessionLocal
from db.models import Transaction, LineItem, CreditorDues, Inventory, HsnMaster

async def seed_data():
    print("Initializing Database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database Reset Complete.")

    today = date.today()
    
    async with AsyncSessionLocal() as db:
        print("Seeding HSN Master...")
        hsn1 = HsnMaster(hsn_code="8471", description="Computers, laptops", gst_rate=18.0)
        hsn2 = HsnMaster(hsn_code="9403", description="Furniture", gst_rate=18.0)
        hsn3 = HsnMaster(hsn_code="9983", description="IT services", gst_rate=18.0, is_service=True)
        db.add_all([hsn1, hsn2, hsn3])

        print("Seeding Inventory...")
        inv1 = Inventory(item_name="Dell Inspiron 15", hsn_code="8471", quantity=5, avg_cost=45000, reorder_level=10)
        inv2 = Inventory(item_name="Office Chair", hsn_code="9403", quantity=20, avg_cost=3000, reorder_level=5)
        # This one should trigger a low stock alert
        inv3 = Inventory(item_name="Logitech Mouse", hsn_code="8471", quantity=2, avg_cost=500, reorder_level=5)
        db.add_all([inv1, inv2, inv3])

        print("Seeding Transactions and Line Items...")
        
        # 1. Today's Sale
        t1 = Transaction(
            intent="sales", party_name="Ramesh Enterprises", party_state="Maharashtra",
            total_amount=53100, gst_amount=8100, net_amount=45000,
            date=today, payment_status="pending", tally_posted=False
        )
        db.add(t1)
        await db.flush()
        li1 = LineItem(transaction_id=t1.id, description="Dell Inspiron 15", hsn_sac_code="8471", quantity=1, unit_price=45000, amount=45000, gst_rate=18)
        db.add(li1)
        
        # Add to creditor dues (Pending)
        cd1 = CreditorDues(transaction_id=t1.id, party_name=t1.party_name, invoice_no="INV-2026-001",
                           invoice_date=today, due_date=today + timedelta(days=15), amount=53100)
        db.add(cd1)

        # 2. Past Purchase (Creates GST Claim)
        past_date = today - timedelta(days=10)
        t2 = Transaction(
            intent="purchase", party_name="Dell India", party_state="Karnataka",
            total_amount=118000, gst_amount=18000, net_amount=100000,
            date=past_date, payment_status="paid", tally_posted=True
        )
        db.add(t2)
        await db.flush()
        li2 = LineItem(transaction_id=t2.id, description="Dell Laptops Stock", hsn_sac_code="8471", quantity=5, unit_price=20000, amount=100000, gst_rate=18)
        db.add(li2)

        # 3. Expense with TDS (Creates TDS Deducted)
        t3 = Transaction(
            intent="expense", party_name="Suresh CA", party_state="Rajasthan",
            total_amount=10000, gst_amount=1800, tds_amount=1000, net_amount=10000.0,
            date=today - timedelta(days=5), payment_status="paid"
        )
        db.add(t3)
        await db.flush()
        li3 = LineItem(transaction_id=t3.id, description="Audit Fees", hsn_sac_code="9983", quantity=1, unit_price=10000, amount=10000, gst_rate=18)
        db.add(li3)

        # 4. Overdue Invoice > 7 days
        overdue_date = today - timedelta(days=20)
        t4 = Transaction(
            intent="sales", party_name="Acme Corp", party_state="Delhi",
            total_amount=25000, gst_amount=0, net_amount=25000,
            date=overdue_date, payment_status="pending"
        )
        db.add(t4)
        await db.flush()
        
        cd2 = CreditorDues(
            transaction_id=t4.id, party_name="Acme Corp", party_email="test@acmecorp.com",
            invoice_no="INV-2026-OLD", invoice_date=overdue_date, 
            due_date=today - timedelta(days=10), # 10 days overdue
            amount=25000, status='pending'
        )
        db.add(cd2)

        await db.commit()
        print("Data Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(seed_data())
