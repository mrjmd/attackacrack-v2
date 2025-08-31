# QuickBooks Discovery Session Insights

*Captured from deep dive conversation on August 30, 2025*

## 🔍 Key Discoveries Through Conversation

### The Quote-to-Text Workflow (Manual Today)
**Current Process:**
1. Create quote in QuickBooks (manual data entry from OpenPhone)
2. Send quote via QuickBooks
3. **Immediately** (within 5 min) switch to OpenPhone
4. Send manual text: "Hey, I just sent that quote over..."
5. Include example photo for crack repairs
6. Mention next available appointment slot

**Pain Points:**
- Double work (QuickBooks then OpenPhone)
- Copy/paste from text threads
- Manual customer creation
- Time-consuming

**Dream State:**
- One button: Create quote + send + auto-text
- AI analyzes photos to suggest pricing
- Auto-include relevant job type photos
- Pull actual availability from calendar
- Total time: 2 minutes (vs 15+ today)

### The Money Tracking Problem
**Current State: "It's all in my head"**
- No system for tracking who's paid
- Manual checking in QuickBooks
- Often forgets to invoice (especially builders)
- Sometimes a week+ before sending invoice

**Real Example:**
- Recently lost 4 days on approved quote
- Customer approved via email
- User never saw it
- Customer had to follow up: "Do you still want the job?"

**Critical Scenarios:**
1. **Builder jobs** - Not on-site for payment
2. **Forgotten invoices** - No reminder system
3. **Unpaid tracking** - Mental overhead

**Solution Needs:**
- Dashboard alerts for unpaid >2 days
- Automatic invoice generation
- Remote payment flags
- Aggressive reminders

### Pricing Intelligence Insights
**Not standardized but has patterns:**
- Base rates exist
- Adjustments based on:
  - Property value (wealthy appearance)
  - Customer age
  - Financial situation mentions
  - Competition for the job
- "It's an art not a science"
- AI could learn patterns over time

### QuickBooks Replacement Vision
**The Frustration:**
- Slow app
- Monthly fees
- Overly complex for needs
- Simple needs, complex tool

**The Challenge:**
- Accountant uses it
- Banking integration
- Tax reporting
- Payment processing hardware

**The Strategy:**
- MVP: Deep integration
- Phase 2: Build own quote/invoice system
- Phase 3: Evaluate full replacement
- Not short/medium term priority

**Key Question:** "Which is more work - deep integration or building our own?"

### Financial Insights Desired
**What matters (not MVP):**
- This week vs last week revenue
- This month vs last month
- Outstanding money (unpaid invoices)
- Quote conversion rate
- Open estimate value
- Average job value trends
- Expense categorization
- Cost-cutting suggestions

### Critical Process Insights
**Quote Approval Flow:**
- Email from QuickBooks often missed
- Sometimes customer texts approval
- Sometimes just clicks button
- No consistent notification system

**Invoice Generation:**
- Currently manual day-of
- Wants automatic morning generation
- Convert quotes → invoices for that day's jobs
- Ready when technician arrives

**Payment Methods:**
- Card to technician (auto-tracked)
- Cash/check (manual marking)
- Remote payment links

## 🎯 MVP vs Future Clarifications

### MVP Must-Haves
- Quote approval detection
- Basic customer sync (eliminate copy/paste)
- Morning invoice generation
- Unpaid job alerts

### Phase 2 Additions
- Auto-text after quote
- AI pricing suggestions
- Photo library by job type
- Two-way sync
- Financial dashboard

### Long-Term Vision
- Full QuickBooks replacement
- Direct banking integration
- Expense tracking
- Complete financial management

## 💡 Architectural Implications

### Integration Depth
Given eventual replacement desire:
- Don't over-invest in deep integration
- Build own models from start
- Use QuickBooks as data source only
- Plan for gradual replacement

### Data Flow
```
OpenPhone → CRM → QuickBooks
         ↓
    Our Database
         ↓
   Future: Replace QB
```

### Key Decision Point
**Build vs Integrate Trade-off:**
- Integration: Faster MVP, technical debt
- Build: Slower MVP, future-proof
- Hybrid: Minimal integration + own models

## 🔴 Never Forget
- Quote approvals = money waiting
- Every manual step = lost time
- Payment tracking chaos = cash flow issues
- The goal: Make money collection automatic

---

*This discovery session revealed that QuickBooks is both critical (today) and frustrating (always). The integration must solve immediate pains while planning for eventual independence.*