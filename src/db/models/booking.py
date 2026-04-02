from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.master import Master
    from src.db.models.service import Service
    from src.db.models.timeslot import TimeSlot
    from src.db.models.user import User


class BookingStatus(str, enum.Enum):  # noqa: UP042 — Python 3.9 compat
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_booking_master_timeslot", "master_id", "timeslot_id"),
        Index("ix_booking_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    master_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("masters.id", ondelete="RESTRICT"), nullable=False
    )
    timeslot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("timeslots.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False
    )
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_24h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_2h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="bookings")
    service: Mapped[Service] = relationship("Service", back_populates="bookings")
    master: Mapped[Master] = relationship("Master", back_populates="bookings")
    timeslot: Mapped[TimeSlot] = relationship("TimeSlot", back_populates="booking")

    def __repr__(self) -> str:
        return f"<Booking id={self.id} user_id={self.user_id} status={self.status}>"
