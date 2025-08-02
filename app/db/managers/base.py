from datetime import datetime
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.core.database import Base
from app.db.models.base import File, GuestUser

logger = logging.getLogger(__name__)
ModelType = TypeVar("ModelType", bound=Base)


class BaseManager(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get_all(self, db: AsyncSession) -> Optional[List[ModelType]]:
        result = (await db.execute(select(self.model))).scalars().all()
        return result

    async def get_all_ids(self, db: AsyncSession) -> Optional[List[ModelType]]:
        result = (await db.execute(select(self.model.id))).scalars().all()
        # ids = [item[0] for item in items]
        return result

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        return (
            await db.execute(select(self.model).where(self.model.id == id))
        ).scalar_one_or_none()

    async def create(
        self, db: AsyncSession, obj_in: Optional[dict] = None
    ) -> Optional[ModelType]:
        """Create with proper error handling"""
        if obj_in is None:
            obj_in = {}
        
        try:
            obj_in["created_at"] = datetime.utcnow()
            obj_in["updated_at"] = obj_in["created_at"]
            obj = self.model(**obj_in)

            db.add(obj)
            await db.flush()  # Flush but don't commit yet
            await db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            logger.error(f"Database error in create: {e}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create: {e}")
            await db.rollback()
            raise

    async def bulk_create(self, db: AsyncSession, obj_in: list) -> Optional[List]:
        """Bulk create with proper error handling"""
        try:
            items = await db.execute(
                insert(self.model)
                .values(obj_in)
                .on_conflict_do_nothing()
                .returning(self.model.id)
            )
            await db.flush()  # Flush but don't commit yet
            ids = [item[0] for item in items]
            return ids
        except SQLAlchemyError as e:
            logger.error(f"Database error in bulk_create: {e}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in bulk_create: {e}")
            await db.rollback()
            raise

    async def update(
        self, db: AsyncSession, db_obj: Optional[ModelType], obj_in: Optional[dict]
    ) -> Optional[ModelType]:
        """Update with proper error handling"""
        if not db_obj or not obj_in:
            return None
            
        try:
            for attr, value in obj_in.items():
                setattr(db_obj, attr, value)
            db_obj.updated_at = datetime.utcnow()

            await db.flush()  # Flush but don't commit yet
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Database error in update: {e}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in update: {e}")
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, db_obj: Optional[ModelType]):
        """Delete with proper error handling"""
        if db_obj:
            try:
                await db.delete(db_obj)
                await db.flush()  # Flush but don't commit yet
            except SQLAlchemyError as e:
                logger.error(f"Database error in delete: {e}")
                await db.rollback()
                raise
            except Exception as e:
                logger.error(f"Unexpected error in delete: {e}")
                await db.rollback()
                raise

    async def delete_by_id(self, db: AsyncSession, id: UUID):
        """Delete by ID with proper error handling"""
        try:
            to_delete = (
                await db.execute(select(self.model).where(self.model.id == id))
            ).scalar_one_or_none()
            if to_delete:
                await db.delete(to_delete)
                await db.flush()  # Flush but don't commit yet
        except SQLAlchemyError as e:
            logger.error(f"Database error in delete_by_id: {e}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in delete_by_id: {e}")
            await db.rollback()
            raise

    async def delete_all(self, db: AsyncSession):
        """Delete all with proper error handling"""
        try:
            to_delete = await db.delete(self.model)
            await db.execute(to_delete)
            await db.flush()  # Flush but don't commit yet
        except SQLAlchemyError as e:
            logger.error(f"Database error in delete_all: {e}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in delete_all: {e}")
            await db.rollback()
            raise

    async def safe_commit(self, db: AsyncSession):
        """Safe commit with error handling"""
        try:
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Commit failed: {e}")
            await db.rollback()
            raise


class FileManager(BaseManager[File]):
    pass


class GuestUserManager(BaseManager[GuestUser]):
    pass


file_manager = FileManager(File)
guestuser_manager = GuestUserManager(GuestUser)
