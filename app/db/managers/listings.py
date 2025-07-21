from typing import Optional, List, Any, Dict
from sqlalchemy import or_, select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.managers.base import BaseManager
from app.db.models.listings import Category, Listing, WatchList, Bid

from uuid import UUID
from slugify import slugify
import random
import string


def get_random_string(length: int) -> str:
    """Generate random string of given length"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


class CategoryManager(BaseManager[Category]):
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Category]:
        category = (
            await db.execute(select(self.model).where(self.model.name == name))
        ).scalar_one_or_none()
        return category

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Category]:
        category = (
            await db.execute(select(self.model).where(self.model.slug == slug))
        ).scalar_one_or_none()
        return category

    async def create(self, db: AsyncSession, obj_in) -> Optional[Category]:
        # Generate unique slug
        created_slug = slugify(obj_in["name"])
        updated_slug = obj_in.get("slug")
        slug = updated_slug if updated_slug else created_slug

        obj_in["slug"] = slug
        slug_exists = await self.get_by_slug(db, slug)
        if slug_exists:
            random_str = get_random_string(4)
            obj_in["slug"] = f"{created_slug}-{random_str}"
            return await self.create(db, obj_in)

        return await super().create(db, obj_in)


class ListingManager(BaseManager[Listing]):
    async def get_all(self, db: AsyncSession) -> Optional[List[Listing]]:
        return (
            (
                await db.execute(
                    select(self.model).order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )

    async def get_by_auctioneer_id(
        self, db: AsyncSession, auctioneer_id: UUID
    ) -> Optional[Listing]:
        return (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.auctioneer_id == auctioneer_id)
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )

    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Listing]:
        listing = (
            await db.execute(select(self.model).where(self.model.slug == slug))
        ).scalar_one_or_none()
        return listing

    async def get_related_listings(
        self, db: AsyncSession, category_id: Any, slug: str
    ) -> Optional[List[Listing]]:
        listings = (
            (
                await db.execute(
                    select(self.model)
                    .where(
                        self.model.category_id == category_id, self.model.slug != slug
                    )
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return listings

    async def get_by_category(
        self, db: AsyncSession, category: Optional[Category]
    ) -> Optional[Listing]:
        if category:
            category = category.id

        listings = (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.category_id == category)
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return listings

    async def create(self, db: AsyncSession, obj_in) -> Optional[Listing]:
        # Generate unique slug

        created_slug = slugify(obj_in["name"])
        updated_slug = obj_in.get("slug")
        slug = updated_slug if updated_slug else created_slug
        obj_in["slug"] = slug
        slug_exists = await self.get_by_slug(db, slug)
        if slug_exists:
            random_str = get_random_string(4)
            obj_in["slug"] = f"{created_slug}-{random_str}"
            return await self.create(db, obj_in)

        return await super().create(db, obj_in)

    async def update(self, db: AsyncSession, db_obj: Listing, obj_in) -> Listing:
        name = obj_in.get("name")
        if name and name != db_obj.name:
            # Generate unique slug
            created_slug = slugify(name)
            updated_slug = obj_in.get("slug")
            slug = updated_slug if updated_slug else created_slug
            obj_in["slug"] = slug
            slug_exists = await self.get_by_slug(db, slug)
            if slug_exists and not slug == db_obj.slug:
                random_str = get_random_string(4)
                obj_in["slug"] = f"{created_slug}-{random_str}"
                return await self.update(db, db_obj, obj_in)

        return await super().update(db, db_obj, obj_in)


class WatchListManager(BaseManager[WatchList]):
    async def get_by_user_id(
        self, db: AsyncSession, user_id: UUID
    ) -> Optional[List[WatchList]]:
        watchlist = (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.user_id == user_id)
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return watchlist

    async def get_by_session_key(
        self, db: AsyncSession, session_key: UUID, user_id: UUID
    ) -> Optional[List[WatchList]]:
        subquery = select(self.model.listing_id).where(self.model.user_id == user_id)
        watchlist = (
            (
                await db.execute(
                    select(self.model.listing_id)
                    .where(self.model.session_key == session_key)
                    .where(~self.model.listing_id.in_(subquery))
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return watchlist

    async def get_by_client_id(
        self, db: AsyncSession, client_id: Optional[UUID]
    ) -> Optional[List[WatchList]]:
        if not client_id:
            return []
        watchlist = (
            (
                await db.execute(
                    select(self.model)
                    .where(
                        or_(
                            self.model.user_id == client_id,
                            self.model.session_key == client_id,
                        )
                    )
                    .order_by(self.model.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return watchlist

    async def get_by_client_id_and_listing_id(
        self, db: AsyncSession, client_id: Optional[UUID], listing_id: UUID
    ) -> Optional[List[WatchList]]:
        if not client_id:
            return None

        watchlist = (
            await db.execute(
                select(self.model)
                .where(
                    or_(
                        self.model.user_id == client_id,
                        self.model.session_key == client_id,
                    )
                )
                .where(self.model.listing_id == listing_id)
            )
        ).scalar_one_or_none()
        return watchlist

    async def create(self, db: AsyncSession, obj_in: dict):
        user_id = obj_in.get("user_id")
        session_key = obj_in.get("session_key")
        listing_id = obj_in["listing_id"]
        key = user_id if user_id else session_key

        # Avoid duplicates
        existing_watchlist = await watchlist_manager.get_by_client_id_and_listing_id(
            db, key, listing_id
        )
        if existing_watchlist:
            return existing_watchlist
        return await super().create(db, obj_in)


class BidManager(BaseManager[Bid]):
    async def get_by_user_id(
        self, db: AsyncSession, user_id: UUID
    ) -> Optional[List[Bid]]:
        bids = (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.user_id == user_id)
                    .order_by(self.model.updated_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return bids

    async def get_by_listing_id(
        self, db: AsyncSession, listing_id: UUID
    ) -> Optional[List[Bid]]:
        bids = (
            (
                await db.execute(
                    select(self.model)
                    .where(self.model.listing_id == listing_id)
                    .order_by(self.model.updated_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return bids

    async def get_by_user_and_listing_id(
        self, db: AsyncSession, user_id: UUID, listing_id: UUID
    ) -> Optional[Bid]:
        bid = (
            await db.execute(
                select(self.model).where(
                    self.model.user_id == user_id, self.model.listing_id == listing_id
                )
            )
        ).scalar_one_or_none()
        return bid

    async def create(self, db: AsyncSession, obj_in: dict):
        user_id = obj_in["user_id"]
        listing_id = obj_in["listing_id"]

        existing_bid = await bid_manager.get_by_user_and_listing_id(
            db, user_id, listing_id
        )
        if existing_bid:
            obj_in.pop("user_id", None)
            obj_in.pop("listing_id", None)
            return await self.update(db, existing_bid, obj_in)

        new_bid = await super().create(db, obj_in)
        return new_bid


class StatsManager:
    """Manager for platform statistics"""
    
    @staticmethod
    async def get_active_bids_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get active bids statistics"""
        now = datetime.utcnow()
        
        # Count active auctions (listings that are still accepting bids)
        active_auctions = await db.execute(
            select(func.count(Listing.id)).where(
                and_(
                    Listing.closing_date > now,
                    Listing.active == True
                )
            )
        )
        
        # Count total active bids
        active_bids = await db.execute(
            select(func.count(Bid.id)).join(Listing).where(
                and_(
                    Listing.closing_date > now,
                    Listing.active == True
                )
            )
        )
        
        # Get highest bid amount
        highest_bid = await db.execute(
            select(func.max(Bid.amount)).join(Listing).where(
                and_(
                    Listing.closing_date > now,
                    Listing.active == True
                )
            )
        )
        
        # Get average bid amount
        avg_bid = await db.execute(
            select(func.avg(Bid.amount)).join(Listing).where(
                and_(
                    Listing.closing_date > now,
                    Listing.active == True
                )
            )
        )
        
        # Count auctions ending today
        tomorrow = now + timedelta(days=1)
        ending_today = await db.execute(
            select(func.count(Listing.id)).where(
                and_(
                    Listing.closing_date > now,
                    Listing.closing_date < tomorrow,
                    Listing.active == True
                )
            )
        )
        
        # Count auctions ending this week
        next_week = now + timedelta(days=7)
        ending_this_week = await db.execute(
            select(func.count(Listing.id)).where(
                and_(
                    Listing.closing_date > now,
                    Listing.closing_date < next_week,
                    Listing.active == True
                )
            )
        )
        
        return {
            "total_active_auctions": active_auctions.scalar() or 0,
            "total_active_bids": active_bids.scalar() or 0,
            "highest_bid_amount": float(highest_bid.scalar() or 0),
            "average_bid_amount": float(avg_bid.scalar() or 0),
            "auctions_ending_today": ending_today.scalar() or 0,
            "auctions_ending_this_week": ending_this_week.scalar() or 0
        }
    
    @staticmethod
    async def get_commodities_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get commodities statistics"""
        
        # Total commodities
        total_commodities = await db.execute(select(func.count(Listing.id)))
        
        # Active commodities
        now = datetime.utcnow()
        active_commodities = await db.execute(
            select(func.count(Listing.id)).where(
                and_(
                    Listing.closing_date > now,
                    Listing.active == True
                )
            )
        )
        
        # Pending approval - using active=False as pending
        pending_approval = await db.execute(
            select(func.count(Listing.id)).where(Listing.active == False)
        )
        
        # Categories count
        categories_count = await db.execute(select(func.count(Category.id)))
        
        # Most popular category (category with most listings)
        most_popular = await db.execute(
            select(Category.name, func.count(Listing.id).label('listing_count'))
            .join(Listing)
            .group_by(Category.id, Category.name)
            .order_by(func.count(Listing.id).desc())
            .limit(1)
        )
        most_popular_result = most_popular.first()
        most_popular_category = most_popular_result[0] if most_popular_result else "N/A"
        
        # Average commodity price
        avg_price = await db.execute(select(func.avg(Listing.price)))
        
        return {
            "total_commodities": total_commodities.scalar() or 0,
            "active_commodities": active_commodities.scalar() or 0,
            "pending_approval": pending_approval.scalar() or 0,
            "categories_count": categories_count.scalar() or 0,
            "most_popular_category": most_popular_category,
            "average_commodity_price": float(avg_price.scalar() or 0)
        }
    
    @staticmethod
    async def get_platform_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive platform statistics"""
        from app.db.models.accounts import User
        
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # User stats
        total_users = await db.execute(select(func.count(User.id)))
        active_users = await db.execute(
            select(func.count(User.id)).where(User.is_email_verified == True)
        )
        verified_users = await db.execute(
            select(func.count(User.id)).where(User.is_verified == True)
        )
        
        # Listing stats
        total_listings = await db.execute(select(func.count(Listing.id)))
        active_listings = await db.execute(
            select(func.count(Listing.id)).where(
                and_(
                    Listing.closing_date > now,
                    Listing.active == True
                )
            )
        )
        pending_listings = await db.execute(
            select(func.count(Listing.id)).where(Listing.active == False)
        )
        
        # Bid stats
        total_bids = await db.execute(select(func.count(Bid.id)))
        active_auctions = await db.execute(
            select(func.count(Listing.id)).where(
                and_(
                    Listing.closing_date > now,
                    Listing.active == True
                )
            )
        )
        
        # Revenue calculation (sum of highest bids for completed auctions)
        # Get the highest bid amount for each listing (simplified calculation)
        total_revenue = await db.execute(
            select(func.sum(Listing.highest_bid)).where(Listing.active == False)
        )
        
        monthly_revenue = await db.execute(
            select(func.sum(Listing.highest_bid))
            .where(
                and_(
                    Listing.closing_date >= current_month_start,
                    Listing.closing_date < now,
                    Listing.active == False  # Completed auctions
                )
            )
        )
        
        # Transaction counts (completed auctions)
        total_transactions = await db.execute(
            select(func.count(Listing.id)).where(Listing.active == False)
        )
        
        monthly_transactions = await db.execute(
            select(func.count(Listing.id)).where(
                and_(
                    Listing.closing_date >= current_month_start,
                    Listing.closing_date < now,
                    Listing.active == False
                )
            )
        )
        
        return {
            "total_users": total_users.scalar() or 0,
            "active_users": active_users.scalar() or 0,
            "verified_users": verified_users.scalar() or 0,
            "total_listings": total_listings.scalar() or 0,
            "active_listings": active_listings.scalar() or 0,
            "pending_approval_listings": pending_listings.scalar() or 0,
            "total_bids": total_bids.scalar() or 0,
            "active_auctions": active_auctions.scalar() or 0,
            "total_revenue": float(total_revenue.scalar() or 0),
            "monthly_revenue": float(monthly_revenue.scalar() or 0),
            "total_transactions": total_transactions.scalar() or 0,
            "monthly_transactions": monthly_transactions.scalar() or 0
        }


# How to use
category_manager = CategoryManager(Category)
listing_manager = ListingManager(Listing)
watchlist_manager = WatchListManager(WatchList)
bid_manager = BidManager(Bid)
stats_manager = StatsManager()


# this can now be used to perform any available crud actions e.g category_manager.get_by_id(db=db, id=id)
