from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Message(Base):
    __tablename__ = 'messages'
    
    message_id = Column(String, primary_key=True, index=True)
    chat_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    sender_name = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    reply_to_message_id = Column(String, nullable=True)
    
    # Add indexes for efficient querying
    __table_args__ = (
        Index('idx_chat_timestamp', 'chat_id', 'timestamp'),
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )


class MessageEmbedding(Base):
    __tablename__ = 'message_embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, ForeignKey('messages.message_id'), nullable=False, unique=True)
    embedding = Column(Text, nullable=False)  # Store as JSON-serialized list
    embedding_model = Column(String, nullable=False, default='text-embedding-ada-002')
    created_at = Column(DateTime, nullable=False)
    
    # Relationship to Message
    message = relationship("Message", backref="embedding")