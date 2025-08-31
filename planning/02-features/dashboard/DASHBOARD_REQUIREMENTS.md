# Dashboard Requirements - Attack-a-Crack v2

## Vision
The dashboard is the morning command center that surfaces money-making opportunities and critical actions in priority order, working backwards through the sales funnel from closed deals to new leads.

## Priority Framework (Working Backwards Through Funnel)

### 🔴 TIER 1: Money Waiting (Immediate Action Required)
1. **Approved Quotes Not Scheduled**
   - Display: Customer name, $ amount, days since approval
   - Action: One-click to jump into conversation and schedule
   - Alert: ⚠️ icon if >24 hours old

2. **Quotes to Generate/Send**
   - Display: Customer name, property address, requested service
   - Action: Click to open quote builder
   - Context: Show last conversation snippet

3. **Items Needing Scheduling**
   - Estimates to schedule
   - Follow-up appointments
   - Crew assignments for approved jobs

### 🟡 TIER 2: Daily Operations
4. **Today's Schedule**
   - Current day appointments with times
   - Crew assignments
   - Customer contact info with one-click call/text

5. **Week View**
   - Next 7 days calendar overview
   - Capacity indicators
   - Weather overlay on relevant days

6. **Follow-Up Automation Status**
   - Post-job follow-ups (Day 1: "How did everything go?")
   - Review requests (Day 7-10: Google review link)
   - Display: Pending, sent, responded counts

### 🟢 TIER 3: Growth & Intelligence
7. **Activity Feed (Toggleable)**
   - Default: Latest texts/calls from OpenPhone
   - Toggle: Latest emails (filtered for importance)
   - Show: Last 10-20 items with timestamps
   - Smart filtering: Customer communications prioritized

8. **Campaign Performance**
   - Yesterday's A/B test results
   - Response rates
   - Opt-outs
   - Next test scheduled

9. **Weather Forecast with Google Ads Control**
   - 5-10 day forecast for Greater Boston
   - Rain probability highlighted with ☔ icon
   - **Google Ads Quick Adjust**: [+$50] [+$100] [2x Rain Boost]
   - Current daily budget display
   - Alert: ⚠️ Heavy rain in 24-48 hours → Auto-add to TODO
   - Automated recommendation when rain >70% coming

10. **Financial Snapshot** (Future)
    - Month-to-date revenue
    - Comparison to previous month
    - Jobs completed this week
    - Outstanding invoices

### 🔵 TIER 4: Task Management
11. **Smart Todo List**
    - Auto-generated items:
      - Follow up on quote (3 days old)
      - Schedule approved job
      - Respond to review
    - Manual items: Quick add at top
    - Check off completed items
    - Carry over incomplete from yesterday

12. **Smart Email Highlights** (Future)
    - AI-filtered important emails only:
      - Customer communications
      - Quote approvals
      - Vendor/materials updates
      - Legal/compliance
      - B&I chapter communications
    - Learn from user interaction patterns

13. **Google Reviews** (Future)
    - New reviews needing response
    - Review velocity (reviews/week)
    - Overall rating trend

## User Interface Design

