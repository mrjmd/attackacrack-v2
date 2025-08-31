# Conversation View Requirements - Attack-a-Crack v2

## Vision
The conversation view is the command center for customer interactions, providing instant access to all context needed to close deals, schedule work, and deliver exceptional service - all without leaving the conversation.

## The Problem Today
Currently, when a text comes in, you need to:
- Switch to Google Maps to check location
- Search QuickBooks for customer history
- Check calendar for availability
- Look up property data separately
- Manually create quotes
- Copy/paste between systems

## The Solution: Context-Rich Sidebar

### Layout Concept
```
┌──────────────────────────────────┬────────────────────────────┐
│                                  │                            │
│         CONVERSATION             │      CONTEXT SIDEBAR       │
│                                  │                            │
│  [OpenPhone Message Thread]      │   [Smart Context Panel]    │
│                                  │                            │
│  Customer: "Can you fix my       │   📍 LOCATION              │
│  basement crack?"                │   42 Elm St, Newton MA     │
│                                  │   📏 12 min (4.2 mi)       │
│  You: "Absolutely! When works    │   [Get Directions]         │
│  for you?"                       │                            │
│                                  │   🏠 PROPERTY DATA         │
│  Customer: "Thursday?"           │   Built: 1965              │
│  [Photo of crack]                │   Value: $850,000          │
│                                  │   Sq Ft: 2,400             │
│  You: "I can do 10am or 2pm"    │   Basement: Yes            │
│                                  │   Last roof: Unknown       │
│                                  │                            │
│  [Type message...]               │   👤 CUSTOMER HISTORY      │
│  [📎] [📷] [📅] [💰] [🤖]        │   ✅ Existing customer     │
│                                  │   Last job: May 2023       │
│                                  │   Total spent: $3,500      │
│                                  │   [View Details]           │
│                                  │                            │
│                                  │   📅 APPOINTMENTS          │
│                                  │   None scheduled           │
│                                  │   [Schedule Now]           │
│                                  │                            │
│                                  │   💰 QUOTES/INVOICES       │
│                                  │   No open quotes           │
│                                  │   [Start Quote]            │
│                                  │                            │
│                                  │   🤖 AI ASSISTANT          │
│                                  │   [Draft Response]         │
│                                  │   [Extract Address]        │
│                                  │   [Analyze Photos]         │
└──────────────────────────────────┴────────────────────────────┘
```

## Sidebar Components (Priority Order)

### 1. 📍 Location & Directions
**Always Visible at Top**

**Data Shown:**
- Property address (extracted or confirmed)
- Distance from business (508 Boston Post Rd, Sudbury)
- Drive time with current traffic
- Map thumbnail (clickable for full view)

**Actions:**
- [Get Directions] - Opens in Google Maps
- [Street View] - See property exterior
- [Add to Route] - Optimize with other jobs

**Smart Features:**
- Auto-extract address from conversation
- Gemini highlights address mentions
- One-click confirmation if uncertain

### 2. 🏠 Property Intelligence
**From PropertyRadar Integration**

**Essential Data:**
- Year built (determines foundation type)
- Square footage
- Property value (for quote sizing)
- Basement (yes/no)
- Lot size (for drainage issues)
- Owner names (verify customer)

**Actionable Insights:**
- "Built 1965 - Likely poured concrete ✓"
- "High value property - Premium service opportunity"
- "Large lot - Check drainage patterns"

**Actions:**
- [Full Property Report]
- [View Similar Properties]
- [Check Permits] (future)

### 3. 👤 Customer Context
**Instant History Check**

**Customer Status:**
- 🆕 New customer
- ✅ Existing customer (show total history)
- ⚠️ Has open quote (X days old)
- 🔄 Has scheduled work
- ⭐ Left review previously

**Historical Data:**
- Previous jobs (with dates and amounts)
- Total lifetime value
- Average response time
- Preferred communication style
- Any notes or flags

**Actions:**
- [View Full History]
- [Add Note]
- [Flag for Follow-up]

### 4. 📅 Calendar History & Scheduling
**Full Calendar Context at a Glance**

**Past Jobs with This Customer:**
```
HISTORY:
✅ May 15, 2023 - Crack Repair ($2,400)
✅ Aug 3, 2022 - Assessment (Led to quote)
[View Details]
```

**Upcoming Appointments:**
```
SCHEDULED:
📅 Nov 20, 2024 - Assessment 10:00 AM
   Type: Foundation evaluation
   Location: 42 Elm St, Newton
   [View in Calendar] [Reschedule]
```

**Smart Scheduling:**
```
NEXT AVAILABLE SLOTS:
Thu 11/14: [10:00 AM] [2:00 PM]
Fri 11/15: [8:00 AM] [3:00 PM]
Mon 11/18: [9:00 AM] [1:00 PM]

[Suggest Times to Customer]
```

**Quick Actions:**
- [Schedule Assessment] - 30 min, purple
- [Schedule Repair] - 4 hr default, green
- [Check Full Calendar]
- [Send Calendar Invite]

**Related Jobs Nearby:**
```
OTHER JOBS IN AREA:
Tomorrow 2 PM - Smith (0.3 mi away)
[Add to Route] [Combine Trip]
```

### 5. 💰 Financial Status
**Quote & Invoice Quick View**

**Current Status:**
- Open quotes (with amounts and age)
- Unpaid invoices
- Payment history
- Credit status

**Quick Actions:**
- [Start New Quote] - Opens quote builder
- [Send Existing Quote]
- [Convert Quote to Invoice]
- [Process Payment]

