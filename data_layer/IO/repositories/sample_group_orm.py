from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Enum, Column, ForeignKey, Table, Boolean, Float, Text, JSON, JSONB, LargeBinary
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base_orm import BaseORMVersioned

class SampleGroupTable(BaseORMVersioned):
    """A SQLAlchemy table for storing SampleGroup data in a database."""
    __tablename__ = "sample_groups"
    __table_args__ = {'extend_existing': True}

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(Enum('ACTIVE', 'INACTIVE', 'DELETED', name='status_enum'), nullable=False, default='ACTIVE')
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, default='Default')
    metrics: Mapped[JSON] = mapped_column(JSON, nullable=False)
    analysis_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    notes: Mapped[str] = mapped_column(String(50), nullable=False, default='None')


