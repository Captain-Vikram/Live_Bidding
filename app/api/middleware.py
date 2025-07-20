from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.db.models.accounts import User, UserRole


async def require_verified_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Middleware function that requires users to be KYC verified for certain operations.
    Used for bidding and other sensitive operations.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "KYC verification required",
                "error": "You must complete KYC verification before bidding. Please contact support to verify your account."
            }
        )
    return current_user


async def require_farmer_role(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Middleware function that requires users to have farmer role.
    Used for commodity listing creation.
    """
    if current_user.role != UserRole.FARMER:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Farmer role required",
                "error": "Only farmers can create commodity listings."
            }
        )
    return current_user


async def require_admin_role(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Middleware function that requires users to have admin role or be superuser.
    Used for admin operations like approving listings.
    """
    if not (current_user.is_superuser or current_user.is_staff or current_user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Admin privileges required",
                "error": "You don't have permission to perform this action."
            }
        )
    return current_user
