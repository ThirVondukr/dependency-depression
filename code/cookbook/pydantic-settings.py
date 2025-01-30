from collections.abc import Sequence

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

import aioinject


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="app_")

    version: str
    site_url: str


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="database_")

    url: PostgresDsn


_settings_classes: Sequence[type[BaseSettings]] = [
    AppSettings,
    DatabaseSettings,
]


def create_container() -> aioinject.Container:
    container = aioinject.Container()

    for settings_cls in _settings_classes:
        # Type is inferred from the instance passed into "Object"
        container.register(aioinject.Object(settings_cls()))

    return container
