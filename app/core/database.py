from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from contextlib import asynccontextmanager
import logging

from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Enhanced engine with connection pooling
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "server_settings": {
            "application_name": "bidout_auction_api",
        }
    }
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Create alias for compatibility
async_session = SessionLocal


async def get_db():
    """Enhanced database session with proper error handling"""
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        await session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def get_db_transaction():
    """Context manager for explicit transactions"""
    session = SessionLocal()
    try:
        async with session.begin():
            yield session
    except Exception as e:
        logger.error(f"Transaction error: {e}")
        raise
    finally:
        await session.close()


async def check_db_connection():
    """Validate database connectivity"""
    try:
        async with SessionLocal() as session:
            await session.execute(select(1))
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
