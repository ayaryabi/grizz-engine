from app.db.models import Message
from sqlalchemy.orm import Session
from app.llm.openai_client import stream_chat_completion
import logging
import asyncio
from typing import Callable, Any
from fastapi import HTTPException, status
from app.db.database import run_database_operation

# Configure logging
logger = logging.getLogger(__name__)

# Placeholder imports for memory_service and chat_agent
try:
    from app.services.memory_service import fetch_recent_messages
except ImportError:
    def fetch_recent_messages(conversation_id, db, limit=10):
        return []
try:
    from app.agents.chat_agent import build_prompt
except ImportError:
    def build_prompt(context_messages, user_message):
        system_prompt = "You are a helpful assistant."
        prompt = [ {"role": "system", "content": system_prompt} ]
        for msg in context_messages:
            prompt.append({"role": getattr(msg, 'role', 'user'), "content": getattr(msg, 'content', str(msg))})
        prompt.append({"role": "user", "content": user_message})
        return prompt

async def handle_chat_message(user_id, conversation_id, user_message, db: Session, stream_callback: Callable[[str], Any]):
    """
    Main chat pipeline: save user message, fetch context, build prompt, call LLM, save AI response, stream to UI.
    """
    try:
        # 1. Save user message using thread pool with timeout protection
        try:
            def save_user_msg():
                user_msg = Message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role="user",
                    content=user_message,
                )
                db.add(user_msg)
                db.commit()
                db.refresh(user_msg)
                return user_msg

            await run_database_operation(save_user_msg, timeout=3.0)
            logger.info(f"Saved user message for conversation: {conversation_id}, user: {user_id}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout saving user message for conversation: {conversation_id}")
            await stream_callback("\n\n[Error: The system is experiencing high load. Please try again in a moment.]")
            return
        
        # 2. Fetch context with timeout protection
        try:
            def get_context():
                return fetch_recent_messages(conversation_id, db)

            context = await run_database_operation(get_context, timeout=3.0)
            logger.info(f"Fetched {len(context)} context messages")
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching context for conversation: {conversation_id}")
            await stream_callback("\n\n[Error: The system is experiencing high load. Please try again in a moment.]")
            return

        # 3. Build prompt
        prompt = build_prompt(context, user_message)
        logger.info("Built prompt for AI completion")

        # 4. Call LLM and stream response with proper timeout handling
        ai_content = ""
        try:
            async for chunk in stream_chat_completion(prompt):
                ai_content += chunk
                try:
                    # Don't block if the client disconnects
                    await asyncio.wait_for(stream_callback(chunk), timeout=2.0)
                except asyncio.TimeoutError:
                    logger.warning("Client callback timed out, client may have disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error sending chunk to client: {str(e)}")
                    break
        except Exception as llm_error:
            logger.error(f"Error during LLM streaming: {str(llm_error)}")
            error_message = "\n\n[Error: Unable to get a complete response from AI service]"
            ai_content += error_message
            try:
                await stream_callback(error_message)
            except:
                pass

        # 5. Save AI response only if we got something
        if ai_content:
            try:
                def save_ai_msg():
                    ai_msg = Message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role="assistant",
                        content=ai_content,
                    )
                    db.add(ai_msg)
                    db.commit()
                    db.refresh(ai_msg)
                    return ai_msg
                
                await run_database_operation(save_ai_msg, timeout=3.0)
                logger.info(f"Saved AI response ({len(ai_content)} chars) to database")
            except asyncio.TimeoutError:
                logger.error("Timeout saving AI response to database")
                # Don't send error to client since they already got the AI response
            except Exception as db_error:
                logger.error(f"Failed to save AI response: {str(db_error)}")
        else:
            logger.warning("No AI content was generated, skipping database save")
    
    except Exception as e:
        logger.error(f"Unhandled error in chat pipeline: {str(e)}", exc_info=True)
        try:
            error_msg = f"\n\n[System Error: {str(e)}]"
            await stream_callback(error_msg)
        except:
            pass 