# OpenPhone Integration Requirements - The Backbone of Attack-a-Crack CRM

## Critical Context
**OpenPhone is THE backbone of the entire system** - not just a communication channel, but the central hub through which all customer interactions flow. This integration is more important than any other.

## Current State

### Account Structure
- **Phone Numbers**: 1 main business line (Massachusetts)
- **Future**: Will expand to multiple numbers/locations
- **MVP**: Single number support is sufficient

### Existing Data Volume
- **History**: ~9 months of data
- **Conversations**: 7,000+ total
- **Contacts**: Thousands (trapped in web UI - API can't access)
- **Media**: Hundreds/thousands of foundation crack photos

### Critical API Limitations (Major Problems)
1. **Can't access web UI contacts** - Thousands of contacts unreachable via API
2. **Can't retrieve historical media** - Photos in old messages inaccessible via API
3. **Media only available via webhooks** - Makes webhook reliability critical

## Data Import Requirements

### Initial Historical Import - EVERYTHING
**Every single piece of data that's accessible:**
- All text messages (sent and received)
- All call records (completed, missed, voicemail)
- Call recordings (audio files)
- Voicemail recordings
- AI-generated transcripts
- AI-generated summaries
- Media attachments (photos/videos) - if possible
- Timestamps for everything
- Phone numbers (including group conversations)

### The Contact Enrichment Challenge
Since API can't access web UI contacts:
1. Import all conversation/activity data first
2. One-time manual enrichment from other sources
3. Push enriched contacts back to OpenPhone as API contacts
4. Become source of truth for contact data going forward

## Webhook Requirements

### Events to Capture (All Critical)
- `message.received` - **Most important** - incoming texts
- `message.updated` - Status changes
- `call.completed` - Finished calls
- `call.missed` - Missed calls  
- `call.recording.ready` - Recording available
- `call.transcript.ready` - Transcript complete
- `call.summary.ready` - AI summary ready

### Real-Time Processing Needs
- **Speed**: Near-instant processing during business hours
- **Notifications**: Push to mobile app immediately
- **Media**: MUST capture photos via webhooks (only reliable way)

## Integration with Core Features

### Campaign Integration
**Critical Requirements:**
- Campaign responses appear in main activity feed
- Outgoing campaign messages should be:
  - Recorded in system (via webhook)
  - Hidden by default in activity view
  - Filterable (show/hide campaign messages)
  - Linked to campaign for tracking

**Key Insight**: Campaign messages clutter the UI when sending 125/day

### Gemini AI Integration (Future but Important)
**Auto-Detection Features:**
- Extract names from messages → Update contact
- Extract addresses → Link to property
- Extract email addresses → Add to contact
- Identify problem descriptions → Create draft quote/appointment

**Image Analysis (Game-Changer Future Feature):**
- Analyze foundation crack photos
- Auto-generate quotes if confident
- Request additional photos if needed
- Flag for human review if uncertain

### Media Handling
**Critical Business Need**: Foundation crack photos are VITAL

**Requirements:**
- Store all media permanently
- Link media to contact/property/conversation
- Make accessible for:
  - Google Calendar appointments (attach to events)
  - Quote generation (visual reference)
  - Future AI analysis
  - Historical reference

**Storage Strategy Needed**: S3? Local? CDN?

### Google Calendar Integration
When scheduling appointments:
- Auto-attach all relevant photos
- Include conversation summary
- Link back to CRM contact

### QuickBooks Integration  
More than financial:
- Link conversations to quotes/invoices
- Track job history per contact
- Enrich with service records

## Message Threading & Organization

### Conversation Structure
- **Primary**: Group by phone number (1-on-1)
- **Group Conversations**: Support multiple participants
  - Our number + 2+ other numbers
  - Separate thread from individual conversations
- **Campaign Flagging**: Mark conversations with campaign messages

### Activity Feed Design
**Default View**: 
- Show all incoming messages
- Hide outgoing campaign messages
- Show manual outgoing messages

**Filter Options**:
- Show/hide campaign messages
- Show only responses
- Show only non-campaign
- Show by date range

## Sync Strategy & Reliability

### Primary Strategy: Webhooks First
- Real-time webhooks for all events
- Immediate processing and storage
- Source of truth: OpenPhone for conversations

### Backup Strategy: Daily Reconciliation
- Run daily at 2 AM
- Query OpenPhone API for previous day
- Compare with webhook-received data
- Alert if discrepancies found

### Health Monitoring
- Every 6 hours (4x daily)
- Send test message between internal numbers
- Verify webhook receipt within 2 minutes
- Alert if health check fails

### Source of Truth Decisions
- **Conversations**: OpenPhone is truth
- **Contact Info**: We become truth (after enrichment)
- **Phone Formatting**: OpenPhone's format
- **Media**: Our storage (with OpenPhone URLs as backup)

## Local Development Solution

### Requirements
- Consistent endpoint (not changing like ngrok)
- Free or low-cost
- Reliable forwarding
- Easy setup

### Options Priority
1. **Production proxy endpoint** - Most reliable
2. **smee.io** - If free and consistent
3. **ngrok with paid plan** - If stable endpoint
4. **Webhook record/replay** - For testing

## Notification & Alerting

### Critical Alerts
- Webhook failures (immediate)
- Health check failures (immediate)
- Reconciliation discrepancies (daily summary)
- Media download failures (immediate)

### Notification Channels
- Email (primary)
- SMS to owner (critical only)
- Dashboard banner (always visible)

## Data Model Implications

### Tables Needed
- `conversations` - Thread tracking
- `messages` - Individual messages
- `calls` - Call records
- `media_attachments` - Photos/videos
- `call_recordings` - Audio files
- `transcripts` - AI transcripts
- `summaries` - AI summaries
- `webhook_events` - Raw webhook data
- `sync_status` - Track import/sync state

### Many-to-Many Relationships
- Conversations ↔ Contacts (group conversations)
- Messages ↔ Media (multiple attachments)
- Conversations ↔ Campaigns (tracking)

## Success Metrics

### MVP Success
- [ ] Import all 7,000+ conversations
- [ ] Zero webhook misses in first week
- [ ] All media captured and stored
- [ ] Campaign messages properly filtered
- [ ] Sub-second processing time

### Long-term Success
- [ ] 99.99% webhook reliability
- [ ] Automatic contact enrichment working
- [ ] AI photo analysis in beta
- [ ] Seamless quote generation flow
- [ ] Perfect sync with OpenPhone

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. Webhook endpoint setup
2. Database schema for all entities
3. Basic webhook processing
4. Health check system

### Phase 2: Historical Import (Week 2)
1. Bulk import all conversations
2. Import all accessible call data
3. Attempt media retrieval
4. Handle contact enrichment

### Phase 3: Real-time Operations (Week 3)
1. Full webhook processing
2. Media storage system
3. Activity feed with filters
4. Reconciliation script

### Phase 4: Intelligence (Week 4+)
1. Gemini integration for extraction
2. Campaign message handling
3. Advanced filtering
4. Notification system

## Open Questions

1. **Media Storage**: S3, Cloudflare R2, or local storage?
2. **Contact Enrichment**: What's the one-time process for 7,000 conversations?
3. **Group Conversations**: How many exist? Special handling needed?
4. **Rate Limits**: Any OpenPhone API rate limits to worry about?
5. **Retention**: Keep all data forever or archive old conversations?

---

*This is the most critical integration in the entire system. Without reliable OpenPhone sync, nothing else matters.*