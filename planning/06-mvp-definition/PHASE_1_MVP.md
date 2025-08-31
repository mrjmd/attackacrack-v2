# Attack-a-Crack v2 - MVP Definition (Phase 1)
*Target: 4-6 weeks development*

## MVP Philosophy
**"The smallest system that delivers real business value every day"**

Focus on the core workflow: **Lead → Quote → Schedule → Complete → Get Paid**

## 🎯 MVP Core Features (MUST HAVE)

### 1. OpenPhone Integration (Basic)
**What's IN:**
- ✅ Send/receive SMS via API
- ✅ Contact sync (one-way from OpenPhone)
- ✅ Basic conversation view
- ✅ Click-to-text from contacts

**What's OUT:**
- ❌ Historical import (Phase 2)
- ❌ Call handling
- ❌ Voicemail transcription
- ❌ Media attachments (Phase 2)

### 2. Contact Management
**What's IN:**
- ✅ Create/edit contacts
- ✅ Phone number deduplication
- ✅ Basic search
- ✅ Manual notes

**What's OUT:**
- ❌ PropertyRadar enrichment (Phase 2)
- ❌ Address-contact relationships
- ❌ Tags and segments
- ❌ Import from other sources

### 3. Campaign System (Core)
**What's IN:**
- ✅ CSV import (single, working implementation)
- ✅ Create campaign with template
- ✅ A/B testing (50/50 split)
- ✅ Daily limit (125 messages)
- ✅ Business hours enforcement
- ✅ Basic opt-out handling

**What's OUT:**
- ❌ Response analytics (Phase 2)
- ❌ Smart follow-ups
- ❌ Weather triggers
- ❌ Automated messaging (Phase 2)

### 4. Dashboard (Simplified)
**What's IN:**
- ✅ Money Waiting section (manual entries)
- ✅ Today's todos (manual)
- ✅ Recent texts (last 20)
- ✅ Campaign status (sent today)

**What's OUT:**
- ❌ QuickBooks quote approvals (Phase 2)
- ❌ Weather integration
- ❌ Financial metrics
- ❌ Google Ads controls

### 5. User Authentication
**What's IN:**
- ✅ Single owner login
- ✅ Secure session management
- ✅ Environment-based config

**What's OUT:**
- ❌ Multi-user support (Phase 2)
- ❌ Role-based access
- ❌ Marketer dashboard

## 🏗️ Technical Architecture (MVP)

### Backend: FastAPI
```python
# Simple, direct implementation
app/
├── main.py              # FastAPI app
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── services/
│   ├── openphone.py     # OpenPhone API client
│   ├── campaign.py      # Campaign logic
│   └── contact.py       # Contact management
├── api/
│   ├── contacts.py      # Contact endpoints
│   ├── campaigns.py     # Campaign endpoints
│   └── dashboard.py     # Dashboard data
└── database.py          # PostgreSQL connection
```

### Frontend: SvelteKit
```
src/
├── routes/
│   ├── +page.svelte         # Dashboard
│   ├── contacts/            # Contact management
│   ├── campaigns/           # Campaign creation
│   └── conversations/       # Message view
└── lib/
    ├── api.js               # Backend calls
    └── components/          # Shared UI
```

### Database: PostgreSQL (Simple Schema)
```sql
-- Minimal tables for MVP
contacts (id, name, phone, email, notes)
campaigns (id, name, template_a, template_b, daily_limit)
campaign_sends (id, campaign_id, contact_id, version, sent_at)
messages (id, contact_id, direction, content, created_at)
todos (id, description, completed, due_date)
```

### Deployment: Docker + DigitalOcean
- Single Docker Compose file
- PostgreSQL + Redis + FastAPI + SvelteKit
- $50/month droplet
- Daily backups

## 📊 MVP Success Metrics

### Must Achieve:
- Send 625 campaign messages/week reliably
- Track responses accurately
- Zero data loss on CSV import
- <5 second page loads
- 99% uptime

### Nice to Have:
- 2% response rate on campaigns
- Mobile responsive
- Export campaign results

## 🚀 Development Approach

