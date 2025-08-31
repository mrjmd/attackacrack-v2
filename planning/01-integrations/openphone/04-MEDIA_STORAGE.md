# Media Storage Architecture - Start Simple, Scale Later

## Key Decision: Local Storage for MVP

### Why Local Storage Makes Sense for MVP
- **v1 never needed S3** - This wasn't a problem before
- **Avoid over-engineering** - Start simple, migrate later if needed
- **Faster development** - No AWS setup, credentials, etc.
- **Lower cost** - No S3 charges initially
- **Easy migration path** - Can move to S3 later transparently

## MVP Implementation: Local File Storage

### Directory Structure
```
/media/
  /2025/
    /01/
      /15/
        /617-555-0123/
          /messages/
            /1642282800_photo.jpg
            /1642282801_photo_thumb.jpg
          /voicemails/
            /1642282900_voicemail.mp3
```

### Database Schema
```sql
CREATE TABLE media_attachments (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    message_id UUID REFERENCES messages(id),
    
    -- Storage
    file_path VARCHAR(500) NOT NULL,  -- Local path
    file_name VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- Source
    openphone_url TEXT,  -- Original URL from OpenPhone
    downloaded_at TIMESTAMP,
    
    -- Metadata
    media_type VARCHAR(20),  -- 'photo', 'video', 'audio'
    thumbnail_path VARCHAR(500),  -- For images
    duration_seconds INTEGER,  -- For audio/video
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_conversation (conversation_id),
    INDEX idx_message (message_id)
);
```

### Download Strategy
```python
class MediaDownloader:
    """
    Simple local storage for MVP
    """
    def download_from_webhook(self, webhook_data):
        # 1. Extract media URLs from webhook
        media_urls = webhook_data.get('media', [])
        
        for url in media_urls:
            # 2. Download immediately (critical!)
            response = requests.get(url, timeout=30)
            
            # 3. Save locally
            file_path = self.generate_local_path(
                phone=webhook_data['from'],
                timestamp=webhook_data['timestamp']
            )
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # 4. Generate thumbnail for images
            if self.is_image(file_path):
                self.create_thumbnail(file_path)
            
            # 5. Save to database
            self.save_media_record(file_path, webhook_data)
```

### Serving Media
```python
# FastAPI endpoint for media access
@app.get("/media/{media_id}")
async def get_media(media_id: UUID):
    media = db.get_media(media_id)
    return FileResponse(media.file_path)

@app.get("/media/{media_id}/thumbnail")
async def get_thumbnail(media_id: UUID):
    media = db.get_media(media_id)
    return FileResponse(media.thumbnail_path)
```

## Future Migration to S3 (When Needed)

### When to Migrate
- **Storage exceeds 100GB** on server
- **Need CDN** for performance
- **Multiple servers** require shared storage
- **Backup becomes complex** with local files

### Migration Path
```python
class MediaStorage:
    """Abstract storage that can switch backends"""
    
    def __init__(self, backend='local'):
        if backend == 'local':
            self.storage = LocalStorage()
        elif backend == 's3':
            self.storage = S3Storage()
    
    def store(self, file_data, path):
        return self.storage.store(file_data, path)
    
    def retrieve(self, path):
        return self.storage.retrieve(path)
```

## Critical Requirements

### For Foundation Crack Photos
1. **Never lose a photo** - Business critical
2. **Fast access** - View immediately in conversation
3. **Link to everything** - Quotes, appointments, invoices
4. **Future AI analysis** - Keep originals at full resolution

### Backup Strategy for MVP
- Daily backup of /media directory
- Database backup includes media metadata
- Consider rsync to backup server

## Implementation Checklist

### Week 1: Basic Storage
- [ ] Create media directory structure
- [ ] Implement download from webhook
- [ ] Save media records to database
- [ ] Create serving endpoints

### Week 2: Enhancements
- [ ] Thumbnail generation for images
- [ ] Audio player for voicemails
- [ ] Link media to conversations
- [ ] Backup script

### Future: S3 Migration
- [ ] Abstract storage interface
- [ ] Implement S3 backend
- [ ] Migration script
- [ ] CDN setup

---

*Start simple with local storage. Media is critical but doesn't need over-engineering from day one.*