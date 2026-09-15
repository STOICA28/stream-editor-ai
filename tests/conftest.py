"""Test conftest.py - M3 compatible."""
import tempfile
from pathlib import Path

import pytest

from stream_editor.editorial.providers.mock import MockEditorialProvider


@pytest.fixture
def tmp_storage():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def mock_editorial_provider():
    return MockEditorialProvider()

import sys
from unittest.mock import MagicMock
sys.modules['torch'] = MagicMock()


from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from stream_editor.api.database import Base, get_db
from stream_editor.api.main import app

@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

@pytest.fixture
async def async_client(async_db):
    app.dependency_overrides[get_db] = lambda: async_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

