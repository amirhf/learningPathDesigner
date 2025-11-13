# Phase 4: Content Extraction Pipeline - Implementation Plan

**Date:** 2025-11-09 01:25  
**Goal:** Extract content from learning resources and store in S3 for quiz generation

---

## 📋 Current State Analysis

### What We Have
- ✅ 49 resources in `resource` table
- ✅ Resources have: `id`, `title`, `url`, `provider`, `media_type`
- ✅ `s3_cache_key` field exists but is NULL for all resources
- ✅ Quiz service ready to use S3 content
- ✅ S3 client already implemented in quiz service

### What We Need
- ❌ Actual content extracted from URLs
- ❌ Content stored in S3
- ❌ `s3_cache_key` populated in database

---

## 🎯 Implementation Strategy

### Approach: Incremental Content Extraction

**Why this approach:**
1. Not all resources may be scrapable (videos, paywalled content)
2. Some resources may require different extraction methods
3. We want to handle failures gracefully
4. We can test with a subset first

**Strategy:**
- Extract content based on `media_type`
- Store raw text snippets (first 5000 chars)
- Update database with S3 keys
- Log failures for manual review

---

## 📊 Resource Analysis

### By Media Type (from your data):

```sql
SELECT media_type, COUNT(*) 
FROM resource 
GROUP BY media_type;
```

**Expected types:**
- `reading` - Articles, blog posts, documentation (easiest to extract)
- `video` - YouTube, Vimeo (use transcripts if available)
- `course` - Course platforms (may need API access)
- `interactive` - Interactive tutorials (complex)
- `audio` - Podcasts (transcripts if available)

**Phase 4 Focus:** Start with `reading` type resources

---

## 🏗️ Architecture Design

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Content Extraction Pipeline                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  1. Fetch URL    │→ │  2. Extract Text │→ │  3. Upload to S3 │
│  (requests)      │  │  (BeautifulSoup) │  │  (boto3)         │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                                                      │
                                                      ▼
                                          ┌──────────────────────┐
                                          │  4. Update Database  │
                                          │  (s3_cache_key)      │
                                          └──────────────────────┘
```

### Data Flow

```
resource table → extract_content.py → S3 bucket → resource.s3_cache_key
                                           ↓
                                    quiz service reads
```

---

## 🛠️ Implementation Plan

### Step 1: Environment Setup (5 minutes)

**1.1. Check S3 Configuration**
- Verify S3 bucket exists or create one
- Check AWS credentials
- Test S3 connectivity

**1.2. Install Dependencies**
```bash
pip install beautifulsoup4 requests boto3 lxml
```

**1.3. Update `.env` with S3 settings**
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=learnpath-content
```

---

### Step 2: Create Content Extractor (30 minutes)

**File:** `ingestion/extract_content.py`

**Features:**
- ✅ Fetch content from URLs
- ✅ Extract text using BeautifulSoup
- ✅ Handle different content types
- ✅ Retry logic for failed requests
- ✅ Rate limiting to avoid blocking
- ✅ Progress tracking

**Key Functions:**
```python
def fetch_url(url: str) -> Optional[str]
    """Fetch HTML content from URL with retries"""

def extract_text_content(html: str, url: str) -> Optional[str]
    """Extract main text content from HTML"""

def clean_text(text: str) -> str
    """Clean and normalize extracted text"""

def create_snippet(text: str, max_chars: int = 5000) -> str
    """Create snippet from full text"""
```

---

### Step 3: Create S3 Uploader (15 minutes)

**File:** `ingestion/s3_uploader.py`

**Features:**
- ✅ Upload text to S3
- ✅ Generate consistent S3 keys
- ✅ Handle upload errors
- ✅ Verify uploads

**Key Functions:**
```python
def upload_snippet(resource_id: str, content: str) -> Optional[str]
    """Upload content snippet to S3, return S3 key"""

def verify_upload(s3_key: str) -> bool
    """Verify content was uploaded successfully"""

def get_s3_key_for_resource(resource_id: str) -> str
    """Generate S3 key: snippets/{resource_id}.txt"""
```

---

### Step 4: Create Database Updater (10 minutes)

**File:** `ingestion/update_s3_keys.py`

**Features:**
- ✅ Update `s3_cache_key` in database
- ✅ Track update status
- ✅ Rollback on errors

**Key Functions:**
```python
def update_resource_s3_key(resource_id: str, s3_key: str) -> bool
    """Update resource with S3 key"""

def get_resources_without_content() -> List[Dict]
    """Get resources where s3_cache_key IS NULL"""
```

---

### Step 5: Create Main Pipeline Script (20 minutes)

**File:** `ingestion/run_content_extraction.py`

**Features:**
- ✅ Orchestrate entire pipeline
- ✅ Filter by media type
- ✅ Batch processing
- ✅ Error handling and logging
- ✅ Progress reporting
- ✅ Summary statistics

**Workflow:**
```python
1. Get resources without content (WHERE s3_cache_key IS NULL)
2. Filter by media_type = 'reading' (for Phase 4)
3. For each resource:
   a. Fetch URL content
   b. Extract text
   c. Create snippet
   d. Upload to S3
   e. Update database
   f. Log result
4. Generate summary report
```

---

### Step 6: Testing & Validation (15 minutes)

**6.1. Test with Single Resource**
```bash
python -m ingestion.run_content_extraction --limit 1 --dry-run
```

**6.2. Test with Small Batch**
```bash
python -m ingestion.run_content_extraction --limit 5
```

**6.3. Verify Results**
```sql
SELECT id, title, s3_cache_key 
FROM resource 
WHERE s3_cache_key IS NOT NULL 
LIMIT 5;
```

