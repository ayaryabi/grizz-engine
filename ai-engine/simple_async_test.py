import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, String, Integer, select
from sqlalchemy.ext.declarative import declarative_base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Base class for declarative models
Base = declarative_base()

# Define a sample model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"

async def main():
    """
    Demonstrate the async database approach with SQLite
    This doesn't actually connect to a database but shows the correct approach
    """
    logger.info("Starting async database demo")
    
    # Create an in-memory SQLite engine
    # Note: This is just for demonstration; SQLite doesn't actually support real async operations
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=True
    )
    
    # Create a session factory
    async_session = async_sessionmaker(
        bind=engine,
        expire_on_commit=False
    )
    
    # Create the tables
    async with engine.begin() as conn:
        logger.info("Creating tables")
        await conn.run_sync(Base.metadata.create_all)
    
    # Insert data
    async with async_session() as session:
        logger.info("Inserting test data")
        
        # Create user
        user = User(name="Test User", email="test@example.com")
        session.add(user)
        await session.commit()
        logger.info(f"Created user: {user}")
        
        # Query user
        query = select(User).where(User.name == "Test User")
        result = await session.execute(query)
        found_user = result.scalar_one_or_none()
        
        if found_user:
            logger.info(f"Found user: {found_user}")
        else:
            logger.error("Failed to find user")
    
    logger.info("Async database demo completed successfully")
    return True

if __name__ == "__main__":
    try:
        asyncio.run(main())
        print("✅ Async database demonstration successful!")
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        print("❌ Async database demonstration failed!") 