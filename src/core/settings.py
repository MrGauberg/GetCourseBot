from __future__ import annotations
from typing import Optional

from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict
from os import path


class BaseSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', extra='ignore'
    )
    # model_config = SettingsConfigDict(secrets_dir='/run/secrets')


class ApplicationSettings(BaseSettings):
    APPLICATION_URL: str


application_settings = ApplicationSettings()


class UserSettings(BaseSettings):
    BOT_TOKEN: str
    UKASSA_TOKEN: str
    USER_TG_ID: str
    USER_TG_NAME: str
    USER_ID: str
    YOOKASSA_SHOP_ID: str
    YOOKASSA_SECRET_KEY: str


user_settings = UserSettings()


class RedisSettings(BaseSettings):
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[str] = None


redis_settings = RedisSettings()
