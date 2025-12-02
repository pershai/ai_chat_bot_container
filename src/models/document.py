from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from src.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_type = Column(String, nullable=True)  # pdf, docx, txt, etc.
    chunk_count = Column(Integer, nullable=True)  # Number of chunks created
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
