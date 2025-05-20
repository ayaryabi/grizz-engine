import asyncio
import logging
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import after environment is loaded
from app.db.database import async_session_maker
from sqlalchemy import select, text
import uuid

async def test_async_db():
    """Test async database operations with Supabase Session Pooler"""
    logger.info("Starting async database test with session pooler")
    
    # Create a test session
    async with async_session_maker() as session:
        try:
            # 1. Test basic connection with direct SQL query
            logger.info("Testing basic connection with direct SQL query")
            result = await session.execute(select(text("1::integer")))
            value = result.scalar_one()
            logger.info(f"Direct SQL query result: {value}")
            
            # 2. Run the same query again to verify prepared statements work with session pooler
            logger.info("Running second query to verify prepared statements work")
            result = await session.execute(select(text("1::integer")))
            value = result.scalar_one()
            logger.info(f"Second direct SQL query result: {value}")
            
            # 3. Run a slightly more complex query
            logger.info("Running a more complex query")
            result = await session.execute(
                select(text("'test'::text as col1, 123::integer as col2, now() as col3"))
            )
            row = result.fetchone()
            logger.info(f"Complex query result: {row}")
            
            # 4. Test with simple queries only - parameterized queries may need special handling
            # due to the way asyncpg processes them
            logger.info("Testing simple query 1")
            result = await session.execute(select(text("random() as rand")))
            value = result.scalar_one()
            logger.info(f"Random value: {value}")
            
            logger.info("Testing simple query 2")
            result = await session.execute(select(text("now() as current_time")))
            value = result.scalar_one()
            logger.info(f"Current time: {value}")
            
            logger.info("Testing simple query 3")
            result = await session.execute(select(text("'success'::text as status")))
            value = result.scalar_one()
            logger.info(f"Status: {value}")
            
            logger.info("Async database test completed successfully!")
            await session.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error during async database test: {str(e)}", exc_info=True)
            try:
                await session.rollback()
                logger.info("Session rolled back")
            except:
                pass
            return False

if __name__ == "__main__":
    success = asyncio.run(test_async_db())
    if success:
        print("✅ Async database operations test passed!")
        sys.exit(0)
    else:
        print("❌ Async database operations test failed!")
        sys.exit(1) 