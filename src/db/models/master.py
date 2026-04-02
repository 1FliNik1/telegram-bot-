from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.booking import Booking
    from src.db.models.service import Service
    from src.db.models.timeslot import TimeSlot


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    specialization: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    master_services: Mapped[list[MasterService]] = relationship(
        "MasterService", back_populates="master"
    )
    timeslots: Mapped[list[TimeSlot]] = relationship("TimeSlot", back_populates="master")
    bookings: Mapped[list[Booking]] = relationship("Booking", back_populates="master")

    def __repr__(self) -> str:
        return f"<Master id={self.id} name={self.name}>"


class MasterService(Base):
    __tablename__ = "master_services"
    __table_args__ = (UniqueConstraint("master_id", "service_id", name="uq_master_service"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    custom_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    custom_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    master: Mapped[Master] = relationship("Master", back_populates="master_services")
    service: Mapped[Service] = relationship("Service", back_populates="master_services")

    def __repr__(self) -> str:
        return f"<MasterService master_id={self.master_id} service_id={self.service_id}>"
