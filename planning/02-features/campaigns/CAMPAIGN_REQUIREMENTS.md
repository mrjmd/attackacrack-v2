# Campaign System Requirements - Attack-a-Crack v2

## Business Context
Attack-a-Crack is a foundation repair company specializing in:
- Concrete foundation crack repair (primary)
- Concrete resurfacing (stairs, walkways, pool decks)
- Bulkhead leak repairs
- Field stone and cinderblock work (not marketed)

Target customers: Homes built after 1950 (poured concrete foundations)

## Core Campaign Requirements

### 1. Data Model - Many-to-Many Relationships

#### Critical Insight
**Addresses ↔ Contacts is MANY-TO-MANY**
- One person can own/represent multiple properties (realtors, investors, landlords)
- One property can have multiple contacts (spouses, property managers, tenants)
- Every property must have a designated **primary contact**

#### Database Design Implications
```sql
-- Junction table for many-to-many
CREATE TABLE property_contacts (
    property_id UUID REFERENCES properties(id),
    contact_id UUID REFERENCES contacts(id),
    is_primary BOOLEAN DEFAULT FALSE,
    relationship_type VARCHAR(50), -- 'owner', 'realtor', 'manager', etc.
    PRIMARY KEY (property_id, contact_id)
);
```

### 2. Contact History Integration

#### OpenPhone Historical Data Import - CRITICAL
Must import ALL historical OpenPhone activity to enable:

**Campaign Behavior Configuration (Per Campaign)**
- **Option A**: Flag previously contacted for manual review
- **Option B**: Skip all previously contacted automatically
- **Option C**: Gemini generates context-aware follow-up based on history
- **Option A+C Hybrid**: Gemini suggests, human approves

**Absolute Rule**: Anyone who has EVER sent STOP/UNSUBSCRIBE is permanently excluded

### 3. Schedule & Throttling

#### Business Hours
- **Days**: Monday - Friday only
- **Hours**: 9:00 AM - 5:00 PM ET
- **Future**: Narrow based on response data analytics

#### Volume Limits
- **OpenPhone limit**: 125 cold messages/day
- **Throttling**: Spread throughout day to appear natural
- **Starting point**: Batches of 25 every 30 minutes

### 4. Message Templates & Personalization

#### Example Template (Current Style)
```
Hey {{first_name}}, I'm Matt from Attack A Crack—family-run in Quincy, 
fixing foundations and concrete full-time. We repair basement cracks, 
bulkhead leaks, stairs, walkways, pool decks—you name it.

Free quotes, great reviews, lifetime guarantee. Text us a photo or 
we can swing by. Need anything checked out?
```

#### Personalization Tokens
**Available Now:**
- `{{first_name}}` - From contact record
- `{{city}}` or `{{neighborhood}}` - Property location
- `{{year_built}}` - Property age indicator
- `{{year_purchased}}` - How long they've owned

**Future Tokens (Need Data):**
- `{{has_basement}}` - Basement indicator
- `{{has_pool}}` - Pool deck opportunity
- `{{property_value_range}}` - High/medium/low value

#### Template Library Needed
Build collection of 10-20 variations:
- Introductory messages
- Seasonal (spring thaw, winter prep)
- Neighborhood presence
- Educational/informational
- Special offers
- Follow-ups for previous contacts

### 5. A/B Testing Strategy

#### MVP A/B Testing
- **Split**: 50/50 distribution
- **Minimum sample**: 100 per variant (200 total)
- **Metrics**: Response rate as primary KPI
- **Manual review**: Check results after completion
- **No automation**: Human decides winner

#### Future A/B Testing
- **Statistical significance**: Chi-square test at 95% confidence
- **Early stopping**: Pause losing variant if clear winner emerges
- **Auto-scaling**: Gradually shift traffic to winner (70/30, 90/10, 100/0)
- **Multi-variant**: Test 3+ messages simultaneously

### 6. Response Handling

#### MVP Response Processing
- **Positive responses**: Mark as responded, no auto-reply
- **STOP/UNSUBSCRIBE**: Flag contact, send confirmation, never text again
- **All others**: Pass through to OpenPhone inbox

#### Future Enhancements
- Gemini-powered responses for simple questions
- Auto-scheduling for inspection requests
- Sentiment analysis for prioritization

### 7. Compliance & Safety

#### Opt-Out Management
- **Global config**: Default opt-out text for all campaigns
- **Per-campaign toggle**: Option to include/exclude opt-out text
- **Keywords detected**: STOP, UNSUBSCRIBE, REMOVE, CANCEL, QUIT, END
- **Confirmation required**: "You've been unsubscribed. Reply START to resubscribe."

#### Message Compliance
- **Sender ID**: Always identify Attack-a-Crack
- **Business hours**: Enforce 9-5 ET M-F
- **Service area**: Only message properties within service radius
- **Property type**: Residential only (skip commercial)
- **Frequency cap**: Max 1 message per month per contact

#### Phone Validation
- **MVP**: NumVerify validation before sending
- **Future**: DNC list checking (not MVP)
- **No consent tracking**: Not implementing consent documentation

### 8. Analytics & Reporting

#### Campaign Metrics (MVP)
- Messages sent
- Messages delivered
- Responses received (count & rate)
- Opt-outs (count & rate)
- Time to response distribution

#### Future Analytics
- Geographic clustering of responses
- Job type analysis by area
- Best time/day analysis
- Message performance by template
- Customer lifetime value tracking

### 9. Success Benchmarks

#### Industry Standards (Research Needed)
- **Response rate**: 3-5% typical, 8-10% good, 15%+ excellent
- **Opt-out rate**: <2% good, 2-5% acceptable, >5% concerning
- **Conversion rate**: Responses → Inspections → Jobs

#### Measurement Strategy
1. Run initial campaigns without targets
2. Establish baseline from first 1,000 sends
3. Set improvement goals from baseline
4. Iterate based on data

## Technical Implementation Notes

### Campaign States
```
DRAFT → SCHEDULED → ACTIVE → PAUSED → COMPLETED
                        ↓
                    CANCELLED
```

### Daily Campaign Execution
```python
# Pseudocode for daily campaign run
for campaign in active_campaigns:
    if not campaign.should_run_today():
        continue
    
    contacts = campaign.get_next_batch(limit=25)
    
    for contact in contacts:
        if contact.has_opted_out():
            continue
        if campaign.skip_previously_contacted and contact.was_contacted():
            continue
        if campaign.use_ai_personalization and contact.was_contacted():
            message = gemini.personalize(template, contact.history)
            queue_for_review(message)
        else:
            send_message(contact, campaign.template)
```

## Open Questions

1. **Message frequency**: If someone doesn't respond, when can we message again?
2. **Cross-campaign coordination**: Can same person be in multiple active campaigns?
3. **Geographic prioritization**: Should closer properties get messaged first?
4. **Seasonal templates**: Different messages for different times of year?
5. **Response window**: How long to wait before considering non-response?

## MVP vs Future Phases

### MVP (Phase 1)
- Basic campaign creation with single template
- Manual A/B test review
- Simple opt-out handling
- Basic response tracking
- PropertyRadar CSV import

### Phase 2
- A/B testing with statistical significance
- Gemini message personalization
- Geographic analytics
- DNC list integration
- Automated response handling

### Phase 3
- Multi-channel (SMS + Email)
- Drip sequences
- Advanced segmentation
- Predictive scoring
- ROI tracking with QuickBooks

---

*Last Updated: August 2025*
*Status: Requirements Gathered*