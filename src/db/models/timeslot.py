from __future__ import annotations

from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.booking import Booking
    from src.db.models.master import Master


class TimeSlot(Base):
    __tablename__ = "timeslots"
    __table_args__ = (
        Index("ix_timeslot_master_date", "master_id", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    master_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("masters.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    master: Mapped[Master] = relationship("Master", back_populates="timeslots")
    booking: Mapped[Booking | None] = relationship("Booking", back_populates="timeslot")

    def __repr__(self) -> str:
        return (
            f"<TimeSlot id={self.id} master_id={self.master_id} "
            f"date={self.date} {self.start_time}-{self.end_time} available={self.is_available}>"
        )
