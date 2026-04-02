from __future__ import annotations

from sqlalchemy import select

from src.db.models.master import Master, MasterService
from src.db.repositories.base import BaseRepository


class MasterRepository(BaseRepository[Master]):
    model = Master

    async def get_masters_by_service(self, service_id: int) -> list[Master]:
        """Active masters who can perform the given service."""
        stmt = (
            select(Master)
            .join(MasterService, MasterService.master_id == Master.id)
            .where(MasterService.service_id == service_id)
            .where(Master.is_active.is_(True))
            .order_by(Master.sort_order, Master.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_masters(self) -> list[Master]:
        stmt = (
            select(Master)
            .where(Master.is_active.is_(True))
            .order_by(Master.sort_order, Master.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
