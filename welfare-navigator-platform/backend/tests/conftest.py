import os
import sys
import pytest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database.connection import init_sync_db, SyncSessionLocal
from database.seed import seed_database

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_sync_db()
    seed_database()
    yield

@pytest.fixture
def db_session():
    session = SyncSessionLocal()
    yield session
    session.close()
