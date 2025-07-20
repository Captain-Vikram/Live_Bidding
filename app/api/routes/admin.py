from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.middleware import require_admin_role
from app.core.database import get_db
from app.db.models.accounts import User
from app.db.managers.commodities import commodity_listing_manager
from app.api.schemas.commodities import (
    CommodityListResponseSchema,
    CommodityApprovalSchema,
    CommodityApprovalResponseSchema,
)
from app.common.exception_handlers import RequestError

router = APIRouter()


@router.get(
    "/pending-commodities/",
    summary="Get pending commodity approvals",
    description="Get all commodity listings pending admin approval",
    response_model=CommodityListResponseSchema,
)
async def get_pending_commodities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Get all commodity listings pending approval"""
    commodities = await commodity_listing_manager.get_pending_approval(db, skip, limit)
    return {"message": "Pending commodities retrieved successfully", "data": commodities}


@router.post(
    "/approve-commodity/{commodity_id}",
    summary="Approve/Reject commodity listing",
    description="Approve or reject a commodity listing",
    response_model=CommodityApprovalResponseSchema,
)
async def approve_commodity(
    commodity_id: str,
    data: CommodityApprovalSchema,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a commodity listing"""
    commodity = await commodity_listing_manager.get_by_id(db, commodity_id)
    if not commodity:
        raise RequestError(
            err_msg="Commodity not found",
            status_code=404,
            data={"detail": "Commodity with this ID does not exist"}
        )
    
    await commodity_listing_manager.approve_listing(db, commodity_id, data.is_approved)
    
    status = "approved" if data.is_approved else "rejected"
    return {
        "message": f"Commodity {status} successfully",
        "data": {"commodity_id": commodity_id, "is_approved": data.is_approved}
    }
