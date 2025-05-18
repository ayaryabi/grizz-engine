from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False)  # References auth.users.id
    context_byte_id = Column(String, nullable=True)  # Optional reference to bytes
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

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, nullable=True)  # Optional, can be null for system messages
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    meta_data = Column(Text, nullable=True)  # JSON for any additional data, renamed from 'metadata'
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    conversation = relationship("Conversation", back_populates="messages")
    
    # Add index for faster querying by conversation_id
    __table_args__ = (
        Index('idx_message_conversation_id', 'conversation_id'),
    )