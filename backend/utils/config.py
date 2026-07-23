from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALG: str
    REDIS_URL: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )


Config = Settings()
