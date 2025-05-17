from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
import re
import logging

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

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using them
    echo=True,  # Log SQL queries (remove in production)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()