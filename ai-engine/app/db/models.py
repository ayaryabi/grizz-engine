from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Date, Index, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .database import Base
import uuid

def generate_uuid():
    return uuid.uuid4()

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    user_id = Column(UUID, nullable=False)  # Changed to UUID to match database schema
    context_byte_id = Column(UUID, nullable=True)  # Changed to UUID to match database schema
    title = Column(String(100), default="New Conversation")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    conv_day = Column(Date, nullable=False)  # For storing the conversation's date (UTC)
    user_tz = Column(String, nullable=False, default="UTC")  # For storing the user's timezone
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    # Add indices for faster querying
    __table_args__ = (
        Index('idx_conversation_user_id', 'user_id'),
        Index('idx_conversation_user_day', 'user_id', 'conv_day', unique=True),
    )

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    conversation_id = Column(UUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID, nullable=True)  # Changed to UUID to match database schema
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_metadata = Column("metadata", JSONB, nullable=True)  # Explicitly use JSONB for metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    conversation = relationship("Conversation", back_populates="messages")
    
    # Add index for faster querying by conversation_id
    __table_args__ = (
        Index('idx_message_conversation_id', 'conversation_id'),
    )

class Memory(Base):
    __tablename__ = "memory"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID, nullable=False)
    item_type = Column(Text, nullable=False, default="note")
    title = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Changed to TEXT as requested
    properties = Column(JSONB, nullable=True, default=lambda: {})
    file_url = Column(Text, nullable=True)
    mime_type = Column(Text, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Add indices for faster querying
    __table_args__ = (
        Index('idx_memory_user_id', 'user_id'),
        Index('idx_memory_user_created', 'user_id', 'created_at'),
        Index('idx_memory_item_type', 'item_type'),
    )