### Layout Concept (Mobile-First Fixed Layout)
```
┌─────────────────────────────────────────────────────────┐
│ ATTACK-A-CRACK DASHBOARD          [Weather: ☔ 70% Thurs]│
├─────────────────────────────────────────────────────────┤
│                                                           │
│ 💰 MONEY WAITING (3)                        [Quick Add+] │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ⚠️ Johnson - $4,500 approved 2 days ago [SCHEDULE]  │ │
│ │ ⚠️ Smith - Quote needed for foundation    [CREATE]   │ │
│ │ 📌 Martinez - Estimate tomorrow 10am      [DETAILS]  │ │
│ │ ✅ Quote approval from QuickBooks (Auto)  [TODO TOP] │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ 📅 TODAY'S SCHEDULE                    🗓️ THIS WEEK     │
│ ┌────────────────────┐  ┌────────────────────────────┐ │
│ │ 8am - Wilson        │  │ Mon: 3 jobs               │ │
│ │   Crack repair      │  │ Tue: 4 jobs (RAIN ☔)     │ │
│ │ 10am - Davis        │  │ Wed: 2 jobs               │ │
│ │   Estimate          │  │ Thu: 5 jobs               │ │
│ │ 2pm - Chen          │  │ Fri: 3 jobs               │ │
│ │   Bulkhead repair   │  │ Sat: 1 job                │ │
│ └────────────────────┘  └────────────────────────────┘ │
│                                                           │
│ 📋 MY TODOS (5)                     [+ Add Task]         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ☐ Call Johnson about scheduling                     │ │
│ │ ☐ Follow up with Martinez estimate                  │ │
│ │ ☐ Order bulkhead materials for Chen job             │ │
│ │ ✓ Send Day-1 follow-up to yesterday's jobs (AUTO)   │ │
│ │ ☐ Review campaign results from yesterday            │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ 📱 ACTIVITY        [Texts ↕️ Emails]                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 2m ago: "Is tomorrow still good for..." - Wilson    │ │
│ │ 15m ago: "Thanks for the quote!" - Johnson          │ │
│ │ 1h ago: Voicemail from (617) 555-0123               │ │
│ │ 2h ago: "Can you give me an estimate..." - New Lead │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ 📊 YESTERDAY'S CAMPAIGN                                  │
│ A/B Test #47: Foundation vs Waterproofing                │
│ Version A: 2.4% response | Version B: 3.1% response ⭐   │
│                                                           │
│ ☔ WEATHER ALERT: Heavy rain Thursday                     │
│ Google Ads: $200/day → [BOOST TO $400] [Custom Amount]   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Mobile Responsive Design
- Cards stack vertically on mobile
- Swipe between sections
- Critical actions (Money Waiting) always at top
- One-thumb reachable action buttons

## Data Sources & Integration Points

### Required Integrations
1. **QuickBooks**: Quote approvals, invoice status
2. **OpenPhone**: Recent activity, conversation snippets
3. **Google Calendar**: Schedule data
4. **Gmail API**: Smart filtered emails
5. **Weather API**: 5-10 day forecast
6. **Google My Business API**: Reviews (future)
7. **Google Ads API**: Spend recommendations (future)

### Real-time Updates
- WebSocket for instant updates when possible
- Polling fallback every 30 seconds for critical items
- Push notifications for money-waiting items

## Smart Features

### Auto-Generated Todos
Rules for automatic task creation:
- Quote older than 3 days → "Follow up with [customer]"
- Job completed yesterday → "Send day-1 follow-up with review request"
- Job completed 7 days ago (no review yet) → "Follow-up review request"
- Approved quote → "Schedule job for [customer]"
- Missed call from customer → "Return call to [customer]"
- QuickBooks quote approval email → ⭐ TOP PRIORITY TODO
- Heavy rain in 48 hours → "📈 Increase Google Ads spend"
- Exterior job with rain forecast → "⚠️ Contact [customer] to reschedule"
- Tomorrow's repair jobs → "Generate invoices for tomorrow's jobs" (6 AM)
- Gemini detects commitment → "Follow up with [customer] on [date]"

### Email Intelligence (Future)
Train on user behavior to identify important emails:
- Track which emails user opens from dashboard
- Learn sender patterns (customers, vendors, specific domains)
- Keyword detection (quote, approval, schedule, emergency)
- Ignore newsletters, promotions, automated emails

### Weather-Driven Actions
- Rain >70% probability → Auto-TODO: "📈 Increase Google Ads budget"
- Heavy rain warning → Dashboard alert + TODO: "Prepare for increased call volume"
- Extended dry spell → "Consider promotional campaign"
- Exterior job + rain → Auto-TODO: "Reschedule [customer]'s exterior work"

## Success Metrics

### MVP Metrics
- Time to identify money-waiting items: <2 seconds
- Actions to schedule approved job: 2 clicks max
- Dashboard load time: <1 second
- Todo completion rate: >80% daily

### Future Metrics
- Google review response rate improvement
- Email triage time reduction
- Revenue impact from weather-based ad adjustments

## Technical Implementation Notes

### Performance Requirements
- Initial load: <1 second
- Updates: Real-time where possible
- Mobile: Optimized for phone screens
- Offline: Cache last state, sync when connected

### Priority Implementation Order
1. Money Waiting section (quotes, scheduling)
2. Today's Schedule
3. Todo List
4. Activity Feed (texts only)
5. Week View
6. Campaign metrics
7. Weather
8. Email integration
9. Financial metrics
10. Google reviews

## Questions for Next Session

1. **Follow-up Timing**: You mentioned 7-10 days for review requests. Should we A/B test this timing?

2. **Email Filtering**: Should we start with a whitelist of important senders, or train the AI from your behavior?

3. **Todo Persistence**: Should incomplete todos carry over automatically, or require manual review?

4. **Weather Threshold**: At what rain probability should we recommend ad spend increases?

5. **Schedule View**: Do you need to see crew names on the schedule, or just job counts?

6. **Financial Metrics**: What specific KPIs matter most? Revenue? Job count? Average ticket?

7. **Activity Feed Depth**: How many recent items? 10? 20? Last 24 hours?

8. **Mobile vs Desktop**: What % of dashboard use will be mobile vs desktop?

---

*This dashboard design prioritizes revenue-generating activities and reduces the time to identify and act on money-waiting opportunities.*