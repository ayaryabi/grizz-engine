from app.db.models import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import logging
import asyncio

logger = logging.getLogger(__name__)

async def fetch_recent_messages(conversation_id: str, db: AsyncSession, limit: int = 10):
    """
    Fetch the last N messages for a conversation, ordered chronologically.
    Uses SQLAlchemy 2.0 style select for async support.
    """
    loop = asyncio.get_event_loop()
    func_start_time = loop.time()
    try:
        # Create a query to select entire Message objects
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        
        # Execute the query
        db_exec_start_time = loop.time()
        result = await db.execute(query)
        db_exec_duration = loop.time() - db_exec_start_time
        logger.info(f"MemoryService: DB execute for conv {conversation_id} took {db_exec_duration:.4f}s")
        
        # Get all Message objects
        scalars_start_time = loop.time()
        messages = result.scalars().all()
        scalars_duration = loop.time() - scalars_start_time
        logger.info(f"MemoryService: result.scalars().all() for conv {conversation_id} took {scalars_duration:.4f}s")
        
        # Return in chronological order (oldest first)
        list_ops_start_time = loop.time()
        messages_list = list(messages)
        messages_list.reverse()
        list_ops_duration = loop.time() - list_ops_start_time
        logger.info(f"MemoryService: List ops for conv {conversation_id} took {list_ops_duration:.4f}s")
        
        total_func_duration = loop.time() - func_start_time
        logger.info(f"Fetched {len(messages_list)} messages for conversation {conversation_id} in {total_func_duration:.4f}s (total function time)")
        return messages_list
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}", exc_info=True)
        # Return empty list to avoid breaking the chat flow
        return [] 