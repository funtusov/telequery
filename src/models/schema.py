from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Index, ForeignKey, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Message(Base):
    __tablename__ = 'messages'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Core message fields - matching actual database schema
    telegram_id = Column(BigInteger, nullable=False, index=True)
    chat_id = Column(Integer, nullable=False, index=True)
    text = Column(Text, nullable=True)
    message_type = Column(String(50), nullable=False)
    sender_id = Column(BigInteger, nullable=True)
    sender_name = Column(String(255), nullable=True)
    sender_username = Column(String(255), nullable=True)
    telegram_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    is_outgoing = Column(Boolean, nullable=True)
    is_reply = Column(Boolean, nullable=True)
    reply_to_message_id = Column(BigInteger, nullable=True)
    forward_from_id = Column(BigInteger, nullable=True)
    forward_from_name = Column(String(255), nullable=True)
    media_type = Column(String(50), nullable=True)
    media_file_id = Column(String(255), nullable=True)
    media_file_name = Column(String(255), nullable=True)
    media_file_size = Column(BigInteger, nullable=True)
    
    # Properties for compatibility with TelegramMessage model
    @property
    def message_id(self):
        return str(self.telegram_id)
    
    @property
    def timestamp(self):
        return self.telegram_date
    
    @property
    def user_id(self):
        return str(self.sender_id) if self.sender_id else "unknown"


class MessageEmbedding(Base):
    __tablename__ = 'message_embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, ForeignKey('messages.telegram_id'), nullable=False, unique=True)
    embedding = Column(Text, nullable=False)  # Store as JSON-serialized list
    embedding_model = Column(String, nullable=False, default='text-embedding-ada-002')
    created_at = Column(DateTime, nullable=False)
    
    # Relationship to Message
    message = relationship("Message", backref="embedding")