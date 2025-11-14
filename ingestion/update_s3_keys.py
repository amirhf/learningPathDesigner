"""
Database updater for S3 keys
Updates resource table with S3 cache keys after content extraction
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseUpdater:
    """Update database with S3 keys"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment")
        
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor
            )
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def get_resources_without_content(
        self,
        media_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get resources where s3_cache_key IS NULL
        
        Args:
            media_type: Filter by media type (e.g., 'reading')
            limit: Maximum number of resources to return
        
        Returns:
            List of resource dictionaries
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                    SELECT id, title, url, media_type, provider
                    FROM resource
                    WHERE snippet_s3_key IS NULL
                """
                params = []
                
                if media_type:
                    query += " AND media_type = %s"
                    params.append(media_type)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cur.execute(query, params)
                results = cur.fetchall()
                
                resources = [dict(row) for row in results]
                logger.info(f"Found {len(resources)} resources without content")
                return resources
                
        except Exception as e:
            logger.error(f"Error fetching resources: {e}")
            return []
    
    def get_all_resources(
        self,
        media_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all resources (for stats/reporting)
        
        Args:
            media_type: Filter by media type
            limit: Maximum number of resources
        
        Returns:
            List of resource dictionaries
        """
        try:
            with self.conn.cursor() as cur:
                query = """
                    SELECT id, title, url, media_type, provider, s3_cache_key
                    FROM resource
                """
                params = []
                
                if media_type:
                    query += " WHERE media_type = %s"
                    params.append(media_type)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cur.execute(query, params)
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Error fetching resources: {e}")
            return []
    
    def update_resource_s3_key(self, resource_id: str, s3_key: str) -> bool:
        """
        Update resource with S3 key
        
        Args:
            resource_id: UUID of the resource
            s3_key: S3 key where content is stored
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE resource
                    SET snippet_s3_key = %s, updated_at = NOW()
                    WHERE id = %s
                """, (s3_key, resource_id))
                
                self.conn.commit()
                
                if cur.rowcount > 0:
                    logger.info(f"Updated resource {resource_id} with S3 key: {s3_key}")
                    return True
                else:
                    logger.warning(f"No resource found with id: {resource_id}")
                    return False
                    
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating resource {resource_id}: {e}")
            return False
    
    def batch_update_s3_keys(self, updates: List[Dict[str, str]]) -> int:
        """
        Batch update multiple resources
        
        Args:
            updates: List of dicts with 'resource_id' and 's3_key'
        
        Returns:
            Number of successful updates
        """
        success_count = 0
        
        try:
            with self.conn.cursor() as cur:
                for update in updates:
                    resource_id = update['resource_id']
                    s3_key = update['s3_key']
                    
                    cur.execute("""
                        UPDATE resource
                        SET snippet_s3_key = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (s3_key, resource_id))
                    
                    if cur.rowcount > 0:
                        success_count += 1
                
                self.conn.commit()
                logger.info(f"Batch updated {success_count}/{len(updates)} resources")
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error in batch update: {e}")
        
        return success_count
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about content extraction"""
        try:
            with self.conn.cursor() as cur:
                # Total resources
                cur.execute("SELECT COUNT(*) as total FROM resource")
                total = cur.fetchone()['total']
                
                # Resources with content
                cur.execute("SELECT COUNT(*) as with_content FROM resource WHERE s3_cache_key IS NOT NULL")
                with_content = cur.fetchone()['with_content']
                
                # By media type
                cur.execute("""
                    SELECT 
                        media_type,
                        COUNT(*) as total,
                        COUNT(s3_cache_key) as with_content
                    FROM resource
                    GROUP BY media_type
                    ORDER BY total DESC
                """)
                by_media_type = [dict(row) for row in cur.fetchall()]
                
                return {
                    'total_resources': total,
                    'with_content': with_content,
                    'without_content': total - with_content,
                    'percentage_complete': round((with_content / total * 100) if total > 0 else 0, 2),
                    'by_media_type': by_media_type
                }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def mark_resource_as_failed(self, resource_id: str, reason: str) -> bool:
        """
        Mark a resource as failed extraction (optional tracking)
        For now, we just log it. Could add a failed_extraction table later.
        """
        logger.warning(f"Resource {resource_id} failed extraction: {reason}")
        return True
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Singleton instance
_db_updater = None


def get_db_updater() -> DatabaseUpdater:
    """Get singleton DatabaseUpdater instance"""
    global _db_updater
    if _db_updater is None:
        _db_updater = DatabaseUpdater()
    return _db_updater


if __name__ == "__main__":
    # Test database connection and queries
    print("Testing database connection...\n")
    
    try:
        db = DatabaseUpdater()
        
        print("[OK] Database connected")
        
        # Get stats
        stats = db.get_extraction_stats()
        print(f"\nExtraction Statistics:")
        print(f"  Total resources: {stats.get('total_resources', 0)}")
        print(f"  With content: {stats.get('with_content', 0)}")
        print(f"  Without content: {stats.get('without_content', 0)}")
        print(f"  Completion: {stats.get('percentage_complete', 0)}%")
        
        print(f"\nBy Media Type:")
        for item in stats.get('by_media_type', []):
            media_type = item.get('media_type') or 'null'
            total = item.get('total', 0)
            with_content = item.get('with_content', 0)
            print(f"  {media_type}: {with_content}/{total}")
        
        # Get resources without content
        resources = db.get_resources_without_content(media_type='reading', limit=5)
        print(f"\nSample resources without content (reading type):")
        for r in resources:
            print(f"  - {r['title'][:50]}... ({r['url'][:50]}...)")
        
        db.close()
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
