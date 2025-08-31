# Marketer Dashboard Requirements - Attack-a-Crack v2

## Vision
A dedicated dashboard for the marketing team member that streamlines social media content creation, campaign management, and marketing analytics while maintaining appropriate access controls and separation from operational data.

## User Profile: The Marketer

### Current Workflow (Manual)
1. Receives Google Calendar invite when technician adds photos
2. Goes to Calendar event to download photos
3. Creates social media posts manually
4. Posts to each platform individually
5. Manages campaigns through separate tools
6. No unified analytics view

### Dream Workflow (Automated)
1. Logs into dedicated marketer dashboard
2. Sees new photos ready for social media
3. AI generates post suggestions
4. One-click publishes to all platforms
5. Manages all campaigns from one place
6. Sees unified analytics and ROI

## Dashboard Components

### 1. Photo Queue (Top Priority)
**New Photos Section:**
```
📸 NEW CONTENT READY (3)

Yesterday's Jobs:
┌─────────────────────────────────────────────┐
│ Wilson Foundation Repair                     │
│ 📍 Newton, MA                                │
│ [Before] [During] [After] - 6 photos        │
│ Tech notes: "Amazing transformation!"        │
│ [Generate Post] [View All] [Archive]        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Chen Bulkhead Replacement                    │
│ 📍 Brookline, MA                             │
│ [Before] [After] - 4 photos                 │
│ ⭐ Customer left 5-star review!              │
│ [Generate Post] [View All] [Archive]        │
└─────────────────────────────────────────────┘
```

### 2. Social Media Publishing
**AI-Generated Posts:**
```
GENERATED POST FOR: Wilson Foundation Repair

Caption Version A (Professional):
"Another successful foundation repair in Newton! 
This crack was allowing water into the basement, 
but our specialized injection process sealed it 
permanently. #FoundationRepair #NewtonMA #BasementWaterproofing"

Caption Version B (Casual):
"Before ➡️ After! 💪 This Newton homeowner can 
sleep easy knowing their basement is dry for good. 
No more water worries! #AttackACrack #FixedIt"

[Edit] [Regenerate] [Use Version A] [Use Version B]

PUBLISH TO:
☑ Instagram  ☑ Facebook  ☑ LinkedIn  
☑ Twitter    ☑ Google Business Profile

[Schedule for Best Time] [Post Now]
```

### 3. Campaign Management

**Text Campaign Center:**
- Create new campaigns
- View active A/B tests
- See response analytics
- Manage templates
- Handle opt-outs

**Email Campaign Tools:**
- Newsletter builder
- Customer segmentation
- Drip campaigns
- Performance tracking

### 4. Marketing Analytics

**Performance Dashboard:**
```
📊 THIS WEEK'S PERFORMANCE

Social Media:
- Posts published: 12
- Total reach: 4,500
- Engagement rate: 3.2% ↑
- Best performing: Bulkhead before/after

Campaigns:
- SMS sent: 625
- Response rate: 2.8%
- A/B winner: Version B (urgency)
- New leads: 18

Reviews:
- New reviews: 4 ⭐⭐⭐⭐⭐
- Response rate: 100%
- Social posts from reviews: 2
```

### 5. Content Calendar

**Scheduling View:**
- Planned social posts
- Campaign launches
- Review request sequences
- Seasonal promotions
- Blog post schedule

## Access Controls

### What Marketer CAN Access:
✅ All job photos
✅ Customer names and locations (for posts)
✅ Review content
✅ Campaign tools
✅ Social media accounts
✅ Marketing analytics

### What Marketer CANNOT Access:
❌ Financial data (quotes, invoices)
❌ Full customer contact info
❌ Operational scheduling
❌ Employee conversations
❌ Sensitive business metrics

## Automation Features

### 1. Photo Flow Automation
**Current Manual Process:**
1. Technician adds photos to Calendar
2. Adds marketer as invitee
3. Marketer gets email
4. Downloads from Calendar
5. Uploads to social platforms

**New Automated Process:**
1. Technician adds photos to Calendar
2. System auto-detects new photos
3. Appears in marketer queue
4. AI generates captions
5. One-click multi-platform publish

### 2. AI Content Generation

**Powered by Gemini:**
- Analyzes before/after photos
- Generates engaging captions
- Suggests relevant hashtags
- Adapts tone per platform
- Creates story narratives

**Learning Component:**
- Trains on best-performing posts
- Adapts to brand voice
- Seasonal awareness
- Local event tie-ins

### 3. Optimal Timing

**Smart Scheduling:**
- Best times per platform
- Audience online patterns
- Avoid over-posting
- Event-based timing (rain → waterproofing posts)

## Platform Integrations

### Social Media APIs:
1. **Instagram** (via Facebook Graph API)
2. **Facebook** (Graph API)
3. **LinkedIn** (Marketing API)
4. **Twitter/X** (API v2)
5. **Google Business Profile** (Posts API)

### Future Integrations:
- TikTok (for younger demographic)
- Nextdoor (local community)
- YouTube Shorts
- Pinterest (home improvement)

## Blog Publishing (Future)

### CMS Integration:
- WordPress API connection
- SEO optimization
- Image optimization
- Auto-categorization
- Schema markup for local SEO

### Content Types:
- Case studies with photos
- Seasonal tips
- FAQ articles
- Customer testimonials
- Educational content

## Implementation Phases

### MVP (Must Have):
1. Separate login/dashboard
2. Photo queue from Calendar
3. Manual social posting interface
4. Basic campaign access
5. Simple analytics

### Phase 2 (Should Have):
1. AI caption generation
2. Multi-platform publishing
3. Content calendar
4. Advanced analytics
5. A/B testing for social

### Phase 3 (Could Have):
1. Blog publishing
2. Video content support
3. Influencer tracking
4. Competitor analysis
5. ROI attribution

## Success Metrics

### Efficiency Metrics:
- Time to publish: <5 minutes (from 30+)
- Posts per week: 15+ (from 5)
- Platform coverage: 5 simultaneous

### Performance Metrics:
- Social engagement rate: >3%
- Lead attribution: Track source
- Review showcase rate: 80% of 5-stars
- Content consistency: Daily posting

## Technical Implementation

### User Roles:
```python
class UserRole(Enum):
    OWNER = "owner"  # Full access
    MARKETER = "marketer"  # Marketing tools only
    TECHNICIAN = "technician"  # Job updates only
    ADMIN = "admin"  # System administration
```

### Photo Processing:
```python
class PhotoQueueService:
    def check_new_photos(self):
        # Check Calendar events for new photos
        # Download and store locally
        # Generate thumbnails
        # Queue for AI processing
        
    def generate_social_post(self, photos, job_details):
        # Send to Gemini with context
        # Generate multiple caption options
        # Suggest optimal hashtags
        # Return formatted for each platform
```

## Questions for Next Session

1. **Platform Priorities**: Which social platforms are most important?
2. **Posting Frequency**: Target posts per week per platform?
3. **Content Mix**: What % before/after vs educational vs promotional?
4. **Team Growth**: Planning to add more marketing team members?
5. **Budget Tools**: Need paid ad management in platform?
6. **Brand Voice**: Formal, casual, or varies by platform?

---

*The Marketer Dashboard transforms marketing from a time-consuming manual process to an efficient, AI-powered content engine.*