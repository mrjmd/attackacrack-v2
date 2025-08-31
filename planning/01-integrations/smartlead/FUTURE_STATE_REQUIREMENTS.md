# SmartLead Integration - Future State Requirements

## Status: POST-MVP FEATURE
*This integration is planned for Phase 3/4 after core SMS campaigns are working well*

## Vision
Extend Attack-a-Crack's campaign capabilities to include sophisticated email outreach, complementing SMS campaigns for a true multi-channel approach to customer engagement.

## Why SmartLead?
- Proven email campaign platform
- Cold email compliance built-in
- A/B testing capabilities
- Detailed analytics
- Good API for integration

## Key Integration Points

### 1. Campaign System Extension
When designing the campaign system in v2, ensure architecture supports:
- **Multiple channel types** (SMS, Email, future: Voice)
- **Channel-specific settings** (SMS daily limits vs email warmup)
- **Unified campaign analytics** across channels
- **Template system** that works for both SMS and email

### 2. Gmail Integration Coordination
SmartLead emails will flow through Gmail, so ensure:
- Gmail integration can identify SmartLead campaigns
- Responses are properly tagged and routed
- Conversation threading works across campaign emails
- Unsubscribe handling is unified

### 3. Contact List Management
- Same lists should work for SMS and email
- Channel preferences per contact
- Bounce handling for emails
- Deliverability scoring

## Architecture Considerations for V2

### Campaign Service Design
```python
class CampaignService:
    def create_campaign(self, campaign_data):
        # Design to support multiple channels from day 1
        channel_type = campaign_data.get('channel', 'sms')  # sms, email, multi
        
        if channel_type == 'email':
            # Future: delegate to SmartLead
            pass
        elif channel_type == 'sms':
            # Current: OpenPhone implementation
            pass
```

### Database Schema Considerations
- Campaign table should have `channel_type` field
- Template table should support both SMS (160 char) and email (HTML)
- Analytics should be channel-agnostic where possible

## Future Workflow

### Email Campaign Creation
1. Create campaign in Attack-a-Crack CRM
2. Select "Email" as channel type
3. Choose SmartLead template or create new
4. Set email-specific parameters:
   - Warmup schedule
   - Daily sending limits
   - Follow-up sequences
5. Launch through SmartLead API
6. Monitor responses in unified conversation view

### Response Handling
- SmartLead webhooks → Attack-a-Crack
- Gmail integration picks up responses
- Unified conversation view shows email + SMS
- Gemini AI processes all responses equally

## Implementation Phases

### Phase 1: Architecture Preparation (During V2 MVP)
- Design campaign system to be channel-agnostic
- Ensure database schema supports multiple channels
- Keep email campaigns in mind for UI design

### Phase 2: Basic Integration (Post-MVP)
- SmartLead API connection
- Simple campaign creation
- Response webhook handling

### Phase 3: Advanced Features
- A/B testing for email subjects/content
- Warmup automation
- Deliverability monitoring
- Multi-step sequences

### Phase 4: Full Unification
- Unified campaign builder for SMS + Email
- Cross-channel campaign orchestration
- Combined analytics dashboard
- Gemini AI optimization for both channels

## Key Design Decisions for V2

### DO:
- Design campaign system to be extensible
- Use channel-agnostic terminology where possible
- Plan for unified analytics from day 1
- Consider email templates in template system design

### DON'T:
- Don't hard-code SMS assumptions
- Don't create SMS-only database schemas
- Don't design UI that can't accommodate email

## Success Metrics (Future)
- Email campaign creation in <2 minutes
- 30%+ open rates
- Unified conversation view includes all emails
- Zero lost responses
- Seamless SMS ↔ Email campaign coordination

## Technical Notes
- SmartLead API is RESTful
- Supports webhooks for real-time events
- Has good template management
- Provides detailed analytics API
- Rate limits are reasonable

---

*This document ensures V2 architecture accommodates future email campaigns without requiring major refactoring. Focus remains on SMS for MVP, but the foundation supports multi-channel from day one.*