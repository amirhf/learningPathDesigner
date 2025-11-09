"""
S3 uploader module for content snippets
Uploads extracted content to S3 for quiz generation
"""
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Uploader:
    """Upload content snippets to S3"""
    
    def __init__(self):
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'learnpath-snippets')
        
        self.s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3 client"""
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            logger.warning("AWS credentials not found. S3 upload will be disabled.")
            return
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
    
    def ensure_bucket_exists(self) -> bool:
        """Ensure S3 bucket exists, create if it doesn't"""
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, try to create it
                try:
                    logger.info(f"Creating bucket: {self.bucket_name}")
                    if self.aws_region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.aws_region}
                        )
                    logger.info(f"Bucket {self.bucket_name} created successfully")
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    return False
            else:
                logger.error(f"Error checking bucket: {e}")
                return False
    
    def get_s3_key_for_resource(self, resource_id: str) -> str:
        """Generate S3 key for resource snippet"""
        return f"snippets/{resource_id}.txt"
    
    def upload_snippet(self, resource_id: str, content: str) -> Optional[str]:
        """
        Upload content snippet to S3
        
        Args:
            resource_id: UUID of the resource
            content: Text content to upload
        
        Returns:
            S3 key if successful, None if failed
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return None
        
        s3_key = self.get_s3_key_for_resource(resource_id)
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/plain',
                Metadata={
                    'resource_id': resource_id,
                    'content_length': str(len(content))
                }
            )
            logger.info(f"Uploaded snippet to S3: {s3_key} ({len(content)} bytes)")
            return s3_key
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
            return None
    
    def verify_upload(self, s3_key: str) -> bool:
        """Verify that content was uploaded successfully"""
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
    
    def get_snippet(self, s3_key: str) -> Optional[str]:
        """Retrieve snippet content from S3 (for testing)"""
        if not self.s3_client:
            return None
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            content = response['Body'].read().decode('utf-8')
            return content
        except ClientError as e:
            logger.error(f"Failed to retrieve from S3: {e}")
            return None
    
    def delete_snippet(self, s3_key: str) -> bool:
        """Delete snippet from S3"""
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted snippet from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete from S3: {e}")
            return False
    
    def list_snippets(self, prefix: str = "snippets/", max_keys: int = 100):
        """List snippets in S3 bucket"""
        if not self.s3_client:
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError as e:
            logger.error(f"Failed to list S3 objects: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check S3 connection"""
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            return False


# Singleton instance
_uploader = None


def get_uploader() -> S3Uploader:
    """Get singleton S3Uploader instance"""
    global _uploader
    if _uploader is None:
        _uploader = S3Uploader()
    return _uploader


def upload_content(resource_id: str, content: str) -> Optional[str]:
    """
    Convenience function to upload content
    
    Args:
        resource_id: UUID of the resource
        content: Text content to upload
    
    Returns:
        S3 key if successful, None if failed
    """
    uploader = get_uploader()
    return uploader.upload_snippet(resource_id, content)


if __name__ == "__main__":
    # Test S3 connection
    print("Testing S3 connection...\n")
    
    uploader = S3Uploader()
    
    if uploader.s3_client:
        print(f"[OK] S3 client initialized")
        print(f"  Bucket: {uploader.bucket_name}")
        print(f"  Region: {uploader.aws_region}")
        
        # Check bucket
        if uploader.ensure_bucket_exists():
            print(f"[OK] Bucket is accessible")
            
            # Test upload
            test_content = "This is a test snippet for content extraction."
            test_id = "test-resource-id"
            
            print(f"\nTesting upload...")
            s3_key = uploader.upload_snippet(test_id, test_content)
            
            if s3_key:
                print(f"[OK] Upload successful: {s3_key}")
                
                # Verify
                if uploader.verify_upload(s3_key):
                    print(f"[OK] Upload verified")
                    
                    # Retrieve
                    retrieved = uploader.get_snippet(s3_key)
                    if retrieved == test_content:
                        print(f"[OK] Content matches")
                    
                    # Cleanup
                    uploader.delete_snippet(s3_key)
                    print(f"[OK] Test cleanup complete")
        else:
            print(f"[FAIL] Bucket not accessible")
    else:
        print("[FAIL] S3 client not initialized")
        print("  Check AWS credentials in .env.local or .env")
