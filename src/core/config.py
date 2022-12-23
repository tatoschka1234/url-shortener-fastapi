import os
from logging import config as logging_config
from pydantic import BaseSettings

from src.core.logger import LOGGING

logging_config.dictConfig(LOGGING)


class AppSettings(BaseSettings):
    PROJECT_HOST = os.getenv('PROJECT_HOST', '0.0.0.0')
    PROJECT_PORT: int = int(os.getenv('PROJECT_PORT', '8000'))
    SHORT_URL_MAX_LEN: int = 30
    app_title: str = "LibraryApp"
    database_dsn: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    )
    database_doker_dsn: str = (
        "postgresql+asyncpg://postgres:postgres@db:5432/postgres"
    )
    database_dsn_test: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/db_tests"
    )
    blacklist: set = ("localhost", )
    if os.getenv('RUN_IN_DOCKER'):
        os.environ['DATABASE_DSN'] = database_doker_dsn
        database_dsn = database_doker_dsn
    else:
        os.environ['DATABASE_DSN'] = database_dsn

    class Config:
        env_file = './src/.env'


app_settings = AppSettings()
