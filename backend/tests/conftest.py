import sys
import os
import asyncio
from pathlib import Path

# Add project root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from fastapi.testclient import TestClient

# Set testing environment variables
os.environ["DB_PATH"] = "./data/test_knowledge_inbox.db"
os.environ["CHROMA_PERSIST_DIR"] = "./data/test_chroma"
os.environ["LLM_PROVIDER"] = "local"
os.environ["EMBEDDING_PROVIDER"] = "local"

from backend.main import app
from backend.app.db.database import db

@pytest.fixture(scope="session", autouse=True)
def init_test_environment():
    asyncio.run(db.init_db())
    yield
    # Cleanup test db
    if os.path.exists("./data/test_knowledge_inbox.db"):
        try:
            os.remove("./data/test_knowledge_inbox.db")
        except Exception:
            pass

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
