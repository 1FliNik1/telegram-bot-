from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_user, get_session
from src.api.schemas.catalog import (
    CategoriesResponse,
    CategoryBrief,
    CategoryOut,
    MasterSummaryOut,
    ServiceDetailResponse,
    ServiceOut,
    ServicesInCategoryResponse,
)
from src.db.models.service import ServiceCategory
from src.db.models.user import User
from src.db.repositories.master_repo import MasterRepository
from src.db.repositories.service_repo import (
    ServiceCategoryRepository,
    ServiceRepository,
)

router = APIRouter()


@router.get("/categories", response_model=CategoriesResponse)
async def list_categories(
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_db_user),
) -> CategoriesResponse:
    cat_repo = ServiceCategoryRepository(session)
    svc_repo = ServiceRepository(session)
    categories = await cat_repo.get_active_categories()
    items = []
    for cat in categories:
        svcs = await svc_repo.get_services_by_category(cat.id)
        items.append(
            CategoryOut(id=cat.id, name=cat.name, emoji=cat.emoji, services_count=len(svcs))
        )
    return CategoriesResponse(categories=items)


@router.get("/services", response_model=ServicesInCategoryResponse)
async def list_all_services(
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_db_user),
) -> ServicesInCategoryResponse:
    """All active services across all categories — used by the 'Все' tab."""
    svc_repo = ServiceRepository(session)
    master_repo = MasterRepository(session)

    categories = await ServiceCategoryRepository(session).get_active_categories()
    service_items = []
    for cat in categories:
        svcs = await svc_repo.get_services_by_category(cat.id)
        for svc in svcs:
            masters = await master_repo.get_masters_by_service(svc.id)
            service_items.append(
                ServiceOut(
                    id=svc.id,
                    name=svc.name,
                    description=svc.description,
                    price=svc.price,
                    price_max=svc.price_max,
                    duration_minutes=svc.duration_minutes,
                    photo_file_id=svc.photo_file_id,
                    masters_count=len(masters),
                )
            )

    return ServicesInCategoryResponse(
        category=CategoryBrief(id=0, name="Всі послуги", emoji="💅"),
        services=service_items,
    )


@router.get("/categories/{category_id}/services", response_model=ServicesInCategoryResponse)
async def list_services_in_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_db_user),
) -> ServicesInCategoryResponse:
    svc_repo = ServiceRepository(session)
    master_repo = MasterRepository(session)

    result = await session.execute(
        select(ServiceCategory)
        .where(ServiceCategory.id == category_id)
        .where(ServiceCategory.is_active.is_(True))
    )
    cat = result.scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    svcs = await svc_repo.get_services_by_category(category_id)
    service_items = []
    for svc in svcs:
        masters = await master_repo.get_masters_by_service(svc.id)
        service_items.append(
            ServiceOut(
                id=svc.id,
                name=svc.name,
                description=svc.description,
                price=svc.price,
                price_max=svc.price_max,
                duration_minutes=svc.duration_minutes,
                photo_file_id=svc.photo_file_id,
                masters_count=len(masters),
            )
        )

    return ServicesInCategoryResponse(
        category=CategoryBrief(id=cat.id, name=cat.name, emoji=cat.emoji),
        services=service_items,
    )


@router.get("/services/{service_id}", response_model=ServiceDetailResponse)
async def get_service_detail(
    service_id: int,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_db_user),
) -> ServiceDetailResponse:
    svc_repo = ServiceRepository(session)
    master_repo = MasterRepository(session)

    svc = await svc_repo.get_service_by_id(service_id)
    if svc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    all_masters = await master_repo.get_masters_by_service(service_id)
    masters_with_pricing = await svc_repo.get_masters_with_pricing(service_id)
    pricing_map = {ms.master_id: ms for _, ms in masters_with_pricing}

    master_items = []
    for master in all_masters:
        ms = pricing_map.get(master.id)
        master_items.append(
            MasterSummaryOut(
                id=master.id,
                name=master.name,
                specialization=master.specialization,
                bio=master.bio,
                photo_file_id=master.photo_file_id,
                custom_price=ms.custom_price if ms else None,
                custom_duration=ms.custom_duration if ms else None,
            )
        )

    service_out = ServiceOut(
        id=svc.id,
        name=svc.name,
        description=svc.description,
        price=svc.price,
        price_max=svc.price_max,
        duration_minutes=svc.duration_minutes,
        photo_file_id=svc.photo_file_id,
        masters_count=len(master_items),
    )
    return ServiceDetailResponse(service=service_out, masters=master_items)