**6.4. Test Quiz Generation**
```bash
# Use extracted resource IDs to generate quiz
curl -X POST http://localhost:8080/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"resource_ids": ["<id>"], "num_questions": 3}'
```

---

### Step 7: Full Extraction (Variable)

**7.1. Run for All Reading Resources**
```bash
python -m ingestion.run_content_extraction --media-type reading
```

**7.2. Monitor Progress**
- Watch logs for errors
- Track success rate
- Identify problematic URLs

**7.3. Handle Failures**
- Review failed URLs
- Manually add content for critical resources
- Update extraction logic for common patterns

---

## 🔧 Technical Specifications

### Content Extraction Rules

**For `reading` type:**
```python
# Priority order for content extraction:
1. <article> tag
2. <main> tag
3. <div class="content"> or similar
4. <body> tag (fallback)

# Remove:
- <script>, <style>, <nav>, <header>, <footer>
- Ads, popups, cookie notices
- Social media widgets
```

**Text Cleaning:**
```python
- Strip extra whitespace
- Remove special characters
- Normalize line breaks
- Limit to 5000 characters
- Preserve paragraph structure
```

### S3 Structure

```
s3://learnpath-content/
├── snippets/
│   ├── {resource_id_1}.txt
│   ├── {resource_id_2}.txt
│   └── ...
└── metadata/
    └── extraction_log.json
```

### Database Schema

```sql
-- Already exists in resource table:
s3_cache_key TEXT  -- Format: "snippets/{resource_id}.txt"
```

---

## 📝 Error Handling Strategy

### Common Issues & Solutions

**1. URL Not Accessible (404, 403, etc.)**
- Log error
- Mark resource as "unavailable"
- Skip and continue

**2. Content Behind Paywall**
- Log as "paywalled"
- Skip and continue
- Consider manual content addition

**3. JavaScript-Required Content**
- Log as "requires-js"
- Consider using Selenium for important resources
- Skip for now

**4. Rate Limiting / Blocking**
- Implement exponential backoff
- Add delays between requests (1-2 seconds)
- Rotate user agents

**5. S3 Upload Failures**
- Retry up to 3 times
- Log error
- Don't update database if upload fails

---

## 🎯 Success Criteria

### Phase 4 Complete When:

- [ ] Content extraction script created and tested
- [ ] S3 uploader working
- [ ] Database updater working
- [ ] At least 20 resources have content extracted
- [ ] Quiz generation works with extracted content
- [ ] End-to-end test passes:
  - Generate quiz from resources with content
  - Quiz has meaningful questions
  - Questions reference actual content
  - Citations are accurate

---

## 📊 Expected Outcomes

### Metrics to Track

```
Total resources:           49
Reading type:              ~30-40 (estimated)
Successfully extracted:    Target: 80%+
Failed (unavailable):      Expected: 10-15%
Failed (paywall):          Expected: 5-10%
```

### Quality Checks

```python
# For each extracted content:
assert len(content) > 100  # Minimum content length
assert content.strip() != ""  # Not empty
assert s3_key in S3  # Actually uploaded
assert resource.s3_cache_key == s3_key  # DB updated
```

---

## 🚀 Execution Timeline

**Total Estimated Time: 2-3 hours**

| Step | Task | Time | Status |
|------|------|------|--------|
| 1 | Environment setup | 5 min | ⏳ Pending |
| 2 | Create content extractor | 30 min | ⏳ Pending |
| 3 | Create S3 uploader | 15 min | ⏳ Pending |
| 4 | Create DB updater | 10 min | ⏳ Pending |
| 5 | Create main pipeline | 20 min | ⏳ Pending |
| 6 | Testing & validation | 15 min | ⏳ Pending |
| 7 | Full extraction | 30-60 min | ⏳ Pending |
| 8 | End-to-end quiz test | 10 min | ⏳ Pending |

---

## 🔄 Alternative Approaches (If Issues Arise)

### Plan B: Mock Content for Testing

If extraction proves difficult:
```python
# Generate mock educational content
def generate_mock_content(resource: Dict) -> str:
    return f"""
    {resource['title']}
    
    This is a comprehensive guide about {resource['title']}.
    
    Key concepts include:
    - Understanding the fundamentals
    - Practical applications
    - Best practices and patterns
    
    [Mock content for testing purposes]
    """
```

### Plan C: Manual Content Addition

For critical resources:
```sql
UPDATE resource 
SET s3_cache_key = 'snippets/{id}.txt'
WHERE id = '<important-resource-id>';

-- Then manually upload content to S3
```

---

## 📚 Dependencies

### Python Packages
```txt
beautifulsoup4>=4.12.0
requests>=2.31.0
boto3>=1.28.0
lxml>=4.9.0
python-dotenv>=1.0.0
```

### AWS Resources
- S3 bucket (new or existing)
- IAM credentials with S3 write permissions

### Environment Variables
```env
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
S3_BUCKET_NAME
DATABASE_URL
```

---

## 🎓 Learning Outcomes

After Phase 4, you'll have:
1. ✅ Fully functional content extraction pipeline
2. ✅ Reusable S3 upload utilities
3. ✅ Content-based quiz generation
4. ✅ Foundation for future content updates
5. ✅ Understanding of web scraping best practices

---

## 🔜 Next Steps After Phase 4

1. **Expand to Other Media Types**
   - Video transcripts (YouTube API)
   - Course content (platform APIs)
   
2. **Content Refresh Pipeline**
   - Periodic re-extraction for updated content
   - Version control for content changes

3. **Content Quality Improvements**
   - Better text extraction algorithms
   - Content summarization
   - Keyword extraction

4. **Advanced Features**
   - Multi-language support
   - Content categorization
   - Automatic tagging

---

**Ready to implement? Let's start with Step 1! 🚀**
