# Automated Messaging Requirements - Attack-a-Crack v2

## Vision
Leverage the campaign system infrastructure to power ALL automated messages - from appointment reminders to follow-ups to review requests - with built-in A/B testing capability to continuously optimize message performance.

## Key Insight: Campaigns Power Everything
Instead of building separate messaging systems, we use the campaign infrastructure for all automated messages, gaining:
- A/B testing for every message type
- Performance tracking and analytics
- Centralized message management
- Consistent delivery infrastructure
- Opt-out handling

## Message Types & Triggers

### 1. Appointment Reminders
**Trigger**: 24 hours before scheduled appointment
**Message Types**:
- Assessment reminder
- Repair job reminder
**A/B Testing Opportunity**: Test formal vs casual tone, time of day

Example:
```
Version A: "Hi {name}, just a reminder about your appointment tomorrow at {time}. Our technician will be evaluating your {job_type}. Reply CONFIRM to confirm or RESCHEDULE if needed."

Version B: "Hey {name}! Looking forward to seeing you tomorrow at {time} for your {job_type} assessment. We'll text when we're on the way. Any questions before we arrive?"
```

### 2. Post-Job Follow-Up & Review Request
**Trigger**: Job completion (Calendar event + QuickBooks invoice)
**Sequence**:
- Day 1: Follow-up + review request
- Day 7-10: Review reminder (if no review detected)

**A/B Testing Opportunity**: Test review request timing, wording, incentives

Day 1 Examples:
```
Version A: "Hi {name}, thanks for choosing Attack-a-Crack! How did everything go with your {job_type} yesterday? We'd love to hear about your experience: {review_link}"

Version B: "Hey {name}! Just checking that your {job_type} went smoothly yesterday. If you have 30 seconds, we'd really appreciate a review - it helps other homeowners find us: {review_link}"
```

**Personalization by Job Type**:
- Crack repair: "How's the basement looking?"
- Bulkhead: "Is the bulkhead closing properly?"
- Waterproofing: "Any moisture issues since we finished?"
- Resurfacing: "How's the new surface holding up?"

### 3. Quote Follow-Up
**Trigger**: Quote sent, no response after X days
**Sequence**:
- Day 3: Gentle reminder
- Day 7: Check-in with incentive
- Day 14: Final follow-up

**A/B Testing Opportunity**: Test follow-up frequency, incentives, urgency

### 4. Weather-Driven Messages
**Trigger**: Heavy rain forecast + customers with water issues
**Message**: Proactive check-in

Example:
```
"Hi {name}, with heavy rain coming Thursday, we wanted to check on your basement. If you notice any water issues, we're here to help. Priority scheduling available for past customers."
```

### 5. Smart TODO-Generated Follow-Ups
**Trigger**: Gemini detects commitment in conversation
**Example**: "I'll check back with you next week" → Automated follow-up scheduled

## Campaign System Integration

### Message Creation Interface
```
AUTOMATED MESSAGE TEMPLATE
Name: Post-Job Day 1 Follow-Up
Trigger: Job Completion
Delay: Next business day, 10 AM

VERSION A (50%):
"Hi {name}, thanks for..."
Performance: 34% response rate

VERSION B (50%):  
"Hey {name}! Just checking..."
Performance: 41% response rate ⭐

[Edit A] [Edit B] [View Analytics] [Declare Winner]
```

### Trigger Configuration
- Calendar events (appointments, completions)
- QuickBooks events (quote sent, invoice paid)
- Time-based (X days after event)
- Weather conditions
- Gemini detection (commitments, questions)
- Manual triggers

### Performance Tracking
Track for each message type:
- Delivery rate
- Response rate
- Positive vs negative sentiment
- Review conversion rate
- Appointment confirmation rate
- Click-through rate on links

## Smart Features

### 1. Suppression Rules
Never send if:
- Customer already left review (for review requests)
- Customer is repeat (configurable)
- Opt-out detected
- Negative sentiment in previous response
- Manual override set

### 2. Intelligent Timing
- Business hours only (9 AM - 6 PM)
- Adjust for time zones
- Skip holidays
- Respect "do not disturb" preferences

### 3. Context Awareness
- Include relevant job details
- Reference previous conversations
- Adjust tone based on customer history
- Personalize based on property type

### 4. A/B Test Automation
- Automatically split recipients 50/50
- Track performance metrics
- Statistical significance calculation
- Auto-promote winners after threshold
- Archive losing versions

## Implementation Architecture

### Database Schema
```sql
CREATE TABLE automated_messages (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    trigger_type ENUM('calendar', 'invoice', 'time', 'weather', 'gemini'),
    trigger_config JSONB,
    active BOOLEAN DEFAULT true
);

CREATE TABLE message_versions (
    id UUID PRIMARY KEY,
    message_id UUID REFERENCES automated_messages,
    version CHAR(1), -- 'A' or 'B'
    template TEXT,
    performance_metrics JSONB,
    is_winner BOOLEAN DEFAULT false
);

CREATE TABLE message_sends (
    id UUID PRIMARY KEY,
    message_id UUID REFERENCES automated_messages,
    version_id UUID REFERENCES message_versions,
    contact_id UUID REFERENCES contacts,
    sent_at TIMESTAMP,
    delivered BOOLEAN,
    response TEXT,
    sentiment ENUM('positive', 'negative', 'neutral')
);
```

### Trigger System
```python
class MessageTriggerService:
    def check_triggers(self):
        # Run every 15 minutes
        self.check_calendar_triggers()
        self.check_invoice_triggers()  
        self.check_time_based_triggers()
        self.check_weather_triggers()
        
    def queue_message(self, trigger, contact):
        # Check suppression rules
        if self.should_suppress(contact, trigger):
            return
            
        # Get A/B version
        version = self.get_test_version(trigger)
        
        # Personalize template
        message = self.personalize(version.template, contact)
        
        # Queue for sending
        campaign_service.send_message(message, contact)
```

## Success Metrics

### Core Metrics
- Review conversion rate: >30%
- Appointment confirmation rate: >80%
- Follow-up response rate: >40%
- A/B test velocity: 2-3 tests/week

### Optimization Goals
- Find optimal review request timing
- Maximize positive response rate
- Minimize opt-outs
- Increase customer satisfaction

## Integration Points

### Required Integrations
- **Google Calendar**: Event triggers
- **QuickBooks**: Invoice triggers
- **OpenPhone**: Message delivery
- **Weather API**: Condition triggers
- **Gemini**: Commitment detection
- **Google Business Profile**: Review detection

### Data Flow
1. Trigger detected (calendar, invoice, etc.)
2. Check suppression rules
3. Select A/B version
4. Personalize message
5. Queue for sending
6. Track delivery and response
7. Update performance metrics
8. Adjust A/B split if needed

## Future Enhancements

### Phase 2
- Multi-channel (SMS + Email)
- Dynamic timing optimization
- Sentiment-based branching
- Automated escalation paths

### Phase 3
- AI-generated message variations
- Predictive response modeling
- Cross-campaign learnings
- Industry benchmark comparisons

## Questions for Next Session

1. **Message Frequency**: Maximum messages per customer per week?
2. **A/B Testing**: How aggressive should testing be? Every message or selected?
3. **Review Incentives**: Ever offer discounts for reviews? Legal?
4. **Escalation**: If no response to follow-ups, when to call instead?
5. **Templates**: Want to start with proven templates or write from scratch?

---

*By using the campaign system for all automated messages, we gain powerful A/B testing and analytics capabilities that will continuously improve performance.*