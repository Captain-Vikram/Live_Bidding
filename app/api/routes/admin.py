from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.dependencies import get_current_user
from app.api.middleware import require_admin_role
from app.core.database import get_db
from app.db.models.accounts import User
from app.db.managers.commodities import commodity_listing_manager
from app.db.managers.accounts import user_manager
from app.db.managers.listings import stats_manager
from app.api.schemas.commodities import (
    CommodityListResponseSchema,
    CommodityApprovalSchema,
    CommodityApprovalResponseSchema,
)
from app.api.schemas.admin import (
    UserListResponse,
    UserDetailResponse,
    UserVerificationUpdate,
    UserVerificationResponse,
    DeleteUserResponse,
    PlatformStatsResponse,
    ActiveBidsStatsResponse,
    CommoditiesStatsResponse,
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


# User Management Endpoints

@router.get(
    "/users",
    summary="List all users",
    description="Get paginated list of all users for admin management",
    response_model=UserListResponse,
)
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Get all users with pagination"""
    users = await user_manager.get_all_users_paginated(db, skip, limit)
    total_count = await user_manager.get_total_users_count(db)
    
    # Convert users to response format
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "is_verified": user.is_verified,
            "is_active": user.is_email_verified,  # Using is_email_verified as is_active
            "created_at": user.created_at,
            "last_login": user.updated_at,  # Using updated_at as last_login approximation
        })
    
    return {
        "message": "Users retrieved successfully",
        "data": user_list,
        "total_count": total_count,
        "page": (skip // limit) + 1,
        "page_size": limit
    }


@router.get(
    "/users/{user_id}",
    summary="Get user details",
    description="Get detailed information about a specific user",
    response_model=UserDetailResponse,
)
async def get_user_details(
    user_id: UUID = Path(..., description="User ID"),
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed user information with statistics"""
    user_data = await user_manager.get_user_with_stats(db, user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "message": "User details retrieved successfully",
        "data": user_data
    }


@router.patch(
    "/users/{user_id}/verification",
    summary="Update user verification",
    description="Update user verification status and add admin notes",
    response_model=UserVerificationResponse,
)
async def update_user_verification(
    user_id: UUID = Path(..., description="User ID"),
    verification_data: UserVerificationUpdate = ...,
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Update user verification status"""
    user = await user_manager.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await user_manager.verify_kyc(db, user_id, verification_data.is_verified)
    
    return {
        "message": f"User verification {'approved' if verification_data.is_verified else 'rejected'} successfully",
        "data": {
            "user_id": str(user_id),
            "is_verified": verification_data.is_verified,
            "verification_notes": verification_data.verification_notes,
            "updated_by": current_user.email
        }
    }


@router.delete(
    "/users/{user_id}",
    summary="Delete user",
    description="Soft delete a user account (deactivate)",
    response_model=DeleteUserResponse,
)
async def delete_user(
    user_id: UUID = Path(..., description="User ID"),
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a user account"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    success = await user_manager.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "message": "User deleted successfully",
        "data": {
            "user_id": str(user_id),
            "deleted_by": current_user.email,
            "status": "deactivated"
        }
    }


# Statistics Endpoints

@router.get(
    "/active-bids",
    summary="Get active bids statistics",
    description="Get statistics about currently active auctions and bids",
    response_model=ActiveBidsStatsResponse,
)
async def get_active_bids_stats(
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Get active bids and auctions statistics"""
    stats = await stats_manager.get_active_bids_stats(db)
    
    return {
        "message": "Active bids statistics retrieved successfully",
        "data": stats
    }


@router.get(
    "/commodities/count",
    summary="Get commodities statistics",
    description="Get statistics about commodities and categories",
    response_model=CommoditiesStatsResponse,
)
async def get_commodities_stats(
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Get commodities statistics"""
    stats = await stats_manager.get_commodities_stats(db)
    
    return {
        "message": "Commodities statistics retrieved successfully",
        "data": stats
    }


@router.get(
    "/stats/platform",
    summary="Get platform statistics",
    description="Get comprehensive platform statistics including revenue and transactions",
    response_model=PlatformStatsResponse,
)
async def get_platform_stats(
    current_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive platform statistics"""
    stats = await stats_manager.get_platform_stats(db)
    
    return {
        "message": "Platform statistics retrieved successfully",
        "data": stats
    }
