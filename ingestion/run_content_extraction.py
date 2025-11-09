"""
Main content extraction pipeline
Orchestrates the entire process of extracting content from resources
"""
import logging
import argparse
import time
from typing import Dict, List, Any
from datetime import datetime

from ingestion.extract_content import ContentExtractor
from ingestion.s3_uploader import S3Uploader
from ingestion.update_s3_keys import DatabaseUpdater

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentExtractionPipeline:
    """Main pipeline for content extraction"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.extractor = ContentExtractor()
        self.uploader = S3Uploader()
        self.db = DatabaseUpdater()
        
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def process_resource(self, resource: Dict[str, Any]) -> bool:
        """
        Process a single resource
        
        Returns:
            True if successful, False otherwise
        """
        resource_id = str(resource['id'])
        title = resource['title']
        url = resource['url']
        
        logger.info(f"Processing: {title[:50]}...")
        logger.info(f"  URL: {url}")
        
        try:
            # Step 1: Extract content
            result = self.extractor.extract_from_url(url, max_chars=5000)
            
            if not result:
                logger.warning(f"  ✗ Failed to extract content")
                self.stats['failed'] += 1
                self.stats['errors'].append({
                    'resource_id': resource_id,
                    'title': title,
                    'url': url,
                    'error': 'Content extraction failed'
                })
                return False
            
            content = result['content']
            logger.info(f"  ✓ Extracted {result['snippet_length']} chars (from {result['full_length']} total)")
            
            if len(content) < 100:
                logger.warning(f"  ⚠ Content too short ({len(content)} chars), skipping")
                self.stats['skipped'] += 1
                return False
            
            # Step 2: Upload to S3 (if not dry run)
            if self.dry_run:
                logger.info(f"  [DRY RUN] Would upload to S3")
                s3_key = f"snippets/{resource_id}.txt"
            else:
                s3_key = self.uploader.upload_snippet(resource_id, content)
                
                if not s3_key:
                    logger.error(f"  ✗ Failed to upload to S3")
                    self.stats['failed'] += 1
                    self.stats['errors'].append({
                        'resource_id': resource_id,
                        'title': title,
                        'url': url,
                        'error': 'S3 upload failed'
                    })
                    return False
                
                logger.info(f"  ✓ Uploaded to S3: {s3_key}")
            
            # Step 3: Update database (if not dry run)
            if self.dry_run:
                logger.info(f"  [DRY RUN] Would update database with S3 key")
            else:
                success = self.db.update_resource_s3_key(resource_id, s3_key)
                
                if not success:
                    logger.error(f"  ✗ Failed to update database")
                    self.stats['failed'] += 1
                    return False
                
                logger.info(f"  ✓ Updated database")
            
            self.stats['success'] += 1
            logger.info(f"  ✓ Complete!")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Error processing resource: {e}")
            self.stats['failed'] += 1
            self.stats['errors'].append({
                'resource_id': resource_id,
                'title': title,
                'url': url,
                'error': str(e)
            })
            return False
    
    def run(
        self,
        media_type: str = 'reading',
        limit: int = None,
        delay: float = 1.0
    ):
        """
        Run the extraction pipeline
        
        Args:
            media_type: Filter by media type (default: 'reading')
            limit: Maximum number of resources to process
            delay: Delay between requests in seconds
        """
        logger.info("=" * 60)
        logger.info("Content Extraction Pipeline")
        logger.info("=" * 60)
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        # Get resources
        logger.info(f"\nFetching resources (media_type={media_type}, limit={limit})...")
        resources = self.db.get_resources_without_content(
            media_type=media_type,
            limit=limit
        )
        
        if not resources:
            logger.info("No resources found to process")
            return
        
        self.stats['total'] = len(resources)
        logger.info(f"Found {len(resources)} resources to process\n")
        
        # Check S3 connection
        if not self.dry_run:
            if not self.uploader.s3_client:
                logger.error("S3 client not initialized. Aborting.")
                return
            
            if not self.uploader.ensure_bucket_exists():
                logger.error("S3 bucket not accessible. Aborting.")
                return
            
            logger.info(f"✓ S3 bucket ready: {self.uploader.bucket_name}\n")
        
        # Process each resource
        start_time = time.time()
        
        for i, resource in enumerate(resources, 1):
            logger.info(f"\n[{i}/{len(resources)}] " + "-" * 50)
            
            self.process_resource(resource)
            
            # Rate limiting
            if i < len(resources):
                time.sleep(delay)
        
        # Summary
        elapsed_time = time.time() - start_time
        self.print_summary(elapsed_time)
    
    def print_summary(self, elapsed_time: float):
        """Print execution summary"""
        logger.info("\n" + "=" * 60)
        logger.info("EXTRACTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total processed:    {self.stats['total']}")
        logger.info(f"Successful:         {self.stats['success']} ✓")
        logger.info(f"Failed:             {self.stats['failed']} ✗")
        logger.info(f"Skipped:            {self.stats['skipped']} ⚠")
        logger.info(f"Success rate:       {(self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0:.1f}%")
        logger.info(f"Elapsed time:       {elapsed_time:.1f}s")
        logger.info(f"Avg time/resource:  {(elapsed_time / self.stats['total']) if self.stats['total'] > 0 else 0:.1f}s")
        
        if self.stats['errors']:
            logger.info(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:  # Show first 10
                logger.info(f"  - {error['title'][:40]}...")
                logger.info(f"    Error: {error['error']}")
        
        # Get updated stats from database
        if not self.dry_run:
            logger.info("\n" + "-" * 60)
            db_stats = self.db.get_extraction_stats()
            logger.info(f"Database Statistics:")
            logger.info(f"  Total resources:    {db_stats.get('total_resources', 0)}")
            logger.info(f"  With content:       {db_stats.get('with_content', 0)}")
            logger.info(f"  Without content:    {db_stats.get('without_content', 0)}")
            logger.info(f"  Completion:         {db_stats.get('percentage_complete', 0)}%")
        
        logger.info("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Extract content from learning resources and upload to S3'
    )
    
    parser.add_argument(
        '--media-type',
        type=str,
        default='reading',
        help='Filter by media type (default: reading)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of resources to process'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making changes (test mode)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run pipeline
    pipeline = ContentExtractionPipeline(dry_run=args.dry_run)
    
    try:
        pipeline.run(
            media_type=args.media_type,
            limit=args.limit,
            delay=args.delay
        )
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        pipeline.print_summary(0)
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}", exc_info=True)
    finally:
        pipeline.db.close()


if __name__ == "__main__":
    main()
