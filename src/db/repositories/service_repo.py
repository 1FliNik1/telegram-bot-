from __future__ import annotations

from typing import List, Tuple

from sqlalchemy import select

from src.db.models.master import Master, MasterService
from src.db.models.service import Service, ServiceCategory
from src.db.repositories.base import BaseRepository


class ServiceCategoryRepository(BaseRepository[ServiceCategory]):
    model = ServiceCategory

    async def get_active_categories(self) -> list[ServiceCategory]:
        """Повертає активні категорії які мають хоча б одну активну послугу (US-001)."""
        stmt = (
            select(ServiceCategory)
            .join(Service, Service.category_id == ServiceCategory.id)
            .where(ServiceCategory.is_active.is_(True))
            .where(Service.is_active.is_(True))
            .distinct()
            .order_by(ServiceCategory.sort_order, ServiceCategory.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ServiceRepository(BaseRepository[Service]):
    model = Service

    async def get_services_by_category(self, category_id: int) -> list[Service]:
        """Активні послуги категорії, відсортовані за sort_order (US-002)."""
        stmt = (
            select(Service)
            .where(Service.category_id == category_id)
            .where(Service.is_active.is_(True))
            .order_by(Service.sort_order, Service.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_masters_with_pricing(
        self, service_id: int
    ) -> List[Tuple[Master, MasterService]]:
        """Returns (Master, MasterService) tuples for active masters of a service."""
        stmt = (
            select(Master, MasterService)
            .join(MasterService, MasterService.master_id == Master.id)
            .where(MasterService.service_id == service_id)
            .where(Master.is_active.is_(True))
            .order_by(Master.sort_order, Master.name)
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_service_by_id(self, service_id: int) -> Service | None:
        """Повертає активну послугу за id (US-003)."""
        stmt = (
            select(Service)
            .where(Service.id == service_id)
            .where(Service.is_active.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
