from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.db.managers.base import BaseManager
from app.db.models.listings import CommodityListing
from app.db.models.accounts import User
from uuid import UUID
from slugify import slugify


class CommodityListingManager(BaseManager[CommodityListing]):
    async def get_approved_listings(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[CommodityListing]:
        """Get all approved and active commodity listings"""
        query = (
            select(self.model)
            .options(selectinload(self.model.farmer))
            .options(selectinload(self.model.category))
            .options(selectinload(self.model.image))
            .where(
                and_(
                    self.model.is_approved == True,
                    self.model.is_active == True
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_farmer(
        self, 
        db: AsyncSession, 
        farmer_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommodityListing]:
        """Get all commodity listings by a specific farmer"""
        query = (
            select(self.model)
            .options(selectinload(self.model.farmer))
            .options(selectinload(self.model.category))
            .options(selectinload(self.model.image))
            .where(self.model.farmer_id == farmer_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_pending_approval(
        self, 
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommodityListing]:
        """Get all commodity listings pending approval"""
        query = (
            select(self.model)
            .options(selectinload(self.model.farmer))
            .options(selectinload(self.model.category))
            .options(selectinload(self.model.image))
            .where(self.model.is_approved == False)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[CommodityListing]:
        """Get commodity listing by slug"""
        query = (
            select(self.model)
            .options(selectinload(self.model.farmer))
            .options(selectinload(self.model.category))
            .options(selectinload(self.model.image))
            .where(self.model.slug == slug)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def search_commodities(
        self,
        db: AsyncSession,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CommodityListing]:
        """Search commodities by name or description"""
        query = (
            select(self.model)
            .options(selectinload(self.model.farmer))
            .options(selectinload(self.model.category))
            .options(selectinload(self.model.image))
            .where(
                and_(
                    self.model.is_approved == True,
                    self.model.is_active == True,
                    or_(
                        self.model.commodity_name.ilike(f"%{search_term}%"),
                        self.model.description.ilike(f"%{search_term}%")
                    )
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: dict) -> CommodityListing:
        """Create a new commodity listing with auto-generated slug"""
        # Generate slug from commodity name
        base_slug = slugify(obj_in["commodity_name"])
        slug = base_slug
        counter = 1
        
        # Ensure slug is unique
        while await self.get_by_slug(db, slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        obj_in["slug"] = slug
        return await super().create(db, obj_in)

    async def approve_listing(
        self, 
        db: AsyncSession, 
        listing_id: UUID, 
        is_approved: bool = True
    ) -> Optional[CommodityListing]:
        """Approve or reject a commodity listing"""
        listing = await self.get_by_id(db, listing_id)
        if listing:
            return await self.update(db, listing, {"is_approved": is_approved})
        return None


# Instance to use throughout the application
commodity_listing_manager = CommodityListingManager(CommodityListing)
