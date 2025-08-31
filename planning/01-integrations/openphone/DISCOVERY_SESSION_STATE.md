# OpenPhone Integration - Discovery Session State

*Last Updated: August 2025*
*Status: In Progress - Taking a break*

## ✅ What We've Covered

### 1. Integration Importance
- **OpenPhone is THE backbone** of the entire system
- Not just communication, but central nervous system
- More important than any other integration

### 2. Historical Import Strategy
- **v1 got this right** - Reuse Celery background worker approach
- ~7,000 conversations (not as many messages as initially thought)
- Many are single outbound messages with no response
- System can be read-only during import
- Turn off webhooks during import
- Import dashboard essential for local/staging/production iterations

### 3. Contact Enrichment Plan
- **One-time operation** to bootstrap system
- Separate enrichment dashboard for CSV imports
- Multiple sources: PropertyRadar, QuickBooks, other CSVs
- Match by phone number primarily
- Manual review for conflicts
- After enrichment, we become source of truth

### 4. Key Technical Decisions Made
- **Same script for import and reconciliation** (just different time ranges)
- Import all at once, not in batches
- Webhooks are primary sync strategy
- Daily reconciliation as backup
- Health checks every 6 hours

## ✅ Topics Addressed in Latest Session

### 1. Media Storage Architecture - DECIDED
**Decision: Local storage for MVP**
- v1 never needed S3 - avoid over-engineering
- Simple directory structure on server
- Easy migration path to S3 later if needed
- Daily backups of media directory
- Thumbnails for images, embedded players for audio

### 2. Activity Feed UI/UX
**Design Decisions:**
- Exact layout and information hierarchy
- Filter persistence (remember user preferences?)
- Real-time updates via WebSocket?
- Desktop vs mobile variations
- Notification badges/counts
- Pagination vs infinite scroll

### 3. Group Conversations
**Need to Define:**
- How many exist (rough estimate)
- Special handling rules
- Campaign exclusions
- Contact matching for multiple participants
- UI differences from 1-on-1

### 4. Gemini Information Extraction
**Auto-Detection Priorities:**
1. Address → PropertyRadar lookup
2. Name → Contact update
3. Email → Contact enrichment
4. Problem description → Quote/appointment draft

**Key Questions:**
- Confidence thresholds for auto-action vs review
- How to handle ambiguous extractions
- Versioning/history of AI extractions
- Training/improvement loop

### 5. Daily Workflow
**Morning Routine:**
- Overnight summary design
- Priority message highlighting
- Campaign response aggregation

**Real-time Operations:**
- Notification preferences
- Auto-draft responses
- Quick actions menu

**End of Day:**
- Activity summary
- Tomorrow's preview
- Pending items

### 6. Critical Technical Decisions

**Webhook Processing Strategy:**
- Sync vs async processing
- Queue architecture
- Error handling
- Retry logic
- Dead letter queue

**Database Decisions:**
- Store raw webhooks forever?
- Partition strategy for large tables
- Archive old conversations?
- Index strategy for performance

## 🔧 Component Breakdown

### Created Sub-Documents
1. ✅ **01-HISTORICAL_IMPORT.md** - Mass import specification
2. ✅ **02-CONTACT_ENRICHMENT.md** - One-time enrichment dashboard

### Still Need Sub-Documents
3. **03-WEBHOOK_PROCESSING.md** - Real-time webhook handling
4. **04-MEDIA_STORAGE.md** - Photo/video storage system
5. **05-ACTIVITY_FEED.md** - UI/UX for message display
6. **06-HEALTH_MONITORING.md** - Reliability and alerting
7. **07-GEMINI_EXTRACTION.md** - AI information extraction
8. **08-API_INTEGRATION.md** - OpenPhone API wrapper

## 💡 Key Insights So Far

### What Makes This Complex
1. **Scale**: 7,000 conversations to import
2. **Media**: Photos are business-critical but API limited
3. **Contacts**: Can't access web UI contacts via API
4. **Real-time**: Near-instant message processing needed
5. **Reliability**: Can't afford to miss customer messages

### What v1 Got Right
- Historical import using Celery
- Background processing architecture
- Progress tracking
- Webhook processing flow

### What v1 Missed
- Contact enrichment strategy
- Media storage from historical messages
- Health monitoring implementation
- Efficient activity feed filtering

## 🎯 Next Session Priorities

### COMPLETED:
- ✅ Media storage: Local for MVP (avoid over-engineering)
- ✅ Activity feed: Basic design complete
- ✅ Daily workflow: Documented with weather/quote priorities

### HIGH PRIORITY - NEED DEEP DIVES:
1. **Dashboard Design** - Full exploration of morning priorities
2. **Conversation View** - Sidebar with map, property data, quotes
3. **Gemini Voice Training** - Learn from historical messages
4. **Real-time Updates** - Polling vs WebSocket decision

### REMAINING SPECS:
1. **Webhook Processing** - Async queue details
2. **Health Monitoring** - Consider 2nd number for testing
3. **Appointment Scheduling** - Two types need definition

## 📊 Progress Tracking

### OpenPhone Planning Progress
- [x] Account structure understanding
- [x] Historical import strategy
- [x] Contact enrichment plan
- [x] Webhook requirements
- [x] Campaign integration needs
- [ ] Media storage architecture
- [ ] Activity feed design
- [ ] Group conversation handling
- [ ] Gemini extraction flow
- [ ] Daily workflow optimization
- [ ] Technical architecture decisions

### Documents Completed
- Requirements.md - ✅
- Historical Import spec - ✅
- Contact Enrichment spec - ✅
- Discovery Session State - ✅ (this document)

### Documents Remaining
- Webhook Processing spec
- Media Storage spec
- Activity Feed spec
- Health Monitoring spec
- Gemini Extraction spec
- API Integration spec

---

## Quote from Session
> "I'm really appreciating doing this careful, detailed planning phase before we start doing any more work."

This methodical approach is ensuring we build exactly what's needed without the over-engineering that plagued v1.

---

*Ready to continue with media storage architecture, activity feed design, and remaining components when you return.*