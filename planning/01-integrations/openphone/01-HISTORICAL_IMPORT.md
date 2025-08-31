# OpenPhone Historical Import - Component Specification

## Overview
One-time mass import of ~7,000 conversations from OpenPhone, executed before production launch.

## Key Insights from v1 Success
- **v1 got this right** - Use Celery background workers
- **Same script as reconciliation** - Just different time ranges
  - Historical import: All time
  - Daily reconciliation: Last 24 hours
- **System can be read-only** during import
- **Webhooks off** during import to avoid conflicts

## Data Volume Reality Check
- **7,000 conversations** total
- **NOT 20 messages average** - Much lower
- **Many single messages** - Thousands are single outbound, no response
- **Estimated total records**: ~20,000-30,000 messages (not 140,000)

## Import Strategy

### Pre-Import Checklist
1. Set system to read-only mode
2. Disable webhooks
3. Clear any partial data
4. Start import dashboard
5. Begin import process

### Import Flow
```python
class OpenPhoneHistoricalImport:
    """
    Based on v1's successful implementation
    Same as reconciliation script but with full timeline
    """
    def import_all_history(self):
        # 1. Get all conversations (paginated)
        conversations = self.fetch_all_conversations()
        
        # 2. Process in Celery tasks (parallel)
        for batch in chunk(conversations, 100):
            import_conversation_batch.delay(batch)
        
        # 3. For each conversation:
        #    - Import all messages
        #    - Import call records
        #    - Import voicemails
        #    - Queue media downloads
        #    - Import transcripts/summaries
        
        # 4. Update progress dashboard
        # 5. Verify completeness
```

### Import Dashboard Requirements
**Essential for development iteration** (local → staging → production)

```
┌─────────────────────────────────────────────┐
│ OpenPhone Historical Import                  │
├─────────────────────────────────────────────┤
│ Status: RUNNING                              │
│                                              │
│ Progress:                                    │
│ Conversations: [████████░░] 4,521/7,000      │
│ Messages:      [██████░░░░] 12,043/20,000    │
│ Calls:         [█████████░] 892/1,000        │
│ Media:         [███░░░░░░░] 234/800          │
│                                              │
│ Current: Processing conversation 617-555-0123 │
│                                              │
│ Errors: 3 [View Details]                     │
│ Warnings: 12 [View Details]                  │
│                                              │
│ Elapsed: 00:42:15                            │
│ Estimated remaining: 00:35:00                │
│                                              │
│ [Pause] [Cancel] [View Logs]                 │
└─────────────────────────────────────────────┘
```

### Database Schema for Import Tracking
```sql
CREATE TABLE import_runs (
    id UUID PRIMARY KEY,
    type VARCHAR(20), -- 'historical', 'reconciliation'
    status VARCHAR(20), -- 'pending', 'running', 'completed', 'failed'
    
    -- Progress tracking
    total_conversations INTEGER,
    processed_conversations INTEGER,
    total_messages INTEGER,
    processed_messages INTEGER,
    total_calls INTEGER,
    processed_calls INTEGER,
    total_media INTEGER,
    processed_media INTEGER,
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    errors JSONB,
    warnings JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Reconciliation Script Reuse

Since import and reconciliation are the same logic with different time ranges:

```python
class OpenPhoneSync:
    """
    Single sync engine for both historical and daily
    """
    def sync(self, start_date=None, end_date=None):
        if not start_date:
            # Historical import - all time
            start_date = datetime(2020, 1, 1)
        
        if not end_date:
            end_date = datetime.now()
        
        # Same logic for both cases
        return self._sync_timerange(start_date, end_date)
    
    def historical_import(self):
        """Full import"""
        return self.sync()
    
    def daily_reconciliation(self):
        """Last 24 hours"""
        yesterday = datetime.now() - timedelta(days=1)
        return self.sync(start_date=yesterday)
```

## Error Handling

### Retry Strategy
- Network errors: Exponential backoff
- Rate limits: Respect and queue
- Missing data: Log and continue
- Media failures: Queue for later retry

### Rollback Plan
If import fails midway:
1. Note last successful conversation ID
2. Clear all imported data
3. Fix issue
4. Restart from beginning (idempotent)

## Post-Import Verification

### Completeness Checks
- Total conversation count matches
- No gaps in date ranges
- All media URLs captured
- All phone numbers imported

### Next Step: Contact Enrichment
After successful import, move to one-time enrichment phase

---

*Based on v1's successful implementation using Celery background workers*