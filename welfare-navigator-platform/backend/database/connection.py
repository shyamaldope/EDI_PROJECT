import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from config import settings

Base = declarative_base()

# Async Engine Setup
async_database_url = settings.DATABASE_URL
if async_database_url.startswith("sqlite"):
    async_engine = create_async_engine(
        async_database_url,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    async_engine = create_async_engine(
        async_database_url,
        echo=False,
        pool_pre_ping=True
    )

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Sync Engine Setup (for seeder, standalone scripts & celery)
sync_database_url = settings.SYNC_DATABASE_URL
if sync_database_url.startswith("sqlite"):
    sync_engine = create_engine(
        sync_database_url,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    sync_engine = create_engine(
        sync_database_url,
        echo=False,
        pool_pre_ping=True
    )

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db():
    """FastAPI async dependency yield session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    """Sync context manager for CLI/seeder/tests"""
    db = SyncSessionLocal()
    try:
        return db
    finally:
        pass

async def init_db():
    """Creates tables asynchronously if not existing"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def init_sync_db():
    """Creates tables synchronously"""
    Base.metadata.create_all(bind=sync_engine)
