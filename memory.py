"""Thread-based conversation history backed by SQLite.

Replaces LangGraph's SQLite checkpointer with a lightweight store that
serialises PydanticAI ``ModelMessage`` lists per ``thread_id``.
"""

import logging

import aiosqlite
from pydantic_ai.messages import ModelMessagesTypeAdapter

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS history (
    thread_id TEXT PRIMARY KEY,
    messages  TEXT NOT NULL
)
"""


async def load_history(db_path: str, thread_id: str) -> list:
    """Returns the stored message list for *thread_id*, or ``[]`` if none."""
    try:
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT messages FROM history WHERE thread_id = ?", (thread_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return ModelMessagesTypeAdapter.validate_json(row[0])
    except Exception as e:
        logger.warning("Could not load history for thread %s: %s", thread_id, e)
    return []


async def save_history(db_path: str, thread_id: str, messages: list) -> None:
    """Persists *messages* for *thread_id*."""
    try:
        data = ModelMessagesTypeAdapter.dump_json(messages).decode()
        async with aiosqlite.connect(db_path) as db:
            await db.execute(_CREATE_TABLE)
            await db.execute(
                "INSERT OR REPLACE INTO history (thread_id, messages) VALUES (?, ?)",
                (thread_id, data),
            )
            await db.commit()
    except Exception as e:
        logger.warning("Could not save history for thread %s: %s", thread_id, e)