**Smart Features:**
- Auto-suggest quote based on photos
- Price history for similar jobs
- Margin calculator

### 6. 🤖 AI Assistant (Gemini)
**Context-Aware Help**

**Automatic Actions:**
- Extract address from messages
- Identify job type from description
- Analyze crack photos for severity
- Detect scheduling preferences
- Flag urgent issues

**On-Demand Actions:**
- [Draft Response] - In your voice
- [Analyze Photos] - Damage assessment
- [Suggest Quote] - Based on description
- [Extract Details] - Pull all job info
- [Generate Summary] - For calendar event

**Smart Draft Responses (Full Messages Ready to Send):**
```
Customer: "The crack is getting worse"

AI DRAFT (Ready to copy/paste):
"I understand your concern. Water infiltration 
can worsen quickly. I have Thursday at 10am or 
2pm available for an assessment. The evaluation 
is free and takes about 30 minutes. Which works 
better for you?"

[Copy Message] [Edit Draft] [Regenerate]
```

**Personalization Features:**
- Learns your communication style
- Includes relevant context (customer name, history)
- Adjusts formality based on conversation
- Suggests appointment times from real calendar
- One tap to copy entire message

### 7. 📎 Media Gallery
**All Shared Media in One Place**

**Organization:**
- Photos from customer
- Photos from previous jobs
- Documents (quotes, invoices)
- Videos
- Voice messages

**Actions:**
- [Full Screen View]
- [Add to Quote]
- [Save to Job File]
- [Share with Team]

### 8. 🎯 Quick Actions Bar
**One-Click Common Tasks**

Bottom of sidebar:
```
[📅 Schedule] [💰 Quote] [📝 Note] [📞 Call] 
[✅ Complete] [🔄 Follow-up] [🚫 Not Interested]
```

## Dynamic Sidebar Behavior

### Context-Aware Display
**Sidebar adapts based on conversation state:**

1. **New Lead** - Emphasize property data and scheduling
2. **Existing Customer** - Show history prominently
3. **Has Open Quote** - Quote status and follow-up tools
4. **Job Scheduled** - Countdown and prep info
5. **Job Complete** - Payment and review request tools

### Real-Time Updates
- Property data loads asynchronously
- Calendar availability refreshes live
- Quote status updates instantly
- New photos appear immediately

### Mobile Experience (Critical)
**Challenge:** Can't be a sidebar on mobile

**Solution: Context Drawer**
- Small floating button during conversation
- One tap opens full-screen context overlay
- Swipe between context sections
- Quick return to conversation

**Mobile Priority Order:**
1. Customer status (new/existing)
2. Calendar (history & upcoming)
3. Location & directions
4. Quick actions (Schedule, Quote)
5. AI draft responses (copy button)
6. Property data
7. Financial status

**Key Mobile Features:**
- Copy AI draft with one tap
- Click address to open Maps
- Tap phone number to call
- Swipe gestures between sections
- Large buttons for common actions

## Integration Requirements

### Data Sources
1. **PropertyRadar** - Property intelligence
2. **Google Maps** - Distance, directions, traffic
3. **Google Calendar** - Availability, scheduling
4. **QuickBooks** - Customer history, financial
5. **OpenPhone** - Conversation, media
6. **Gemini** - AI analysis, drafting
7. **Internal CRM** - Notes, flags, history

### Performance Requirements
- Initial sidebar load: <2 seconds
- Property data: <3 seconds
- AI suggestions: <5 seconds
- All data cached after first load

## Smart Features

### 1. Address Intelligence
**Multi-Source Verification:**
- Extract from conversation via Gemini
- Verify against PropertyRadar
- Confirm with customer if uncertain
- Remember for future conversations

### 2. Photo Analysis
**Automatic Assessment:**
- Crack width estimation
- Water damage detection
- Structural concern flagging
- Before/after comparison

### 3. Conversation Coaching
**AI Suggestions Based on Patterns:**
- "Customer seems price-sensitive, emphasize value"
- "They mentioned urgency 3 times, offer sooner slot"
- "Previous customer was happy, ask for referral"

### 4. Predictive Actions
**Anticipate Next Steps:**
- Customer asks about timing → Show calendar
- Mentions specific problem → Pull similar quotes
- Sends photos → Start damage assessment
- Discusses price → Show financing options

## Success Metrics

### Efficiency Metrics
- Time to schedule: <2 minutes (from 10+)
- Time to quote: <5 minutes (from 20+)
- Context switches eliminated: 90%
- Information at hand: 100%

### Quality Metrics
- Accurate address extraction: >95%
- Relevant AI suggestions: >80%
- Customer satisfaction: Increased response speed
- Close rate improvement: >15%

## Implementation Phases

### MVP (Must Have)
1. Property address and map
2. Basic customer history
3. Calendar availability
4. Quote/invoice status
5. Simple AI drafts

### Phase 2 (Should Have)
1. Full PropertyRadar integration
2. Photo analysis
3. Smart scheduling
4. Conversation coaching
5. Media gallery

### Phase 3 (Could Have)
1. Route optimization
2. Predictive actions
3. Advanced AI features
4. Team collaboration
5. Offline mode

## Questions for Next Session

1. **Sidebar Position**: Right side always? Or configurable?
2. **Information Priority**: What's MOST important to see first?
3. **AI Drafts**: How much automation vs suggestions?
4. **Mobile Usage**: What % of conversations on phone vs desktop?
5. **Team Access**: Will Mike (technician) use this view too?
6. **Custom Fields**: Any business-specific data to track?

---

*The conversation view sidebar transforms every interaction into an information-rich, action-oriented experience that drives faster closes and better service.*