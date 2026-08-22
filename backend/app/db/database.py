import aiosqlite
import os
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from backend.app.core.config import settings
from backend.app.core.logging import logger

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    url TEXT,
    source_metadata TEXT NOT NULL DEFAULT '{}',
    tags TEXT NOT NULL DEFAULT '[]',
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    token_estimate INTEGER NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_item_id ON chunks(item_id);
"""

class Database:
    def __init__(self, db_path: str = settings.DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        conn = await aiosqlite.connect(self.db_path)
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("PRAGMA journal_mode = WAL;")
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()

    async def init_db(self) -> None:
        logger.info(f"Initializing SQLite database at: {self.db_path}")
        async with self.get_connection() as conn:
            await conn.executescript(CREATE_TABLES_SQL)
            await conn.commit()
        logger.info("SQLite tables and indexes successfully verified.")

db = Database()
