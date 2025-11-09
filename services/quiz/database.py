"""
Database operations for Quiz service
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from config import get_settings
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Client for database operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.conn = None
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(
                self.settings.database_url,
                cursor_factory=RealDictCursor
            )
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check database connection"""
        try:
            if not self.conn or self.conn.closed:
                self.connect()
            
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_resource_info(self, resource_ids: List[str]) -> List[Dict[str, Any]]:
        """Get resource information from database"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id::text as resource_id, title, url, s3_cache_key as snippet_s3_key
                    FROM resource
                    WHERE id::text = ANY(%s)
                """, (resource_ids,))
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching resources: {e}")
            return []
    
    def save_quiz(
        self,
        quiz_id: str,
        resource_ids: List[str],
        questions: List[Dict[str, Any]]
    ):
        """Save quiz to database"""
        try:
            with self.conn.cursor() as cur:
                # Store in original quiz table with items JSONB field
                quiz_data = {
                    'resource_ids': resource_ids,
                    'questions': questions
                }
                cur.execute("""
                    INSERT INTO quiz (id, lesson_id, items, created_at)
                    VALUES (%s, NULL, %s, %s)
                """, (
                    quiz_id,
                    psycopg2.extras.Json(quiz_data),
                    datetime.utcnow()
                ))
                self.conn.commit()
                logger.info(f"Saved quiz {quiz_id}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error saving quiz: {e}")
            raise
    
    def get_quiz(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a quiz"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT id, items FROM quiz WHERE id = %s",
                    (quiz_id,)
                )
                result = cur.fetchone()
                if result:
                    # Extract questions from items JSONB
                    return {
                        'quiz_id': str(result['id']),
                        'questions': result['items'].get('questions', [])
                    }
                return None
        except Exception as e:
            logger.error(f"Error fetching quiz: {e}")
            return None
    
    def save_quiz_attempt(
        self,
        quiz_id: str,
        user_id: str,
        score: float,
        answers: List[Dict[str, Any]]
    ):
        """Save quiz attempt results"""
        try:
            with self.conn.cursor() as cur:
                # Store in original quiz_attempt table
                cur.execute("""
                    INSERT INTO quiz_attempt 
                    (id, quiz_id, user_id, score, answers, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()),
                    quiz_id,
                    user_id,
                    score,
                    psycopg2.extras.Json(answers),
                    datetime.utcnow()
                ))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error saving quiz attempt: {e}")


_db_client = None


def get_db_client() -> DatabaseClient:
    """Get singleton database client instance"""
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
        _db_client.connect()
    return _db_client
