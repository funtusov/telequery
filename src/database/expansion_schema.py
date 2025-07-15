from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class MessageExpansion(Base):
    __tablename__ = 'message_expansions'

    # Use the original message_id as our primary key
    message_id = Column(String, primary_key=True)

    # The LLM-generated expanded text
    expanded_text = Column(Text, nullable=False)

    # Metadata for tracking which model was used
    model_used = Column(String, nullable=False)

    # Timestamp for when the expansion was created
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_created_at', 'created_at'),
    )