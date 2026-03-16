from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from db.models import TallyQueue

router = APIRouter()

@router.get("/pending-tally-posts")
async def get_pending_posts(db: AsyncSession = Depends(get_db)):
    """Used by the local Tally bridge to fetch pending vouchers."""
    result = await db.execute(
        select(TallyQueue).where(TallyQueue.status == 'pending').limit(50)
    )
    vouchers = result.scalars().all()
    
    return [
        {
            "id": v.id,
            "xml_payload": v.xml_payload,
        } for v in vouchers
    ]

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
