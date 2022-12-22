import asyncio
import asyncpg
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.db.db import engine
from src.main import app
from src.models.urlmodel import Base

BASE_URL = 'http://127.0.0.1'
TEST_DB_NAME = "db_tests"


async def _create_test_db() -> None:
    user, password, database = 'postgres', 'postgres', TEST_DB_NAME
    try:
        await asyncpg.connect(database=database, user=user, password=password)
    except asyncpg.InvalidCatalogNameError:
        conn = await asyncpg.connect(database='postgres', user=user,
                                     password=password)
        await conn.execute(f'CREATE DATABASE "{database}" OWNER "{user}"')
        await conn.close()
        await asyncpg.connect(database=database, user=user, password=password)


@pytest_asyncio.fixture(scope='function')
async def client() -> AsyncGenerator:
    async with AsyncClient(app=app, follow_redirects=False,
                           base_url=BASE_URL) as async_client:
        yield async_client


@pytest_asyncio.fixture(scope="module")
async def async_session() -> AsyncGenerator:
    await _create_test_db()
    session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with session() as s:
        yield s

    await engine.dispose()


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()
