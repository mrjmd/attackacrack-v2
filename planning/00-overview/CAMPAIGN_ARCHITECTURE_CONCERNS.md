# Campaign System Architecture Concerns

## The Challenge
Using the campaign system to power ALL automated messaging (appointment reminders, follow-ups, review requests, etc.) is powerful for DRY principles and A/B testing, but risks creating an overly complex system.

## Architectural Concerns

### 1. Trigger Complexity
**Current campaign triggers (simple):**
- Schedule for date/time
- Send to list
- A/B split

**Required triggers for automation (complex):**
- Calendar events (appointments, completions)
- Invoice states (sent, paid, overdue)
- Weather conditions
- Time-relative (X days after Y event)
- Gemini detection (commitments in conversation)
- Cascade triggers (if no response, then...)
- Conditional triggers (if customer has property value > X)

### 2. Risk of Over-Engineering
**Warning Signs:**
- Campaign system becomes too generic
- Configuration becomes programming
- Testing becomes nightmare
- Performance degradation
- Debugging difficulty

### 3. Potential Solutions

#### Option A: Layered Architecture
```
┌─────────────────────────────────┐
│   Automation Layer (Triggers)    │
├─────────────────────────────────┤
│   Campaign Engine (Core)         │
├─────────────────────────────────┤
│   Delivery Layer (SMS/Email)     │
└─────────────────────────────────┘
```

**Pros:**
- Separation of concerns
- Campaign engine stays simple
- Triggers are pluggable

**Cons:**
- More code
- Potential duplication

#### Option B: Plugin System
```python
class CampaignTrigger(ABC):
    @abstractmethod
    def should_fire(self, context) -> bool:
        pass

class CalendarCompletionTrigger(CampaignTrigger):
    def should_fire(self, context):
        return context.has_completed_job

class WeatherTrigger(CampaignTrigger):
    def should_fire(self, context):
        return context.rain_probability > 0.7
```

**Pros:**
- Extensible
- Testable
- Clear interfaces

**Cons:**
- Complexity in trigger combinations
- State management

#### Option C: Separate Systems with Shared Components
```
Marketing Campaigns → Campaign System
Automated Messages → Automation System
                    ↓
            Shared: A/B Testing, Analytics, Delivery
```

**Pros:**
- Clear boundaries
- Simpler systems
- Easier to reason about

**Cons:**
- Some duplication
- Harder to share learnings

### 4. Recommendation: Hybrid Approach

**Core Principle:** Start with Option C, refactor to Option A if needed

1. **Phase 1 (MVP):** 
   - Build simple automation system
   - Share only delivery infrastructure
   - Learn what's actually needed

2. **Phase 2:**
   - Extract common patterns
   - Build shared A/B testing service
   - Unify analytics

3. **Phase 3:**
   - If warranted, merge into unified system
   - Keep trigger plugins separate
   - Maintain clear boundaries

### 5. Design Principles

**DO:**
- Keep triggers simple and composable
- Make each trigger independently testable
- Use events/queues for loose coupling
- Maintain clear separation between marketing and transactional

**DON'T:**
- Build a "god system" that does everything
- Create complex configuration languages
- Mix marketing and transactional logic
- Sacrifice clarity for DRY

### 6. Technical Implementation Strategy

```python
# Shared services used by both systems
class ABTestService:
    """Shared A/B testing logic"""
    
class MessageDeliveryService:
    """Shared SMS/Email delivery"""
    
class AnalyticsService:
    """Shared tracking and reporting"""

# Marketing-specific
class MarketingCampaignService:
    """Traditional campaigns with lists"""
    
# Automation-specific  
class AutomatedMessageService:
    """Triggered transactional messages"""
    def __init__(self):
        self.triggers = [
            CalendarTrigger(),
            InvoiceTrigger(),
            WeatherTrigger()
        ]
```

### 7. Success Criteria

**Good Architecture Indicators:**
- New trigger types can be added in <1 hour
- Each component can be tested in isolation
- Performance remains constant as triggers grow
- Debugging is straightforward
- New developers understand system quickly

**Red Flags:**
- Cascading changes for simple features
- Trigger interactions become unpredictable
- Performance degradation
- Configuration requires documentation
- Bugs in one area affect others

## Decision Point [RESOLVED]

### Final Architecture Decision: Separate Services with Shared Components

Based on team review and v1 lessons learned, we will implement **two distinct services**:

1. **MarketingCampaignService** - For bulk marketing messages
   - A/B testing for templates
   - Daily limits (125 messages)
   - Business hours enforcement (9am-6pm ET)
   - Opt-out handling
   - List-based sending
   - Response tracking and analytics

2. **TransactionalNotificationService** - For automated business messages
   - Appointment reminders (1 day before)
   - Job completion follow-ups
   - Review requests
   - Payment reminders
   - MUST always deliver (no daily limits)
   - Immediate sending (no business hours restriction)
   - Higher priority in queue

### Shared Components
Both services will share these underlying components:
```python
class OpenPhoneDeliveryClient:
    """Handles actual SMS sending via OpenPhone API"""
    
class ABTestingEngine:
    """A/B testing logic for both marketing and transactional"""
    
class MessageAnalytics:
    """Unified analytics for all message types"""
    
class OptOutManager:
    """Central opt-out list management"""
```

### Job Completion Triggers (Critical Business Logic)
A job is marked complete when BOTH conditions are met:
1. The job's Google Calendar event has passed (end_time < now)
2. The job's QuickBooks invoice is marked as paid

```python
def is_job_complete(job) -> bool:
    """
    Job completion requires both calendar event completion 
    AND invoice payment. This triggers follow-up sequences.
    """
    calendar_complete = job.calendar_event.end_time < datetime.now()
    invoice_paid = job.invoice.status == 'paid'
    return calendar_complete and invoice_paid
```

### Why This Architecture?
- **Avoids "God System"**: Each service has clear, focused responsibility
- **Different Requirements**: Marketing has limits, transactional must always send
- **Easier Testing**: Each service can be tested independently
- **Clear Mental Model**: Developers know exactly where code belongs
- **Proven Pattern**: This separation is industry standard (SendGrid, Twilio, etc.)

---

*The campaign system architecture decision will significantly impact maintainability and development speed. Starting simple and refactoring based on real needs is lower risk than over-engineering from the start.*