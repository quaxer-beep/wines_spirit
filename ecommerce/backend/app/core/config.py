from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Wines & Spirits E-Commerce"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "wines_spirits_ecommerce"

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MPESA_ENV: str = "sandbox"
    MPESA_CONSUMER_KEY: str = ""
    MPESA_CONSUMER_SECRET: str = ""
    MPESA_PASSKEY: str = ""
    MPESA_SHORTCODE: str = ""
    MPESA_CALLBACK_URL: str = ""

    FCM_SERVER_KEY: str = ""

    GOOGLE_MAPS_API_KEY: str = ""

    SMS_API_URL: str = ""
    SMS_API_KEY: str = ""
    SMS_SENDER_ID: str = "WINESPOS"

    WHATSAPP_API_URL: str = ""
    WHATSAPP_API_KEY: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "eu-west-1"
    S3_BUCKET_NAME: str = "wines-spirits-verification-docs"

    SENTRY_DSN: str = ""

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    DELIVERY_BASE_FEE: float = 100.0
    DELIVERY_PER_KM_RATE: float = 30.0
    DELIVERY_FUEL_ADJUSTMENT_PCT: float = 5.0

    LOYALTY_POINTS_PER_KES: float = 1.0
    LOYALTY_REDEMPTION_RATE: float = 0.05
    LOYALTY_MIN_REDEMPTION: int = 100
    LOYALTY_EXPIRY_DAYS: int = 365

    LEGAL_DRINKING_AGE: int = 18

    SYNC_INTERVAL_SECONDS: int = 300
    POS_DATABASE_PATH: str = ""
    USE_SQLITE: bool = True

    @property
    def database_url(self) -> str:
        if self.USE_SQLITE:
            db_path = Path(__file__).resolve().parent.parent.parent / "data" / "ecommerce.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        if self.USE_SQLITE:
            db_path = Path(__file__).resolve().parent.parent.parent / "data" / "ecommerce.db"
            return f"sqlite:///{db_path}"
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
