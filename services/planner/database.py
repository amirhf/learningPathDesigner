"""
Database operations for Planner service
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
    
    def get_skill_names(self, skill_ids: List[str]) -> List[str]:
        """Get skill names from IDs"""
        if not skill_ids:
            return []
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT name FROM skill WHERE id::text = ANY(%s)",
                    (skill_ids,)
                )
                results = cur.fetchall()
                return [row['name'] for row in results]
        except Exception as e:
            logger.error(f"Error fetching skill names: {e}")
            return []
    
    def save_plan(
        self,
        user_id: str,
        goal: str,
        plan_data: Dict[str, Any],
        total_hours: float,
        estimated_weeks: int
    ) -> str:
        """Save a learning plan to database"""
        plan_id = str(uuid.uuid4())
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO learning_plans 
                    (plan_id, user_id, goal, plan_data, total_hours, estimated_weeks, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    plan_id,
                    user_id,
                    goal,
                    psycopg2.extras.Json(plan_data),
                    total_hours,
                    estimated_weeks,
                    datetime.utcnow()
                ))
                self.conn.commit()
                logger.info(f"Saved plan {plan_id}")
                return plan_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error saving plan: {e}")
            raise
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a learning plan"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM learning_plans WHERE plan_id = %s",
                    (plan_id,)
                )
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error fetching plan: {e}")
            # Rollback the transaction to recover from error
            self.conn.rollback()
            return None
    
    def get_plans_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all plans for a user"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT plan_id, user_id, goal, total_hours, estimated_weeks, created_at, updated_at
                    FROM learning_plans 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error fetching plans for user {user_id}: {e}")
            self.conn.rollback()
            return []
    
    def update_plan(
        self,
        plan_id: str,
        plan_data: Dict[str, Any],
        total_hours: float,
        estimated_weeks: int
    ):
        """Update an existing plan"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE learning_plans 
                    SET plan_data = %s, total_hours = %s, estimated_weeks = %s, updated_at = %s
                    WHERE plan_id = %s
                """, (
                    psycopg2.extras.Json(plan_data),
                    total_hours,
                    estimated_weeks,
                    datetime.utcnow(),
                    plan_id
                ))
                self.conn.commit()
                logger.info(f"Updated plan {plan_id}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating plan: {e}")
            raise


_db_client = None


def get_db_client() -> DatabaseClient:
    """Get singleton database client instance"""
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
        _db_client.connect()
    return _db_client
