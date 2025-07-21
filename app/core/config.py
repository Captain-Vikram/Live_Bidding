from fastapi_mail import ConnectionConfig
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import AnyUrl, BaseSettings, EmailStr, validator

PROJECT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    # DEBUG
    DEBUG: bool

    # TOKENS
    EMAIL_OTP_EXPIRE_SECONDS: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    # SECURITY
    SECRET_KEY: str

    # PROJECT DETAILS
    PROJECT_NAME: str
    FRONTEND_URL: str
    CORS_ALLOWED_ORIGINS: Union[List, str]

    # POSTGRESQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URL: Optional[str] = None

    # FIRST SUPERUSER
    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # FIRST SELLER
    FIRST_SELLER_EMAIL: EmailStr
    FIRST_SELLER_PASSWORD: str

    # FIRST REVIEWER
    FIRST_REVIEWER_EMAIL: EmailStr
    FIRST_REVIEWER_PASSWORD: str

    # EMAIL CONFIG
    MAIL_SENDER_EMAIL: str
    MAIL_SENDER_PASSWORD: str
    MAIL_SENDER_HOST: str
    MAIL_SENDER_PORT: int
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: str
    TEMPLATE_FOLDER: Optional[str] = f"{PROJECT_DIR}/app/templates"

    EMAIL_CONFIG: Optional[ConnectionConfig] = None
    
    # SMS CONFIG (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    SMS_ENABLED: bool = False
    
    # ADMIN CONTACT INFO (for notifications and testing)
    ADMIN_PHONE_NUMBER: Optional[str] = None
    ADMIN_EMAIL: Optional[str] = None
    DEVELOPER_EMAIL: Optional[str] = None
    
    # CLOUDINARY CONFIG
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    # REDIS CONFIG
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CELERY CONFIG
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # PHASE 5: Price History and Alerts Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Price tracking configuration
    PRICE_GENERATION_ENABLED: bool = True
    PRICE_VOLATILITY_FACTOR: float = 0.1  # 10% max daily price change
    
    # Alert configuration
    ALERT_CHECK_INTERVAL_MINUTES: int = 30
    MAX_ALERTS_PER_USER_PER_DAY: int = 10
    
    # On-site notification configuration
    ONSITE_NOTIFICATION_RETENTION_DAYS: int = 30
    MAX_ONSITE_NOTIFICATIONS_PER_USER: int = 100

    @validator("SQLALCHEMY_DATABASE_URL", pre=True)
    def assemble_postgres_connection(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> str:

        # Assemble postgres url
        if isinstance(v, str):
            return v
        if values.get("DEBUG"):
            postgres_server = "localhost"
        else:
            postgres_server = values.get("POSTGRES_SERVER")

        return AnyUrl.build(
            scheme="postgresql+psycopg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=postgres_server or "localhost",
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB')}",
        )

    @validator("CORS_ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            # Split by comma first, then by space, and clean up
            origins = []
            for item in v.replace(',', ' ').split():
                if item.strip():
                    origins.append(item.strip())
            return origins
        return v

    @validator("EMAIL_CONFIG", pre=True)
    def _assemble_email_config(cls, v: Optional[str], values):
        return ConnectionConfig(
            MAIL_USERNAME=values.get("MAIL_SENDER_EMAIL"),
            MAIL_PASSWORD=values.get("MAIL_SENDER_PASSWORD"),
            MAIL_FROM=values.get("MAIL_SENDER_EMAIL"),
            MAIL_PORT=values.get("MAIL_SENDER_PORT"),
            MAIL_SERVER=values.get("MAIL_SENDER_HOST"),
            MAIL_FROM_NAME=values.get("MAIL_FROM_NAME"),
            MAIL_STARTTLS=values.get("MAIL_STARTTLS"),
            MAIL_SSL_TLS=values.get("MAIL_SSL_TLS"),
            USE_CREDENTIALS=values.get("USE_CREDENTIALS"),
            TEMPLATE_FOLDER=values.get("TEMPLATE_FOLDER"),
        )

    class Config:
        env_file = f"{PROJECT_DIR}/.env"
        case_sensitive = True


settings: Settings = Settings()
