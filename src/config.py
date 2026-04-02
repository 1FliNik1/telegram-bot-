from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str

    # Database
    # Railway provides DATABASE_URL as "postgres://..." — normalize to async driver
    database_url: str = "sqlite+aiosqlite:///./beauty_salon.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        # Railway/Heroku use "postgres://" — SQLAlchemy needs "postgresql+asyncpg://"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Admin IDs — JSON-масив у .env: ADMIN_IDS=[123456789,987654321]
    admin_ids: list[int] = []

    # Salon info — override in .env as needed
    salon_name: str = "Салон краси"
    salon_address: str = "вул. Хрещатик, 1, Київ"
    salon_phone: str = "+380 XX XXX XX XX"
    salon_schedule: str = "Пн–Сб: 09:00–20:00, Нд: 10:00–18:00"
    salon_maps_url: str = ""        # e.g. https://maps.google.com/?q=50.45,30.52
    salon_photo_file_id: str = ""   # Telegram file_id of salon photo

    # Mini App URL — встанови після деплою, наприклад: https://your-app.railway.app
    # або ngrok URL для локальної розробки: https://xxxx.ngrok-free.app
    miniapp_url: str = ""


settings = Settings()
