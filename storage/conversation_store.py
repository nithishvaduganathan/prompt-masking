"""
Conversation Store — SQLite-based persistence for conversations & messages.
"""

import sqlite3
import uuid
import threading
from datetime import datetime, timezone

from config import Config


class ConversationStore:
    """Thread-safe SQLite store for chat conversations."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self._local = threading.local()
        self._init_db()

    # ------------------------------------------------------------------
    # Connection management (one connection per thread)
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id              TEXT PRIMARY KEY,
                title           TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id              TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role            TEXT NOT NULL,
                content         TEXT NOT NULL,
                masked_content  TEXT,
                masking_map     TEXT,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_msg_conv
                ON messages(conversation_id, created_at);
        """)
        conn.commit()

    # ------------------------------------------------------------------
    # Conversations CRUD
    # ------------------------------------------------------------------

    def create_conversation(self, title: str = "New Chat") -> str:
        conv_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, title, now, now),
        )
        conn.commit()
        return conv_id

    def list_conversations(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_conversation(self, conv_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
            (conv_id,),
        ).fetchone()
        return dict(row) if row else None

    def delete_conversation(self, conv_id: str) -> bool:
        conn = self._get_conn()
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
        return cur.rowcount > 0

    def update_conversation_title(self, conv_id: str, title: str):
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, conv_id),
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Messages CRUD
    # ------------------------------------------------------------------

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        masked_content: str = "",
        masking_map: str = "",
    ) -> str:
        msg_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, masked_content, masking_map, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, masked_content, masking_map, now),
        )
        # Touch the conversation timestamp
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()
        return msg_id

    def get_messages(self, conversation_id: str) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, role, content, masked_content, masking_map, created_at "
            "FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# Module-level singleton
conversation_store = ConversationStore()
