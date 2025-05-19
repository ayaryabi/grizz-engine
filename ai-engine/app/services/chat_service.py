from app.db.models import Message
from sqlalchemy.orm import Session
from app.llm.openai_client import stream_chat_completion

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

async def handle_chat_message(user_id, conversation_id, user_message, db: Session, stream_callback):
    """
    Main chat pipeline: save user message, fetch context, build prompt, call LLM, save AI response, stream to UI.
    """
    # 1. Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. Fetch context
    context = fetch_recent_messages(conversation_id, db)

    # 3. Build prompt
    prompt = build_prompt(context, user_message)

    # 4. Call LLM and stream response
    ai_content = ""
    async for chunk in stream_chat_completion(prompt):
        ai_content += chunk
        await stream_callback(chunk)  # Stream to WebSocket

    # 5. Save AI response
    ai_msg = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="assistant",
        content=ai_content,
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg) 