from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Enum, Column, ForeignKey, Table, Boolean, Float, Text, JSON, JSONB, LargeBinary
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base_orm import BaseORMVersioned

class Specimen_Table(BaseORMVersioned):
    """ORM class for Specimen table."""
    __tablename__ = 'specimen'
    __table_args__ = {'extend_existing': True}

    # Columns
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(Enum('ACTIVE', 'INACTIVE', 'DELETED', name='status_enum'), nullable=False, default='ACTIVE')
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default='Compression')
    property: Mapped[JSON] = mapped_column(JSON, nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False, default='Default')
    metrics: Mapped[JSON] = mapped_column(JSON, nullable=False)
    analysis_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    production_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    cross_sectional_image: Mapped[LargeBinary] = mapped_column(LargeBinary, nullable=True)
    notes: Mapped[str] = mapped_column(String(50), nullable=False, default='None')