### Week 1-2: Foundation
- [ ] FastAPI project setup
- [ ] Database schema
- [ ] Basic auth
- [ ] SvelteKit setup
- [ ] Docker environment

### Week 3-4: Core Features
- [ ] Contact CRUD
- [ ] OpenPhone integration
- [ ] CSV import
- [ ] Campaign creation
- [ ] A/B testing logic

### Week 5-6: Polish & Deploy
- [ ] Dashboard
- [ ] Testing
- [ ] Bug fixes
- [ ] Production deployment
- [ ] Data migration

## ❌ Explicitly NOT in MVP

### Major Features Deferred:
1. **PropertyRadar** - Manual property lookups for now
2. **QuickBooks** - Manual quote/invoice creation
3. **Google Calendar** - Manual scheduling
4. **Automated Messages** - Manual follow-ups
5. **Gemini AI** - No AI features
6. **Weather** - Check weather.com manually
7. **Multi-user** - Owner only
8. **Historical Import** - Start fresh

### Workarounds for MVP:
- **Quote Approvals**: Check QuickBooks manually
- **Scheduling**: Use Google Calendar directly
- **Follow-ups**: Set manual reminders
- **Property Data**: Look up manually when needed
- **Team Communication**: Continue using current methods

## 🎯 Definition of Done for MVP

### Acceptance Criteria:
- [ ] Can import CSV and send campaign
- [ ] Can track opt-outs
- [ ] Can see responses in conversation view
- [ ] A/B test results visible
- [ ] Daily limits enforced
- [ ] Mobile usable (not perfect)
- [ ] Deployed and accessible
- [ ] Owner can login securely
- [ ] Data persists reliably
- [ ] Can export contacts

### Launch Checklist:
- [ ] All tests passing
- [ ] Deployed to production
- [ ] SSL certificate active
- [ ] Backups configured
- [ ] Monitoring in place
- [ ] Owner trained on system
- [ ] Support process defined

## 📈 Post-MVP Roadmap

### Phase 2 (Weeks 7-10): Integration Layer
- QuickBooks quote approvals
- Google Calendar scheduling
- PropertyRadar enrichment
- OpenPhone historical import
- Automated follow-ups

### Phase 3 (Weeks 11-14): Intelligence
- Gemini AI integration
- Smart scheduling
- Weather automation
- Response analytics
- Conversation sidebar

### Phase 4 (Weeks 15-18): Scale
- Multi-user support
- Marketer dashboard
- Mobile apps
- Advanced reporting
- Connecticut branch

## 💡 Key Decisions for MVP

### Architecture Choices:
1. **Modular Monolith** - Single deployable unit
2. **Server-Side Rendering** - SvelteKit SSR for speed
3. **PostgreSQL Only** - No fancy databases yet
4. **Polling Over Webhooks** - Simpler for MVP
5. **Manual Over Magic** - Explicit over automatic

### Trade-offs Accepted:
- Manual work remains (scheduling, quotes)
- No historical data import
- Single user limitation
- Basic UI (functional over beautiful)
- Limited analytics

## 🔥 Risk Mitigation

### Technical Risks:
- **Risk**: OpenPhone API limits
  - **Mitigation**: Rate limiting, queuing
  
- **Risk**: CSV import failures
  - **Mitigation**: Extensive testing, validation

### Business Risks:
- **Risk**: Missing quote approvals
  - **Mitigation**: Daily manual check routine
  
- **Risk**: Campaign delivery issues
  - **Mitigation**: Monitoring, alerts, retry logic

## ✅ Go/No-Go Criteria

### MVP is Ready When:
1. Can run a full campaign start-to-finish
2. Zero data loss for 1 week
3. Owner successfully uses for 3 days
4. Response tracking accurate
5. System stays up 24 hours

### MVP Fails If:
1. Loses customer data
2. Sends duplicate messages
3. Violates opt-outs
4. Can't track responses
5. Requires developer intervention daily

---

*This MVP focuses on proving the core campaign system works reliably. Everything else can wait.*

**Remember: "Launch something in 6 weeks, not everything in 6 months"**