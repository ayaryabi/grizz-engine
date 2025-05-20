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
from app.db.database import async_session_maker, get_async_db
from app.db.models import Conversation, Message
from sqlalchemy import select
from datetime import datetime
import pytz
import uuid

async def test_async_db():
    """Test async database operations"""
    logger.info("Starting async database test")
    
    # Create a test session
    async with async_session_maker() as session:
        try:
            # 1. Test creating a conversation
            test_user_id = "test_async_user"
            test_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Create a test conversation
            test_convo = Conversation(
                user_id=test_user_id,
                title=f"Test Conversation {test_timestamp}",
                conv_day=datetime.now(pytz.UTC).date(),
                user_tz="UTC",
            )
            session.add(test_convo)
            await session.commit()
            await session.refresh(test_convo)
            logger.info(f"Created test conversation with ID: {test_convo.id}")
            
            # 2. Test adding messages
            user_msg = Message(
                conversation_id=test_convo.id,
                user_id=test_user_id,
                role="user",
                content=f"Test message {test_timestamp}",
            )
            session.add(user_msg)
            await session.commit()
            await session.refresh(user_msg)
            logger.info(f"Added user message with ID: {user_msg.id}")
            
            # 3. Test querying messages
            stmt = select(Message).where(Message.conversation_id == test_convo.id)
            result = await session.execute(stmt)
            messages = result.scalars().all()
            logger.info(f"Found {len(messages)} messages for conversation {test_convo.id}")
            
            # 4. Test the dependency function
            logger.info("Testing get_async_db dependency")
            async for db in get_async_db():
                result = await db.execute(select(Conversation).where(Conversation.id == test_convo.id))
                found_convo = result.scalar_one_or_none()
                if found_convo:
                    logger.info(f"Successfully retrieved conversation {found_convo.id} using dependency")
                else:
                    logger.error(f"Failed to retrieve conversation {test_convo.id} using dependency")
                break
            
            logger.info("Async database test completed successfully!")
            return True
        
        except Exception as e:
            logger.error(f"Error during async database test: {str(e)}", exc_info=True)
            return False

if __name__ == "__main__":
    success = asyncio.run(test_async_db())
    if success:
        print("✅ Async database operations test passed!")
        sys.exit(0)
    else:
        print("❌ Async database operations test failed!")
        sys.exit(1) 