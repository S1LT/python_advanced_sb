import asyncio
from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import Base as DatabaseBase

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def async_engine() -> AsyncGenerator[create_async_engine, None]:
    engine = create_async_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(DatabaseBase.metadata.drop_all)
        await conn.run_sync(DatabaseBase.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(
    async_engine: create_async_engine,
) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        engine=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        try:
            await session.begin()
            yield session
        finally:
            await session.rollback()
