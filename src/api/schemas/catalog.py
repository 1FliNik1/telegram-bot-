from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    name: str
    emoji: Optional[str]
    services_count: int

    model_config = {"from_attributes": True}


class CategoriesResponse(BaseModel):
    categories: List[CategoryOut]


class CategoryBrief(BaseModel):
    id: int
    name: str
    emoji: Optional[str]

    model_config = {"from_attributes": True}


class ServiceOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: Decimal
    price_max: Optional[Decimal]
    duration_minutes: int
    photo_file_id: Optional[str]
    masters_count: int

    model_config = {"from_attributes": True}


class ServicesInCategoryResponse(BaseModel):
    category: CategoryBrief
    services: List[ServiceOut]


class MasterSummaryOut(BaseModel):
    id: int
    name: str
    specialization: Optional[str]
    bio: Optional[str]
    photo_file_id: Optional[str]
    custom_price: Optional[Decimal]
    custom_duration: Optional[int]


class ServiceDetailResponse(BaseModel):
    service: ServiceOut
    masters: List[MasterSummaryOut]
