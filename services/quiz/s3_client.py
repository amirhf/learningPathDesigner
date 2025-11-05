"""
S3 client for retrieving resource snippets
"""
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from config import get_settings

logger = logging.getLogger(__name__)


class S3Client:
    """Client for S3 operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.s3 = None
        if self.settings.aws_access_key_id and self.settings.aws_secret_access_key:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region
            )
    
    def get_snippet(self, s3_key: str) -> Optional[str]:
        """Retrieve snippet content from S3"""
        if not self.s3:
            logger.warning("S3 client not configured")
            return None
        
        try:
            response = self.s3.get_object(
                Bucket=self.settings.s3_bucket_name,
                Key=s3_key
            )
            content = response['Body'].read().decode('utf-8')
            return content
        except ClientError as e:
            logger.error(f"Error retrieving snippet from S3: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check S3 connection"""
        if not self.s3:
            return False
        
        try:
            self.s3.head_bucket(Bucket=self.settings.s3_bucket_name)
            return True
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            return False


_s3_client = None


def get_s3_client() -> S3Client:
    """Get singleton S3 client instance"""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client
