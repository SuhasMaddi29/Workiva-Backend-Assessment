import aiosqlite
import os
from datetime import datetime
from typing import List, Optional
from models.schemas import ConversationRecord
import logging
from contextlib import asynccontextmanager
import asyncio

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for handling database operations for conversation logging."""
    
    def __init__(self):
        self.db_path = os.getenv("DB_PATH", "conversations.db")
        self.connection: Optional[aiosqlite.Connection] = None
        self._connection_lock = asyncio.Lock()
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager for database connections."""
        async with self._connection_lock:
            if not self.connection:
                await self.init_db()
            try:
                yield self.connection
            except Exception as e:
                logger.error(f"Database connection error: {str(e)}")
                if self.connection:
                    await self.connection.close()
                    self.connection = None
                raise
    
    async def init_db(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            await self.connection.execute("PRAGMA journal_mode=WAL")  # Enable Write-Ahead Logging
            await self.connection.execute("PRAGMA synchronous=NORMAL")  # Improve write performance
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    model TEXT NOT NULL DEFAULT 'gpt-3.5-turbo',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await self.connection.commit()
            logger.info(f"Database initialized successfully at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            if self.connection:
                await self.connection.close()
                self.connection = None
            raise RuntimeError(f"Database initialization failed: {str(e)}")
    
    async def save_conversation(self, prompt: str, response: str, model: str = "gpt-3.5-turbo") -> int:
        """
        Save a conversation to the database.
        
        Args:
            prompt: The user's prompt
            response: The AI's response
            model: The AI model used
            
        Returns:
            The ID of the saved conversation
        """
        async with self.get_connection() as conn:
            try:
                timestamp = datetime.now().isoformat()
                cursor = await conn.execute(
                    "INSERT INTO conversations (prompt, response, timestamp, model) VALUES (?, ?, ?, ?)",
                    (prompt, response, timestamp, model)
                )
                await conn.commit()
                conversation_id = cursor.lastrowid
                logger.info(f"Saved conversation with ID: {conversation_id}")
                return conversation_id
            except Exception as e:
                logger.error(f"Failed to save conversation: {str(e)}")
                raise RuntimeError(f"Failed to save conversation: {str(e)}")
    
    async def get_all_conversations(self) -> List[ConversationRecord]:
        """
        Retrieve all conversations from the database.
        
        Returns:
            List of conversation records
        """
        async with self.get_connection() as conn:
            try:
                cursor = await conn.execute(
                    "SELECT id, prompt, response, timestamp, model FROM conversations ORDER BY timestamp DESC"
                )
                rows = await cursor.fetchall()
                
                conversations = []
                for row in rows:
                    conversations.append(ConversationRecord(
                        id=row[0],
                        prompt=row[1],
                        response=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        model=row[4]
                    ))
                
                logger.info(f"Retrieved {len(conversations)} conversations")
                return conversations
            except Exception as e:
                logger.error(f"Failed to retrieve conversations: {str(e)}")
                raise RuntimeError(f"Failed to retrieve conversations: {str(e)}")
    
    async def get_conversation_count(self) -> int:
        """
        Get the total number of conversations in the database.
        
        Returns:
            The total count of conversations
        """
        async with self.get_connection() as conn:
            try:
                cursor = await conn.execute("SELECT COUNT(*) FROM conversations")
                result = await cursor.fetchone()
                count = result[0] if result else 0
                logger.info(f"Total conversations count: {count}")
                return count
            except Exception as e:
                logger.error(f"Failed to get conversation count: {str(e)}")
                raise RuntimeError(f"Failed to get conversation count: {str(e)}")
    
    async def clear_all_conversations(self) -> int:
        """
        Delete all conversations from the database.
        
        Returns:
            The number of conversations deleted
        """
        async with self.get_connection() as conn:
            try:
                # Get count before deletion
                cursor = await conn.execute("SELECT COUNT(*) FROM conversations")
                result = await cursor.fetchone()
                count = result[0] if result else 0
                
                if count > 0:
                    # Begin transaction
                    await conn.execute("BEGIN TRANSACTION")
                    try:
                        # Delete all conversations
                        await conn.execute("DELETE FROM conversations")
                        # Reset the auto-increment counter
                        await conn.execute("DELETE FROM sqlite_sequence WHERE name='conversations'")
                        await conn.commit()
                        logger.info(f"Cleared {count} conversations from database")
                    except Exception as e:
                        await conn.rollback()
                        logger.error(f"Failed to clear conversations: {str(e)}")
                        raise RuntimeError(f"Failed to clear conversations: {str(e)}")
                else:
                    logger.info("No conversations to clear")
                
                return count
            except Exception as e:
                logger.error(f"Failed to clear conversations: {str(e)}")
                raise RuntimeError(f"Failed to clear conversations: {str(e)}")
    
    async def close(self):
        """Close the database connection."""
        async with self._connection_lock:
            if self.connection:
                await self.connection.close()
                self.connection = None
                logger.info("Database connection closed") 