# OpenPhone Webhook Processing Architecture

## Processing Strategy: Queue & Async

### Webhook Handler Flow
```
1. Webhook arrives at endpoint
   ↓
2. Basic validation (< 100ms)
   - Verify signature
   - Check event type
   ↓
3. Queue immediately to Celery
   - Store raw webhook payload
   - Return 200 OK to OpenPhone
   ↓
4. Async processing (Celery worker)
   - Parse webhook data
   - Update database
   - Trigger any follow-up actions
   - Handle errors with retry
```

### Why This Approach
- **Already have Celery/Redis** - No additional complexity
- **Reliability** - Never lose webhooks due to processing errors
- **Fast response** - OpenPhone gets 200 OK immediately
- **Retry logic** - Built into Celery for failed processing
- **Scalable** - Can add more workers if needed

### Implementation Details
```python
# FastAPI webhook endpoint
@router.post("/webhooks/openphone")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    # Quick validation (< 100ms)
    signature = request.headers.get("X-OpenPhone-Signature")
    body = await request.body()
    
    if not verify_signature(body, signature):
        raise HTTPException(400, "Invalid signature")
    
    # Queue immediately
    celery_app.send_task(
        "process_openphone_webhook",
        args=[body.decode()]
    )
    
    # Return fast
    return {"status": "queued"}

# Celery task
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_openphone_webhook(self, webhook_data: str):
    try:
        data = json.loads(webhook_data)
        
        # Process based on event type
        if data["type"] == "message.received":
            handle_incoming_message(data)
        elif data["type"] == "call.completed":
            handle_call_completed(data)
        # ... etc
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc)
```

## Real-Time Updates: 5-Second Polling

### Frontend Polling Strategy
```typescript
// SvelteKit store with polling
export function createPollingStore(endpoint: string) {
    const { subscribe, set } = writable([]);
    
    async function poll() {
        const data = await fetch(endpoint).then(r => r.json());
        set(data);
    }
    
    // Poll every 5 seconds
    const interval = setInterval(poll, 5000);
    poll(); // Initial load
    
    return {
        subscribe,
        destroy: () => clearInterval(interval)
    };
}
```

### Why Polling Over WebSockets
- **Simpler** - No connection management
- **5 seconds is fine** - User confirmed this latency is acceptable
- **Works everywhere** - Mobile, desktop, behind firewalls
- **Less complexity** - No reconnection logic needed

## Health Monitoring (Post-MVP)

### Second Phone Number Strategy
- **Dedicated monitoring number** - ~$10/month
- **Every 6 hours** - Send test message
- **Verify receipt** - Check webhook within 2 minutes
- **Alert on failure** - Email + dashboard banner

### Implementation
```python
@celery_app.task
def health_check():
    # Send test message
    test_message_id = openphone_api.send_message(
        from_number=MONITOR_NUMBER,
        to_number=MAIN_NUMBER,
        text=f"Health check: {datetime.now()}"
    )
    
    # Schedule verification in 2 minutes
    verify_health_check.apply_async(
        args=[test_message_id],
        countdown=120
    )

@celery_app.task
def verify_health_check(message_id: str):
    # Check if webhook was received
    webhook_received = check_webhook_log(message_id)
    
    if not webhook_received:
        send_alert("OpenPhone webhook failure detected!")
```

## Gemini Processing Strategy

### What Gets Processed
- **All incoming SMS** - Extract names, addresses, emails
- **Call transcripts** - Extract key information
- **Call summaries** - Parse AI-generated summaries
- **Voicemail transcripts** - Extract callback needs

### Smart Approval Logic
```python
def process_gemini_extraction(contact_id, extracted_data):
    contact = get_contact(contact_id)
    
    for field, value in extracted_data.items():
        if field in ["name", "email", "address"]:
            if getattr(contact, field) is None:
                # New data - auto-add
                setattr(contact, field, value)
                log_extraction(f"Auto-added {field}: {value}")
            else:
                # Existing data - queue for approval
                create_approval_request(
                    contact_id=contact_id,
                    field=field,
                    current_value=getattr(contact, field),
                    suggested_value=value
                )
```

### Rate Limiting Strategy
- Process immediately for now (low volume)
- Future: Batch process if > 100 messages/hour
- Monitor Gemini API costs monthly

## Call Activity Integration

### What We Log
- **All calls** - Completed, missed, voicemail
- **Call recordings** - Store audio files
- **Transcripts** - AI-generated transcriptions
- **Summaries** - AI-generated call summaries
- **Metadata** - Duration, direction, participants

### Display in CRM
```
Conversation View:
├── SMS Messages (threaded)
├── Call: Incoming - 5 min (with recording link)
├── Call: Missed (with callback button - future)
├── Voicemail: 30 sec (with transcript)
└── Call Summary: "Discussed foundation crack..."
```

### Future: Click-to-Call
```python
# Future endpoint for initiating calls
@router.post("/contacts/{contact_id}/call")
async def initiate_call(contact_id: str):
    # Use OpenPhone API to trigger call
    # Returns: "Call initiated on your OpenPhone app"
    pass
```

## Webhook Event Priority

### Critical Events (Process Immediately)
- `message.received` - Incoming texts
- `call.missed` - Need follow-up
- `voicemail.received` - Urgent callback

### Standard Events (Can delay 1-2 min)
- `message.delivered` - Delivery confirmation
- `call.completed` - Call ended
- `transcript.ready` - AI transcript done

### Low Priority (Batch process)
- `message.read` - Read receipts
- `summary.ready` - AI summary done

## Error Handling

### Webhook Failures
1. **Retry 3 times** with exponential backoff
2. **Dead letter queue** after 3 failures
3. **Daily report** of failed webhooks
4. **Manual retry button** in admin panel

### OpenPhone API Errors
- Rate limiting: Exponential backoff
- 500 errors: Retry with delay
- 400 errors: Log and alert (likely our bug)

## Database Schema for Webhooks

```sql
-- Raw webhook storage
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(50),
    payload JSONB,
    received_at TIMESTAMP,
    processed_at TIMESTAMP,
    status VARCHAR(20), -- pending, processed, failed
    error_message TEXT,
    retry_count INT DEFAULT 0
);

-- Create index for monitoring
CREATE INDEX idx_webhook_status ON webhook_events(status, received_at);
```

## Monitoring & Alerts

### Key Metrics
- Webhook processing time (target: < 2 seconds)
- Failed webhook percentage (target: < 0.1%)
- Health check success rate (target: 100%)
- Gemini extraction accuracy (manual review sample)

### Alert Conditions
- Webhook processing > 5 seconds
- Failed webhooks > 1%
- Health check failure
- Queue depth > 1000 messages

---

*All architectural decisions confirmed with user. Ready for implementation.*