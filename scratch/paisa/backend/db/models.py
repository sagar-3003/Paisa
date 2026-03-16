from sqlalchemy import Column, String, Float, Boolean, Date, DateTime, Integer, ForeignKey, text
from sqlalchemy.sql import func
from db.database import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    intent = Column(String, nullable=False) # sales/purchase/expense/payment
    party_name = Column(String)
    party_gstin = Column(String)
    party_state = Column(String)
    total_amount = Column(Float)
    gst_amount = Column(Float)
    tds_amount = Column(Float, default=0.0)
    net_amount = Column(Float)
    payment_status = Column(String, default='pending')
    tally_posted = Column(Boolean, default=False)
    tally_voucher_id = Column(String)
    source_type = Column(String, default='chat') # chat/ocr/bank
    source_file_url = Column(String)
    raw_input = Column(String)
    date = Column(Date, default=datetime.utcnow().date)
    created_at = Column(DateTime, default=datetime.utcnow)

class LineItem(Base):
    __tablename__ = "line_items"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey("transactions.id"))
    description = Column(String)
    hsn_sac_code = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    amount = Column(Float)
    gst_rate = Column(Float)

class CreditorDues(Base):
    __tablename__ = "creditor_dues"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey("transactions.id"))
    party_name = Column(String, nullable=False)
    party_gstin = Column(String)
    party_email = Column(String)
    invoice_no = Column(String)
    invoice_date = Column(Date)
    due_date = Column(Date)
    amount = Column(Float)
    paid_amount = Column(Float, default=0.0)
    status = Column(String, default='pending')
    reminder_count = Column(Integer, default=0)
    last_reminder = Column(DateTime)

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    item_name = Column(String, nullable=False)
    hsn_code = Column(String)
    unit = Column(String, default='Nos')
    quantity = Column(Float, default=0.0)
    avg_cost = Column(Float)
    reorder_level = Column(Float, default=10.0)
    updated_at = Column(DateTime, default=datetime.utcnow)

class HsnMaster(Base):
    __tablename__ = "hsn_master"
    
    hsn_code = Column(String, primary_key=True)
    description = Column(String, nullable=False)
    gst_rate = Column(Float, nullable=False)
    category = Column(String)
    is_service = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

class TallyQueue(Base):
    __tablename__ = "tally_queue"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey("transactions.id"))
    xml_payload = Column(String, nullable=False)
    status = Column(String, default='pending') # pending/posted/failed
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
