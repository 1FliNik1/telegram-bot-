from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class PricelistServiceOut(BaseModel):
    name: str
    price: Decimal
    price_max: Optional[Decimal]
    duration_minutes: int


class PricelistCategoryOut(BaseModel):
    name: str
    emoji: Optional[str]
    services: List[PricelistServiceOut]


class PricelistResponse(BaseModel):
    salon_name: str
    categories: List[PricelistCategoryOut]
