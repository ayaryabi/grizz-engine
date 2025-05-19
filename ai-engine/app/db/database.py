from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import concurrent.futures
import asyncio
from app.core.config import get_settings
import re
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

settings = get_settings()

# Get database URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

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
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql:"):
    logger.info("Using PostgreSQL database")
    # For Supabase Pooler, we need SSL
    if "pooler.supabase.com" in SQLALCHEMY_DATABASE_URL:
        connect_args = {
            "sslmode": "require"
        }
        logger.info(f"Using Supabase connection pooler with SSL mode: {connect_args.get('sslmode')}")

logger.info(f"Connecting to database with URL: {safe_url}")

# Set max workers to match available CPU cores, retrieved from environment or default to 4
MAX_WORKERS = int(os.getenv("MAX_DB_WORKERS", "4"))
logger.info(f"Configuring database with MAX_WORKERS={MAX_WORKERS}")

# Create a synchronous engine with optimized settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,      # Verify connections before using them
    pool_recycle=180,        # Drop idle connections after 3 minutes
    pool_size=MAX_WORKERS,   # Match pool size to thread pool size
    max_overflow=0,          # Don't allow extra connections beyond pool_size
    echo=True,               # Log SQL queries (remove in production)
)

# Create synchronous session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Create thread pool for running database operations without blocking
# Number of workers now matches the database pool size for optimal resource usage
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Dependency for synchronous database access
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Async wrapper for database operations with timeout protection
async def run_database_operation(operation_func, *args, timeout=5.0, **kwargs):
    """
    Run a synchronous database operation in a thread pool
    with timeout protection to prevent blocking the async event loop.
    
    Args:
        operation_func: The database function to run
        timeout: Maximum time to wait for DB operation (defaults to 5s)
        *args, **kwargs: Arguments to pass to the operation function
    
    Raises:
        asyncio.TimeoutError: If the operation takes longer than the timeout
    """
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(
                thread_pool, 
                lambda: operation_func(*args, **kwargs)
            ),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Database operation timed out after {timeout}s")
        raise  # Re-raise for the caller to handle

# Example usage in an async endpoint:
# async def get_user(user_id: str):
#     def _get_user_sync(user_id):
#         with SessionLocal() as session:
#             return session.query(User).filter(User.id == user_id).first()
#     
#     try:
#         return await run_database_operation(_get_user_sync, user_id, timeout=3.0)
#     except asyncio.TimeoutError:
#         # Handle timeout, e.g., return a 503 Service Unavailable
#         raise HTTPException(status_code=503, detail="Database operation timed out")