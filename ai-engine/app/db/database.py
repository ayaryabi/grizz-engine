from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging
from app.core.config import get_settings
import re
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

settings = get_settings()

# Get database URL from settings and convert to async format
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Convert SQLAlchemy URL to asyncpg format if needed
if SQLALCHEMY_DATABASE_URL.startswith("postgresql:"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql:", "postgresql+asyncpg:")
    logger.info("Converted database URL to use asyncpg")

# Log connection details safely (without password)
safe_url = SQLALCHEMY_DATABASE_URL
if '@' in safe_url:
    # Mask password in URL for logging
    safe_url = re.sub(r'\/\/([^:]+):([^@]+)@', r'//\1:****@', safe_url)

logger.info(f"Database URL: {safe_url}")

# Handle different database types
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite:"):
    logger.info("Using SQLite database")
    connect_args = {"check_same_thread": False}
    # Note: SQLite doesn't have an async driver, consider using aiosqlite if needed
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql+asyncpg:"):
    logger.info("Using PostgreSQL with asyncpg")
    # For Supabase Pooler, we need SSL
    if "pooler.supabase.com" in SQLALCHEMY_DATABASE_URL:
        connect_args = {
            "ssl": "require",
            "prepared_statement_cache_size": 0  # Disable prepared statements for pgbouncer compatibility
        }
        logger.info(f"Using Supabase connection pooler with SSL mode: {connect_args.get('ssl')}")
        logger.info("Disabled prepared statements for pgbouncer compatibility")

logger.info(f"Connecting to database with URL: {safe_url}")

# Create an async engine with optimized settings
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,      # Verify connections before using them
    pool_recycle=180,        # Drop idle connections after 3 minutes
    echo=True,               # Log SQL queries (remove in production)
)

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Prevent loading expired attributes
)

Base = declarative_base()

# Dependency for async database access
async def get_async_db():
    """Async database session dependency"""
    session = async_session_maker()
    try:
        yield session
    finally:
        await session.close()

# Backward compatibility for existing code during migration
def get_db():
    """
    Legacy synchronous database session dependency.
    This is kept for backward compatibility during migration.
    New code should use get_async_db instead.
    """
    logger.warning("Using deprecated synchronous database session. Please migrate to async.")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create a synchronous engine for backward compatibility
    sync_engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=180,
        echo=True,
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()