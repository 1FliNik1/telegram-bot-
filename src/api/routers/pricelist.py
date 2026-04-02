from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_user, get_session
from src.api.schemas.pricelist import (
    PricelistCategoryOut,
    PricelistResponse,
    PricelistServiceOut,
)
from src.config import settings
from src.db.models.user import User
from src.db.repositories.service_repo import (
    ServiceCategoryRepository,
    ServiceRepository,
)

router = APIRouter()


@router.get("/pricelist", response_model=PricelistResponse)
async def get_pricelist(
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_db_user),
) -> PricelistResponse:
    cat_repo = ServiceCategoryRepository(session)
    svc_repo = ServiceRepository(session)

    categories = await cat_repo.get_active_categories()
    result = []
    for cat in categories:
        svcs = await svc_repo.get_services_by_category(cat.id)
        result.append(
            PricelistCategoryOut(
                name=cat.name,
                emoji=cat.emoji,
                services=[
                    PricelistServiceOut(
                        name=s.name,
                        price=s.price,
                        price_max=s.price_max,
                        duration_minutes=s.duration_minutes,
                    )
                    for s in svcs
                ],
            )
        )
    return PricelistResponse(salon_name=settings.salon_name, categories=result)
