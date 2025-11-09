"""
Content extraction module for learning resources
Extracts text content from web pages for quiz generation
"""
import logging
import requests
import time
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extract text content from web URLs"""
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL with retries"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching URL: {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching {url}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error fetching {url}: {e}")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching {url}: {e}")
                return None
        
        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None
    
    def extract_text_content(self, html: str, url: str) -> Optional[str]:
        """Extract main text content from HTML"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                                'aside', 'iframe', 'noscript']):
                element.decompose()
            
            # Try to find main content in priority order
            content = None
            
            # 1. Try <article> tag
            article = soup.find('article')
            if article:
                content = article.get_text()
                logger.debug("Extracted content from <article> tag")
            
            # 2. Try <main> tag
            if not content:
                main = soup.find('main')
                if main:
                    content = main.get_text()
                    logger.debug("Extracted content from <main> tag")
            
            # 3. Try common content divs
            if not content:
                for class_name in ['content', 'post-content', 'entry-content', 
                                  'article-content', 'main-content', 'post-body']:
                    div = soup.find('div', class_=class_name)
                    if div:
                        content = div.get_text()
                        logger.debug(f"Extracted content from div.{class_name}")
                        break
            
            # 4. Fallback to body
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text()
                    logger.debug("Extracted content from <body> tag (fallback)")
            
            if content:
                return self.clean_text(content)
            
            logger.warning(f"No content found for {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting text from {url}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Split into lines and strip whitespace
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        # Join with single newlines
        cleaned = '\n'.join(lines)
        
        # Remove excessive whitespace
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def create_snippet(self, text: str, max_chars: int = 5000) -> str:
        """Create snippet from full text"""
        if len(text) <= max_chars:
            return text
        
        # Try to cut at a sentence boundary
        snippet = text[:max_chars]
        
        # Find last sentence ending
        for delimiter in ['. ', '.\n', '! ', '?\n']:
            last_sentence = snippet.rfind(delimiter)
            if last_sentence > max_chars * 0.8:  # At least 80% of target length
                return snippet[:last_sentence + 1].strip()
        
        # Fallback: cut at word boundary
        last_space = snippet.rfind(' ')
        if last_space > 0:
            return snippet[:last_space].strip() + '...'
        
        return snippet + '...'
    
    def extract_from_url(self, url: str, max_chars: int = 5000) -> Optional[Dict[str, Any]]:
        """
        Extract content from URL and return snippet
        
        Returns:
            Dict with 'content', 'length', 'snippet_length' or None if failed
        """
        # Fetch HTML
        html = self.fetch_url(url)
        if not html:
            return None
        
        # Extract text
        text = self.extract_text_content(html, url)
        if not text:
            return None
        
        # Create snippet
        snippet = self.create_snippet(text, max_chars)
        
        return {
            'content': snippet,
            'full_length': len(text),
            'snippet_length': len(snippet),
            'url': url
        }
    
    def is_accessible(self, url: str) -> bool:
        """Quick check if URL is accessible"""
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False


def extract_content(url: str, max_chars: int = 5000) -> Optional[Dict[str, Any]]:
    """
    Convenience function to extract content from a URL
    
    Args:
        url: URL to extract content from
        max_chars: Maximum characters for snippet
    
    Returns:
        Dict with extracted content or None if failed
    """
    extractor = ContentExtractor()
    return extractor.extract_from_url(url, max_chars)


if __name__ == "__main__":
    # Test with a sample URL
    import sys
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"Testing content extraction from: {test_url}\n")
        
        result = extract_content(test_url)
        
        if result:
            print(f"✓ Success!")
            print(f"  Full length: {result['full_length']} chars")
            print(f"  Snippet length: {result['snippet_length']} chars")
            print(f"\nSnippet preview (first 500 chars):")
            print("-" * 50)
            print(result['content'][:500])
            print("-" * 50)
        else:
            print("✗ Failed to extract content")
    else:
        print("Usage: python extract_content.py <url>")
