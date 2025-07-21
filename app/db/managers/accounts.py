from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash
from app.db.managers.base import BaseManager
from app.db.models.accounts import Jwt, Otp, User
from uuid import UUID
import random


class UserManager(BaseManager[User]):
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        user = (
            await db.execute(select(self.model).where(self.model.email == email))
        ).scalar_one_or_none()
        return user

    async def create(self, db: AsyncSession, obj_in) -> User:
        # hash the password
        obj_in.update({"password": get_password_hash(obj_in["password"])})
        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: User, obj_in) -> Optional[User]:
        # hash the password
        password = obj_in.get("password")
        if password:
            obj_in["password"] = get_password_hash(password)
        user = await super().update(db, db_obj, obj_in)
        return user
    
    async def verify_kyc(self, db: AsyncSession, user_id: UUID, is_verified: bool = True) -> Optional[User]:
        """Verify or unverify a user's KYC status"""
        user = await self.get_by_id(db, user_id)
        if user:
            return await self.update(db, user, {"is_verified": is_verified})
        return None
    
    async def get_all_users_paginated(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination for admin"""
        query = select(self.model).offset(skip).limit(limit).order_by(self.model.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_total_users_count(self, db: AsyncSession) -> int:
        """Get total count of users"""
        result = await db.execute(select(func.count(self.model.id)))
        return result.scalar()
    
    async def get_users_stats(self, db: AsyncSession) -> Dict[str, int]:
        """Get user statistics for admin dashboard"""
        total_users = await db.execute(select(func.count(self.model.id)))
        active_users = await db.execute(
            select(func.count(self.model.id)).where(self.model.is_email_verified == True)
        )
        verified_users = await db.execute(
            select(func.count(self.model.id)).where(self.model.is_verified == True)
        )
        
        return {
            "total_users": total_users.scalar(),
            "active_users": active_users.scalar(),
            "verified_users": verified_users.scalar()
        }
    
    async def get_user_with_stats(self, db: AsyncSession, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user details with statistics"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
            
        # Get user's listing count
        from app.db.models.listings import Listing
        listings_count = await db.execute(
            select(func.count(Listing.id)).where(Listing.seller_id == user_id)
        )
        
        # Get user's bid count
        from app.db.models.listings import Bid
        bids_count = await db.execute(
            select(func.count(Bid.id)).where(Bid.user_id == user_id)
        )
        
        user_dict = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "is_verified": user.is_verified,
            "is_active": user.is_email_verified,  # Using is_email_verified as is_active
            "created_at": user.created_at,
            "last_login": user.updated_at,  # Using updated_at as last_login approximation
            "phone_number": user.phone_number,
            "profile_picture": user.avatar.file_name if user.avatar else None,
            "address": None,  # Address field doesn't exist in current model
            "total_listings": listings_count.scalar() or 0,
            "total_bids": bids_count.scalar() or 0,
            "total_purchases": 0  # You can add purchase tracking later
        }
        
        return user_dict
    
    async def delete_user(self, db: AsyncSession, user_id: UUID) -> bool:
        """Soft delete a user by marking email as unverified"""
        user = await self.get_by_id(db, user_id)
        if user:
            await self.update(db, user, {"is_email_verified": False})
            return True
        return False


class OtpManager(BaseManager[Otp]):
    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Optional[Otp]:
        otp = (
            await db.execute(select(self.model).where(self.model.user_id == user_id))
        ).scalar_one_or_none()
        return otp

    async def create(self, db: AsyncSession, obj_in) -> Optional[Otp]:
        code = random.randint(100000, 999999)
        obj_in.update({"code": code})
        existing_otp = await self.get_by_user_id(db, obj_in["user_id"])
        if existing_otp:
            return await self.update(db, existing_otp, {"code": code})
        return await super().create(db, obj_in)


class JwtManager(BaseManager[Jwt]):
    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> Optional[Jwt]:
        jwt = (
            await db.execute(select(self.model).where(self.model.user_id == user_id))
        ).scalar_one_or_none()
        return jwt

    async def get_by_refresh(self, db: AsyncSession, refresh: str) -> Optional[Jwt]:
        jwt = (
            await db.execute(select(self.model).where(self.model.refresh == refresh))
        ).scalar_one_or_none()
        return jwt

    async def delete_by_user_id(self, db: AsyncSession, user_id: UUID):
        jwt = (
            await db.execute(select(self.model).where(self.model.user_id == user_id))
        ).scalar_one_or_none()
        await self.delete(db, jwt)


# How to use
user_manager = UserManager(User)
otp_manager = OtpManager(Otp)
jwt_manager = JwtManager(Jwt)


# this can now be used to perform any available crud actions e.g user_manager.get_by_id(db=db, id=id)
