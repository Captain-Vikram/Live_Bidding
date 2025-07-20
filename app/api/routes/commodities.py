from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.middleware import require_farmer_role, require_admin_role
from app.core.database import get_db
from app.db.models.accounts import User
from app.db.managers.commodities import commodity_listing_manager
from app.api.schemas.commodities import (
    CommodityCreateSchema,
    CommodityUpdateSchema,
    CommodityResponseSchema,
    CommodityListResponseSchema,
    CommodityDetailResponseSchema,
    CommodityApprovalSchema,
    CommodityApprovalResponseSchema,
)
from app.common.exception_handlers import RequestError

router = APIRouter()


@router.get(
    "/",
    summary="Get approved commodity listings",
    description="Retrieve all approved and active commodity listings",
    response_model=CommodityListResponseSchema,
)
async def get_commodities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get all approved commodity listings with optional search"""
    if search:
        commodities = await commodity_listing_manager.search_commodities(
            db, search, skip, limit
        )
    else:
        commodities = await commodity_listing_manager.get_approved_listings(
            db, skip, limit
        )
    
    return {"message": "Commodities retrieved successfully", "data": commodities}


@router.get(
    "/{commodity_slug}",
    summary="Get commodity by slug",
    description="Retrieve a specific commodity listing by its slug",
    response_model=CommodityDetailResponseSchema,
)
async def get_commodity(
    commodity_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single commodity listing by slug"""
    commodity = await commodity_listing_manager.get_by_slug(db, commodity_slug)
    if not commodity:
        raise RequestError(
            err_msg="Commodity not found",
            status_code=404,
            data={"detail": "Commodity with this slug does not exist"}
        )
    
    return {"message": "Commodity retrieved successfully", "data": commodity}


@router.post(
    "/",
    summary="Create commodity listing",
    description="Create a new commodity listing (farmers only)",
    status_code=201,
    response_model=CommodityDetailResponseSchema,
)
async def create_commodity(
    data: CommodityCreateSchema,
    current_user: User = Depends(require_farmer_role),
    db: AsyncSession = Depends(get_db),
):
    """Create a new commodity listing"""
    commodity_data = data.dict()
    commodity_data["farmer_id"] = current_user.id
    
    commodity = await commodity_listing_manager.create(db, commodity_data)
    return {"message": "Commodity listing created successfully", "data": commodity}


@router.get(
    "/my-listings/",
    summary="Get my commodity listings",
    description="Get all commodity listings created by the current farmer",
    response_model=CommodityListResponseSchema,
)
async def get_my_commodities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(require_farmer_role),
    db: AsyncSession = Depends(get_db),
):
    """Get current farmer's commodity listings"""
    commodities = await commodity_listing_manager.get_by_farmer(
        db, current_user.id, skip, limit
    )
    return {"message": "My commodities retrieved successfully", "data": commodities}


@router.put(
    "/{commodity_id}",
    summary="Update commodity listing",
    description="Update a commodity listing (owner only)",
    response_model=CommodityDetailResponseSchema,
)
async def update_commodity(
    commodity_id: str,
    data: CommodityUpdateSchema,
    current_user: User = Depends(require_farmer_role),
    db: AsyncSession = Depends(get_db),
):
    """Update a commodity listing"""
    commodity = await commodity_listing_manager.get_by_id(db, commodity_id)
    if not commodity:
        raise RequestError(
            err_msg="Commodity not found",
            status_code=404,
            data={"detail": "Commodity with this ID does not exist"}
        )
    
    # Check if user owns the commodity
    if commodity.farmer_id != current_user.id:
        raise RequestError(
            err_msg="Permission denied",
            status_code=403,
            data={"detail": "You can only update your own commodity listings"}
        )
    
    update_data = data.dict(exclude_unset=True)
    updated_commodity = await commodity_listing_manager.update(db, commodity, update_data)
    
    return {"message": "Commodity updated successfully", "data": updated_commodity}


@router.delete(
    "/{commodity_id}",
    summary="Delete commodity listing",
    description="Delete a commodity listing (owner only)",
)
async def delete_commodity(
    commodity_id: str,
    current_user: User = Depends(require_farmer_role),
    db: AsyncSession = Depends(get_db),
):
    """Delete a commodity listing"""
    commodity = await commodity_listing_manager.get_by_id(db, commodity_id)
    if not commodity:
        raise RequestError(
            err_msg="Commodity not found",
            status_code=404,
            data={"detail": "Commodity with this ID does not exist"}
        )
    
    # Check if user owns the commodity
    if commodity.farmer_id != current_user.id:
        raise RequestError(
            err_msg="Permission denied",
            status_code=403,
            data={"detail": "You can only delete your own commodity listings"}
        )
    
    await commodity_listing_manager.delete(db, commodity)
    return {"message": "Commodity deleted successfully"}
